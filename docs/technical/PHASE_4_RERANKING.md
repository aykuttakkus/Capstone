# Phase 4: Evidence Reranking

## Goal

Select the best evidence candidates before nuggetization, grounding, and source reporting.

## What Changed

1. Added a dedicated `EvidenceReranker`.
2. The reranker now orders candidates by score, topic alignment, confidence, and metadata signals.
3. The reranker limits the candidate set by both `top_k` and total context budget.
4. `AssistantService` now reranks retrieved chunks before nuggetization and grounding.

## Keep / Replace / Remove

### Keep

1. The retrieval contract.
2. Evidence gate behavior.
3. Source reporting.

### Replace

1. Raw retrieval order with reranked evidence order.
2. Unlimited candidate context with a bounded evidence budget.

### Remove

1. Duplicate ranking logic inside the chat flow.
2. Long candidate lists that are not used for grounding.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/unit/core/test_reranker.py tests/unit/services/test_assistant_service.py tests/integration/api/test_config_api.py tests/unit/core/test_qdrant_store.py tests/unit/core/test_hybrid_retriever_backend_switch.py tests/integration/retrieval/test_retrieval_pipeline.py
```

Result:

- 14 passed

## Notes

1. Reranking can be disabled through `ENABLE_RERANKER=false`.
2. Default settings keep reranking enabled with `top_k=3` and a `1200` character context budget.
