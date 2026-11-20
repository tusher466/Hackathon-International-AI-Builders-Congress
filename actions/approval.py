"""Approval handling."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from storage.db import get_db
from storage.repositories import save_approval, list_pending_approvals, update_approval, get_approval_by_alert
from storage.models import ApprovalORM
from agents.graph import resume_after_approval
from actions.ticketing import update_ticket_status

logger = logging.getLogger(__name__)


def create_approval_request(alert_id: str, ticket_id: Optional[str] = None) -> ApprovalORM:
    session = get_db()
    try:
        approval_dict = {
            "alert_id": alert_id,
            "ticket_id": ticket_id,
            "status": "pending",
        }
        orm = save_approval(session, approval_dict)
        logger.info(f"Approval request created for alert {alert_id} ticket {ticket_id}")
        return orm
    finally:
        session.close()


def list_pending() -> List[ApprovalORM]:
    session = get_db()
    try:
        return list_pending_approvals(session)
    finally:
        session.close()


def get_approval(alert_id: str) -> Optional[ApprovalORM]:
    session = get_db()
    try:
        return get_approval_by_alert(session, alert_id)
    finally:
        session.close()


async def approve(alert_id: str, decided_by: str, comment: Optional[str] = None) -> Optional[ApprovalORM]:
    session = get_db()
    try:
        orm = update_approval(session, alert_id, "approved", decided_by, comment)
        if not orm:
            logger.warning(f"No approval found for {alert_id}")
            return None
        logger.info(f"Approval approved for {alert_id} by {decided_by}")

        # Resume graph
        try:
            final_state = await resume_after_approval(alert_id, "approved", decided_by, comment)
            # If ticket exists, move it from awaiting_approval to in_progress or open
            if orm.ticket_id:
                update_ticket_status(orm.ticket_id, "in_progress")
        except Exception as e:
            logger.warning(f"Failed to resume after approval for {alert_id}: {e}")

        return orm
    finally:
        session.close()


async def reject(alert_id: str, decided_by: str, comment: Optional[str] = None) -> Optional[ApprovalORM]:
    session = get_db()
    try:
        orm = update_approval(session, alert_id, "rejected", decided_by, comment)
        if not orm:
            logger.warning(f"No approval found for {alert_id}")
            return None
        logger.info(f"Approval rejected for {alert_id} by {decided_by}")

        # Update ticket to rejected
        if orm.ticket_id:
            update_ticket_status(orm.ticket_id, "rejected")

        try:
            await resume_after_approval(alert_id, "rejected", decided_by, comment)
        except Exception as e:
            logger.warning(f"Resume after reject failed {e}")

        return orm
    finally:
        session.close()


def approval_to_dict(orm: ApprovalORM) -> Dict[str, Any]:
    return {
        "alert_id": orm.alert_id,
        "ticket_id": orm.ticket_id,
        "status": orm.status,
        "requested_at": orm.requested_at,
        "decided_by": orm.decided_by,
        "decided_at": orm.decided_at,
        "comment": orm.comment,
    }
