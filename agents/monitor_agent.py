"""Monitor Agent."""
from __future__ import annotations

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

from agents.state import FactoryState, TraceEvent
from agents.llm import get_llm
from config.settings import get_settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "monitor.md"


def _load_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Monitor Agent"


def _parse_json_response(text: str) -> Dict[str, Any]:
    # Try to extract JSON
    try:
        return json.loads(text)
    except Exception:
        # try find JSON block
        import re
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    # fallback rule-based
    return {}


class MonitorAgent:
    def __init__(self):
        self.prompt = _load_prompt()
        self.llm = get_llm()
        self.settings = get_settings()

    async def run(self, state: FactoryState) -> FactoryState:
        start = time.time()
        alert = state.get("alert", {})
        machine_context = state.get("machine_context", {})

        user_msg = f"""
Alert: {json.dumps(alert, default=str)[:2000]}
Machine context: {json.dumps(machine_context, default=str)[:2000]}
Decide ignore/watch/escalate.
"""

        try:
            resp_text = await self._call_llm(self.prompt, user_msg)
            parsed = _parse_json_response(resp_text)
            if not parsed or "decision" not in parsed:
                # retry up to 2 times
                for attempt in range(self.settings.LLM_MAX_RETRIES):
                    resp_text = await self._call_llm(self.prompt, user_msg + "\n\nPrevious output invalid, output valid JSON only")
                    parsed = _parse_json_response(resp_text)
                    if parsed and "decision" in parsed:
                        break
                if not parsed or "decision" not in parsed:
                    # fallback rule-based
                    parsed = self._rule_based(alert)
                    state.setdefault("errors", []).append("monitor_agent: LLM invalid JSON, fallback to rule-based")

            decision = parsed.get("decision", "escalate")
            reason = parsed.get("reason", "No reason provided")
            confidence = parsed.get("confidence", 0.7)

            # Ensure valid decision
            if decision not in ("ignore", "watch", "escalate"):
                decision = "escalate"

        except Exception as e:
            logger.exception(f"Monitor agent error: {e}")
            parsed = self._rule_based(alert)
            decision = parsed["decision"]
            reason = parsed["reason"]
            confidence = parsed["confidence"]
            state.setdefault("errors", []).append(f"monitor_agent: exception {e}")

        duration = int((time.time() - start) * 1000)

        # Update trace
        trace_event = {
            "agent": "monitor",
            "ts": datetime.now(timezone.utc),
            "input_summary": f"Alert {alert.get('alert_id')} severity {alert.get('severity')}",
            "output_summary": f"Decision {decision} confidence {confidence}",
            "reasoning": reason,
            "duration_ms": duration,
        }
        state.setdefault("trace", []).append(trace_event)
        state["supervisor"] = {
            "next_node": "diagnosis" if decision == "escalate" else "end",
            "iterations": state.get("supervisor", {}).get("iterations", 0) + 1,
            "escalate": False,
            "reason": f"Monitor decision {decision}: {reason}",
        }
        # Store monitor result in state
        state["machine_context"] = {**machine_context, "monitor_decision": decision, "monitor_reason": reason}

        return state

    async def _call_llm(self, system: str, user: str) -> str:
        # Run in threadpool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.llm.complete(system, user, json_mode=True))

    def _rule_based(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        severity = alert.get("severity", "low")
        confidence = alert.get("confidence", 0.5)
        if severity in ("critical", "high"):
            return {"decision": "escalate", "reason": f"High severity {severity} with confidence {confidence}, requires escalation", "confidence": 0.9}
        if severity == "low" and confidence < 0.5:
            return {"decision": "watch", "reason": f"Low severity low confidence ({confidence}), monitor trend", "confidence": 0.6}
        return {"decision": "escalate", "reason": f"Alert severity {severity} needs diagnosis", "confidence": 0.7}
