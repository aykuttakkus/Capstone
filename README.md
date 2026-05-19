# Calma

## Overview
Calma is a psychology-oriented RAG assistant for psychoeducational support. It answers from curated mental-health sources, keeps responses grounded in retrieved evidence, and applies safety checks for crisis, medication, and prompt-injection cases. The project is built for local development and capstone/jury review with FastAPI, React 19, SQLite, FAISS, and Ollama.

## Features
- Chat UI with session persistence and sidebar history.
- Source-grounded responses from curated PDF knowledge.
- Hybrid retrieval with FAISS and optional Qdrant support.
- Optional graph-based retrieval for eligible queries.
- Independent safety layer for crisis, self-harm, medication, and injection signals.
- User context from profile, mood, journal, and conversation history.
- Offline evaluation and jury benchmark tooling.

## Architecture
- Backend: `server/app/main.py` boots FastAPI, mounts API routers, and exposes health/readiness endpoints.
- Chat flow: `server/app/api/chat/routes.py` loads user state, runs RAG augmentation, generates responses with `server/app/services/conversational_assistant.py`, applies safety checks, and persists sessions through `server/app/services/session_store.py`.
- Retrieval: `server/app/core/retrieval/` contains the corpus loader, hybrid retriever, FAISS/Qdrant backends, reranking, and optional graph RAG.
- Safety: `server/app/services/risk_detection.py` scans user and assistant text for crisis and medication signals, while the assistant also checks for prompt injection.
- Frontend: `client/src/App.jsx` implements the React 19 + Vite UI, including chat, session list, and supporting profile/mood/journal screens.
- Evaluation: `tests/jtest.py` is the primary jury benchmark; `server/app/evaluation/` contains offline evaluation runners and datasets.

## Project Structure
- `server/app/main.py` FastAPI entrypoint and router wiring.
- `server/app/api/` HTTP routes for chat, sessions, auth, feedback, journal, mood, profile, and screening.
- `server/app/services/` conversation, RAG, safety, session, profile, mood, and journal services.
- `server/app/core/retrieval/` corpus loading, retrieval backends, reranking, and graph store code.
- `server/app/core/generation/` Ollama client and generation helpers.
- `server/app/evaluation/` evaluation runners and benchmark datasets.
- `client/src/` React UI, styling, assets, and API config.
- `data/raw/` source PDFs used to build the knowledge base.
- `data/indexes/` chunked index inputs used by offline index-building scripts.
- `data/store/` runtime SQLite, FAISS, and session-memory artifacts.
- `tests/` automated test suite and `tests/jtest.py` benchmark runner.
- `benchmarks/` generated benchmark reports and latest jury outputs.
- `build_faiss_indexes.py` and `refine_pdf_audit.py` offline data/index maintenance scripts.
- `compose.yaml`, `compose.override.yaml`, `compose.frontend-standalone.yaml` Docker runtime definitions.

## Installation
Requires Python 3, Node.js, and Ollama for local development.

1. Install dependencies:

```bash
make install
```

2. Start Ollama and make sure the configured model is available.

3. For a containerized setup, run:

```bash
make run-stack
```

## Environment Variables
Defaults are defined in `.env.example` and `compose.yaml`.

- `APP_NAME`, `DEPLOYMENT_MODE`, `BACKEND_HOST`, `BACKEND_PORT`
- `RETRIEVAL_BACKEND`, `QDRANT_URL`, `QDRANT_COLLECTION`
- `ENABLE_GRAPH_RAG`, `GRAPH_RAG_MIN_CHUNKS`, `GRAPH_RAG_MIN_QUERY_TERMS`
- `ENABLE_QDRANT_FALLBACK`, `ENABLE_OLLAMA_FALLBACK`
- `ENABLE_RERANKER`, `RERANK_TOP_K`, `RERANK_MAX_CHARS`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- `FRONTEND_ORIGINS`, `VITE_API_URL`, `FRONTEND_API_UPSTREAM`
- `TOP_K`, `EVIDENCE_MIN_SCORE`, `EVIDENCE_MIN_CHUNKS`, `EMBEDDING_MODEL`
- `MODEL_CONTRACT_VERSION`, `SENSITIVE_LOG_REDACTION_ENABLED`
- `RAW_CHAT_RETENTION_DAYS`, `SESSION_SUMMARY_RETENTION_DAYS`, `SCREENING_RETENTION_DAYS`, `CONSENT_RETENTION_DAYS`, `AUDIT_LOG_RETENTION_DAYS`

## Usage
- Backend: `make run-server`
- Frontend: `make run-client`
- Full stack: `make run-stack`
- Default dev stack: `make docker-dev`
- Production-style compose stack: `make docker-prod`
- Frontend only: `make docker-frontend-standalone`
- Seed runtime store volume: `make docker-init-store`

## Testing & Benchmark
- Unit tests: `make test-unit`
- Integration tests: `make test-integration`
- All backend tests: `make test`
- Delivery check: `make verify`
- Jury benchmark and evaluations: `make test-eval`
- Frontend validation: `make frontend-check`
- Compose validation: `make compose-check`

## Safety Boundaries
- Calma does not diagnose conditions.
- Calma does not prescribe, recommend, or adjust medication.
- Crisis, self-harm, and severe risk signals are escalated to urgent human-support guidance.
- Prompt-injection attempts are rejected.
- Answers are grounded in retrieved sources when available.

## Limitations
- Full behavior depends on a local Ollama server and the configured model.
- Retrieval quality depends on the source PDFs and generated indices.
- The system is not a replacement for clinicians, emergency services, or medical care.
- Safety detection is conservative and may produce false positives.
- When retrieval or LLM backends are unavailable, the system degrades rather than failing silently.
