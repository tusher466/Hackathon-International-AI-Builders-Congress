"""Ticketing actions."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from storage.db import get_db
from storage.repositories import save_ticket, get_ticket, list_tickets, update_ticket
from storage.models import TicketORM
import json

logger = logging.getLogger(__name__)


def create_ticket(
    ticket_id: str,
    alert_id: str,
    machine_id: str,
    title: str,
    description: str,
    priority: str = "medium",
    status: str = "open",
    instructions: str = "",
    assigned_to: Optional[str] = None,
) -> TicketORM:
    """Create ticket in DB."""
    session = get_db()
    try:
        ticket_dict = {
            "ticket_id": ticket_id,
            "alert_id": alert_id,
            "machine_id": machine_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": status,
            "assigned_to": assigned_to,
            "instructions": instructions,
        }
        orm = save_ticket(session, ticket_dict)
        logger.info(f"Ticket created {ticket_id} alert {alert_id} status {status}")
        return orm
    finally:
        session.close()


def update_ticket_status(ticket_id: str, status: str, assigned_to: Optional[str] = None, instructions: Optional[str] = None) -> Optional[TicketORM]:
    session = get_db()
    try:
        updates: Dict[str, Any] = {"status": status}
        if assigned_to is not None:
            updates["assigned_to"] = assigned_to
        if instructions is not None:
            updates["instructions"] = instructions
        orm = update_ticket(session, ticket_id, updates)
        if orm:
            logger.info(f"Ticket {ticket_id} updated to {status}")
        return orm
    finally:
        session.close()


def get_ticket_by_id(ticket_id: str) -> Optional[TicketORM]:
    session = get_db()
    try:
        return get_ticket(session, ticket_id)
    finally:
        session.close()


def list_all_tickets(limit: int = 50, offset: int = 0) -> List[TicketORM]:
    session = get_db()
    try:
        return list_tickets(session, limit=limit, offset=offset)
    finally:
        session.close()


def ticket_orm_to_dict(orm: TicketORM) -> Dict[str, Any]:
    return {
        "ticket_id": orm.id,
        "alert_id": orm.alert_id,
        "machine_id": orm.machine_id,
        "title": orm.title,
        "description": orm.description,
        "priority": orm.priority,
        "status": orm.status,
        "assigned_to": orm.assigned_to,
        "instructions": orm.instructions,
        "created_at": orm.created_at,
        "updated_at": orm.updated_at,
    }
