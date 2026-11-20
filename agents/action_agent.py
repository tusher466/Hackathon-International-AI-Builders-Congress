"""Action Agent."""
from __future__ import annotations

import json
import time
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from agents.state import FactoryState
from agents.llm import get_llm
from config.settings import get_settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "action.md"


def _load_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Action Agent"


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


class ActionAgent:
    def __init__(self):
        self.prompt = _load_prompt()
        self.llm = get_llm()
        self.settings = get_settings()

    async def run(self, state: FactoryState) -> FactoryState:
        start = time.time()
        alert = state.get("alert", {})
        diagnosis = state.get("diagnosis", {})
        plan = state.get("plan", {})

        user_msg = f"""
Alert: {json.dumps(alert, default=str)[:2000]}
Diagnosis: {json.dumps(diagnosis, default=str)[:2000]}
Plan: {json.dumps(plan, default=str)[:2000]}
Citations: {state.get('citations_formatted', [])[:5]}

Generate repair instructions. Must include LOTO reminder if physical intervention.
If requires_approval true, note awaiting approval.
"""

        try:
            import asyncio
            loop = asyncio.get_event_loop()
            resp_text = await loop.run_in_executor(None, lambda: self.llm.complete(self.prompt, user_msg, json_mode=True))
            parsed = _parse_json(resp_text)
            if not parsed or "repair_instructions" not in parsed:
                for _ in range(self.settings.LLM_MAX_RETRIES):
                    resp_text = await loop.run_in_executor(None, lambda: self.llm.complete(self.prompt, user_msg + "\nOutput valid JSON only", json_mode=True))
                    parsed = _parse_json(resp_text)
                    if parsed and "repair_instructions" in parsed:
                        break
                if not parsed or "repair_instructions" not in parsed:
                    parsed = self._rule_based(alert, diagnosis, plan)
                    state.setdefault("errors", []).append("action_agent: invalid JSON fallback")
        except Exception as e:
            logger.exception(f"Action agent error {e}")
            parsed = self._rule_based(alert, diagnosis, plan)
            state.setdefault("errors", []).append(f"action_agent exception {e}")

        duration = int((time.time() - start) * 1000)

        # Import ticketing and notifier lazily to avoid circular imports
        # Ticket creation will be done in graph wrapper or here? We'll create dict and let graph handle actual DB save?
        # For simplicity, we prepare ticket data here, but actual creation in actions/ticketing.py via function that needs DB session.
        # We'll just generate ticket_id and instructions; the pipeline will persist.

        ticket_id = str(uuid.uuid4())
        # If approval required, ticket status awaiting_approval
        if plan.get("requires_approval"):
            ticket_status = "awaiting_approval"
        else:
            ticket_status = "open"

        # Build action output
        action_output = {
            "repair_instructions": parsed.get("repair_instructions", ""),
            "ticket_id": ticket_id,
            "ticket_status": ticket_status,
            "safety_warnings": parsed.get("safety_warnings", ["LOTO required"]),
            "required_tools": parsed.get("required_tools", []),
            "expected_result": parsed.get("expected_result", ""),
            "notifications": parsed.get("notifications", []),
        }

        # Ensure LOTO reminder present if physical action
        physical_actions = ["schedule_maintenance", "stop_machine", "inspect_quality", "reroute_production", "reduce_load"]
        if plan.get("action_type") in physical_actions:
            instr = action_output["repair_instructions"].lower()
            if "lockout" not in instr and "loto" not in instr:
                # prepend safety reminder
                action_output["repair_instructions"] = "1. **Safety**: Follow lockout/tagout (LOTO) procedure per safety_loto.md before any physical intervention. Wear PPE.\n" + action_output["repair_instructions"]

        state["action_output"] = action_output

        trace_event = {
            "agent": "action",
            "ts": datetime.now(timezone.utc),
            "input_summary": f"Plan {plan.get('action_type')} requires_approval {plan.get('requires_approval')}",
            "output_summary": f"Ticket {ticket_id} status {ticket_status} instructions generated",
            "reasoning": f"Generated repair instructions for {plan.get('action_type')} with safety warnings",
            "duration_ms": duration,
        }
        state.setdefault("trace", []).append(trace_event)

        # Approval state
        if plan.get("requires_approval"):
            state["approval"] = {
                "status": "pending",
                "decided_by": None,
                "ts": None,
                "comment": None,
            }
        else:
            state["approval"] = {
                "status": "not_required",
            }

        state["supervisor"] = {
            "next_node": "end",
            "iterations": state.get("supervisor", {}).get("iterations", 0) + 1,
            "escalate": False,
            "reason": f"Action completed ticket {ticket_id}",
        }

        return state

    def _rule_based(self, alert: Dict[str, Any], diagnosis: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        action_type = plan.get("action_type", "schedule_maintenance")
        root_cause = diagnosis.get("root_cause", "unknown")

        instructions_map = {
            "stop_machine": f"1. **Safety**: Follow lockout/tagout (LOTO) procedure per safety_loto.md before any physical intervention. Wear PPE: safety glasses, gloves, face shield if hot oil.\n2. Review diagnosis: {root_cause}\n3. Stop machine via controlled stop command\n4. Isolate: disconnect main breaker, close pneumatic valve, bleed pressure, verify zero energy with multimeter\n5. Perform repair per manual: for HPC degradation, replace shroud segments, check tip clearance with feeler gauge\n6. Verify: run 10 cycles at reduced load, monitor s9 stability, ensure RUL recovery\n7. Document, remove LOTO, restore energy\n8. Expected: health score returns >80, RUL >50",
            "reduce_load": f"1. Safety: No LOTO required for load reduction, but LOTO for subsequent maintenance\n2. Reduce load by 20-30% via control system\n3. Monitor sensors {alert.get('top_sensors')}\n4. Schedule maintenance at next window per {root_cause}\n5. Verify RUL stabilizes",
            "schedule_maintenance": f"1. **Safety**: LOTO required per safety_loto.md for physical maintenance\n2. Diagnosis: {root_cause}\n3. Gather tools: multimeter, torque analyzer as per manual\n4. Perform maintenance: e.g., compressor wash 80psi 2gpm 5min for fouling, or calibrate MFCs\n5. Run 3 dummy wafers or 5 test cycles\n6. Verify sensor deviations return to baseline, anomaly <0.3",
            "inspect_quality": f"1. **Safety**: LOTO for station access per safety_loto.md, wear safety glasses\n2. Diagnosis: {root_cause}\n3. Inspect quality: first article inspection\n4. For torque drift: calibrate to 5Nm ±0.1Nm using torque analyzer\n5. For fixture wear: replace plate if groove >0.2mm, align with dial indicator\n6. Run 5 test parts, measure torque\n7. Expected: defect prob <0.3",
        }

        instructions = instructions_map.get(action_type, instructions_map["schedule_maintenance"])

        return {
            "repair_instructions": instructions,
            "safety_warnings": ["LOTO required for physical intervention", "Never bypass safety interlocks", "Wear PPE"],
            "required_tools": ["multimeter", "torque analyzer", "dial indicator", "compressor wash rig", "oil filler"],
            "expected_result": "Sensor readings nominal, anomaly <0.3, health score >80",
            "notifications": [f"Ticket for {alert.get('machine_id')} {action_type} created"]
        }
