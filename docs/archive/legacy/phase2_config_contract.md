# Phase 2 Configuration Contract

## Purpose

This note defines the runtime configuration boundary for backend and frontend.

Phase 2 is about making every runtime-critical value explicit, documented, and environment-driven.

## Backend Contract

### Required or documented values

- `APP_NAME`
- `BACKEND_HOST`
- `BACKEND_PORT`
- `FRONTEND_ORIGINS`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `TOP_K`
- `EVIDENCE_MIN_SCORE`
- `EVIDENCE_MIN_CHUNKS`
- `EMBEDDING_MODEL`
- `RAW_CHAT_RETENTION_DAYS`
- `SESSION_SUMMARY_RETENTION_DAYS`
- `SCREENING_RETENTION_DAYS`
- `CONSENT_RETENTION_DAYS`
- `STREAMLIT_SERVER_PORT`

## Frontend Contract

### Required values

- `VITE_API_URL`

## Design Rules

- backend host and port come from env, not hardcoded in startup code
- frontend API URL comes from `web/.env`, not from a fallback inside the UI code
- CORS origins are controlled by `FRONTEND_ORIGINS`
- local defaults are documented in `.env.example`, not hidden in application logic

## Verification

- backend startup command reads `BACKEND_HOST` and `BACKEND_PORT`
- frontend config requires `VITE_API_URL`
- `.env.example` and `web/.env.example` describe the runtime contract

## Status

- completed when config is explicit and tests prove the contract

## Verification Result

- backend config contract test: passed
- full backend test suite: passed (`56 passed`)
- frontend lint: passed
- frontend build: passed
- backend startup honored `BACKEND_HOST` and `BACKEND_PORT`
- frontend startup served successfully with `VITE_API_URL` supplied
