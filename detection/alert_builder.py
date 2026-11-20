"""Combine model outputs into Alert."""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any

from config.settings import get_settings
from ingestion.schemas import SensorReading

logger = logging.getLogger(__name__)


class AlertBuilder:
    """Builds Alert dict with deterministic severity rules and cooldown."""

    def __init__(self):
        self.settings = get_settings()
        # cooldown tracked per (machine_id, alert_type) -> remaining readings count before next alert allowed
        self._cooldown_counters: Dict[tuple[str, str], int] = {}

    def _decrement_cooldowns(self) -> None:
        for key in list(self._cooldown_counters.keys()):
            self._cooldown_counters[key] = max(0, self._cooldown_counters[key] - 1)

    def should_suppress(self, machine_id: str, alert_type: str) -> bool:
        key = (machine_id, alert_type)
        remaining = self._cooldown_counters.get(key, 0)
        return remaining > 0

    def _set_cooldown(self, machine_id: str, alert_type: str) -> None:
        key = (machine_id, alert_type)
        self._cooldown_counters[key] = self.settings.ALERT_COOLDOWN_READINGS

    def _determine_severity_and_type(
        self,
        anomaly_score: Optional[float],
        predicted_rul: Optional[float],
        defect_prob: Optional[float],
        machine_type: str,
    ) -> tuple[str, str, float]:
        """Returns (alert_type, severity, confidence). Deterministic rules from settings."""
        s = self.settings
        # Default
        alert_type = "anomaly"
        severity = "low"
        confidence = 0.0

        # Check each signal
        candidates = []

        if anomaly_score is not None:
            # anomaly severity
            if anomaly_score >= s.ANOMALY_THRESHOLD_CRITICAL:
                sev = "critical"
            elif anomaly_score >= s.ANOMALY_THRESHOLD_HIGH:
                sev = "high"
            elif anomaly_score >= s.ANOMALY_THRESHOLD_MEDIUM:
                sev = "medium"
            elif anomaly_score >= s.ANOMALY_THRESHOLD_LOW:
                sev = "low"
            else:
                sev = None
            if sev:
                candidates.append(("anomaly", sev, anomaly_score))

        if predicted_rul is not None and machine_type == "turbofan":
            if predicted_rul <= s.RUL_CRITICAL:
                sev = "critical"
            elif predicted_rul <= s.RUL_HIGH:
                sev = "high"
            elif predicted_rul <= s.RUL_MEDIUM:
                sev = "medium"
            else:
                sev = None
            if sev:
                # confidence derived from how low RUL is
                conf = 1.0 - (predicted_rul / 200.0)  # heuristic
                conf = max(0.0, min(1.0, conf))
                candidates.append(("degradation", sev, conf))

        if defect_prob is not None and machine_type == "bosch":
            if defect_prob >= s.DEFECT_PROB_CRITICAL:
                sev = "critical"
            elif defect_prob >= s.DEFECT_PROB_HIGH:
                sev = "high"
            elif defect_prob >= s.DEFECT_PROB_MEDIUM:
                sev = "medium"
            elif defect_prob >= s.DEFECT_PROB_LOW:
                sev = "low"
            else:
                sev = None
            if sev:
                candidates.append(("defect_risk", sev, defect_prob))

        if not candidates:
            return "anomaly", "low", 0.0

        # Choose highest severity
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        # sort by severity desc, then confidence desc
        candidates_sorted = sorted(candidates, key=lambda x: (severity_order[x[1]], x[2]), reverse=True)
        chosen = candidates_sorted[0]

        # Special handling: if turbofan degradation is high/critical and anomaly also high, make it failure_risk
        if machine_type == "turbofan" and any(c[0] == "degradation" and c[1] in ("high", "critical") for c in candidates):
            if any(c[0] == "anomaly" and c[1] in ("high", "critical") for c in candidates):
                # combined
                return "failure_risk", chosen[1], max(c[2] for c in candidates)

        return chosen[0], chosen[1], float(chosen[2])

    def build(
        self,
        reading: SensorReading,
        anomaly_score: Optional[float],
        predicted_rul: Optional[float],
        defect_prob: Optional[float],
        top_sensors: List[Dict[str, Any]],
        feature_snapshot: Dict[str, Any],
        confidence_override: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Build alert dict or None if suppressed or no alert condition."""
        self._decrement_cooldowns()

        alert_type, severity, conf = self._determine_severity_and_type(
            anomaly_score, predicted_rul, defect_prob, reading.machine_type
        )

        # If confidence low and severity low, don't emit? Spec says low-severity low-confidence can be watch, but builder still emits?
        # We will emit if severity at least low and confidence >= 0.3 or severity >= medium
        if conf < 0.3 and severity == "low":
            # suppress low low alerts
            return None

        # Additional rule: for turbofan, if RUL > RUL_MEDIUM and anomaly low, no alert
        if reading.machine_type == "turbofan" and predicted_rul and predicted_rul > self.settings.RUL_MEDIUM:
            if (anomaly_score is None or anomaly_score < self.settings.ANOMALY_THRESHOLD_MEDIUM):
                return None

        # Cooldown check
        if self.should_suppress(reading.machine_id, alert_type):
            logger.debug(f"Alert suppressed by cooldown for {reading.machine_id} {alert_type}")
            return None

        final_conf = confidence_override if confidence_override is not None else conf

        alert = {
            "alert_id": str(uuid.uuid4()),
            "machine_id": reading.machine_id,
            "machine_type": reading.machine_type,
            "ts": reading.ts,
            "alert_type": alert_type,
            "severity": severity,
            "confidence": float(final_conf),
            "anomaly_score": float(anomaly_score) if anomaly_score is not None else None,
            "predicted_rul": float(predicted_rul) if predicted_rul is not None else None,
            "defect_probability": float(defect_prob) if defect_prob is not None else None,
            "top_sensors": top_sensors,
            "feature_snapshot": feature_snapshot,
            "status": "open",
        }

        self._set_cooldown(reading.machine_id, alert_type)
        logger.info(f"Alert built {alert['alert_id']} machine={reading.machine_id} type={alert_type} severity={severity} conf={final_conf:.2f}")
        return alert

    def reset(self) -> None:
        self._cooldown_counters.clear()
