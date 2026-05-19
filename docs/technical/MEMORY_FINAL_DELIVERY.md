# Memory Final Delivery

**Project:** Calma  
**Purpose:** Final handoff for the implemented memory architecture.

---

## 1. Technical Summary

The memory system now works as a layered conversational memory stack:

- full transcript is stored in the database,
- session summaries keep the current thread coherent,
- semantic profile memory stores stable user facts,
- episodic and reflective memory capture meaningful past events,
- selective scoring retrieves only the most relevant memory items,
- compaction keeps long-term memory small and useful,
- pinning preserves stable preferences and important facts,
- privacy and consent gate long-term memory usage,
- observability reports expose what memory was used,
- rollout flags allow safe staged release.

In practice, the assistant now:

- understands the current turn,
- reads the last few turns,
- recalls relevant earlier context,
- remembers stable user preferences,
- avoids storing transient or unsafe details,
- logs memory decisions for debugging and evaluation.

---

## 2. File-by-File Change Summary

### Core chat flow

| File | What changed |
|---|---|
| `server/app/services/assistant.py` | Added memory bundle assembly, selective memory recall, compaction, observability, and rollout gating |
| `server/app/services/memory_context.py` | Added memory bundle schema, turn normalization, memory scoring, selection, and debug metadata |
| `server/app/services/memory_observability.py` | Added structured memory observability reporting |
| `server/app/services/rollout.py` | Added rollout decision helper for stable/canary/off modes |

### Short-term continuity

| File | What changed |
|---|---|
| `server/app/services/session.py` | Added session summary compaction and pinned fact helpers |
| `server/app/services/session_store.py` | Continues to persist full transcript and session turns |
| `server/app/core/agents/conversation_state.py` | Helps interpret agenda, resistance, and session phase |

### Semantic and episodic memory

| File | What changed |
|---|---|
| `server/app/services/profile.py` | Stable facts are merged carefully and blocked when consent is off |
| `server/app/services/memory_store.py` | Improved extraction of profile facts, episodic events, and reflections |
| `server/app/core/agents/memory_agent.py` | Rebuilt to support parse, trend summary, and structured memory merges |
| `server/app/services/flows/session_card.py` | Keeps session-card bridge behavior intact |

### Safety, privacy, and persistence

| File | What changed |
|---|---|
| `server/app/core/safety/policy.py` | Existing safety gates remain the first stop for crisis, diagnosis, medication, and injection |
| `server/app/core/agents/safety_guardian.py` | Maintains structured safety analysis and compatibility aliasing |
| `server/app/utils/audit_logger.py` | Records redacted interaction audit events |
| `server/app/workers/retention_worker.py` | Keeps raw chat and session retention bounded |

### Evaluation and rollout

| File | What changed |
|---|---|
| `server/app/main.py` | Exposes rollout and runtime readiness values |
| `server/app/core/config.py` | Adds rollout and memory behavior flags |
| `tests/unit/services/test_memory_context*.py` | Covers memory scoring, selection, compaction, and bundle assembly |
| `tests/unit/services/test_privacy_phase6.py` | Covers consent and safety boundaries |
| `tests/unit/services/test_memory_observability.py` | Covers memory observability output |
| `tests/unit/services/test_rollout_phase8.py` | Covers rollout mode logic |

---

## 3. Production Env Checklist

### Required runtime settings

| Variable | Recommended value | Purpose |
|---|---|---|
| `DEPLOYMENT_MODE` | `local` / `staging` / `production` | Controls environment-specific behavior |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` in Docker | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5:14b` or approved production model | Active chat model |
| `RETRIEVAL_BACKEND` | `faiss` or `qdrant` | Retrieval store selection |
| `ENABLE_GRAPH_RAG` | `true` only if graph data is ready | Optional graph retrieval |
| `ROLLOUT_MODE` | `stable` / `canary` / `off` | Feature rollout control |
| `ROLLOUT_TRAFFIC_PERCENT` | `0-100` | Canary traffic percentage |
| `CHAT_TWO_STAGE_GENERATION` | `true` | Draft + compose generation flow |
| `CHAT_EVIDENCE_AUGMENTATION` | `true` | Ground answers with evidence |
| `CHAT_UNCERTAINTY_LABELS` | `true` | Show uncertainty when evidence is thin |
| `CHAT_CORPUS_V2` | `true` | Enable the updated corpus metadata pipeline |
| `CHAT_UI_SOURCE_DETAIL` | `true` | Show compact source details in UI |
| `ENABLE_RERANKER` | `true` | Re-rank retrievals before final answer |
| `SENSITIVE_LOG_REDACTION_ENABLED` | `true` | Redact sensitive data in logs |

### Data and retention settings

| Variable | Recommended value | Purpose |
|---|---|---|
| `RAW_CHAT_RETENTION_DAYS` | `90` | Raw message retention |
| `SESSION_SUMMARY_RETENTION_DAYS` | `365` | Session summary retention |
| `SCREENING_RETENTION_DAYS` | `365` | Screening data retention |
| `CONSENT_RETENTION_DAYS` | `365` | Consent record retention |
| `AUDIT_LOG_RETENTION_DAYS` | `365` | Audit log retention |

### Retrieval and model tuning

| Variable | Recommended value | Purpose |
|---|---|---|
| `TOP_K` | `5` | Number of initial retrieval candidates |
| `RERANK_TOP_K` | `3` | Number of final re-ranked sources |
| `RERANK_MAX_CHARS` | `1200` | Chunk size for reranking |
| `EVIDENCE_MIN_SCORE` | `0.22` | Minimum evidence score threshold |
| `EVIDENCE_MIN_CHUNKS` | `1` | Minimum evidence count threshold |

### Operational checklist before release

1. Verify Ollama is reachable from the backend container.
2. Confirm the database migrations are current.
3. Confirm feature flags are set for the desired rollout mode.
4. Confirm retention worker is enabled and logs are writing.
5. Confirm audit log path is writable.
6. Confirm the final corpus and FAISS index were rebuilt after PDF ingestion.
7. Confirm privacy consent gating is active.
8. Confirm observability logs show memory bundle, evidence status, and rollout decisions.

### Rollback checklist

1. Set `ROLLOUT_MODE=off`.
2. Disable `CHAT_TWO_STAGE_GENERATION` and `CHAT_EVIDENCE_AUGMENTATION` if needed.
3. Keep `CHAT_UNCERTAINTY_LABELS` on unless debugging requires otherwise.
4. Restart backend and verify `/health` and `/ready`.
5. Check that long-term memory writes stop when consent is off or safety is triggered.
