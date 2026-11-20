"""Supervisor Agent."""
from __future__ import annotations

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from agents.state import FactoryState
from agents.llm import get_llm
from config.settings import get_settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "supervisor.md"


def _load_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Supervisor Agent"


def _parse_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        import re
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}


class SupervisorAgent:
    def __init__(self):
        self.prompt = _load_prompt()
        self.llm = get_llm()
        self.settings = get_settings()

    async def run(self, state: FactoryState) -> FactoryState:
        start = time.time()
        alert = state.get("alert", {})
        diagnosis = state.get("diagnosis")
        plan = state.get("plan")
        trace = state.get("trace", [])
        supervisor_prev = state.get("supervisor", {})
        iterations = supervisor_prev.get("iterations", 0)

        # Enforce max iteration limit
        if iterations >= self.settings.MAX_AGENT_ITERATIONS:
            next_node = "end"
            reason = f"Max iterations {self.settings.MAX_AGENT_ITERATIONS} reached, ending"
            escalate = True
        else:
            # Determine next based on state
            next_node, reason, escalate = self._determine_next(state)

        duration = int((time.time() - start) * 1000)

        trace_event = {
            "agent": "supervisor",
            "ts": datetime.now(timezone.utc),
            "input_summary": f"Iteration {iterations} alert {alert.get('alert_id')}, diagnosis conf {diagnosis.get('confidence') if diagnosis else 'none'}",
            "output_summary": f"Next node {next_node} escalate {escalate}",
            "reasoning": reason,
            "duration_ms": duration,
        }
        state.setdefault("trace", []).append(trace_event)

        state["supervisor"] = {
            "next_node": next_node,
            "iterations": iterations + 1,
            "escalate": escalate,
            "reason": reason,
        }

        return state

    def _determine_next(self, state: FactoryState) -> tuple[str, str, bool]:
        trace = state.get("trace", [])
        alert = state.get("alert", {})
        diagnosis = state.get("diagnosis")
        plan = state.get("plan")
        action_output = state.get("action_output")

        # Find last agent from trace
        last_agent = None
        if trace:
            # last trace might be supervisor itself, need previous
            # get last non-supervisor
            for t in reversed(trace):
                if t.get("agent") != "supervisor":
                    last_agent = t.get("agent")
                    break

        # After monitor
        if last_agent is None or last_agent == "monitor":
            # check monitor decision stored in machine_context
            ctx = state.get("machine_context", {})
            decision = ctx.get("monitor_decision", "escalate")
            if decision == "escalate":
                return "diagnosis", f"Monitor escalated, routing to diagnosis", False
            else:
                return "end", f"Monitor decision {decision}, ending", False

        if last_agent == "diagnosis":
            if not diagnosis:
                return "diagnosis", "No diagnosis yet, retry", False
            conf = diagnosis.get("confidence", 0.5)
            iterations = state.get("supervisor", {}).get("iterations", 0)
            # If low confidence and first time, loop back with expanded query
            if conf < 0.5 and iterations < 2:
                return "diagnosis", f"Diagnosis confidence {conf} low, looping back to diagnosis with expanded query", False
            elif conf < 0.5:
                return "needs_human_review", f"Diagnosis confidence still low {conf} after retries, escalate to human", True
            else:
                return "planner", f"Diagnosis confidence {conf} sufficient, routing to planner", False

        if last_agent == "planner":
            if not plan:
                return "planner", "No plan yet", False
            if plan.get("action_type") == "monitor_only":
                return "end", "Planner chose monitor_only, ending", False
            return "action", f"Planner chose {plan.get('action_type')}, routing to action", False

        if last_agent == "action":
            return "end", "Action completed, ending run", False

        # default
        return "end", "No further steps, ending", False
