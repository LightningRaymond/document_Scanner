"""FastAPI entrypoint for the Investor Document Intelligence Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

from .config import settings_summary
from .schemas import (
    ComplianceAlertList,
    DocumentIngestionRequest,
    DocumentIngestionResponse,
    QueryRequest,
    QueryResponse,
)
from .services import compliance_service, document_registry, query_engine

app = FastAPI(title="Investor Document Intelligence API")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str | bool]:
    """Return application health metadata."""

    summary = settings_summary()
    summary.update({"status": "ok", "timestamp": datetime.utcnow().isoformat()})
    return summary


@app.post("/documents", response_model=DocumentIngestionResponse, tags=["documents"])
def ingest_document(
    payload: DocumentIngestionRequest,
) -> DocumentIngestionResponse:
    """Accept metadata for a document entering the pipeline."""
    return document_registry.register(payload)


@app.get(
    "/documents/{document_id}",
    response_model=DocumentIngestionRequest,
    tags=["documents"],
)
def get_document(document_id: Annotated[str, Path(title="Document identifier")]):
    """Retrieve stored metadata for a specific document."""

    document = document_registry.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.get("/documents", response_model=list[DocumentIngestionRequest], tags=["documents"])
def list_documents() -> list[DocumentIngestionRequest]:
    """List ingested documents."""

    return document_registry.list()


@app.post("/query", response_model=QueryResponse, tags=["knowledge"])
def query_knowledge_base(payload: QueryRequest) -> QueryResponse:
    """Execute a placeholder knowledge base query."""

    return query_engine.answer(payload)


@app.get("/alerts", response_model=ComplianceAlertList, tags=["compliance"])
def list_compliance_alerts() -> ComplianceAlertList:
    """List compliance alerts using mock service implementation."""

    return compliance_service.list_alerts()
