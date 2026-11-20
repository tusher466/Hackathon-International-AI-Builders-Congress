"""API endpoints tests."""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from storage.db import init_db
from knowledge.vector_store import get_vector_store
from knowledge.ingest_docs import ingest_manuals


@pytest.fixture(scope="module")
def client():
    init_db()
    store = get_vector_store()
    if store.count() == 0:
        ingest_manuals("./data/manuals")
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "components" in data
    # All components should be ok or not_started (stream)
    comp = data["components"]
    assert comp["db"]["status"] == "ok"
    assert comp["vector_store"]["status"] == "ok"


def test_machines_endpoint(client):
    resp = client.get("/api/v1/machines")
    assert resp.status_code == 200
    # May be empty initially, but should return list
    assert isinstance(resp.json(), list)


def test_alerts_endpoint(client):
    resp = client.get("/api/v1/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_knowledge_search(client):
    resp = client.post("/api/v1/knowledge/search", json={"query": "compressor fouling", "k": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert "chunks" in data
    assert len(data["chunks"]) > 0


def test_control_inject_fault(client):
    resp = client.post("/api/v1/control/inject-fault", json={
        "machine_id": "TURBO-01",
        "fault_type": "degradation",
        "magnitude": 1.5,
        "duration_ticks": 10,
        "sensors": ["s7", "s9"]
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "injected"


def test_metrics_impact(client):
    resp = client.get("/api/v1/metrics/impact")
    assert resp.status_code == 200
    data = resp.json()
    assert "downtime_avoided_minutes" in data
    assert "alerts_by_severity" in data


def test_tickets_endpoint(client):
    resp = client.get("/api/v1/tickets")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_approvals_pending(client):
    resp = client.get("/api/v1/approvals/pending")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
