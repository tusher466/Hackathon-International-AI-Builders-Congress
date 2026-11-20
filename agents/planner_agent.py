"""Planner Agent."""
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

PROMPT_PATH = Path(__file__).parent / "prompts" / "planner.md"


def _load_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Planner Agent"


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


class PlannerAgent:
    def __init__(self):
        self.prompt = _load_prompt()
        self.llm = get_llm()
        self.settings = get_settings()

    async def run(self, state: FactoryState) -> FactoryState:
        start = time.time()
        alert = state.get("alert", {})
        diagnosis = state.get("diagnosis", {})
        machine_context = state.get("machine_context", {})

        user_msg = f"""
Alert: {json.dumps(alert, default=str)[:2000]}
Diagnosis: {json.dumps(diagnosis, default=str)[:2000]}
Machine context: {json.dumps(machine_context, default=str)[:1000]}
Citations: {state.get('citations_formatted', [])[:5]}

Choose action_type from [schedule_maintenance, reduce_load, reroute_production, stop_machine, inspect_quality, monitor_only]
Set risk_level and requires_approval. Provide estimated_impact with heuristic formulas.
"""

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            resp_text = await loop.run_in_executor(None, lambda: self.llm.complete(self.prompt, user_msg, json_mode=True))
            parsed = _parse_json(resp_text)
            if not parsed or "action_type" not in parsed:
                for _ in range(self.settings.LLM_MAX_RETRIES):
                    resp_text = await loop.run_in_executor(None, lambda: self.llm.complete(self.prompt, user_msg + "\nOutput valid JSON only", json_mode=True))
                    parsed = _parse_json(resp_text)
                    if parsed and "action_type" in parsed:
                        break
                if not parsed or "action_type" not in parsed:
                    parsed = self._rule_based(alert, diagnosis)
                    state.setdefault("errors", []).append("planner_agent: invalid JSON fallback")
        except Exception as e:
            logger.exception(f"Planner error {e}")
            parsed = self._rule_based(alert, diagnosis)
            state.setdefault("errors", []).append(f"planner_agent exception {e}")

        duration = int((time.time() - start) * 1000)

        # Validate
        valid_actions = ["schedule_maintenance", "reduce_load", "reroute_production", "stop_machine", "inspect_quality", "monitor_only"]
        if parsed.get("action_type") not in valid_actions:
            parsed["action_type"] = "schedule_maintenance"
        if parsed.get("risk_level") not in ("low", "medium", "high"):
            parsed["risk_level"] = "medium"

        # Ensure requires_approval logic
        if parsed["action_type"] in ("stop_machine", "reroute_production") or parsed.get("risk_level") == "high":
            parsed["requires_approval"] = True

        # Ensure estimated_impact exists and has heuristic note
        if "estimated_impact" not in parsed:
            parsed["estimated_impact"] = self._estimate_impact(alert, diagnosis)

        state["plan"] = parsed

        trace_event = {
            "agent": "planner",
            "ts": datetime.now(timezone.utc),
            "input_summary": f"Diagnosis {diagnosis.get('root_cause')} alert {alert.get('severity')}",
            "output_summary": f"Action {parsed.get('action_type')} risk {parsed.get('risk_level')} approval {parsed.get('requires_approval')}",
            "reasoning": parsed.get("rationale", "")[:500],
            "duration_ms": duration,
        }
        state.setdefault("trace", []).append(trace_event)

        # supervisor next
        state["supervisor"] = {
            "next_node": "action",
            "iterations": state.get("supervisor", {}).get("iterations", 0) + 1,
            "escalate": False,
            "reason": f"Planner chose {parsed.get('action_type')}",
        }

        return state

    def _rule_based(self, alert: Dict[str, Any], diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        severity = alert.get("severity", "medium")
        mtype = alert.get("machine_type")
        conf = diagnosis.get("confidence", 0.7) if diagnosis else alert.get("confidence", 0.5)

        # Determine action
        if severity == "critical":
            action = "stop_machine"
            risk = "high"
            requires = True
        elif severity == "high" and mtype == "turbofan":
            # if RUL <20 stop else reduce_load
            rul = alert.get("predicted_rul", 100)
            if rul is not None and rul < 20:
                action = "stop_machine"
                risk = "high"
                requires = True
            else:
                action = "reduce_load"
                risk = "medium"
                requires = False
        elif mtype == "bosch":
            action = "inspect_quality"
            risk = "low" if severity in ("low", "medium") else "high"
            requires = risk == "high"
        else:
            action = "schedule_maintenance"
            risk = "medium"
            requires = False

        impact = self._estimate_impact(alert, diagnosis)

        return {
            "action_type": action,
            "steps": [
                f"Review diagnosis: {diagnosis.get('root_cause', 'unknown')}",
                "Prepare tools per manual",
                "Execute maintenance",
                "Verify fix"
            ],
            "risk_level": risk,
            "requires_approval": requires,
            "rationale": f"Rule-based: severity {severity}, RUL {alert.get('predicted_rul')}, defect {alert.get('defect_probability')}, confidence {conf}",
            "estimated_impact": impact
        }

    def _estimate_impact(self, alert: Dict[str, Any], diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        severity = alert.get("severity", "medium")
        sev_weights = {"low": 0.5, "medium": 1, "high": 2, "critical": 4}
        weight = sev_weights.get(severity, 1)
        conf = alert.get("confidence", 0.7)

        downtime = weight * 60 + conf * 100
        defects = 0
        if alert.get("defect_probability"):
            defects = int(alert["defect_probability"] * 50)
        elif alert.get("machine_type") == "secom":
            defects = int((alert.get("anomaly_score", 0) or 0) * 20)

        energy = 0
        anomaly = alert.get("anomaly_score", 0) or 0
        if alert.get("machine_type") == "turbofan" and alert.get("predicted_rul") is not None:
            energy = anomaly * 10 + (100 - alert["predicted_rul"]) / 10
        else:
            energy = anomaly * 10 + 5

        return {
            "downtime_avoided_minutes": round(downtime, 1),
            "defects_prevented": defects,
            "energy_saved_kwh": round(energy, 1),
            "note": "estimates based on heuristic formulas: downtime = severity_weight*60 + confidence*100, defects = defect_prob*50, energy = anomaly*10 + ..."
        }
