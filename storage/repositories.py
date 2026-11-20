"""Repository helpers for CRUD."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import desc

from storage.models import MachineORM, SensorReadingORM, AlertORM, TicketORM, DecisionTraceORM, ApprovalORM
from ingestion.schemas import SensorReading


def upsert_machine(session: Session, machine_id: str, machine_type: str, status: str = "healthy", health_score: float = 100.0, last_seen: Optional[datetime] = None) -> MachineORM:
    obj = session.get(MachineORM, machine_id)
    if obj is None:
        obj = MachineORM(id=machine_id, machine_type=machine_type, status=status, health_score=health_score, last_seen=last_seen or datetime.now(timezone.utc))
        session.add(obj)
    else:
        obj.machine_type = machine_type
        obj.status = status
        obj.health_score = health_score
        obj.last_seen = last_seen or datetime.now(timezone.utc)
    session.commit()
    session.refresh(obj)
    return obj


def list_machines(session: Session) -> List[MachineORM]:
    return session.query(MachineORM).all()


def get_machine(session: Session, machine_id: str) -> Optional[MachineORM]:
    return session.get(MachineORM, machine_id)


def save_reading(session: Session, reading: SensorReading) -> SensorReadingORM:
    orm = SensorReadingORM(
        machine_id=reading.machine_id,
        machine_type=reading.machine_type,
        ts=reading.ts,
        sequence=reading.sequence,
        sensors_json=json.dumps(reading.sensors),
        meta_json=json.dumps(reading.meta or {}),
    )
    session.add(orm)
    session.commit()
    # update machine last_seen
    upsert_machine(session, reading.machine_id, reading.machine_type, last_seen=reading.ts)
    return orm


def get_recent_readings(session: Session, machine_id: str, limit: int = 100) -> List[SensorReadingORM]:
    return session.query(SensorReadingORM).filter(SensorReadingORM.machine_id == machine_id).order_by(desc(SensorReadingORM.ts)).limit(limit).all()


def save_alert(session: Session, alert: Dict[str, Any]) -> AlertORM:
    orm = AlertORM(
        id=alert["alert_id"],
        machine_id=alert["machine_id"],
        machine_type=alert["machine_type"],
        ts=alert["ts"],
        alert_type=alert["alert_type"],
        severity=alert["severity"],
        confidence=alert.get("confidence", 0.0),
        anomaly_score=alert.get("anomaly_score"),
        predicted_rul=alert.get("predicted_rul"),
        defect_probability=alert.get("defect_probability"),
        top_sensors_json=json.dumps(alert.get("top_sensors", [])),
        feature_snapshot_json=json.dumps(alert.get("feature_snapshot", {})),
        status=alert.get("status", "open"),
    )
    session.add(orm)
    session.commit()
    session.refresh(orm)
    return orm


def get_alert(session: Session, alert_id: str) -> Optional[AlertORM]:
    return session.get(AlertORM, alert_id)


def list_alerts(session: Session, status: Optional[str] = None, severity: Optional[str] = None, machine_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[AlertORM]:
    q = session.query(AlertORM).order_by(desc(AlertORM.ts))
    if status:
        q = q.filter(AlertORM.status == status)
    if severity:
        q = q.filter(AlertORM.severity == severity)
    if machine_id:
        q = q.filter(AlertORM.machine_id == machine_id)
    return q.offset(offset).limit(limit).all()


def save_trace(session: Session, alert_id: str, trace_event: Dict[str, Any], full_state: Optional[Dict] = None) -> DecisionTraceORM:
    orm = DecisionTraceORM(
        alert_id=alert_id,
        agent=trace_event.get("agent", "unknown"),
        ts=trace_event.get("ts") or datetime.now(timezone.utc),
        input_summary=trace_event.get("input_summary", ""),
        output_summary=trace_event.get("output_summary", ""),
        reasoning=trace_event.get("reasoning", ""),
        duration_ms=trace_event.get("duration_ms", 0),
        full_state_json=json.dumps(full_state or {}, default=str),
    )
    session.add(orm)
    session.commit()
    return orm


def list_traces(session: Session, alert_id: str) -> List[DecisionTraceORM]:
    return session.query(DecisionTraceORM).filter(DecisionTraceORM.alert_id == alert_id).order_by(DecisionTraceORM.ts).all()


def save_ticket(session: Session, ticket: Dict[str, Any]) -> TicketORM:
    orm = TicketORM(
        id=ticket["ticket_id"],
        alert_id=ticket["alert_id"],
        machine_id=ticket["machine_id"],
        title=ticket["title"],
        description=ticket.get("description", ""),
        priority=ticket.get("priority", "medium"),
        status=ticket.get("status", "open"),
        assigned_to=ticket.get("assigned_to"),
        instructions=ticket.get("instructions", ""),
    )
    session.add(orm)
    session.commit()
    session.refresh(orm)
    return orm


def get_ticket(session: Session, ticket_id: str) -> Optional[TicketORM]:
    return session.get(TicketORM, ticket_id)


def list_tickets(session: Session, limit: int = 50, offset: int = 0) -> List[TicketORM]:
    return session.query(TicketORM).order_by(desc(TicketORM.created_at)).offset(offset).limit(limit).all()


def update_ticket(session: Session, ticket_id: str, updates: Dict[str, Any]) -> Optional[TicketORM]:
    orm = session.get(TicketORM, ticket_id)
    if not orm:
        return None
    for k, v in updates.items():
        if hasattr(orm, k):
            setattr(orm, k, v)
    session.commit()
    session.refresh(orm)
    return orm


def save_approval(session: Session, approval: Dict[str, Any]) -> ApprovalORM:
    orm = ApprovalORM(
        alert_id=approval["alert_id"],
        ticket_id=approval.get("ticket_id"),
        status=approval.get("status", "pending"),
        decided_by=approval.get("decided_by"),
        comment=approval.get("comment"),
    )
    session.add(orm)
    session.commit()
    session.refresh(orm)
    return orm


def get_approval_by_alert(session: Session, alert_id: str) -> Optional[ApprovalORM]:
    return session.query(ApprovalORM).filter(ApprovalORM.alert_id == alert_id).order_by(desc(ApprovalORM.requested_at)).first()


def list_pending_approvals(session: Session) -> List[ApprovalORM]:
    return session.query(ApprovalORM).filter(ApprovalORM.status == "pending").order_by(ApprovalORM.requested_at).all()


def update_approval(session: Session, alert_id: str, status: str, decided_by: str, comment: Optional[str] = None) -> Optional[ApprovalORM]:
    orm = get_approval_by_alert(session, alert_id)
    if not orm:
        return None
    orm.status = status
    orm.decided_by = decided_by
    orm.decided_at = datetime.now(timezone.utc)
    orm.comment = comment
    session.commit()
    session.refresh(orm)
    return orm
