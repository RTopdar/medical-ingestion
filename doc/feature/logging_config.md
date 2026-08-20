---
type: Module
title: Structured Logging Configuration
description: Application-wide logging configuration using structlog for JSON output and semantic event logging.
resource: logging_config.py
tags: [logging, configuration, observability]
status: stable
---

# Structured Logging Configuration

`logging_config.py`. Centralized application logging setup via `structlog` with JSON output, timestamps, and structured event fields.

## Purpose

Replace all `print()` calls throughout the application with structured, machine-readable logging events. Every log line is valid JSON with:
- ISO 8601 timestamp (`TimeStamper(fmt="iso")`)
- Log level (`add_log_level`)
- Event name (caller-provided, semantic)
- Context fields (caller-provided key-value pairs)
- Stack traces on errors (`format_exc_info`)

This enables:
- **Parsing**: downstream log aggregators (ELK, Datadog, CloudWatch) ingest structured JSON
- **Filtering**: query logs by event type, error type, context values (e.g., "all embedding failures for patient X")
- **Observability**: trace pipeline stages (load → chunk → embed → store) via semantic event names

## Configuration

`structlog.configure()` sets up:
- **Processors**: pipeline transforming raw event into JSON
  - `TimeStamper(fmt="iso")` — adds `timestamp` field in ISO 8601 format
  - `add_log_level` — adds `level` field (info, warning, error, etc.)
  - `StackInfoRenderer()` — renders exception stack traces
  - `format_exc_info` — formats exception info for logging
  - `UnicodeDecoder()` — handles Unicode in messages
  - `JSONRenderer()` — final output: one JSON object per log line
- **Context class**: `dict` (flat context, not nested)
- **Logger factory**: `PrintLoggerFactory()` (writes to stdout/stderr)
- **Cache**: `cache_logger_on_first_use=True` (minor performance win)

## API

```python
from logging_config import get_logger

log = get_logger(__name__)

# Info event with context fields
log.info("documents_loaded", count=42, source="json")

# Warning event
log.warning("file_not_found", path="/path/to/file")

# Error event
log.error("embedding_failed", text_hash="abc123", error=str(e))
```

All arguments after the event name become context fields in the JSON output:
```json
{"timestamp": "2026-08-20T22:30:00+00:00", "level": "info", "event": "documents_loaded", "count": 42, "source": "json"}
```

## Migration from `print()`

All `print()` statements in the application have been migrated to `log.info()`, `log.warning()`, or `log.error()`. Examples:

- `print(f"Loaded {len(docs)} documents")` → `log.info("loaded_documents", count=len(docs))`
- `print(f"  ⊘ No files found in {path}")` → `log.warning("files_not_found", path=path)`
- Summary prints → structured event with all aggregated fields at once

See [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) for example usage in `scripts/ingest_documents.py`.

## Related

- [Ingest Pipeline Script](/doc/feature/ingest_documents_script.md) — primary use site; all document/chunk/embed progress logged via semantic events
