"""Approval flow pending -> approve -> resumed."""
import pytest
from storage.db import init_db, get_db
from actions.approval import create_approval_request, approve, reject, list_pending
from actions.ticketing import create_ticket
from datetime import datetime, timezone


def setup_module():
    init_db()


@pytest.mark.asyncio
async def test_approval_flow():
    # Clean pending? We just create new
    alert_id = "approval-test-alert"
    ticket_id = "approval-test-ticket-001"

    # Create ticket first
    try:
        create_ticket(
            ticket_id=ticket_id,
            alert_id=alert_id,
            machine_id="TURBO-01",
            title="Test ticket",
            description="Test",
            priority="critical",
            status="awaiting_approval",
            instructions="Test instructions with LOTO",
        )
    except Exception as e:
        # May already exist
        print(f"Ticket create warning {e}")

    # Create approval
    approval = create_approval_request(alert_id, ticket_id)
    assert approval.alert_id == alert_id
    assert approval.status == "pending"

    # List pending should include it
    pendings = list_pending()
    assert any(p.alert_id == alert_id for p in pendings)

    # Approve
    approved = await approve(alert_id, decided_by="tester", comment="Approved in test")
    assert approved.status == "approved"
    assert approved.decided_by == "tester"

    # After approve, pending should not include
    pendings2 = list_pending()
    assert not any(p.alert_id == alert_id and p.status == "pending" for p in pendings2)


@pytest.mark.asyncio
async def test_reject_flow():
    alert_id = "reject-test-alert"
    ticket_id = "reject-test-ticket-001"

    try:
        create_ticket(
            ticket_id=ticket_id,
            alert_id=alert_id,
            machine_id="BOSCH-L1",
            title="Reject test",
            description="Test reject",
            priority="high",
            status="awaiting_approval",
            instructions="Test",
        )
    except Exception:
        pass

    create_approval_request(alert_id, ticket_id)
    rejected = await reject(alert_id, decided_by="tester2", comment="Rejected in test")
    assert rejected.status == "rejected"
