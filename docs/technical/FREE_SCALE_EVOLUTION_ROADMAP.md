# Free and Scalable Evolution Roadmap

## Why This Evolution Is Needed

The current project already has a strong base for a psychology-oriented mental health assistant:

1. onboarding and intake questions
2. topic routing
3. personalization signals from profile, memory, mood, and journal context
4. safety and refusal logic
5. retrieval-augmented generation with source-grounded behavior

This is enough for an MVP. However, if the project will grow into a university-level or global-level capstone system with many PDFs, larger corpora, and more user traffic, the current request-time retrieval stack will become the main bottleneck.

The main limitations are:

1. retrieval and ingestion are too tightly coupled to request flow
2. FAISS is good for local prototyping, but not ideal as the long-term multi-source storage layer
3. heavy PDF ingestion or embedding work can cause latency spikes and gateway timeouts
4. the system needs stronger traceability, versioning, and evaluation to look production-grade

The best direction is not to replace the personalization layer. The best direction is to preserve personalization and safety, while upgrading the retrieval/storage side into a modular, free, and scalable architecture.

## Target Principle

The target system should stay:

1. free or self-hostable
2. reproducible
3. explainable
4. clinically bounded
5. modular enough to grow with the corpus

## Project-Specific Constraints

This roadmap is tailored for this project, so the evolution should also respect these constraints:

1. personalization must stay in place
2. the assistant must remain psychoeducational, not diagnostic
3. the system must work fully with free or self-hosted components
4. Turkish text handling must remain strong, including typos and code-switching
5. request-time ingestion must be removed before the corpus grows further
6. every major model and index version must be pinned and auditable
7. the UI must continue to feel like a guided support flow, not a generic chatbot

## Recommended Target Architecture

1. UI and onboarding remain in the client.
2. Personalization data stays in PostgreSQL.
3. Safety and routing stay in the backend service.
4. PDF ingestion moves to an offline worker.
5. Embeddings are generated offline, not during request handling.
6. Vector search moves from FAISS to Qdrant OSS.
7. Retrieval becomes hybrid: vector + metadata filter + keyword layer.
8. Reranking is applied before generation.
9. Ollama remains the local LLM layer.
10. Every answer includes traceable sources and retrieval diagnostics.

## What This Gives Us

1. lower latency
2. better handling of larger PDF collections
3. better traceability
4. stronger versioning
5. cleaner test boundaries
6. easier future growth without paid infrastructure
7. better Turkish and multilingual handling
8. safer rollout with less migration risk

## Free Stack Recommendation

1. FastAPI for the backend API
2. PostgreSQL for users, sessions, profiles, memory, and logs
3. Qdrant OSS for vector retrieval
4. Ollama for local model serving
5. sentence-transformers or multilingual embedding models for embeddings
6. Redis or a simple worker queue for ingestion jobs
7. Docker Compose for local reproducibility
8. pinned model versions for embedding, reranking, and generation
9. structured observability logs for latency, retrieval scores, and refusals

## AI-Friendly Summary Roadmap

If the goal is to implement this project with the least confusion, use this short path:

### Step 1 - Freeze the current system

Keep:
- onboarding
- personalization
- safety rules

Do:
- capture baseline latency, retrieval, and model versions
- save the current behavior as the reference

Remove:
- none yet

### Step 2 - Define the contract

Keep:
- `/api/chat/`
- guided UI

Do:
- pin model versions
- define privacy and fallback rules
- make errors explicit

Remove:
- ambiguous fallback text

### Step 3 - Move ingestion offline

Keep:
- parser
- chunker
- topic extraction

Do:
- run ingestion in a worker
- generate embeddings outside chat requests
- version the corpus

Remove:
- request-time parsing and indexing

### Step 4 - Replace FAISS with Qdrant

Keep:
- retrieval interface
- hybrid scoring idea

Do:
- store chunks in Qdrant
- use metadata filters
- keep FAISS only during migration

Remove:
- FAISS from the final production path

### Step 5 - Improve answer quality

Keep:
- safety gate
- evidence gate
- grounded generation

Do:
- add reranking
- show source cards
- keep Turkish typo handling strong

Remove:
- duplicate ranking paths
- source-less default answers

### Step 6 - Test and rollout

Keep:
- evaluation set
- regression tests

