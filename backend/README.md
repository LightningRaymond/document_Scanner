# Backend Service

This directory contains the FastAPI application that orchestrates document ingestion, knowledge retrieval, and compliance APIs for the Investor Document Intelligence Platform.

## Development

```bash
uv sync  # or: pip install -e .[dev]
uv run uvicorn app.main:app --reload
```

Document metadata is written to `data/documents.json` (relative to this directory). Delete the file to reset the local registry.

## Testing

```bash
uv run pytest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENVIRONMENT` | Environment label surfaced via the health endpoint. | `local` |
| `APP_DOCUMENT_STORE_PATH` | Override the path for persisted document metadata. | `<repo>/backend/data/documents.json` |
