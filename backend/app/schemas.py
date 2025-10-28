"""Shared Pydantic models used by the API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


DocumentSource = Literal["upload", "sftp", "email", "api"]
DocumentStatus = Literal["received", "processing", "processed", "error"]
AlertSeverity = Literal["low", "medium", "high", "critical"]
AlertStatus = Literal["new", "in_review", "resolved", "false_positive"]


class DocumentMetadata(BaseModel):
    """Metadata captured when a document enters the system."""

    document_id: Optional[str] = Field(
        default=None, description="System-assigned identifier; omitted for new uploads."
    )
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenant isolation.")
    issuer: str = Field(..., description="Issuer or asset manager associated with the document.")
    product: str = Field(..., description="Product or fund name the document describes.")
    document_type: str = Field(..., description="Document category (factsheet, report, filing, etc.).")
    reporting_period: Optional[date] = Field(
        default=None,
        description="Reporting period represented in the document, if known.",
    )
    language: str = Field(default="en", description="ISO language code of the document.")
    source: DocumentSource = Field(
        default="upload",
        description="Origin of the document within the ingestion ecosystem.",
    )
    version: int = Field(default=1, description="Version number for reprocessed documents.")


class DocumentIngestionRequest(DocumentMetadata):
    """Payload accepted by the document ingestion endpoint."""

    filename: str = Field(..., description="Original filename for traceability.")
    content_url: Optional[HttpUrl] = Field(
        default=None,
        description="Optional pointer to the binary when uploading via pre-signed URLs or connectors.",
    )


class DocumentIngestionResponse(BaseModel):
    """Response returned once a document is accepted for processing."""

    document_id: str
    status: DocumentStatus
    received_at: datetime


class QueryRequest(BaseModel):
    """Represents a natural language or structured query."""

    query: str = Field(..., description="User question or prompt.")
    document_filters: dict[str, str] | None = Field(
        default=None, description="Optional filter criteria for retrieval."
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of knowledge base chunks to consider in the response.",
    )


class QueryResultSnippet(BaseModel):
    """Snippet returned alongside generated answers."""

    document_id: str
    section_heading: Optional[str] = None
    page: Optional[int] = None
    excerpt: str
    score: float = Field(..., ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    """Structured response from the Q&A endpoint."""

    answer: str
    citations: list[QueryResultSnippet]
    latency_ms: int


class ComplianceAlert(BaseModel):
    """Compliance alert surfaced by the engine."""

    alert_id: str
    document_id: str
    rule_id: str
    severity: AlertSeverity
    status: AlertStatus
    summary: str
    created_at: datetime
    assignee: Optional[str] = None


class ComplianceAlertList(BaseModel):
    """Paginated list of compliance alerts."""

    alerts: list[ComplianceAlert]
    total: int
