"""Agents and decisions routes."""
from __future__ import annotations

import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.deps import verify_api_key
from storage.db import get_db
from storage.repositories import list_traces, get_alert, list_alerts
from storage.models import ApprovalORM, TicketORM, DecisionTraceORM

router = APIRouter(prefix="", dependencies=[Depends(verify_api_key)])


@router.get("/decisions/{alert_id}/trace")
def get_decision_trace(alert_id: str):
    session = get_db()
    try:
        alert = get_alert(session, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        traces = list_traces(session, alert_id)
        # Build ordered trace with citations
        result = []
        for t in traces:
            try:
                full_state = json.loads(t.full_state_json) if t.full_state_json else {}
            except Exception:
                full_state = {}
            # Extract citations if available
            citations = full_state.get("citations_formatted", [])
            evidence = full_state.get("evidence", [])[:3]  # truncated
            result.append({
                "agent": t.agent,
                "ts": t.ts,
                "input_summary": t.input_summary,
                "output_summary": t.output_summary,
                "reasoning": t.reasoning,
                "duration_ms": t.duration_ms,
                "citations": citations,
                "evidence": evidence,
                "full_state": {k: v for k, v in full_state.items() if k not in ("evidence", "feature_snapshot")}  # avoid huge
            })
        # Sort by ts
        result.sort(key=lambda x: x["ts"])
        return {
            "alert_id": alert_id,
            "trace": result,
            "alert": {
                "machine_id": alert.machine_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
            }
        }
    finally:
        session.close()


@router.get("/decisions")
def list_decisions(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    session = get_db()
    try:
        alerts = list_alerts(session, limit=limit, offset=offset)
        # For each alert, get last trace to determine decision status
        decisions = []
        for a in alerts:
            # Check if has traces
            traces = session.query(DecisionTraceORM).filter(DecisionTraceORM.alert_id == a.id).order_by(DecisionTraceORM.ts).all()
            last_agent = traces[-1].agent if traces else "none"
            decisions.append({
                "alert_id": a.id,
                "machine_id": a.machine_id,
                "severity": a.severity,
                "alert_type": a.alert_type,
                "status": a.status,
                "last_agent": last_agent,
                "trace_count": len(traces),
                "ts": a.ts,
            })
        return decisions
    finally:
        session.close()


@router.get("/approvals/pending")
def list_pending_approvals():
    session = get_db()
    try:
        pendings = session.query(ApprovalORM).filter(ApprovalORM.status == "pending").order_by(ApprovalORM.requested_at).all()
        result = []
        for p in pendings:
            result.append({
                "alert_id": p.alert_id,
                "ticket_id": p.ticket_id,
                "status": p.status,
                "requested_at": p.requested_at,
            })
        return result
    finally:
        session.close()


class ApprovalDecision(BaseModel):
    decided_by: str
    comment: Optional[str] = None


@router.post("/approvals/{alert_id}/approve")
async def approve_alert(alert_id: str, body: ApprovalDecision):
    from actions.approval import approve
    session = get_db()
    try:
        # check exists
        ap = session.query(ApprovalORM).filter(ApprovalORM.alert_id == alert_id, ApprovalORM.status == "pending").first()
        if not ap:
            raise HTTPException(status_code=404, detail="Pending approval not found")
    finally:
        session.close()

    orm = await approve(alert_id, body.decided_by, body.comment)
    if not orm:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"alert_id": alert_id, "status": "approved", "decided_by": body.decided_by}


@router.post("/approvals/{alert_id}/reject")
async def reject_alert(alert_id: str, body: ApprovalDecision):
    from actions.approval import reject
    session = get_db()
    try:
        ap = session.query(ApprovalORM).filter(ApprovalORM.alert_id == alert_id, ApprovalORM.status == "pending").first()
        if not ap:
            raise HTTPException(status_code=404, detail="Pending approval not found")
    finally:
        session.close()

    orm = await reject(alert_id, body.decided_by, body.comment)
    if not orm:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"alert_id": alert_id, "status": "rejected", "decided_by": body.decided_by}


# Tickets routes also here
@router.get("/tickets")
def list_tickets_endpoint(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    session = get_db()
    try:
        tickets = session.query(TicketORM).order_by(TicketORM.created_at.desc()).offset(offset).limit(limit).all()
        result = []
        for t in tickets:
            result.append({
                "ticket_id": t.id,
                "alert_id": t.alert_id,
                "machine_id": t.machine_id,
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "assigned_to": t.assigned_to,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })
        return result
    finally:
        session.close()


@router.get("/tickets/{ticket_id}")
def get_ticket_endpoint(ticket_id: str):
    session = get_db()
    try:
        t = session.get(TicketORM, ticket_id)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return {
            "ticket_id": t.id,
            "alert_id": t.alert_id,
            "machine_id": t.machine_id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "instructions": t.instructions,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
    finally:
        session.close()


@router.patch("/tickets/{ticket_id}")
def patch_ticket(ticket_id: str, body: dict):
    session = get_db()
    try:
        t = session.get(TicketORM, ticket_id)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        allowed = {"status", "assigned_to"}
        for k, v in body.items():
            if k in allowed:
                setattr(t, k, v)
        session.commit()
        return {"ticket_id": ticket_id, "status": t.status, "assigned_to": t.assigned_to}
    finally:
        session.close()


# Knowledge routes
class SearchBody(BaseModel):
    query: str
    machine_type: Optional[str] = None
    k: Optional[int] = 5


@router.post("/knowledge/search")
def knowledge_search(body: SearchBody):
    from knowledge.retriever import retrieve, format_citations
    chunks = retrieve(body.query, machine_type=body.machine_type, k=body.k or 5)
    citations = format_citations(chunks)
    return {"query": body.query, "chunks": chunks, "citations": citations}


@router.post("/knowledge/reingest")
def knowledge_reingest(reset: bool = False):
    from knowledge.ingest_docs import ingest_manuals
    try:
        count = ingest_manuals("./data/manuals", reset=reset)
        return {"ingested_chunks": count, "reset": reset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {e}")
