"""SQLAlchemy ORM models."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MachineORM(Base):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    machine_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="healthy")
    health_score: Mapped[float] = mapped_column(Float, default=100.0)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # optional metadata
    meta_json: Mapped[str] = mapped_column(Text, default="{}")


class SensorReadingORM(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String, nullable=False)
    machine_type: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    sensors_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON dict
    meta_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_readings_machine_ts", "machine_id", "ts"),
        Index("idx_readings_machine_seq", "machine_id", "sequence"),
    )


class AlertORM(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # uuid
    machine_id: Mapped[str] = mapped_column(String, nullable=False)
    machine_type: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    alert_type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_rul: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    defect_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_sensors_json: Mapped[str] = mapped_column(Text, default="[]")
    feature_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_alerts_machine", "machine_id"),
        Index("idx_alerts_status", "status"),
        Index("idx_alerts_severity", "severity"),
    )


class TicketORM(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String, nullable=False)
    machine_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String, default="medium")
    status: Mapped[str] = mapped_column(String, default="open")
    assigned_to: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    instructions: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_tickets_alert", "alert_id"),
        Index("idx_tickets_machine", "machine_id"),
    )


class DecisionTraceORM(Base):
    __tablename__ = "decision_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String, nullable=False)
    agent: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    full_state_json: Mapped[str] = mapped_column(Text, default="{}")

    __table_args__ = (
        Index("idx_traces_alert", "alert_id"),
    )


class ApprovalORM(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String, nullable=False)
    ticket_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, approved, rejected, not_required
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_approvals_alert", "alert_id"),
        Index("idx_approvals_status", "status"),
    )
