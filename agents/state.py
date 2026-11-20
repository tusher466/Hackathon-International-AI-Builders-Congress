"""FactoryState for LangGraph."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypedDict

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    """Ordered trace event."""
    agent: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_summary: str = ""
    output_summary: str = ""
    reasoning: str = ""
    duration_ms: int = 0


class DiagnosisResult(BaseModel):
    root_cause: str
    confidence: float
    reasoning: str
    citations: List[int] = Field(default_factory=list)
    evidence_strength: str = "moderate"


class PlanResult(BaseModel):
    action_type: str = Field(..., description="schedule_maintenance, reduce_load, reroute_production, stop_machine, inspect_quality, monitor_only")
    steps: List[str] = Field(default_factory=list)
    risk_level: str = Field(..., description="low|medium|high")
    requires_approval: bool = False
    rationale: str = ""
    estimated_impact: Dict[str, Any] = Field(default_factory=dict)


class ActionOutputResult(BaseModel):
    repair_instructions: str = ""
    ticket_id: Optional[str] = None
    notifications: List[str] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    expected_result: str = ""


class ApprovalResult(BaseModel):
    status: str = Field(..., description="not_required|pending|approved|rejected")
    decided_by: Optional[str] = None
    ts: Optional[datetime] = None
    comment: Optional[str] = None


class SupervisorResult(BaseModel):
    next_node: str = Field(..., description="monitor|diagnosis|planner|action|end|needs_human_review")
    iterations: int = 0
    escalate: bool = False
    reason: str = ""


# TypedDict for LangGraph state
class FactoryState(TypedDict, total=False):
    alert: Dict[str, Any]
    machine_context: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    diagnosis: Dict[str, Any]
    plan: Dict[str, Any]
    action_output: Dict[str, Any]
    approval: Dict[str, Any]
    trace: List[Dict[str, Any]]
    supervisor: Dict[str, Any]
    errors: List[str]
    citations_formatted: List[str]
    retrieval_query: str
