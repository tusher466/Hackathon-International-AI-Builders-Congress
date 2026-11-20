"""Control routes (demo and ops)."""
from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import verify_api_key
from core.pipeline import get_pipeline
from config.settings import get_settings
from storage.db import get_db
from knowledge.vector_store import get_vector_store

router = APIRouter(prefix="/control", dependencies=[Depends(verify_api_key)])


@router.post("/stream/start")
async def start_stream():
    pipeline = get_pipeline()
    await pipeline.start_stream()
    return {"status": "started"}


@router.post("/stream/stop")
async def stop_stream():
    pipeline = get_pipeline()
    await pipeline.stop_stream()
    return {"status": "stopped"}


@router.post("/stream/pause")
def pause_stream():
    pipeline = get_pipeline()
    pipeline.pause_stream()
    return {"status": "paused"}


@router.post("/stream/resume")
def resume_stream():
    pipeline = get_pipeline()
    pipeline.resume_stream()
    return {"status": "resumed"}


class InjectFaultBody(BaseModel):
    machine_id: str
    fault_type: str  # drift, spike, stuck, degradation, defect_burst
    magnitude: float
    duration_ticks: int
    sensors: Optional[List[str]] = None


@router.post("/inject-fault")
async def inject_fault(body: InjectFaultBody):
    valid_types = {"drift", "spike", "stuck", "degradation", "defect_burst"}
    if body.fault_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid fault_type, must be one of {valid_types}")
    pipeline = get_pipeline()
    # inject_fault is synchronous for injection, but event publish needs async
    pipeline.inject_fault_sync(body.machine_id, body.fault_type, body.magnitude, body.duration_ticks, body.sensors)
    # publish event explicitly
    from core.event_bus import get_event_bus
    bus = get_event_bus()
    await bus.publish("fault_injected", {
        "machine_id": body.machine_id,
        "fault_type": body.fault_type,
        "magnitude": body.magnitude,
        "duration_ticks": body.duration_ticks,
        "sensors": body.sensors,
    })
    return {"status": "injected", "machine_id": body.machine_id, "fault_type": body.fault_type}


@router.post("/reset")
async def reset_pipeline():
    pipeline = get_pipeline()
    await pipeline.reset()
    return {"status": "reset"}


@router.get("/health")
def control_health():
    """Extra alias? But /api/v1/health is separate, this is control."""
    return {"status": "control ok"}