Do:
- compare every phase to baseline
- roll out behind feature flags
- monitor latency and drift

Remove:
- old paths after validation

### Step 7 - Optional growth

Keep:
- core chat flow

Do:
- add GraphRAG only if corpus size justifies it

Remove:
- GraphRAG if it does not improve metrics

This is the shortest version of the roadmap and is the best version for an AI assistant to execute without confusion.

## What Should Not Change

These parts should stay as they are conceptually:

1. intake and guided flow logic
2. personalization context assembly
3. crisis and diagnosis refusal policy
4. source-grounded response requirement
5. topic-based support flows

The evolution should improve the retrieval substrate, not the human-facing guidance logic.

---

## Roadmap Overview

This roadmap is intentionally phased. Each phase has:

1. a scope
2. an implementation target
3. tests that must be added
4. a test execution step
5. an exit criterion

That structure prevents the project from becoming a large, risky rewrite.

## Global Quality Rules

These rules apply to every phase:

1. no phase should break personalization
2. no phase should move heavy ingestion into request time
3. every retrieval change must have a test and a baseline comparison
4. every model change must be pinned by version
5. every safety rule change must keep refusal behavior deterministic
6. every UI change must preserve source visibility and guided flow

## Migration Rule

Every migration step must explicitly answer three questions:

1. what stays
2. what replaces it
3. what is removed after validation

No two production implementations of the same responsibility should remain active indefinitely.

When a new path passes its tests and baseline checks:

1. the new path becomes the default
2. the old path is disabled behind a feature flag
3. the old path is removed in the next cleanup step

## System Transition Matrix

This matrix defines the current system and the intended end state for the scalable version.

| Area | Keep | Replace With | Remove | Notes |
|---|---|---|---|---|
| Personalization | Profile, memory, mood, journal, screening, intake flow | None | None | This is a strength and should remain the same conceptually. |
| Safety | Crisis detection, diagnosis refusal, evidence gate, topic gating | Structured refusal payloads and clearer logging | Ad hoc refusal messages only when they are not structured | Safety should stay deterministic. |
| Retrieval store | Retrieval interface and topic-aware query contract | Qdrant OSS | Direct FAISS usage as the final production store | Keep the interface stable while changing the backend. |
| Retrieval ranking | Hybrid retrieval idea | Hybrid retrieval with metadata filters and reranking | Duplicate or parallel final ranking paths | One ranking path should be canonical. |
| PDF ingestion | Parser, chunker, topic taxonomy | Offline worker-based ingestion | Request-time PDF parsing and indexing | Heavy work must leave the chat request path. |
| Embeddings | Free local embedding model approach | Preloaded/cached embedding model inside worker or build layer | Model downloads during chat requests | Startup or build-time loading is acceptable. |
| Generation | Ollama-based local generation | Layered prompt builder and source-grounded generation | Multiple overlapping generator fallbacks | One generator contract should be clear. |
| Observability | Logging and diagnostics intent | Structured logs, latency metrics, refusal reasons | Unstructured debug-only logging | Logs should support evaluation and debugging. |
| Frontend API access | `/api` contract and guided UI | Stable reverse proxy and typed API error handling | Ambiguous "assistant unavailable" as the only error class | The UI should distinguish timeout, auth, and service failures. |
| Storage | PostgreSQL for users, sessions, and profile data | Same | Temporary or duplicated local state for durable data | Durable state should stay centralized. |

## Decommission Policy

When a replacement is validated, the old implementation must be explicitly retired:

1. disable the old path with a feature flag
2. remove old imports and initialization code
3. delete dead fallback branches
4. update tests so they target only the new canonical path
5. update docs so there is no ambiguity about the active system

This prevents the codebase from having two competing answers for the same responsibility.

## Application-Specific Replace / Remove / Keep Map

This section maps the roadmap directly to the current application so the migration is unambiguous.

