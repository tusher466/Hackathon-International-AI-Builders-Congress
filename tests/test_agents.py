"""Each agent node with mock LLM."""
import pytest
from agents.monitor_agent import MonitorAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.planner_agent import PlannerAgent
from agents.action_agent import ActionAgent
from agents.supervisor_agent import SupervisorAgent
from knowledge.ingest_docs import ingest_manuals
from knowledge.vector_store import get_vector_store


@pytest.mark.asyncio
async def test_monitor_agent():
    agent = MonitorAgent()
    state = {
        "alert": {"alert_id": "test", "machine_id": "TURBO-01", "machine_type": "turbofan", "severity": "high", "confidence": 0.8, "alert_type": "degradation"},
        "machine_context": {"health_score": 40},
        "trace": [],
        "supervisor": {"iterations": 0},
        "errors": [],
    }
    new_state = await agent.run(state)
    assert "monitor" in [t["agent"] for t in new_state["trace"]]
    assert new_state["supervisor"]["next_node"] in ("diagnosis", "end")


@pytest.mark.asyncio
async def test_diagnosis_agent():
    store = get_vector_store()
    if store.count() == 0:
        ingest_manuals("./data/manuals")

    agent = DiagnosisAgent()
    state = {
        "alert": {"alert_id": "test2", "machine_id": "TURBO-01", "machine_type": "turbofan", "severity": "critical", "confidence": 0.9, "alert_type": "degradation", "predicted_rul": 15, "top_sensors": [{"name": "s7", "deviation": 4.2}]},
        "machine_context": {},
        "trace": [],
        "supervisor": {"iterations": 0},
        "errors": [],
    }
    new_state = await agent.run(state)
    assert "diagnosis" in new_state
    assert "root_cause" in new_state["diagnosis"]
    assert new_state["diagnosis"]["confidence"] > 0


@pytest.mark.asyncio
async def test_planner_agent():
    agent = PlannerAgent()
    state = {
        "alert": {"alert_id": "test3", "machine_id": "TURBO-01", "machine_type": "turbofan", "severity": "critical", "confidence": 0.9, "predicted_rul": 15, "alert_type": "degradation"},
        "machine_context": {},
        "diagnosis": {"root_cause": "HPC degradation", "confidence": 0.8, "reasoning": "test"},
        "trace": [],
        "supervisor": {"iterations": 1},
        "errors": [],
    }
    new_state = await agent.run(state)
    assert "plan" in new_state
    assert "action_type" in new_state["plan"]
    assert new_state["plan"]["risk_level"] in ("low", "medium", "high")


@pytest.mark.asyncio
async def test_action_agent():
    agent = ActionAgent()
    state = {
        "alert": {"alert_id": "test4", "machine_id": "TURBO-01", "machine_type": "turbofan", "severity": "critical", "confidence": 0.9, "alert_type": "degradation"},
        "diagnosis": {"root_cause": "HPC degradation", "confidence": 0.8, "reasoning": "test"},
        "plan": {"action_type": "stop_machine", "risk_level": "high", "requires_approval": True, "rationale": "critical"},
        "trace": [],
        "supervisor": {"iterations": 2},
        "errors": [],
    }
    new_state = await agent.run(state)
    assert "action_output" in new_state
    assert "repair_instructions" in new_state["action_output"]
    # Check LOTO reminder
    assert "LOTO" in new_state["action_output"]["repair_instructions"] or "lockout" in new_state["action_output"]["repair_instructions"].lower()


@pytest.mark.asyncio
async def test_supervisor_agent():
    agent = SupervisorAgent()
    state = {
        "alert": {"alert_id": "test5"},
        "machine_context": {"monitor_decision": "escalate"},
        "trace": [{"agent": "monitor"}],
        "supervisor": {"iterations": 1},
        "errors": [],
    }
    new_state = await agent.run(state)
    assert "supervisor" in new_state
    assert "next_node" in new_state["supervisor"]
