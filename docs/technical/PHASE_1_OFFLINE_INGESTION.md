# Phase 1: Offline Ingestion

## Goal

Move PDF ingestion and index rebuilding out of the chat request path.

## What Changed

1. `AssistantService` no longer rebuilds the FAISS index during initialization.
2. A dedicated offline worker was added at `server/app/workers/pdf_ingestion_worker.py`.
3. The worker runs PDF ingestion and can rebuild the FAISS index outside the request path.
4. Chat requests now only read the existing index instead of rebuilding it.

## Keep / Replace / Remove

### Keep

1. PDF parsing and chunking logic.
2. Knowledge base loading.
3. FAISS search behavior for now.

### Replace

1. Request-time index rebuild with the offline worker.
2. Inline corpus refresh with explicit worker execution.

### Remove

1. Automatic `FaissIndexStore.build(...)` calls from `AssistantService.__init__`.
2. Any assumption that chat request handling should rebuild the corpus.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/integration/api/test_chat_api.py tests/integration/api/test_config_api.py tests/unit/core/test_routing.py tests/unit/core/test_generation.py tests/unit/core/test_evidence_gate.py tests/unit/services/test_audit_logger.py tests/unit/services/test_assistant_service.py tests/unit/workers/test_pdf_ingestion_worker.py
```

Result:

- 26 passed

## Notes

This phase keeps the current retrieval backend in place. It only changes where the corpus and index are built.
