"""Service layer providing persistence, search, and compliance checks."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Iterable
from uuid import uuid4

from .config import get_settings
from .schemas import (
    ComplianceAlert,
    ComplianceAlertList,
    DocumentIngestionRequest,
    DocumentIngestionResponse,
    QueryRequest,
    QueryResponse,
    QueryResultSnippet,
)

class DocumentRegistry:
    """Filesystem-backed registry representing persisted documents."""

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._lock = Lock()
        self._ensure_store()

    def _ensure_store(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._storage_path.exists():
            self._storage_path.write_text(json.dumps({}))

    def _load(self) -> dict[str, dict]:
        try:
            raw = self._storage_path.read_text().strip()
            if not raw:
                return {}
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _save(self, payload: dict[str, dict]) -> None:
        self._storage_path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    def register(self, payload: DocumentIngestionRequest) -> DocumentIngestionResponse:
        created_at = datetime.utcnow()
        with self._lock:
            data = self._load()
            document_id = payload.document_id or str(uuid4())
            payload.document_id = document_id
            document_payload = {
                "created_at": created_at.isoformat(),
                "document": payload.model_dump(mode="json"),
            }
            data[document_id] = document_payload
            self._save(data)
        return DocumentIngestionResponse(
            document_id=document_id,
            status="received",
            received_at=created_at,
        )

    def get(self, document_id: str) -> DocumentIngestionRequest | None:
        with self._lock:
            stored = self._load().get(document_id)
        if not stored:
            return None
        return DocumentIngestionRequest.model_validate(stored["document"])

    def list(self) -> list[DocumentIngestionRequest]:
        with self._lock:
            payload = self._load()
        documents: list[DocumentIngestionRequest] = []
        for item in payload.values():
            documents.append(DocumentIngestionRequest.model_validate(item["document"]))
        return documents

    # The following helper is used in tests to ensure a clean slate between runs.
    def clear(self) -> None:
        with self._lock:
            self._save({})


class QueryEngine:
    """Simple metadata search leveraging the document registry."""

    def __init__(self, registry: DocumentRegistry) -> None:
        self._registry = registry

    def _filter_documents(
        self, documents: Iterable[DocumentIngestionRequest], filters: dict[str, str] | None
    ) -> list[DocumentIngestionRequest]:
        if not filters:
            return list(documents)
        filtered: list[DocumentIngestionRequest] = []
        for document in documents:
            doc_data = document.model_dump(mode="json")
            if all(str(doc_data.get(key, "")).lower() == value.lower() for key, value in filters.items()):
                filtered.append(document)
        return filtered

    def answer(self, payload: QueryRequest) -> QueryResponse:
        start_time = perf_counter()
        documents = self._filter_documents(self._registry.list(), payload.document_filters)
        query = payload.query.strip().lower()
        matches: list[tuple[DocumentIngestionRequest, float]] = []
        for document in documents:
            searchable = " ".join(
                filter(
                    None,
                    [
                        document.issuer,
                        document.product,
                        document.document_type,
                        document.language,
                        document.source,
                        document.filename,
                        document.reporting_period.isoformat() if document.reporting_period else None,
                    ],
                )
            ).lower()
            if not query:
                score = 0.0
            else:
                score = sum(1 for token in query.split() if token in searchable) / max(len(query.split()), 1)
            if not query or query in searchable or score > 0:
                matches.append((document, min(1.0, max(score, 0.05 if query else 0.1))))

        matches.sort(key=lambda item: item[1], reverse=True)
        matches = matches[: payload.max_results]

        if matches:
            answer_lines = [
                "Found the following documents matching your request:",
            ]
            snippets: list[QueryResultSnippet] = []
            for document, score in matches:
                reporting_period = (
                    document.reporting_period.isoformat() if document.reporting_period else "unspecified period"
                )
                answer_lines.append(
                    f"- {document.product} ({document.document_type}) for {reporting_period}"
                )
                snippets.append(
                    QueryResultSnippet(
                        document_id=document.document_id or "unknown",
                        section_heading="Metadata",
                        page=None,
                        excerpt=(
                            f"Issuer: {document.issuer}. Product: {document.product}. Filename: {document.filename}."
                        ),
                        score=round(score, 2),
                    )
                )
            answer = "\n".join(answer_lines)
        else:
            answer = (
                "No documents matched your query. Try adjusting the query text or filters once documents "
                "have been processed."
            )
            snippets = []

        latency_ms = max(1, int((perf_counter() - start_time) * 1000))
        return QueryResponse(answer=answer, citations=snippets, latency_ms=latency_ms)


class ComplianceService:
    """Derive simple compliance alerts from stored metadata."""

    def __init__(self, registry: DocumentRegistry) -> None:
        self._registry = registry

    def list_alerts(self) -> ComplianceAlertList:
        alerts: list[ComplianceAlert] = []
        now = datetime.utcnow()
        for document in self._registry.list():
            if document.reporting_period is None:
                alerts.append(
                    ComplianceAlert(
                        alert_id=f"{document.document_id}-missing-reporting-period",
                        document_id=document.document_id or "unknown",
                        rule_id="missing_reporting_period",
                        severity="medium",
                        status="new",
                        summary="Document metadata is missing a reporting period.",
                        created_at=now,
                        assignee=None,
                    )
                )
            if document.language.lower() not in {"en", "es", "fr", "de", "it", "zh"}:
                alerts.append(
                    ComplianceAlert(
                        alert_id=f"{document.document_id}-unverified-language",
                        document_id=document.document_id or "unknown",
                        rule_id="unverified_language",
                        severity="low",
                        status="new",
                        summary=(
                            "Language code is outside the verified set; ensure translated disclosures are available."
                        ),
                        created_at=now,
                        assignee=None,
                    )
                )
        return ComplianceAlertList(alerts=alerts, total=len(alerts))


settings = get_settings()
document_registry = DocumentRegistry(settings.document_store_path)
query_engine = QueryEngine(document_registry)
compliance_service = ComplianceService(document_registry)
