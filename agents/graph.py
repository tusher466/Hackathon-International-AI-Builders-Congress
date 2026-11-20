"""LangGraph StateGraph for Factory Brain."""
from __future__ import annotations

import logging
import asyncio
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import FactoryState
from agents.monitor_agent import MonitorAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.planner_agent import PlannerAgent
from agents.action_agent import ActionAgent
from agents.supervisor_agent import SupervisorAgent

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Instantiate agents globally
_monitor_agent = MonitorAgent()
_diagnosis_agent = DiagnosisAgent()
_planner_agent = PlannerAgent()
_action_agent = ActionAgent()
_supervisor_agent = SupervisorAgent()


# Node wrappers
async def monitor_node(state: FactoryState) -> FactoryState:
    return await _monitor_agent.run(state)


async def diagnosis_node(state: FactoryState) -> FactoryState:
    return await _diagnosis_agent.run(state)


async def planner_node(state: FactoryState) -> FactoryState:
    return await _planner_agent.run(state)


async def action_node(state: FactoryState) -> FactoryState:
    return await _action_agent.run(state)


async def supervisor_node(state: FactoryState) -> FactoryState:
    return await _supervisor_agent.run(state)


def supervisor_router(state: FactoryState) -> str:
    """Conditional edge driven by supervisor.next_node."""
    sup = state.get("supervisor", {})
    next_node = sup.get("next_node", "end")
    # Map to graph node names
    mapping = {
        "monitor": "monitor",
        "diagnosis": "diagnosis",
        "planner": "planner",
        "action": "action",
        "end": END,
        "needs_human_review": "needs_human_review",
    }
    # Special case: needs_human_review goes to action to create ticket with that status? But we'll route to action
    # actually spec says escalate to human with needs_human_review ticket
    if next_node == "needs_human_review":
        # still go to action node but action will handle
        # Or go to END after marking
        # We'll route to action to create ticket then END
        # For simplicity map to a custom end handling
        return "action"
    return mapping.get(next_node, END)


def build_graph():
    """Build StateGraph."""

    workflow = StateGraph(FactoryState)

    workflow.add_node("monitor", monitor_node)
    workflow.add_node("diagnosis", diagnosis_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("action", action_node)
    workflow.add_node("supervisor", supervisor_node)

    # Edges
    workflow.add_edge(START, "monitor")
    workflow.add_edge("monitor", "supervisor")

    # Supervisor conditional
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "monitor": "monitor",
            "diagnosis": "diagnosis",
            "planner": "planner",
            "action": "action",
            END: END,
        },
    )

    workflow.add_edge("diagnosis", "supervisor")
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("action", END)

    # Checkpointer for resumability after approval
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


# Global compiled graph
_graph_app = None


def get_graph():
    global _graph_app
    if _graph_app is None:
        _graph_app = build_graph()
    return _graph_app


async def run_alert(alert: Dict[str, Any], machine_context: Optional[Dict[str, Any]] = None) -> FactoryState:
    """Run full graph from alert to ticket. Returns final state."""

    settings = get_settings()
    machine_context = machine_context or {}

    initial_state: FactoryState = {
        "alert": alert,
        "machine_context": machine_context,
        "evidence": [],
        "diagnosis": {},
        "plan": {},
        "action_output": {},
        "approval": {},
        "trace": [],
        "supervisor": {"next_node": "monitor", "iterations": 0, "escalate": False, "reason": "start"},
        "errors": [],
        "citations_formatted": [],
        "retrieval_query": "",
    }

    graph = get_graph()
    # Use alert_id as thread_id for checkpointing
    config = {"configurable": {"thread_id": alert.get("alert_id", "default")}}

    final_state = initial_state
    try:
        # astream for step tracking? but use invoke
        result = await graph.ainvoke(initial_state, config=config)
        final_state = result
    except Exception as e:
        logger.exception(f"Graph run failed: {e}")
        final_state["errors"].append(f"graph_run failed {e}")

    # Post-processing: if needs_human_review flagged
    sup = final_state.get("supervisor", {})
    if sup.get("escalate") and sup.get("next_node") == "needs_human_review":
        # Mark action output ticket status needs_human_review
        if "action_output" not in final_state:
            final_state["action_output"] = {}
        final_state["action_output"]["ticket_status"] = "needs_human_review"

    return final_state


async def resume_after_approval(alert_id: str, decision: str, decided_by: str = "human", comment: Optional[str] = None) -> FactoryState:
    """Resume graph after approval. For simplicity, we just update approval state and continue.

    In real checkpoint resume, we would load checkpoint and continue. Here we fake: if approved, set approval approved and mark ticket progressed.
    If rejected, mark ticket rejected.
    """
    # For now return state indicating resumed
    # This function will be called from approval.py action which has access to DB but not graph state.
    # We'll need to fetch previous traces from DB? For simplicity we return minimal state.

    # In a more complete implementation, we'd load from checkpointer and invoke with new input.
    # We'll implement simple logic: if approved, create final state with approval approved

    final_state: FactoryState = {
        "alert": {"alert_id": alert_id},
        "machine_context": {},
        "evidence": [],
        "diagnosis": {},
        "plan": {},
        "action_output": {},
        "approval": {
            "status": decision,  # approved or rejected
            "decided_by": decided_by,
            "comment": comment,
        },
        "trace": [],
        "supervisor": {"next_node": "end", "iterations": 0, "escalate": False, "reason": f"Resumed after {decision} by {decided_by}"},
        "errors": [],
    }
    return final_state
