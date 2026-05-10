# Phase 3 Containerization

## Purpose

This phase packages Calma into reproducible backend and frontend container images.

## Container Strategy

- backend image runs the FastAPI app
- frontend image builds the Vite app and serves static files through Nginx
- runtime configuration still comes from env files, not from container hardcoding
- backend container must bind to `0.0.0.0` so the host can reach `localhost:8000`
- backend container must publish port `8000:8000`
- frontend container must publish its HTTP port (for example `8080:80`)

## Expected Artifacts

- `Dockerfile.server`
- `Dockerfile.client`

## Design Rules

- backend container stays API-focused
- frontend container stays UI-focused
- no hidden bootstrapping between services
- container builds should work from a clean checkout

## Phase 3 Tests

- backend image builds successfully
- frontend image builds successfully
- backend container starts and serves the API
- frontend container starts and serves the UI build

## Status

- in progress until image builds and startup checks pass

## Verification Result

- phase artifact test: passed
- docker daemon build: blocked in this environment because the Docker socket is unavailable
- next step: rerun `docker build` once Docker Desktop or the local daemon is running
