# Phase 2: Qdrant Migration

## Goal

Replace FAISS as the long-term production retrieval store while keeping the retrieval contract stable.

## What Changed

1. Added `qdrant-client` as an optional retrieval dependency.
2. Added `QdrantStore` as a new retrieval backend.
3. Updated `HybridRetriever` to use Qdrant when `RETRIEVAL_BACKEND=qdrant`.
4. Kept FAISS as the fallback path during migration.
5. Added Qdrant runtime settings to config, env example, and compose.

## Keep / Replace / Remove

### Keep

1. Retrieval contract and `ScoredChunk` shape.
2. Hybrid scoring behavior.
3. FAISS fallback during migration.

### Replace

1. FAISS as the final production store.
2. Manual runtime-only retrieval wiring.

### Remove

1. Hidden retrieval backend selection.
2. Any assumption that FAISS is the permanent store.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/unit/core/test_qdrant_store.py tests/unit/core/test_hybrid_retriever_backend_switch.py tests/integration/retrieval/test_retrieval_pipeline.py tests/unit/services/test_assistant_service.py tests/integration/api/test_chat_api.py tests/integration/api/test_config_api.py
```

Result:

- 13 passed

## Deployment Notes

1. `compose.yaml` now includes a Qdrant service.
2. Set `RETRIEVAL_BACKEND=qdrant` to use Qdrant as the primary backend.
3. Leave FAISS in place until the new collection is populated and validated.
