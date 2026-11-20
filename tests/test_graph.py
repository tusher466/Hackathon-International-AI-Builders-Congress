"""Full graph run from alert to ticket."""
import pytest
from knowledge.vector_store import get_vector_store
from knowledge.ingest_docs import ingest_manuals
from agents.graph import run_alert
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_full_graph_run():
    store = get_vector_store()
    if store.count() == 0:
        ingest_manuals("./data/manuals")

    alert = {
        "alert_id": "test-alert-001",
        "machine_id": "TURBO-01",
        "machine_type": "turbofan",
        "ts": datetime.now(timezone.utc),
        "alert_type": "degradation",
        "severity": "critical",
        "confidence": 0.85,
        "anomaly_score": 0.9,
        "predicted_rul": 18,
        "defect_probability": None,
        "top_sensors": [{"name": "s7", "deviation": 4.2, "direction": "up"}],
        "feature_snapshot": {"s7_mean": 2.5},
        "status": "open",
    }

    machine_context = {
        "machine_id": "TURBO-01",
        "health_score": 30,
        "status": "critical",
        "recent_readings_count": 100,
    }

    final_state = await run_alert(alert, machine_context)

    assert final_state is not None
    assert "trace" in final_state
    assert len(final_state["trace"]) >= 3  # monitor, diagnosis, planner, action, supervisor steps
    assert "diagnosis" in final_state
    assert "plan" in final_state
    assert "action_output" in final_state
    # Check citations present
    assert "evidence" in final_state
    assert len(final_state["evidence"]) > 0
    # Check ticket created in action_output
    assert final_state["action_output"].get("ticket_id") is not None
    # Check LOTO in instructions
    instr = final_state["action_output"].get("repair_instructions", "")
    assert "LOTO" in instr or "lockout" in instr.lower()
