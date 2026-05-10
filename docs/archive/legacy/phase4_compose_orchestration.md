# Phase 4 Compose Orchestration

## Purpose

Make Docker Desktop and CLI usage behave like a professional multi-service capstone.

This phase is about orchestration quality, not new product features.

## Current State

- `docker-compose.yml` already starts backend and frontend together.
- Backend is exposed on `8000`.
- Frontend is exposed on `8080`.
- Docker Desktop launching the compose project starts both services by design.
- The frontend build still relies on `VITE_API_URL` being provided explicitly at build time.

## Target Operating Modes

### Mode 1: Full stack demo

```bash
docker compose up --build
```

### Mode 2: Backend only

```bash
docker compose up backend
```

### Mode 3: Frontend only

```bash
docker compose up frontend
```

## Work Items

1. Add explicit frontend build-time configuration.
2. Add healthchecks for backend and, if useful, frontend.
3. Decide between compose profiles and split compose files for single-service runs.
4. Add `.dockerignore` for predictable build contexts.
5. Document the exact Docker Desktop and CLI startup flow.

## Current Implementation Notes

- backend healthcheck uses `/health`
- frontend build receives `VITE_API_URL` explicitly via compose
- build context is reduced via `.dockerignore`
- backend and frontend are independent services under one compose project

## Design Decisions

- Backend remains the API source of truth.
- Frontend remains static after build.
- Compose should orchestrate, not hide service boundaries.
- Build-time variables must be explicit, not implicit.

## Recommended Technical Direction

- Keep a single main compose file for the full demo stack.
- Keep backend and frontend independently startable in Docker Desktop.
- Pass `VITE_API_URL` into the frontend build explicitly.
- Add a backend healthcheck using `/health`.

## Final Orchestration Choice

- one compose file as the source of truth
- no hidden startup-time coupling between frontend and backend
- backend can be started, stopped, and health-checked independently
- frontend can be started, stopped, and rebuilt independently
- Docker Desktop shows two separate services under one project

## Tests

- `docker compose config` resolves cleanly.
- frontend image build receives `VITE_API_URL` explicitly.
- backend container reports healthy on `/health`.
- backend-only startup works without the frontend container.
- frontend-only startup works without the backend container.
- Docker Desktop shows the same service boundaries as the CLI.

## Verification Result

- `docker compose config` resolves successfully
- compose includes explicit frontend build arg
- backend healthcheck is active
- frontend and backend stay independent in startup-time behavior
- `.dockerignore` is present

## Exit Criteria

- a reviewer can start the full stack without guessing order
- a developer can start either service alone when needed
- compose no longer hides any build/runtime configuration