| Current App Area | Keep | Replace | Remove |
|---|---|---|---|
| Onboarding and intake flow | The guided question flow, screening steps, and profile capture | None | None |
| Personalization layer | Profile, memory, mood, journal, consent, and session summaries | None | None |
| Safety router | Crisis detection, diagnosis refusal, and evidence gating | Structured refusal payloads with clearer logs | Ad hoc fallback wording that hides the reason |
| Chat endpoint contract | `/api/chat/` request and response contract | Internal service flow behind the endpoint | Duplicate chat processing paths |
| Retrieval interface | Topic-aware retrieval contract and source-card output | Qdrant-backed retrieval engine | Final production FAISS path |
| Retrieval ranking | Hybrid scoring behavior | Metadata-aware hybrid scoring + reranking | Parallel ranking branches that compete with each other |
| PDF ingestion | Parser, chunker, and corpus building logic | Offline worker and versioned ingestion pipeline | Request-time parsing, chunking, and embedding generation |
| Embedding backend | Local embedding model concept | Preloaded and cached embedding worker | Downloading or initializing embedding models during chat |
| Generation layer | Ollama-based local generation | Clear prompt builder and grounded answer contract | Multiple overlapping generator fallbacks |
| Error handling UI | User-facing support flow and friendly guidance | Distinct errors for timeout, auth, and unavailable service | A single generic "assistant unavailable" message for everything |
| Storage layer | PostgreSQL for durable app data | Same | Shadow copies of user/session data in temporary stores |
| Logging | Development and audit logs | Structured metrics and refusal reasons | Debug-only logs with no evaluation value |

### App-Specific Rule Set

1. if a new retrieval backend is introduced, the old one must be disabled after validation
2. if a new ingestion worker is introduced, request-time ingestion must be removed
3. if a new refusal format is introduced, the old unstructured message must be removed
4. if a new source-card format is introduced, the old source-less response must be removed
5. if a new model version is introduced, the old pinned model config must be cleaned up to avoid ambiguity

## Repository Implementation Map

This section ties the roadmap to the actual project files so the implementation stays concrete.

| Layer | Current Files | Keep | Replace | Remove |
|---|---|---|---|---|
| Intake and onboarding | `client/src/App.jsx`, `server/app/services/flows/intake_chat.py`, `server/app/services/profile.py` | Guided questions, onboarding state, profile capture | None | None |
| Chat API contract | `server/app/api/chat/routes.py`, `server/app/models/schemas/chat.py`, `client/src/App.jsx` | `/api/chat/` endpoint contract and response shape | Internal orchestration flow inside `AssistantService` | Duplicate chat branches or alternate chat endpoints |
| Personalization | `server/app/services/assistant.py`, `server/app/services/profile.py`, `server/app/services/memory.py`, `server/app/services/mood.py`, `server/app/services/journal.py` | Profile, memory, mood, journal, screening context | None | None |
| Safety | `server/app/core/agents/safety_guardian.py`, `server/app/core/retrieval/evidence_gate.py`, `server/app/core/generation/generator.py` | Crisis detection, diagnosis refusal, evidence-based abstention | Structured refusal payloads and explicit refusal reasons | Unstructured generic fallback text |
| Retrieval backend | `server/app/core/retrieval/faiss_store.py`, `server/app/core/retrieval/hybrid_retriever.py`, `server/app/core/retrieval/retriever.py`, `server/app/core/retrieval/index_store.py` | Retrieval contract and top-k semantics | `QdrantStore` or equivalent Qdrant-backed repository | Final production FAISS usage |
| PDF ingestion | `server/app/services/pdf_pipeline.py`, `server/app/core/retrieval/pdf_ingestion.py`, `server/app/core/retrieval/ingestion/*` | Parser, chunker, topic extraction logic | Offline worker pipeline and versioned ingestion job | Request-time ingestion or rebuild logic |
| Embeddings | `server/app/core/retrieval/embeddings.py`, `requirements.txt`, `compose.yaml` | Local embedding approach | Preloaded embedding model, cached at build/startup | Runtime model download during chat |
| Generation | `server/app/core/generation/llm.py`, `server/app/core/generation/generator.py` | Ollama-based generation and grounded response contract | Prompt builder, timeout policy, source-grounded output shape | Multiple overlapping fallback generators |
| Frontend API behavior | `client/src/App.jsx`, `client/src/config.js`, `client/vite.config.js`, `client/nginx.conf.template` | `/api` proxy pattern and guided UI | Typed error handling for timeout/auth/availability | Single generic "assistant unavailable" message for all failures |
| Deployment | `compose.yaml`, `Dockerfile.server`, `client/Dockerfile` | Docker Compose flow and local reproducibility | Add Qdrant and worker services, plus persistent volumes | Hidden or ad hoc runtime setup |
| Storage | `server/app/core/database.py`, `server/app/models/sql/*`, `data/store/*` | PostgreSQL-backed durable app state | Same | Duplicate durable state in temp files |

