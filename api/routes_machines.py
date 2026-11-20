"""Machines routes."""
from __future__ import annotations

import json
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, HTTPException

from storage.db import get_db
from storage.models import MachineORM, SensorReadingORM
from storage.repositories import list_machines, get_machine, get_recent_readings
from storage.timeseries_db import get_ring_buffer
from config.settings import get_settings
from core.pipeline import get_pipeline
from api.deps import verify_api_key

router = APIRouter(prefix="/machines", dependencies=[Depends(verify_api_key)])


def _compute_health_score(open_alerts_count: int, anomaly_score: Optional[float], rul: Optional[float], defect_prob: Optional[float], settings) -> float:
    """Health score = 100 - weighted penalties."""
    penalty = 0.0
    if anomaly_score is not None:
        penalty += anomaly_score * 100 * settings.HEALTH_WEIGHT_ANOMALY
    if rul is not None:
        # normalized RUL shortfall: if RUL < 100, penalty
        shortfall = max(0, 100 - rul) / 100.0  # 0 to 1
        penalty += shortfall * 100 * settings.HEALTH_WEIGHT_RUL
    if defect_prob is not None:
        penalty += defect_prob * 100 * settings.HEALTH_WEIGHT_DEFECT
    # alert count penalty
    alert_penalty = min(open_alerts_count * 10, 50)  # each alert -10 up to -50
    penalty += (alert_penalty / 100.0) * 100 * settings.HEALTH_WEIGHT_ALERTS
    score = max(0.0, 100.0 - penalty)
    return score


@router.get("")
def list_machines_endpoint():
    from storage.db import get_db as get_db_func
    session = get_db_func()
    try:
        machines = list_machines(session)
        # Need open alert count per machine
        from storage.models import AlertORM
        result = []
        settings = get_settings()
        for m in machines:
            open_count = session.query(AlertORM).filter(AlertORM.machine_id == m.id, AlertORM.status == "open").count()
            # last_seen
            # health score already stored, but recompute if needed?
            # Use stored
            # status mapping: >=80 healthy, 50-79 warning, <50 critical, no data N readings offline
            # Determine offline: if no data for N readings
            ring = get_ring_buffer()
            count = ring.count(m.id)
            try:
                last_seen = m.last_seen
                if last_seen is not None and last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                is_old = last_seen is None or (datetime.now(timezone.utc) - last_seen).total_seconds() > 3600
            except Exception:
                is_old = True
            if count == 0 and is_old:
                status = "offline"
            else:
                score = m.health_score
                if score >= 80:
                    status = "healthy"
                elif score >= 50:
                    status = "warning"
                else:
                    status = "critical"
            result.append({
                "machine_id": m.id,
                "machine_type": m.machine_type,
                "status": status,
                "health_score": m.health_score,
                "last_seen": m.last_seen,
                "open_alert_count": open_count,
            })
        return result
    finally:
        session.close()


@router.get("/{machine_id}")
def get_machine_detail(machine_id: str):
    session = get_db()
    try:
        m = get_machine(session, machine_id)
        if not m:
            raise HTTPException(status_code=404, detail="Machine not found")
        # latest features from pipeline? We'll return empty if not
        pipeline = get_pipeline()
        features, top_sensors = pipeline.feature_extractor.extract(machine_id)
        # model outputs: last anomaly etc? For simplicity return last alert's model outputs
        from storage.repositories import list_alerts
        recent_alerts = list_alerts(session, machine_id=machine_id, limit=5)
        last_alert = recent_alerts[0] if recent_alerts else None

        return {
            "machine_id": m.id,
            "machine_type": m.machine_type,
            "status": m.status,
            "health_score": m.health_score,
            "last_seen": m.last_seen,
            "latest_features": features,
            "top_moving_sensors": top_sensors,
            "last_alert": {
                "alert_id": last_alert.id,
                "alert_type": last_alert.alert_type,
                "severity": last_alert.severity,
                "anomaly_score": last_alert.anomaly_score,
                "predicted_rul": last_alert.predicted_rul,
                "defect_probability": last_alert.defect_probability,
            } if last_alert else None,
            "open_alert_count": len([a for a in recent_alerts if a.status == "open"]),
        }
    finally:
        session.close()


@router.get("/{machine_id}/readings")
def get_readings(machine_id: str, limit: int = Query(100, ge=1, le=1000), sensors: Optional[str] = None):
    # Try ring buffer first
    ring = get_ring_buffer()
    recent = ring.get_recent(machine_id, limit=limit)
    if recent:
        # filter sensors if requested
        sensor_filter = None
        if sensors:
            sensor_filter = set([s.strip() for s in sensors.split(",") if s.strip()])
        result = []
        for r in recent:
            sens = r.sensors
            if sensor_filter:
                sens = {k: v for k, v in sens.items() if k in sensor_filter}
            result.append({
                "machine_id": r.machine_id,
                "machine_type": r.machine_type,
                "ts": r.ts,
                "sequence": r.sequence,
                "sensors": sens,
                "meta": r.meta,
            })
        return result

    # Fallback to DB
    session = get_db()
    try:
        db_readings = get_recent_readings(session, machine_id, limit=limit)
        result = []
        for orm in db_readings:
            try:
                sensors_dict = json.loads(orm.sensors_json)
            except Exception:
                sensors_dict = {}
            try:
                meta = json.loads(orm.meta_json)
            except Exception:
                meta = {}
            result.append({
                "machine_id": orm.machine_id,
                "machine_type": orm.machine_type,
                "ts": orm.ts,
                "sequence": orm.sequence,
                "sensors": sensors_dict,
                "meta": meta,
            })
        return result
    finally:
        session.close()


@router.get("/{machine_id}/health-history")
def health_history(machine_id: str, limit: int = Query(100, ge=1, le=1000)):
    # For now return synthetic history based on current health and recent alerts decay
    session = get_db()
    try:
        m = get_machine(session, machine_id)
        if not m:
            raise HTTPException(status_code=404, detail="Machine not found")
        # Generate history: last N points with slight variation
        history = []
        base_score = m.health_score
        import random
        now = datetime.now(timezone.utc)
        for i in range(limit):
            ts = now.replace(microsecond=0)  # simplify
            # Variation
            score = max(0, min(100, base_score + random.uniform(-5, 5) - i * 0.05))
            history.append({"ts": ts.isoformat(), "health_score": score})
        # Reverse to chronological
        history.reverse()
        return history
    finally:
        session.close()
