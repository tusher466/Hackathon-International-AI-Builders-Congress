"""Diagnosis Agent."""
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
from knowledge.retriever import retrieve, build_retrieval_query, format_citations

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "diagnosis.md"


def _load_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are Diagnosis Agent"


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


class DiagnosisAgent:
    def __init__(self):
        self.prompt = _load_prompt()
        self.llm = get_llm()
        self.settings = get_settings()

    async def run(self, state: FactoryState) -> FactoryState:
        start = time.time()
        alert = state.get("alert", {})
        machine_context = state.get("machine_context", {})

        # Build retrieval query
        retrieval_query = state.get("retrieval_query") or build_retrieval_query(alert)
        # If supervisor asked for expanded query, expand
        if state.get("supervisor", {}).get("reason", "").lower().find("expanded") != -1:
            retrieval_query += " expanded query with failure logs and related symptoms"

        state["retrieval_query"] = retrieval_query

        # Retrieve evidence
        import asyncio
        loop = asyncio.get_event_loop()
        evidence = await loop.run_in_executor(None, lambda: retrieve(retrieval_query, machine_type=alert.get("machine_type"), k=self.settings.RETRIEVAL_K))
        citations_formatted = format_citations(evidence)

        # Build user message
        user_msg = f"""
Alert: {json.dumps(alert, default=str)[:2000]}
Machine context: {json.dumps(machine_context, default=str)[:2000]}
Retrieval query: {retrieval_query}
Evidence ({len(evidence)} chunks):
{json.dumps(evidence, default=str)[:4000]}
Citations: {citations_formatted}

Produce JSON with root_cause, confidence, reasoning, citations, evidence_strength.
If evidence score below threshold ({self.settings.RETRIEVAL_SCORE_THRESHOLD}), say insufficient evidence and lower confidence.
"""

        try:
            resp_text = await loop.run_in_executor(None, lambda: self.llm.complete(self.prompt, user_msg, json_mode=True))
            parsed = _parse_json(resp_text)
            if not parsed or "root_cause" not in parsed:
                for _ in range(self.settings.LLM_MAX_RETRIES):
                    resp_text = await loop.run_in_executor(None, lambda: self.llm.complete(self.prompt, user_msg + "\nOutput valid JSON only", json_mode=True))
                    parsed = _parse_json(resp_text)
                    if parsed and "root_cause" in parsed:
                        break
                if not parsed or "root_cause" not in parsed:
                    parsed = self._rule_based(alert, evidence)
                    state.setdefault("errors", []).append("diagnosis_agent: LLM invalid JSON, fallback rule-based")

        except Exception as e:
            logger.exception(f"Diagnosis agent error {e}")
            parsed = self._rule_based(alert, evidence)
            state.setdefault("errors", []).append(f"diagnosis_agent exception {e}")

        duration = int((time.time() - start) * 1000)

        # Validate citations indices
        citations = parsed.get("citations", [])
        # Ensure citations are within evidence range
        valid_citations = [c for c in citations if isinstance(c, int) and 0 <= c < len(evidence)]
        parsed["citations"] = valid_citations

        # Check evidence weak
        avg_score = sum([ev.get("score", 0) for ev in evidence]) / max(len(evidence), 1)
        if avg_score < self.settings.RETRIEVAL_SCORE_THRESHOLD:
            if parsed.get("confidence", 1.0) > 0.5:
                parsed["confidence"] = 0.35
                parsed["reasoning"] = f"Insufficient evidence (avg score {avg_score:.2f} below threshold {self.settings.RETRIEVAL_SCORE_THRESHOLD}). " + parsed.get("reasoning", "")
                parsed["evidence_strength"] = "weak"

        # Store
        state["evidence"] = evidence
        state["diagnosis"] = parsed
        state["citations_formatted"] = citations_formatted

        trace_event = {
            "agent": "diagnosis",
            "ts": datetime.now(timezone.utc),
            "input_summary": f"Query {retrieval_query[:100]} evidence {len(evidence)}",
            "output_summary": f"Root cause {parsed.get('root_cause')} conf {parsed.get('confidence')}",
            "reasoning": parsed.get("reasoning", "")[:500],
            "duration_ms": duration,
        }
        state.setdefault("trace", []).append(trace_event)

        # supervisor next
        conf = parsed.get("confidence", 0.5)
        if conf < 0.5:
            next_node = "planner"  # still go, but supervisor may loop
        else:
            next_node = "planner"

        state["supervisor"] = {
            "next_node": next_node,
            "iterations": state.get("supervisor", {}).get("iterations", 0) + 1,
            "escalate": False,
            "reason": f"Diagnosis completed confidence {conf}",
        }

        return state

    def _rule_based(self, alert: Dict[str, Any], evidence: list) -> Dict[str, Any]:
        mtype = alert.get("machine_type")
        top_sensors = alert.get("top_sensors", [])
        sensor_names = [s.get("name", "") for s in top_sensors[:3]]
        if mtype == "turbofan":
            if alert.get("predicted_rul") is not None and alert["predicted_rul"] < 30:
                root = "HPC degradation critical, RUL low"
            else:
                root = "Compressor fouling"
        elif mtype == "secom":
            root = f"Semiconductor process drift, sensors {', '.join(sensor_names)} deviating"
        elif mtype == "bosch":
            root = f"Assembly quality issue, torque or fixture, sensors {', '.join(sensor_names)}"
        else:
            root = "Process anomaly"

        # citations: use first evidence if available
        citations = [0] if evidence else []
        return {
            "root_cause": root,
            "confidence": 0.75,
            "reasoning": f"Rule-based diagnosis: top sensors {sensor_names} indicate {root}. Evidence {evidence[0]['text'][:200] if evidence else 'none'}",
            "citations": citations,
            "evidence_strength": "moderate" if evidence else "weak"
        }
