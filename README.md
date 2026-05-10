# Calma

Calma is a psychology-oriented, safety-aware RAG assistant for psychoeducational mental health support. It is designed to answer from curated sources, refuse unsafe requests, and stay grounded in evidence.

## Stack

- Backend: FastAPI, SQLAlchemy async, SQLite
- Frontend: React 19 + Vite
- Retrieval: FAISS by default, Qdrant optional
- LLM: Ollama, default model `mistral:latest`
- Embeddings: `sentence-transformers` (`all-MiniLM-L6-v2`)

## Prerequisites

- Docker and Docker Compose, or
- Python with `pip`
- Node.js with `npm`
- Ollama running locally for non-Docker development

The repo does not pin a Python version, so use a modern Python 3 release that works with the pinned dependencies.

## Quick Start

The fastest path is Docker Compose:

```bash
docker compose up --build
```

This starts the backend, frontend, and Qdrant. The base compose file also exposes the backend on `8000` and the frontend on `8080`.

Open:

- Frontend: `http://localhost:8080`
- Backend health: `http://localhost:8000/health`
- Backend readiness: `http://localhost:8000/ready`
- API docs: `http://localhost:8000/docs`

## Local Development

1. Install dependencies:

```bash
make install
```

2. Start Ollama and make sure `mistral:latest` is available.

3. Run the backend:

```bash
make run-server
```

4. Run the frontend in another terminal:

```bash
make run-client
```

Local dev defaults:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://localhost:5173`

`server/run.py` will use `.venv/bin/python` if it exists; otherwise it falls back to the current Python interpreter.

## Environment Variables

Copy `.env.example` to `.env` if you want local overrides:

```bash
cp .env.example .env
```

Important settings:

- `APP_NAME=Calma`
- `BACKEND_HOST=127.0.0.1`
- `BACKEND_PORT=8000`
- `RETRIEVAL_BACKEND=faiss`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL=mistral:latest`
- `QDRANT_URL=http://localhost:6333`
- `VITE_API_URL=/api`

The full default list is in `.env.example` and `compose.yaml`.

## Data Layout

Expected repository data folders:

- `data/raw` - source PDFs and seed knowledge base files
- `data/processed` - processed corpus artifacts and manifests
- `data/store` - runtime state such as the SQLite DB and FAISS index

Docker Compose mounts these paths into the backend. Treat `data/store` as runtime state, not source data.

Useful ingestion commands:

```bash
make ingest-pdfs
make build-index
```

## Testing And Verification

Run the main quality gates with:

```bash
make verify
```

Other useful commands:

```bash
make test
make test-unit
make test-integration
make test-eval
make frontend-check
make compose-check
```

The evaluation harness writes its report under `tests/eval/`.

## Docker Commands

- `make run-stack` - full stack with Compose
- `make docker-dev` - same default development stack
- `make docker-prod` - base compose stack without the dev override
- `make docker-frontend-standalone` - frontend only, against an external backend
- `make docker-init-store` - seed the named runtime store volume

`docker compose up` automatically applies `compose.override.yaml`, which enables bind mounts and reload-friendly development settings.

## Troubleshooting

- First startup can take a while while Ollama loads the model and the embedding model warms up.
- If chat is slow on the first request, wait for backend startup to finish and re-try.
- Make sure ports `8000`, `8080`, `5173`, `6333`, and `11434` are free when using local services.
- If you change retrieval mode to Qdrant, confirm the Qdrant container or service is running.
- If the frontend cannot reach the backend, check `VITE_API_URL` and `FRONTEND_API_UPSTREAM`.

## Documentation

Useful docs in this repo:

- `docs/technical/PROJECT_OVERVIEW.md`
- `docs/technical/ARCHITECTURE.md`
- `docs/technical/TECH_STACK.md`
- `docs/technical/GOVERNANCE_CONTRACT.md`
- `docs/academic/TEST_RESULTS.md`

## Notes

- The assistant is intended for psychoeducational support, not diagnosis or medical advice.
- The default retrieval backend is FAISS. Qdrant is available if you want to switch later.
