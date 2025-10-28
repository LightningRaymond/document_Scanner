"""Smoke tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import document_registry


client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_registry():
    document_registry.clear()
    yield
    document_registry.clear()


def test_health_endpoint_returns_ok_status():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "app_name" in payload


def test_ingest_and_retrieve_document():
    ingestion_payload = {
        "tenant_id": "tenant-123",
        "issuer": "Example Asset Manager",
        "product": "Fund A",
        "document_type": "factsheet",
        "reporting_period": "2023-12-31",
        "language": "en",
        "source": "upload",
        "version": 1,
        "filename": "fund-a-factsheet.pdf",
    }
    ingest_response = client.post("/documents", json=ingestion_payload)
    assert ingest_response.status_code == 200
    document_id = ingest_response.json()["document_id"]

    get_response = client.get(f"/documents/{document_id}")
    assert get_response.status_code == 200
    retrieved = get_response.json()
    assert retrieved["document_id"] == document_id
    assert retrieved["issuer"] == ingestion_payload["issuer"]


def test_query_endpoint_returns_metadata_backed_answer():
    payload = {
        "tenant_id": "tenant-456",
        "issuer": "Global Investments",
        "product": "Fund B",
        "document_type": "annual report",
        "language": "en",
        "source": "upload",
        "version": 1,
        "filename": "fund-b-annual.pdf",
    }
    ingest_response = client.post("/documents", json=payload)
    assert ingest_response.status_code == 200

    response = client.post("/query", json={"query": "Fund B"})
    assert response.status_code == 200
    body = response.json()
    assert "Fund B" in body["answer"]
    assert body["citations"]


def test_compliance_alerts_highlight_missing_reporting_period():
    payload = {
        "tenant_id": "tenant-789",
        "issuer": "Alpha Partners",
        "product": "Fund C",
        "document_type": "factsheet",
        "language": "en",
        "source": "upload",
        "version": 1,
        "filename": "fund-c-factsheet.pdf",
    }
    ingest_response = client.post("/documents", json=payload)
    assert ingest_response.status_code == 200

    alert_response = client.get("/alerts")
    assert alert_response.status_code == 200
    alerts = alert_response.json()
    assert alerts["total"] == 1
    assert alerts["alerts"][0]["rule_id"] == "missing_reporting_period"
