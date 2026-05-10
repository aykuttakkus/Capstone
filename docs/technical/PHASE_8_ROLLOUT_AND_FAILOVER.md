# Phase 8: Controlled Rollout and Failover

## Goal

Roll out backend changes safely while keeping fallback paths available.

## What Changed

1. Added rollout flags to config and environment settings.
2. Added readiness helpers for database, local index, Qdrant, and Ollama.
3. Readiness can now report `ready`, `degraded`, or `not_ready`.
4. Qdrant fallback to the local index remains available.
5. Ollama failures can be tolerated as a degraded mode when fallback is enabled.

## Keep / Replace / Remove

### Keep

1. Existing chat flow.
2. Existing fallback retrieval path.
3. Existing offline generation fallback behavior.

### Replace

1. Single flat readiness state with a richer readiness contract.
2. Hidden rollout behavior with explicit flags.

### Remove

1. Ambiguous deployment assumptions that do not expose fallback state.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/integration/api/test_config_api.py tests/integration/api/test_readiness_api.py tests/unit/core/test_hybrid_retriever_backend_switch.py tests/unit/services/test_assistant_service.py tests/unit/core/test_qdrant_store.py tests/integration/api/test_chat_api.py
```

Result:

- 17 passed

## Notes

1. `ROLLOUT_MODE` and `ROLLOUT_TRAFFIC_PERCENT` are visible in config.
2. `ENABLE_QDRANT_FALLBACK` and `ENABLE_OLLAMA_FALLBACK` decide whether a dependency failure turns into degraded mode or full not-ready.
3. Qdrant health is checked separately from the local FAISS index.
