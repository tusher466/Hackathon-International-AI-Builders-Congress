"""Run demo: starts everything, injects faults, prints agent chain."""
from __future__ import annotations

import asyncio
import logging
import json
import time
from datetime import datetime, timezone

from config.settings import get_settings
from core.pipeline import get_pipeline
from storage.db import init_db
from knowledge.vector_store import get_vector_store
from knowledge.ingest_docs import ingest_manuals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo():
    settings = get_settings()
    print("=== Factory Brain Demo ===")
    print(f"Settings: STREAM_BACKEND={settings.STREAM_BACKEND} LLM_MODE={settings.LLM_MODE} (mock={settings.is_mock_llm})")

    init_db()
    print("DB initialized")

    # Ensure vector store has docs
    store = get_vector_store()
    print(f"Vector store count before: {store.count()}")
    if store.count() == 0:
        print("Ingesting manuals...")
        count = ingest_manuals("./data/manuals", reset=False)
        print(f"Ingested {count} chunks, count now {store.count()}")
    else:
        print(f"Vector store already has {store.count()} chunks")

    # Init pipeline
    pipeline = get_pipeline()
    await pipeline.init()
    print("Pipeline initialized, starting stream...")

    # Subscribe to events to print chain
    bus = pipeline.event_bus
    q = bus.subscribe()

    # Task to print events
    async def event_printer():
        while True:
            try:
                env = await q.get()
                etype = env["type"]
                payload = env["payload"]
                if etype in ("reading",):
                    # skip frequent reading prints, just occasional
                    if payload["machine_id"] == "TURBO-01" and payload["sequence"] % 20 == 0:
                        print(f"[{etype}] {payload['machine_id']} seq {payload['sequence']}")
                else:
                    print(f"\n>>> EVENT {etype} @ {env['ts']}")
                    print(json.dumps(payload, default=str)[:1000])
                    if etype == "agent_step":
                        print(f"  Agent: {payload.get('agent')} | {payload.get('output_summary')}")
                    if etype == "diagnosis_ready":
                        print(f"  Diagnosis: {payload.get('diagnosis')}")
                        print(f"  Citations: {payload.get('citations')}")
                    if etype == "plan_ready":
                        print(f"  Plan: {payload.get('plan')}")
                    if etype == "ticket_updated":
                        print(f"  Ticket {payload.get('ticket_id')} status {payload.get('status')}")
                    if etype == "approval_required":
                        print(f"  !!! APPROVAL REQUIRED for {payload.get('alert_id')} action {payload.get('action_type')}")

            except Exception as e:
                logger.warning(f"Event printer error {e}")
                break

    printer_task = asyncio.create_task(event_printer())

    # Wait steady state
    print("\nWaiting 5 seconds for steady state...")
    await asyncio.sleep(5)

    # Inject fault on TURBO-01 degradation
    print("\n=== Injecting degradation fault on TURBO-01 ===")
    pipeline.inject_fault("TURBO-01", "degradation", magnitude=2.0, duration_ticks=50, sensors=["s7", "s9", "s11", "s15"])
    await asyncio.sleep(1)

    # Inject drift on SECOM-01
    print("\n=== Waiting 3 sec then injecting drift on SECOM-01 ===")
    await asyncio.sleep(3)
    pipeline.inject_fault("SECOM-01", "drift", magnitude=1.5, duration_ticks=40, sensors=["s12", "s45", "s100"])

    print("\nWaiting 15 seconds for alerts and agent chain to complete...")
    await asyncio.sleep(15)

    # Print metrics
    metrics = pipeline.get_metrics()
    print("\n=== Metrics Impact ===")
    print(json.dumps(metrics, indent=2))

    # Print pending approvals
    from actions.approval import list_pending
    pendings = list_pending()
    print(f"\nPending approvals: {len(pendings)}")
    for p in pendings:
        print(f" - {p.alert_id} ticket {p.ticket_id}")

    # Demonstrate approval flow for first pending
    if pendings:
        first = pendings[0]
        print(f"\nApproving first pending {first.alert_id}...")
        from actions.approval import approve
        await approve(first.alert_id, decided_by="demo_user", comment="Approved in demo")
        print("Approved, waiting 3 sec for resume...")
        await asyncio.sleep(3)

    print("\nDemo complete, shutting down")
    printer_task.cancel()
    try:
        await printer_task
    except asyncio.CancelledError:
        pass

    await pipeline.shutdown()

    # Final metrics
    print("\n=== Final Metrics ===")
    print(json.dumps(pipeline.get_metrics(), indent=2))


if __name__ == "__main__":
    asyncio.run(demo())
