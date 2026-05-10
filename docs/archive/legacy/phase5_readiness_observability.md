# Phase 5 Readiness and Observability

## Purpose

Expose whether the backend is merely alive or actually ready to serve the app.

## Semantics

- `GET /health` means the application process is running.
- `GET /ready` means the application can satisfy its core runtime checks.

## Readiness Checks

- database connection is usable
- configuration values are present
- retrieval index can be loaded

## Why This Matters

- Docker healthchecks can use readiness instead of guessing
- deploys and demos can distinguish startup from runtime failure
- automation can stop early when the app is not ready

## Verification

- `/health` returns `200`
- `/ready` returns `200` with `status`, `ready`, and `checks`

## Status

- implemented and ready for verification

## Verification Result

- `/health` returns `200`
- `/ready` returns `200` with `status`, `ready`, and `checks`
- readiness test passed
- compose and containerization tests still pass
- frontend lint/build still pass

## Note

- FastAPI emits a deprecation warning for `on_event("startup")`; this is acceptable for Phase 5 and can be modernized later with lifespan handlers.