### File-Level Concrete Changes

1. `server/app/services/assistant.py`
   - keep personalization assembly
   - replace direct FAISS dependency with a retrieval repository interface
   - remove any request-time heavy initialization

2. `server/app/core/retrieval/faiss_store.py`
   - keep only as temporary migration support
   - remove from the canonical production path after Qdrant validation

3. `server/app/core/retrieval/hybrid_retriever.py`
   - keep hybrid scoring logic
   - replace final storage reads with Qdrant searches
   - remove parallel final ranking branches

4. `server/app/core/retrieval/pdf_ingestion.py`
   - keep topic extraction and chunk building rules
   - move execution into an offline worker
   - remove request-time corpus rebuild assumptions

5. `server/app/core/generation/generator.py`
   - keep grounded generation
   - replace generic insufficient-evidence handling with structured refusal and clear fallback reasons
   - remove duplicate fallback wording paths

6. `client/src/App.jsx`
   - keep guided chat and onboarding UI
   - replace generic error fallback with typed error states
   - remove ambiguity between timeout, auth, and backend unavailability

7. `compose.yaml`
   - keep backend/frontend services
   - replace retrieval backend wiring with Qdrant and worker services
   - remove any remaining implicit request-time indexing behavior

### Concrete Replacement Rules by Area

1. If Qdrant is introduced, FAISS stays only during migration and is removed after validation.
2. If offline ingestion is introduced, any request-time index build must be deleted.
3. If structured refusal is introduced, generic refusal strings must be removed.
4. If source cards are introduced, source-less answers must be retired from the default path.
5. If timeout-safe generation is introduced, old long-running fallback branches must be removed.

## Operational Phase Checklists

This section turns each phase into a practical execution checklist. Each phase should be executed in the order below: implement, test, validate, clean up.

### Phase 0 Operational Checklist

1. capture the current runtime state from `compose.yaml`, `server/app/core/config.py`, and `client/src/config.js`.
2. record the active embedding model, generator model, and retrieval backend.
3. create a baseline markdown artifact under `docs/technical/`.
4. run the current regression suite.
5. collect sample latency numbers for `/api/chat/`, `/api/config`, and `/health`.
6. mark the baseline as the reference state before migration starts.

### Phase 0.5 Operational Checklist

1. add or update config entries for model versions and backend flags.
2. add privacy and retention rules to documentation.
3. add redaction hooks for sensitive debug output.
4. add tests for consent, fallback, and pinned version expectations.
5. verify that the app still starts with the new contract in place.
6. remove any temporary config ambiguity before moving forward.

### Phase 1 Operational Checklist

1. create the offline ingestion worker entrypoint.
2. move PDF parsing and chunking to the worker.
3. keep the request handler free from corpus rebuild logic.
4. emit version hashes and ingestion metrics.
5. add tests that prove ingestion works without a chat request.
6. remove any leftover request-time ingestion path after verification.

### Phase 2 Operational Checklist

1. add the Qdrant client and collection schema.
2. implement dual-write from ingestion to both FAISS and Qdrant.
3. add a feature flag to read from Qdrant first.
4. compare retrieval results between FAISS and Qdrant on the baseline set.
5. switch the default path to Qdrant once the results are stable.
6. delete the old final-production FAISS path after the switch.

### Phase 3 Operational Checklist

1. wire metadata filters into the retriever.
2. keep keyword fallback but make semantic retrieval the main path.
3. add typo tolerance for Turkish and English mental-health terms.
4. run query-specific precision checks on the gold set.
5. remove any duplicate ranking logic that still competes with the canonical path.
6. document the final retrieval contract.

### Phase 4 Operational Checklist

1. add reranking to the top retrieval candidates only.
2. log before/after scores for each query.
3. measure whether reranking improves answer quality on the baseline set.
4. remove any extra ranking branches that are no longer needed.
5. keep reranking behind a flag until validation is complete.
6. finalize the prompt context size limits.

### Phase 5 Operational Checklist

1. keep crisis and diagnosis refusal before generation.
2. keep evidence gate checks before grounded generation.
3. separate low-evidence, crisis, and off-domain logs.
4. add tests for all refusal and abstention paths.
5. replace unstructured fallback text with structured refusal payloads.
6. remove dead refusal strings after the new payload is active.

