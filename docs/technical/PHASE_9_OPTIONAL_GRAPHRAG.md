# Phase 9: Optional GraphRAG

## Goal

Keep GraphRAG as an optional side path for larger corpora and graph-friendly questions, without affecting the core chat flow.

## What Changed

1. Added graph enablement flags to config.
2. Added corpus-size and query-shape gates for GraphRAG activation.
3. GraphRAG now runs only when it is explicitly enabled and the corpus is large enough.
4. Graph boosts are only applied for graph-friendly queries.
5. Core vector, keyword, and hybrid retrieval remain the default path.

## Keep / Replace / Remove

### Keep

1. Core chat flow.
2. Vector retrieval.
3. Keyword retrieval.
4. Safety and evidence gates.

### Replace

1. Always-on graph traversal with opt-in GraphRAG gating.

### Remove

1. Any assumption that graph reasoning should be part of every query.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/unit/core/test_graph_store.py tests/unit/core/test_hybrid_retriever_backend_switch.py tests/integration/api/test_config_api.py tests/unit/services/test_assistant_service.py tests/integration/api/test_chat_api.py
```

Result:

- 17 passed

## Notes

1. GraphRAG is disabled by default.
2. It becomes eligible only if `ENABLE_GRAPH_RAG=true` and the corpus meets the minimum size threshold.
3. Graph-friendly queries include relational and cross-topic questions.
