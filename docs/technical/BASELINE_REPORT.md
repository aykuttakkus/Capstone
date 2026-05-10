# Baseline Report

## Purpose

This document freezes the current system state before any migration work begins.

## Current System Snapshot

### Backend

1. FastAPI application with routes mounted under `/api`.
2. Chat flow handled by `server/app/api/chat/routes.py` and `server/app/services/assistant.py`.
3. Current retrieval path uses a FAISS-backed hybrid retriever.
4. Current generation path uses Ollama.
5. Current embedding model is `all-MiniLM-L6-v2`.
6. Current local LLM model is `mistral:latest`.

### Frontend

1. React app uses `client/src/App.jsx` as the main chat shell.
2. API calls default to `/api`.
3. Nginx reverse proxy forwards `/api/` to the backend service.

### Personalization

1. Profile, memory, mood, journal, and screening signals are already part of the chat flow.
2. The assistant assembles personalized context before generating the answer.

### Safety

1. Crisis and diagnosis refusal behavior already exists.
2. Evidence gating is used before grounded generation.
3. The assistant can fall back to structured insufficient-evidence responses.

## Baseline Test Status

The current core regression suite is passing:

```bash
pytest tests/unit/core/test_routing.py tests/unit/core/test_generation.py tests/unit/core/test_evidence_gate.py tests/unit/services/test_assistant_service.py
```

Result:

- 16 passed
- 2 warnings

## Known Baseline Constraints

1. Request-time chat still performs retrieval, generation, and persistence work in one request cycle.
2. FAISS is still the production retrieval store.
3. PDF ingestion is still coupled to the current corpus/indexing flow.
4. The stack already works, but it is not yet optimized for large-scale PDF growth.
5. The current system is the reference behavior and should not be changed until the next phase passes validation.

## Baseline Success Criteria

This baseline is valid if all of the following remain true:

1. onboarding and personalization still work
2. safety refusals still work
3. retrieval still returns grounded sources
4. chat API still responds through `/api/chat/`
5. the current regression tests remain green

## Baseline Owner Note

The next phase should preserve the current user-facing flow while moving heavy retrieval and ingestion work into a more scalable architecture.
