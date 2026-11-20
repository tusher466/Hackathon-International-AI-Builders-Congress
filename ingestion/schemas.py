"""Unified message schema."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator


MachineType = Literal["secom", "turbofan", "bosch"]


class SensorReading(BaseModel):
    """Unified sensor reading."""

    machine_id: str = Field(..., description="Machine identifier, e.g., SECOM-01")
    machine_type: MachineType = Field(..., description="Type of machine")
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="ISO-8601 UTC timestamp")
    sequence: int = Field(..., ge=0, description="Monotonic sequence per machine")
    sensors: Dict[str, Optional[float]] = Field(default_factory=dict, description="Sensor name -> value")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata like op_settings, station, ground_truth")

    @field_validator("ts")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    def to_mqtt_payload(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_mqtt_payload(cls, payload: str | bytes) -> "SensorReading":
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return cls.model_validate_json(payload)


class AlertRaw(BaseModel):
    """Intermediate raw detection before alert_builder."""
    machine_id: str
    machine_type: MachineType
    ts: datetime
    anomaly_score: Optional[float] = None
    predicted_rul: Optional[float] = None
    defect_probability: Optional[float] = None
    top_sensors: list[Dict[str, Any]] = Field(default_factory=list)
    feature_snapshot: Dict[str, Any] = Field(default_factory=dict)


# Pydantic response models for API
class SensorReadingResponse(BaseModel):
    machine_id: str
    machine_type: str
    ts: datetime
    sequence: int
    sensors: Dict[str, Optional[float]]
    meta: Dict[str, Any]

    model_config = {"from_attributes": True}