### Phase 6 Operational Checklist

1. add source cards to the response payload.
2. render source metadata in the UI.
3. keep source confidence and page details visible.
4. add tests for source visibility and response shape.
5. remove source-less default responses.
6. ensure the UI still works when sources are empty or unavailable.

### Phase 7 Operational Checklist

1. define the gold set and expected outputs.
2. add retrieval, safety, Turkish, and personalization subsets.
3. run evaluation before and after each migration phase.
4. store evaluation results in docs or artifacts.
5. remove obsolete tests that target retired paths.
6. keep regression tests aligned with the canonical path only.

### Phase 8 Operational Checklist

1. enable feature-flagged rollout.
2. monitor latency, failures, and retrieval drift.
3. verify the fallback route works when Qdrant or Ollama is unavailable.
4. gradually switch traffic to the new path.
5. remove the old path only after the rollout is stable.
6. update docs to reflect the final active architecture.

### Phase 9 Operational Checklist

1. check whether the corpus size actually justifies GraphRAG.
2. if needed, build the graph as an optional side path.
3. keep GraphRAG separate from the core chat flow.
4. add tests for graph extraction and graph retrieval.
5. remove the pilot if it does not improve baseline metrics.
6. keep it disabled unless there is a clear measurable benefit.

## Phase Closure Template

Every phase must end with the same closure sequence:

1. validate the new path with its own tests
2. compare the new path against the baseline
3. switch the default to the new path
4. remove or disable the old path
5. rerun the regression suite
6. update the roadmap and technical docs

If the old path cannot be removed yet, it must at least be isolated behind a flag and marked as temporary.

## Granular Task Breakdown

This section splits the roadmap into smaller execution tasks so each phase can be implemented, tested, and verified with less risk.

### Phase 0 Task Breakdown

1. inventory the current backend flow, retrieval stack, and model names.
2. create the baseline question set with retrieval, safety, and personalization examples.
3. run the current system on the baseline set and capture latency, refusal reason, and source usage.
4. snapshot the current corpus version, embedding model version, and generator model version.
5. add or update regression tests for the current stable behavior.
6. store the baseline report in the docs folder.

### Phase 0.5 Task Breakdown

1. define the data retention, consent, and redaction rules for logs and memory.
2. pin the embedding, reranker, and generator versions in config.
3. define fallback behavior for unavailable retrieval or model backends.
4. add a local-only deployment mode for development and demos.
5. add tests for consent gating, redaction, version snapshots, and fallback behavior.
6. document the governance contract in the technical docs.

### Phase 1 Task Breakdown

1. move PDF parsing and chunking out of request handling.
2. create a worker entrypoint for offline ingestion.
3. emit version hashes and ingestion metrics for every corpus build.
4. keep the current parser and chunker logic but run them asynchronously.
5. add ingestion tests for empty PDF directories, invalid PDFs, and version stability.
6. verify that chat requests no longer wait for ingestion work.

### Phase 2 Task Breakdown

1. define the Qdrant payload schema for chunk metadata.
2. implement Qdrant collection creation and upsert logic.
3. write a temporary dual-write path so FAISS and Qdrant can coexist during migration.
4. add a feature flag to choose the retrieval backend.
5. add tests that validate payload mapping, dual-write consistency, and search results.
6. switch the default read path to Qdrant after validation.

### Phase 3 Task Breakdown

1. add metadata filters for topic, source kind, language, and confidence.
2. keep semantic retrieval as the primary signal and keyword retrieval as the fallback signal.
3. add typo tolerance for common Turkish and English mental-health terms.
4. tune topic boost values against the current corpus distribution.
5. add tests for Turkish typo queries, code-switched queries, and off-topic suppression.
6. measure whether hybrid retrieval improves Precision@5.

### Phase 4 Task Breakdown

1. choose a lightweight reranking strategy.
2. apply reranking only to the top retrieved candidates.
3. log pre-rerank and post-rerank scores for comparison.
4. keep reranking behind a feature flag during rollout.
5. add tests for reranker ordering, truncation, and context-size limits.
6. verify that the generator receives only the best evidence chunks.

### Phase 5 Task Breakdown

