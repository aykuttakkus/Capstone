# Calma Delivery Master Plan

## Purpose

This document is the execution plan for turning the current Calma project into a submission-ready, professionally structured capstone.

The rule is simple: we move phase by phase, and we do not start the next phase until the current one is complete and verified.

## Current State Snapshot

### Already in place

- FastAPI backend with auth, chat, sessions, feedback, screening, and config endpoints
- React/Vite frontend with session management, personalization, and settings UI
- Local SQLite persistence and local RAG pipeline
- Separate frontend API URL handling via `VITE_API_URL`
- Backend CORS configuration starting to respect frontend origin(s)
- Unit and demo readiness tests
- Documentation for demo, freeze, roadmap, and setup

### Still missing for delivery-grade separation

- Dedicated container setup for backend and frontend
- Compose-based local orchestration
- Clear readiness checks beyond basic health
- CI pipeline for tests and builds
- Final submission packaging and release hygiene

## Delivery Principles

- Backend and frontend are separate services, not one launcher
- Configuration comes from environment variables, not hardcoded addresses
- Local development should mirror production shape as much as possible
- Every phase must end with tests and a documented exit criterion
- Keep the project offline/local unless a feature truly needs network access

## Phase 0. Baseline Freeze

### Goal

Lock the current working state so later changes do not break the existing demo flow.

### Work items

- confirm current backend startup command
- confirm current frontend startup command
- list current environment variables
- identify all existing docs and tests that define the behavior
- record what is already complete versus what remains

### Deliverables

- baseline inventory
- final scope list for delivery work
- no ambiguity about current architecture

### Tests

- run the current backend test suite
- run the frontend build
- confirm the existing demo flow still opens without regressions

### Exit criteria

- current app still runs
- current tests still pass
- the plan is accepted as the source of truth

## Phase 1. Runtime Separation

### Goal

Make backend and frontend truly independent at the startup layer.

### Work items

- keep backend as a standalone Python service
- keep frontend as a standalone Vite service
- remove any hidden coupling where one process starts the other
- define exact local commands for each service
- keep `run.py` as backend-only or retire it later if we decide that is cleaner

### Deliverables

- one backend entrypoint
- one frontend entrypoint
- separate run instructions

### Tests

- backend starts without the frontend process launching automatically
- frontend starts without the backend process launching automatically
- backend still answers API requests while the frontend is stopped
- frontend still boots its shell while the backend is stopped

### Exit criteria

- backend starts without frontend
- frontend starts without backend bootstrapping it
- each service can fail independently

## Phase 2. Configuration Contract

### Goal

Move all environment-specific values into explicit config files and env variables.

### Work items

- standardize backend env variables
- standardize frontend env variables
- document required and optional values
- remove hardcoded localhost assumptions where possible
- keep client API base URL in `client/.env`, not in code

### Deliverables

- root `.env.example`
- `client/.env.example`
- documented configuration contract

### Tests

- backend reads `FRONTEND_ORIGINS` from env
- client reads `VITE_API_URL` from `client/.env`
- missing required env values fail clearly or fall back exactly as documented
- documentation matches the actual required variables

### Exit criteria

- a new machine can understand setup without reading source code first
- backend and frontend both boot with documented env values

## Phase 3. Containerization

### Goal

Package the services so they can run in a clean, reproducible environment.

### Work items

- add a backend `Dockerfile`
- add a frontend `Dockerfile`
- keep image responsibilities narrow and predictable
- avoid putting dev-only assumptions into production containers

### Deliverables

- backend container image
- frontend container image
- reproducible builds

### Tests

- backend Docker image builds successfully
- frontend Docker image builds successfully
- each container starts with its documented command
- containerized services expose the expected ports

### Exit criteria

- both services can be built from Docker with no manual patching
- container startup behavior is documented

## Phase 4. Compose Orchestration

### Goal

Provide a single local orchestration file for repeatable demo and development runs.

### Work items

- add `compose.yaml`
- define backend, frontend, and any required local support services
- wire service dependencies and ports clearly
- make local demo setup one-command or near-one-command
- pass build-time frontend API configuration explicitly
- add service healthchecks so startup order is visible
- keep backend and frontend independently startable in Docker Desktop
- add a `.dockerignore` to keep build contexts small and deterministic

### Deliverables

- compose file
- local service topology
- clear port mapping

### Tests

- `docker compose up` starts the stack in the documented order
- backend and frontend containers can reach each other as expected
- all declared ports are reachable from the host
- stopping one service does not silently restart the other
- `docker compose config` resolves without hidden env surprises
- frontend image build receives `VITE_API_URL` explicitly
- backend healthcheck reports healthy before dependent flow proceeds

