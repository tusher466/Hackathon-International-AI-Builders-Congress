"""LLM wrapper with mock fallback."""
from __future__ import annotations

import json
import logging
import random
from typing import Optional, Dict, Any

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Try import anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except Exception:
    ANTHROPIC_AVAILABLE = False

# Path to prompts? Not needed here

class LLMWrapper:
    """Single wrapper with method complete(system, user, json_mode=False)."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        if ANTHROPIC_AVAILABLE and self.settings.ANTHROPIC_API_KEY and not self.settings.is_mock_llm:
            try:
                self.client = anthropic.Anthropic(api_key=self.settings.ANTHROPIC_API_KEY)
                logger.info(f"Anthropic client initialized model={self.settings.LLM_MODEL}")
            except Exception as e:
                logger.warning(f"Anthropic init failed: {e}, using mock")
                self.client = None

    def _mock_complete(self, system: str, user: str, json_mode: bool = False) -> str:
        """Deterministic mock responses based on prompt content."""
        # Lowercase user for detection
        lower_sys = system.lower()
        lower_user = user.lower()

        # Determine which agent based on system prompt keywords
        # Monitor agent
        if "monitor" in lower_sys:
            # Parse alert severity if present in user
            # Mock logic: if critical/high -> escalate, low low -> watch
            if "critical" in lower_user or "high" in lower_user:
                decision = "escalate"
                reason = "High severity alert with significant deviation requires further investigation"
            elif "low" in lower_user and ("0.2" in lower_user or "0.3" in lower_user):
                decision = "watch"
                reason = "Low severity low confidence alert, monitor for trend"
            else:
                decision = "escalate"
                reason = "Alert shows meaningful deviation, should be diagnosed"

            resp = {
                "decision": decision,
                "reason": reason,
                "confidence": 0.85 if decision == "escalate" else 0.6
            }
            return json.dumps(resp)

        # Diagnosis agent
        if "diagnosis" in lower_sys:
            # Check if insufficient evidence phrase
            # We'll extract top sensors and make root cause
            if "turbo" in lower_user or "turbofan" in lower_user:
                if "rul" in lower_user and ("20" in lower_user or "15" in lower_user or "critical" in lower_user):
                    root = "HPC degradation and bearing wear, critical RUL"
                elif "fouling" in lower_user or "s7" in lower_user:
                    root = "Compressor fouling due to dirt accumulation"
                else:
                    root = "Turbofan degradation - likely compressor fouling"
            elif "secom" in lower_user:
                if "pressure" in lower_user or "s12" in lower_user:
                    root = "Chamber pressure excursion due to O-ring leak"
                elif "gas" in lower_user or "mfc" in lower_user:
                    root = "Gas flow calibration drift, MFC issue"
                else:
                    root = "Semiconductor process drift, etch chamber variation"
            elif "bosch" in lower_user:
                if "torque" in lower_user:
                    root = "Torque tool calibration drift"
                elif "fixture" in lower_user:
                    root = "Fixture wear exceeding 0.2mm"
                else:
                    root = "Assembly line quality defect risk - torque and fixture"
            else:
                root = "Process anomaly with multiple sensor deviations"

            # Citations: mock indices 1,2
            resp = {
                "root_cause": root,
                "confidence": 0.78,
                "reasoning": f"Based on top sensors and evidence, root cause identified as {root}. Retrieval shows similar incidents with matching symptoms. See citations.",
                "citations": [0, 1],
                "evidence_strength": "moderate"
            }
            # If user mentions insufficient evidence scenario, lower confidence
            if "weak" in lower_user or "low score" in lower_user:
                resp["confidence"] = 0.35
                resp["reasoning"] = "Evidence is weak, retrieval score below threshold, insufficient evidence to confirm root cause, but preliminary indication points to " + root
                resp["evidence_strength"] = "weak"
            return json.dumps(resp)

        # Planner
        if "planner" in lower_sys:
            # Choose action type based on content
            action_type = "schedule_maintenance"
            risk = "medium"
            requires_approval = False
            if "critical" in lower_user or "failure_risk" in lower_user or "stop" in lower_user:
                action_type = "stop_machine"
                risk = "high"
                requires_approval = True
            elif "medium" in lower_user and "turbo" in lower_user:
                action_type = "reduce_load"
                risk = "medium"
            elif "defect" in lower_user:
                action_type = "inspect_quality"
                risk = "low"
            elif "anomaly" in lower_user and "secom" in lower_user:
                action_type = "schedule_maintenance"
                risk = "medium"
            elif "reroute" in lower_user:
                action_type = "reroute_production"
                risk = "high"
                requires_approval = True

            # Estimate impact using heuristic formulas documented in process_control_spc.md
            # Use simple deterministic formulas
            # downtime_avoided = severity_weight*60 + confidence*100
            # We'll parse severity weight
            sev_weight = 1
            if "critical" in lower_user:
                sev_weight = 4
            elif "high" in lower_user:
                sev_weight = 2
            elif "medium" in lower_user:
                sev_weight = 1
            else:
                sev_weight = 0.5

            conf = 0.78
            downtime = sev_weight * 60 + conf * 100
            defects = 12 if "bosch" in lower_user else 0
            if "defect" in lower_user:
                defects = int(conf * 50)
            energy = conf * 10 + 5

            # For turbofan, add RUL component if present
            if "turbo" in lower_user:
                energy += 10

            resp = {
                "action_type": action_type,
                "steps": [
                    f"Review diagnosis for {root if 'root' in locals() else 'identified cause'}",
                    "Prepare required tools per manual",
                    "Execute maintenance action as per procedure",
                    "Verify fix via sensor monitoring"
                ],
                "risk_level": risk,
                "requires_approval": requires_approval,
                "rationale": f"Chose {action_type} with risk {risk} based on severity and evidence. Action aligns with manual procedures.",
                "estimated_impact": {
                    "downtime_avoided_minutes": round(downtime, 1),
                    "defects_prevented": defects,
                    "energy_saved_kwh": round(energy, 1),
                    "note": "estimates based on heuristic formulas"
                }
            }
            return json.dumps(resp)

        # Action agent
        if "action" in lower_sys or "repair" in lower_sys:
            # Generate plain-language repair instructions
            resp = {
                "repair_instructions": "1. **Safety**: Follow lockout/tagout (LOTO) procedure per safety_loto.md before any physical intervention. Wear PPE: safety glasses, gloves, face shield if hot oil.\n2. Review diagnosis and top sensors showing deviation.\n3. Gather required tools: per manual (multimeter, torque analyzer, oil filler, wash rig as applicable).\n4. Isolate machine: stop via controlled stop, disconnect breaker, verify zero energy.\n5. Perform repair per manual: e.g., for compressor fouling, water wash 80psi 2gpm 5min; for torque drift, calibrate to 5Nm ±0.1Nm; for fixture wear, replace plate and align with dial indicator.\n6. Verify fix: run 5 test cycles or dummy wafers, monitor sensor stability, ensure anomaly score <0.3.\n7. Document completion, remove LOTO lock, restore energy, resume production.\n8. Expected result: sensor deviations return to baseline, health score improves to >80.",
                "safety_warnings": ["LOTO required", "Hot oil hazard if applicable", "Never bypass safety interlocks"],
                "required_tools": ["multimeter", "torque analyzer", "dial indicator", "oil filler", "compressor wash rig"],
                "expected_result": "Sensor readings return to nominal, anomaly score drops, RUL recovers, defect probability <0.3"
            }
            return json.dumps(resp)

        # Supervisor
        if "supervisor" in lower_sys:
            # Simple router mock
            # Decide next based on user content keywords
            # If mentions monitor done, next is diagnosis, etc.
            if "monitor" in lower_user and "escalate" in lower_user:
                next_node = "diagnosis"
            elif "diagnosis" in lower_user and "confidence" in lower_user:
                next_node = "planner"
            elif "planner" in lower_user:
                next_node = "action"
            else:
                next_node = "end"
            resp = {
                "next_node": next_node,
                "reason": f"Supervisor routing to {next_node} based on state",
                "iterations": 1,
                "escalate": False
            }
            return json.dumps(resp)

        # Chat / RAG assistant (Factory Brain Ask)
        if "factory brain" in lower_sys or "answer the user question" in lower_sys or "context" in lower_user and "question" in lower_user:
            # Try to extract question and context
            # Provide deterministic mock for known questions, else summarize context
            if "line 3" in lower_user and ("stop" in lower_user or "2 am" in lower_user or "2am" in lower_user):
                return ("Line 3 stopped at 2AM on 2024-02-18 due to torque tool failure at station 4 [1]. "
                        "Logs show torque variance rising for 2 days before. The insert had exceeded its 5000 cycle life at 5230 cycles [2]. "
                        "Fix was replacement, 45 minutes downtime. Similar to current BOSCH torque deviation alerts. "
                        "Citations: [1] Line 3 Incident 2024-02, [2] BOSCH-TOOL-04 Tooling Manual.")
            if "bottleneck" in lower_user or "slowing" in lower_user or "units lost" in lower_user:
                return ("Current bottlenecks are machines with health_score <80 and open alerts. "
                        "Check /bottlenecks endpoint for live calculation. Example: BOSCH-02 on LINE-C with torque tool worn causing 124 units lost per hour [1]. "
                        "Recommended action: replace tool insert per manual.")
            if "fail" in lower_user and ("most likely" in lower_user or "week" in lower_user or "will fail" in lower_user):
                return ("Based on latest health scores and RUL predictions: machine with lowest health_score and critical alerts is highest risk. "
                        "TURBO machines with bearing wear pattern show RUL 30-50h at critical threshold [1]. "
                        "Check /machines sorted by health_score asc and check RUL <50 indicates high risk [2].")
            if "xyz" in lower_user or "unicorn" in lower_user:
                return "Not enough evidence in the manuals or logs to answer this question. The knowledge base was searched but no relevant passages were found with sufficient similarity."
            # Generic mock using context: extract first citation excerpt if present
            # Look for Source: patterns in user prompt
            # Return with citations
            # Simple heuristic: if context contains bearing, mention it
            if "bearing" in lower_user or "vibration" in lower_user:
                return ("Based on retrieved manuals [1]: Vibration increase >3 sigma on bearing sensors with concomitant core temperature rise indicates early bearing wear. "
                        "Recommended action: reduce load, inspect within 12h, RUL typically 30-50h at this stage [1][2]. "
                        "Check TURBO-03 health gauge and alert detail for top sensors.")
            if "torque" in lower_user:
                return ("According to BOSCH-TOOL-04 [1]: When torque exceeds 2.5 sigma above baseline for >20 cycles, inspect insert for wear. "
                        "Typical life 5000 cycles. Continued use increases defect rate by 12% per day [1]. "
                        "Current BOSCH-02 shows 2.9 sigma deviation, indicating tool wear [2].")
            # Fallback generic
            # Try to include some context excerpt from user (first 200 chars of context)
            ctx_snippet = user[:300].split("Context:")[-1][:200] if "Context:" in user else ""
            return (f"Based on available manuals and logs: {ctx_snippet[:150]}... "
                    f"For question '{user.split('Question:')[1].split(chr(10))[0][:80] if 'Question:' in user else user[:80]}', "
                    f"the system searched {lower_user.count('source')} sources. "
                    f"Key finding: anomalies are triggered when sensor deviation exceeds 2.5 sigma [1]. "
                    f"Check alerts page and machine health charts for related incidents [2].")

        # Default fallback
        return json.dumps({"message": "mock response", "system": system[:50], "user": user[:100]})

    def complete(self, system: str, user: str, json_mode: bool = False) -> str:
        """Complete with system and user prompts.

        Returns raw string response (JSON if json_mode).
        """
        if self.settings.is_mock_llm or self.client is None:
            return self._mock_complete(system, user, json_mode=json_mode)

        try:
            # Use anthropic Messages API
            # If json_mode, add instruction to output JSON
            sys_prompt = system
            if json_mode:
                sys_prompt += "\nYou must output valid JSON only, no extra text."

            response = self.client.messages.create(
                model=self.settings.LLM_MODEL,
                max_tokens=1024,
                system=sys_prompt,
                messages=[{"role": "user", "content": user}],
            )
            # Extract text
            text_blocks = [block.text for block in response.content if hasattr(block, "text")]
            text = "".join(text_blocks)
            return text
        except Exception as e:
            logger.warning(f"Anthropic call failed: {e}, falling back to mock")
            return self._mock_complete(system, user, json_mode=json_mode)


# Singleton
_global_llm: Optional[LLMWrapper] = None


def get_llm() -> LLMWrapper:
    global _global_llm
    if _global_llm is None:
        _global_llm = LLMWrapper()
    return _global_llm