1. keep safety checks before generation.
2. preserve crisis, diagnosis, and treatment refusal rules.
3. preserve evidence gate behavior for weak retrievals.
4. separate low-evidence, off-domain, and crisis cases in logs.
5. add tests for refusal correctness, crisis escalation, and grounded answers.
6. verify that unsupported requests are handled deterministically.

### Phase 6 Task Breakdown

1. return source metadata from the backend response.
2. show PDF name, section, page, and confidence in the UI.
3. display retrieval diagnostics for transparency and debugging.
4. add UI badges for source kind and confidence.
5. add tests for response shape, source cards, and UI rendering.
6. verify that every answer has traceable source information.

### Phase 7 Task Breakdown

1. define a 20 to 30 question gold set.
2. split the gold set into retrieval, safety, Turkish, and personalization subsets.
3. add evaluation scripts for Recall@K, groundedness, refusal accuracy, and latency.
4. compare each migration phase against the baseline results.
5. add regression tests for query classes that previously failed.
6. store evaluation outputs in the docs or artifacts folder.

### Phase 8 Task Breakdown

1. run the new ingestion and retrieval path in parallel with the old path.
2. enable a feature-flag-based rollout for backend selection.
3. monitor latency, failures, and retrieval score drift.
4. keep rollback available until the new path is stable on the full gold set.
5. add failover tests for Qdrant, Ollama, and fallback routing.
6. switch traffic gradually only after validation.

### Phase 9 Task Breakdown

1. measure whether corpus size and relation density justify GraphRAG.
2. extract entities and relations from the corpus only if needed.
3. keep graph-backed retrieval optional and isolated from core chat flow.
4. add tests for entity extraction, relation extraction, and graph retrieval.
5. route only graph-friendly queries to the graph path.
6. keep GraphRAG as an enhancement, not a dependency.

---

## Phase 0 - Baseline and Freeze

### Goal

Stabilize the current system before making architectural changes.

### Scope

1. Document current request flow.
2. Measure current latency for a few representative queries.
3. Record current retrieval quality and refusal behavior.
4. Freeze the existing behavior as the baseline.
5. record current model names, embedding model names, and corpus version identifiers.
6. define a simple latency budget for chat, retrieval, and ingestion.

### Implementation Tasks

1. create a baseline evaluation set with 20 to 30 questions
2. record current answer type, latency, and source usage
3. capture current retrieval results for each query

### Tests to Add

1. regression tests for current safety refusals
2. regression tests for topic routing
3. retrieval snapshot tests for a few representative queries
4. config snapshot tests for pinned model and corpus versions

### Test Command

```bash
pytest tests/unit/core/test_routing.py tests/unit/core/test_generation.py tests/unit/core/test_evidence_gate.py tests/unit/services/test_assistant_service.py
```

### Exit Criterion

The current behavior is documented and protected by tests.

---

## Phase 0.5 - Governance, Privacy, and Model Contract

### Goal

Define the rules that keep the project safe, free, and reproducible as it scales.

### Scope

1. keep user data minimized and local where possible
2. define retention rules for logs and memory data
3. define consent boundaries for personalization inputs
4. pin versions for embedding, reranker, generator, and chunker models
5. define what happens when a model or retrieval backend is unavailable

### Implementation Tasks

1. add a privacy and retention policy document
2. add config fields for model versions and retrieval backend versions
3. add a local-only deployment mode
4. add redaction for sensitive logs and debug output

### Tests to Add

1. consent gating tests
2. redaction tests
3. model version snapshot tests
4. fallback behavior tests for unavailable backends

### Test Command

```bash
pytest tests/unit/services/test_assistant_service.py tests/unit/core/test_generation.py
```

### Exit Criterion

The project has a clear privacy, versioning, and fallback contract before deeper migration begins.

---

## Phase 1 - Offline Ingestion Worker

### Goal

Move PDF parsing, chunking, and embedding generation out of the request path.

### Scope

1. create a background ingestion job
2. parse PDFs offline
3. chunk and classify documents offline
4. write corpus and metadata into persistent storage
5. emit ingestion metrics and corpus version hashes

### Implementation Tasks

1. keep the existing parser and chunker
2. wrap ingestion in a worker entrypoint
3. produce a versioned corpus artifact
4. stop doing heavy document work during user chat requests
5. store ingestion logs with pdf count, chunk count, and version ids

