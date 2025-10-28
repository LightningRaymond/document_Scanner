# Investor Document Intelligence Platform

The Investor Document Intelligence Platform transforms static investor PDFs—factsheets, reports, and regulatory filings—into structured, queryable knowledge that powers analytics, compliance workflows, and investor experiences.

## Project Structure

```
.
├── backend/              # FastAPI service for ingestion, processing orchestration, and APIs
├── docs/                 # Architectural specifications and design notes
├── docker-compose.yml    # Local orchestration for core services
├── README.md             # Project overview and getting started instructions
└── tests/                # (Reserved) Cross-service test harnesses
```

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) or `pip`
- Docker (for local dependencies such as vector DBs, message brokers, etc.)

### Backend Service

```bash
cd backend
uv sync  # or: pip install -r requirements.txt
uv run fastapi dev app/main.py  # or: uvicorn app.main:app --reload
```

The service now persists document metadata to `backend/data/documents.json` so records remain available across restarts. It expos
es early building blocks for:

- **Document ingestion** (`POST /documents`) with metadata capture and filesystem-backed persistence
- **Retrieval/Q&A** (`POST /query`) that searches stored metadata to surface matching documents and citations
- **Compliance alerts** (`GET /alerts`) that flag missing reporting periods or unsupported languages in metadata

### Local Services

A `docker-compose.yml` file defines placeholders for future dependencies (PostgreSQL, vector search, and object storage). Uncomment and configure services as they are implemented.

```bash
docker compose up
```

## Roadmap Highlights

1. **MVP** – Batch ingestion, DeepSeek OCR integration, Markdown outputs, basic search & Q&A, initial compliance checks.
2. **Enhanced Analytics & Compliance** – Advanced metric extraction, multilingual support, comprehensive compliance engine, API/webhooks.
3. **Enterprise & Ecosystem** – Multi-tenant RBAC, third-party integrations, continuous model improvement pipeline.

Refer to `docs/architecture.md` for the full specification and component-level design.
