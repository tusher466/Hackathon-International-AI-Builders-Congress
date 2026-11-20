"""Alerts routes."""
from __future__ import annotations

import json
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from api.deps import verify_api_key
from storage.db import get_db
from storage.repositories import list_alerts, get_alert, list_traces
from storage.models import AlertORM

router = APIRouter(prefix="/alerts", dependencies=[Depends(verify_api_key)])


@router.get("")
def list_alerts_endpoint(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    machine_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_db()
    try:
        alerts = list_alerts(session, status=status, severity=severity, machine_id=machine_id, limit=limit, offset=offset)
        result = []
        for a in alerts:
            try:
                top_sensors = json.loads(a.top_sensors_json)
            except Exception:
                top_sensors = []
            try:
                feature_snapshot = json.loads(a.feature_snapshot_json)
            except Exception:
                feature_snapshot = {}
            result.append({
                "alert_id": a.id,
                "machine_id": a.machine_id,
                "machine_type": a.machine_type,
                "ts": a.ts,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "confidence": a.confidence,
                "anomaly_score": a.anomaly_score,
                "predicted_rul": a.predicted_rul,
                "defect_probability": a.defect_probability,
                "top_sensors": top_sensors,
                "feature_snapshot": feature_snapshot,
                "status": a.status,
                "created_at": a.created_at,
            })
        return result
    finally:
        session.close()


@router.get("/{alert_id}")
def get_alert_detail(alert_id: str):
    session = get_db()
    try:
        alert = get_alert(session, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # linked diagnosis, plan, ticket, approval - fetch from traces and tickets
        from storage.repositories import get_ticket
        from storage.models import TicketORM, ApprovalORM, DecisionTraceORM

        # Find ticket by alert_id
        ticket = session.query(TicketORM).filter(TicketORM.alert_id == alert_id).first()
        approval = session.query(ApprovalORM).filter(ApprovalORM.alert_id == alert_id).order_by(ApprovalORM.requested_at.desc()).first()
        traces = list_traces(session, alert_id)

        # Attempt to parse diagnosis/plan from traces? Actually traces contain full_state_json if saved
        diagnosis = {}
        plan = {}
        for t in traces:
            try:
                full_state = json.loads(t.full_state_json) if t.full_state_json else {}
                if full_state.get("diagnosis"):
                    diagnosis = full_state["diagnosis"]
                if full_state.get("plan"):
                    plan = full_state["plan"]
            except Exception:
                pass

        try:
            top_sensors = json.loads(alert.top_sensors_json)
        except Exception:
            top_sensors = []
        try:
            feature_snapshot = json.loads(alert.feature_snapshot_json)
        except Exception:
            feature_snapshot = {}

        return {
            "alert": {
                "alert_id": alert.id,
                "machine_id": alert.machine_id,
                "machine_type": alert.machine_type,
                "ts": alert.ts,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "confidence": alert.confidence,
                "anomaly_score": alert.anomaly_score,
                "predicted_rul": alert.predicted_rul,
                "defect_probability": alert.defect_probability,
                "top_sensors": top_sensors,
                "feature_snapshot": feature_snapshot,
                "status": alert.status,
            },
            "ticket": {
                "ticket_id": ticket.id,
                "status": ticket.status,
                "title": ticket.title,
                "priority": ticket.priority,
                "instructions": ticket.instructions,
            } if ticket else None,
            "approval": {
                "status": approval.status,
                "decided_by": approval.decided_by,
                "decided_at": approval.decided_at,
                "comment": approval.comment,
            } if approval else None,
            "diagnosis": diagnosis,
            "plan": plan,
            "trace_count": len(traces),
        }
    finally:
        session.close()


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):
    session = get_db()
    try:
        alert = get_alert(session, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert.status = "acknowledged"
        session.commit()
        return {"alert_id": alert_id, "status": "acknowledged"}
    finally:
        session.close()