### Tests to Add

1. ingestion unit tests for PDF directory processing
2. corpus versioning tests
3. test that empty or invalid PDFs do not crash ingestion
4. test that ingestion emits a stable version hash

### Test Command

```bash
pytest tests/unit/services/test_pdf_pipeline.py tests/unit/core/test_routing.py
```

### Exit Criterion

PDF ingestion can run independently from chat requests.

---

## Phase 2 - Qdrant Vector Store

### Goal

Replace FAISS as the primary long-term retrieval store with Qdrant OSS.

### Scope

1. create a Qdrant collection for chunks
2. store chunk metadata as payload
3. upsert embeddings after ingestion
4. query Qdrant during retrieval
5. support dual-write during migration, then switch by feature flag

### Implementation Tasks

1. define a chunk payload schema
2. map topic, source kind, PDF filename, page, confidence, and version into payload
3. implement Qdrant upsert during ingestion
4. implement Qdrant search in the retriever
5. keep FAISS as a temporary fallback until Qdrant is validated
6. add payload version and corpus version into every point

### Tests to Add

1. Qdrant repository unit tests with mocked client
2. payload mapping tests
3. retrieval integration test for a seeded collection
4. dual-write consistency test

### Test Command

```bash
pytest tests/unit/core/test_qdrant_store.py tests/unit/core/test_retrieval.py
```

### Exit Criterion

The retriever can find relevant chunks from Qdrant and return payload-aware results.

---

## Phase 3 - Hybrid Retrieval

### Goal

Improve retrieval quality with vector search, keyword matching, and metadata filters.

### Scope

1. hybridize retrieval
2. apply topic and source filters
3. keep typo-tolerant query handling
4. reduce noise from irrelevant chunks
5. handle Turkish and code-switched queries more reliably
6. keep metadata filters strong for source type, language, and confidence

### Implementation Tasks

1. preserve the current keyword fallback logic
2. add metadata filtering for topic and source kind
3. keep semantic search as the main signal
4. use fusion scoring when multiple candidate sets are available
5. tune topic boosts using the current corpus topic distribution
6. add a small Turkish typo dictionary for common mental-health terms

### Tests to Add

1. test that topic filters improve precision
2. test that keyword fallback still works on weak queries
3. test that noise chunks do not dominate top-k results
4. test Turkish typo and code-switch queries

### Test Command

```bash
pytest tests/unit/core/test_evidence_gate.py tests/unit/core/test_routing.py tests/unit/core/test_retrieval.py
```

### Exit Criterion

Relevant results are ranked higher, and off-topic results are reduced.

---

## Phase 4 - Reranking

### Goal

Improve top-k precision before generation.

### Scope

1. rerank retrieved chunks
2. keep only the best evidence for the prompt
3. avoid context overload
4. make reranking optional behind a feature flag during rollout

### Implementation Tasks

1. choose a light reranker strategy
2. rerank the first retrieval pass
3. pass only top evidence to the generator
4. log pre-rerank and post-rerank scores for evaluation

### Tests to Add

1. reranker ordering tests
2. top-k truncation tests
3. prompt context size tests
4. rerank feature flag tests

### Test Command

```bash
pytest tests/unit/core/test_reranker.py tests/unit/core/test_generation.py
```

### Exit Criterion

Top evidence is more relevant than the raw retrieval output.

---

## Phase 5 - Safety and Groundedness

### Goal

Keep the assistant bounded, safe, and evidence-driven.

### Scope

1. preserve crisis routing
2. preserve diagnosis refusal
3. preserve unsupported medical advice refusal
4. preserve evidence gate behavior
5. preserve crisis escalation and safe fallback behavior when the LLM is unavailable

### Implementation Tasks

1. keep safety before generation
2. keep evidence gate before answer generation when RAG is needed
3. return structured fallback when evidence is not enough
4. distinguish low-evidence, off-domain, and crisis cases in the logs

### Tests to Add

1. crisis detection tests
2. diagnosis refusal tests
3. insufficient evidence tests
4. grounded answer tests
5. crisis escalation routing tests

### Test Command

```bash
pytest tests/unit/core/test_generation.py tests/unit/core/test_evidence_gate.py tests/unit/services/test_assistant_service.py
```

### Exit Criterion

The assistant refuses unsafe or unsupported requests reliably.

---