### Exit criteria

- a reviewer can launch the system without guessing service order
- all service links are explicit

## Phase 5. Readiness and Observability

### Goal

Make service state measurable, not implied.

### Work items

- add or refine `health` endpoint
- add `ready` endpoint if the service needs dependency checks
- ensure backend readiness reflects real startup completion
- document what each endpoint means

### Deliverables

- health check
- readiness check
- startup clarity

### Tests

- `/health` returns healthy when the API is live
- `/ready` returns ready only after required dependencies are available
- readiness failures are distinguishable from general liveness failures

### Exit criteria

- automation can tell whether the system is alive and usable

## Phase 6. Test Strategy

### Goal

Cover the project with tests that prove the delivery behavior, not just implementation details.

### Work items

- keep unit tests for backend logic
- keep frontend build/lint checks
- add smoke tests for startup and critical paths
- add integration checks for the API contract where useful
- define a clear test matrix by layer: unit, smoke, integration, build, readiness
- keep smoke tests lightweight and deterministic
- make Phase 5 readiness part of the smoke gate when applicable

### Deliverables

- test matrix
- startup smoke checks
- repeatable verification steps

### Tests

- backend unit tests pass
- frontend lint passes
- frontend build passes
- smoke tests cover the critical user flow
- `docker compose config` stays valid as a structural smoke check
- `/health` and `/ready` return expected shapes
- a minimal backend auth/session flow still works end to end

### Exit criteria

- critical flows are covered by automated checks
- regressions are visible before submission

## Phase 7. CI Automation

### Goal

Run quality gates automatically on every change.

### Work items

- add GitHub Actions for backend tests
- add GitHub Actions for frontend lint/build
- include smoke or readiness checks if practical
- fail fast on broken builds
- define a single CI workflow that maps to backend, frontend, and compose gates
- keep CI jobs aligned with the local verification commands

### Deliverables

- CI workflow file(s)
- automated quality gate

### Tests

- CI workflow runs backend tests successfully
- CI workflow runs frontend lint/build successfully
- CI fails when a known broken case is introduced
- CI status is visible and easy to interpret
- CI workflow validates compose config as a structural gate

### Exit criteria

- a push or pull request proves the project still works
- no manual guesswork is needed for basic validation

## Phase 8. Documentation and Submission Package

### Goal

Make the project easy to understand, run, and review.

### Work items

- finalize README with separate run instructions
- finalize demo setup notes
- update architecture and roadmap docs
- add final submission notes and freeze guidance
- ensure the reviewer knows what is finished and what is intentionally out of scope

### Deliverables

- polished README
- final demo instructions
- freeze note
- submission checklist

### Tests

- README commands match the actual working commands
- demo setup steps reproduce the current run order
- submission checklist covers the final verification steps

### Exit criteria

- the whole project can be understood from docs alone
- setup and demo steps are unambiguous

## Phase 9. Final Freeze and Demo Rehearsal

### Goal

Lock the project and verify the final user-facing flow one last time.

### Work items

- run the full backend and frontend startup path
- verify onboarding, chat, session management, settings, and personalization
- verify any new docker or CI artifacts are stable
- stop feature work unless a bug blocks delivery

### Deliverables

- frozen submission state
- final verification checklist
- final freeze and rehearsal note

### Tests

- full backend and frontend startup succeeds from a clean environment
- onboarding, chat, sessions, personalization, and settings all still work
- docker and CI artifacts do not break the release state
- demo rehearsal note documents the final lock state

### Exit criteria

- the project is demo-ready
- no unfinished delivery gaps remain

## Optional Future Track

These are not required for submission, but they are natural next steps if time remains:

- release versioning and tags
- changelog
- extended observability
- deployment to a hosted environment
- admin/maintainer dashboard

## Execution Order

1. Phase 0: Baseline Freeze
2. Phase 1: Runtime Separation
3. Phase 2: Configuration Contract
4. Phase 3: Containerization
5. Phase 4: Compose Orchestration
6. Phase 5: Readiness and Observability
7. Phase 6: Test Strategy
8. Phase 7: CI Automation
9. Phase 8: Documentation and Submission Package
10. Phase 9: Final Freeze and Demo Rehearsal

## Rule of Work

We only move forward when the current phase has:

- implemented changes
- documentation updates
- verification evidence
- no open blockers

And for every phase, the listed tests must pass before the next phase starts.
