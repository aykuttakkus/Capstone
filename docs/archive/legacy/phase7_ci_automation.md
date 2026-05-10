# Phase 7 CI Automation

## Purpose

Run delivery-quality checks automatically on every push and pull request.

## What CI Proves

- backend unit and smoke tests still pass
- frontend lint and build still pass
- compose configuration still resolves
- broken changes fail fast before submission

## Workflow Layout

- `backend` job: installs Python deps and runs `pytest`
- `frontend` job: installs Node deps, runs lint, then build
- `compose` job: validates `docker compose config`

## Why This Is the Right Split

- backend and frontend are different runtimes
- compose is configuration, not application logic
- a failure in one job should point directly to one layer

## Verification

- workflow file exists under `.github/workflows/ci.yml`
- backend job uses Python 3.13
- frontend job uses Node 20
- compose job validates the orchestration file

## Verification Result

- workflow file added successfully
- backend pytest gate passes locally
- frontend lint/build gate passes locally
- compose config gate passes locally
- full backend suite remains green after CI wiring (`64 passed`)

## Status

- implemented and ready for verification