## Phase 6 - Source Transparency

### Goal

Make every answer traceable and reviewable.

### Scope

1. show citations in the response UI
2. include source metadata in the API response
3. expose retrieval diagnostics for debugging
4. make source cards visible in the UI with page and section labels

### Implementation Tasks

1. return source cards from backend
2. show PDF name, page, and section in UI
3. keep retrieval score and confidence visible in logs
4. add confidence and source-kind badges in the UI

### Tests to Add

1. API response shape tests for source metadata
2. UI rendering tests for source cards
3. diagnostics field presence tests
4. UI snapshot tests for source cards and confidence badges

### Test Command

```bash
pytest tests/unit/services/test_assistant_service.py tests/integration/api/test_chat_api.py
```

### Exit Criterion

Users can see why the assistant gave a specific answer.

---

## Phase 7 - Evaluation Harness

### Goal

Make quality measurable.

### Scope

1. create a small gold set
2. test retrieval quality
3. test safety and refusal correctness
4. test latency
5. test Turkish typo handling and code-switching
6. test retrieval behavior by topic, source kind, and confidence bucket

### Implementation Tasks

1. define a 20 to 30 question evaluation set
2. label expected topics and desired behavior
3. track metrics before and after each migration phase
4. split the gold set into retrieval, safety, personalization, and Turkish language subsets

### Tests to Add

1. retrieval recall test
2. groundedness smoke test
3. refusal accuracy test
4. latency budget test
5. Turkish query regression test
6. personalization signal regression test

### Test Command

```bash
pytest tests/unit/core/test_routing.py tests/unit/core/test_generation.py tests/unit/core/test_evidence_gate.py
```

### Exit Criterion

Every major change can be measured and compared against baseline.

---

## Phase 8 - Controlled Rollout

### Goal

Deploy the new architecture safely.

### Scope

1. run the new ingestion and retrieval path in parallel
2. compare outputs with the old path
3. switch traffic gradually
4. keep rollback available until the new path is stable for the full test set

### Implementation Tasks

1. add feature flags for retrieval backend selection
2. keep fallback to previous behavior during rollout
3. monitor failures and latency
4. expose deployment health metrics for retrieval, generation, and ingestion separately

### Tests to Add

1. feature flag routing tests
2. fallback path tests
3. healthcheck tests for Qdrant and Ollama
4. failover tests for retrieval backend fallback

### Test Command

```bash
pytest tests/unit/core/test_routing.py tests/unit/services/test_assistant_service.py
```

### Exit Criterion

The new stack runs stably in production-like conditions.

---

## Phase 9 - Optional GraphRAG

### Goal

Add graph reasoning only if the corpus becomes large enough to justify it.

### Scope

1. entity extraction
2. relation extraction
3. graph-backed retrieval
4. community summaries
5. activate only if corpus size and relation density justify the extra complexity

### Implementation Tasks

1. build a small entity graph from the corpus
2. link topics, symptoms, interventions, and sources
3. route only graph-friendly queries into the graph path
4. keep graph output optional and never required for core chat flows

### Tests to Add

1. entity extraction tests
2. relation extraction tests
3. graph retrieval correctness tests

### Test Command

```bash
pytest tests/unit/core/test_graph_store.py
```

### Exit Criterion

GraphRAG is treated as an optional enhancement, not a required dependency.

---

## Recommended Build Order

1. freeze baseline
2. define governance, privacy, and model contract
3. move ingestion offline
4. introduce Qdrant with dual-write and fallback
5. keep hybrid retrieval
6. add reranking
7. keep safety and grounding
8. expose citations
9. build evaluation harness
10. roll out gradually
11. add GraphRAG only if needed

## Success Metrics

1. lower latency
2. better retrieval precision
3. higher grounded answer quality
4. fewer unsupported answers
5. fewer timeouts
6. clearer source transparency
7. stable behavior under larger PDF loads
8. strong Turkish query handling
9. predictable fallback behavior during outages

## Final Definition of Done

The project is considered evolved successfully when:

1. ingestion is offline
2. retrieval is powered by Qdrant OSS
3. personalization remains intact
4. safety and refusal logic remain intact
5. citations are visible
6. tests exist for every phase
7. the system can scale to a larger PDF corpus without request-time bottlenecks
8. the system preserves personalization while moving retrieval to a scalable backend
