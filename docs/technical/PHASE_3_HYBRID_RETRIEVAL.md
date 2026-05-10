# Phase 3: Hybrid Retrieval Upgrade

## Goal

Make retrieval more robust for Turkish and English queries while keeping semantic retrieval as the main signal.

## What Changed

1. Tokenization is now Unicode-safe.
2. Keyword matching is typo tolerant.
3. Retrieval can filter by `topic`, `source_kind`, `language`, and `min_confidence`.
4. `HybridRetriever` now forwards metadata filters to both semantic and keyword paths.
5. Qdrant and FAISS both honor the same filter contract.

## Keep / Replace / Remove

### Keep

1. The retrieval contract.
2. Hybrid scoring.
3. Topic alignment boosts.

### Replace

1. English-only tokenization with Unicode-safe tokenization.
2. Exact keyword overlap only with typo-tolerant matching.
3. Backend-specific filtering with a shared filter contract.

### Remove

1. Duplicate ranking branches.
2. Hardcoded English-only matching assumptions.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/unit/core/test_text_utils.py tests/unit/core/test_retrieval_filters.py tests/unit/core/test_qdrant_store.py tests/unit/core/test_hybrid_retriever_backend_switch.py tests/integration/retrieval/test_retrieval_pipeline.py tests/unit/services/test_assistant_service.py tests/integration/api/test_chat_api.py tests/integration/api/test_config_api.py
```

Result:

- 19 passed

## Notes

1. Language filtering is available as an explicit metadata filter.
2. Language-aware scoring is applied softly so Turkish queries do not lose English corpus coverage.
