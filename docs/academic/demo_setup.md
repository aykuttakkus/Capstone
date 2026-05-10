# Calma Demo Setup

## Purpose

This page gives a minimal, advisor-ready setup summary for running the Calma demo locally.

## Local Requirements

- Python environment with project dependencies installed
- Node.js environment for the frontend
- Ollama running locally
- the local PDF corpus in `data/raw/`

## Core Commands

Backend:

```bash
python -m server.run
```

Frontend:

```bash
cd client
npm ci
npm run dev
```

The backend and frontend are started separately on purpose so each service can be managed and debugged independently.

Verification:

```bash
make verify
```

PDF ingestion:

```bash
python scripts/ingest_pdfs.py
python scripts/build_index.py
```

## Demo Checklist

1. if you need local overrides, create root `.env` from `.env.example`
2. confirm Ollama is running
3. ingest PDFs and build the index
4. log in and complete onboarding
5. confirm the backend says the session is ready
6. ask a grounded question
7. show a refusal example
8. show a safety example
9. reopen a session from history

## Architecture Summary

- local LLM through Ollama
- curated PDF-backed RAG
- session-aware memory
- deterministic and agentic safety layers
- evidence gate before generation
- offline evaluation and feedback capture

## Freeze Rule

After the demo is stable, avoid adding new features unless they clearly improve trust, control, or presentation reliability.

## Docker Demo Path

If using Docker, start the stack with `docker compose up --build`, or use `docker compose -f compose.yaml up --build` for the clean base stack.
Compose has safe defaults and does not require a custom `.env` unless you want overrides.
The base backend container runs in production-style mode; hot reload is only part of the local development override.
The frontend waits for backend health before startup; use `/ready` to confirm the application is fully prepared for the demo.
Runtime state in Docker is persisted in the named volume `calma_store`.
The backend image drops to a non-root runtime user after preparing writable data directories.
The frontend image builds with `npm ci` and is served by nginx with cache and security-header defaults suitable for submission demos.
Then open:

- frontend: `http://localhost:8080`
- backend health: `http://localhost:8000/health`
- backend ready: `http://localhost:8000/ready`
