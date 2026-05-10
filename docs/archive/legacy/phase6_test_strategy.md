# Phase 6 Test Strategy

## Purpose

Define the delivery-quality test matrix for Calma.

This phase does not add new product behavior. It makes sure the existing behavior stays correct as the project gets shipped.

## Test Layers

### Unit

- backend models and services
- retrieval and scoring helpers
- route-level helpers where deterministic
- frontend build/lint already act as a quality gate

### Smoke

- backend starts and answers `/health`
- backend answers `/ready`
- frontend build produces a runnable bundle
- compose config resolves cleanly
- a minimal auth/session flow still works

### Integration

- auth login returns a usable token
- `/auth/me` returns backend-owned clinical state
- `/screen` persists screening completion state
- `/sessions` returns saved conversations and archived ones separately

### Build / Packaging

- backend Docker image builds
- frontend Docker image builds
- compose config resolves without surprises

## Recommended Gate Order

1. unit tests
2. readiness checks
3. smoke tests
4. frontend lint/build
5. compose config validation
6. container build checks where Docker is available

## Current Coverage

- full backend pytest suite exists
- frontend lint/build exists
- readiness endpoint exists
- compose config validation exists
- backend clinical state test exists
- phase-specific tests exist for runtime separation, config, containerization, compose, readiness, and clinical state

## What We Still Need to Treat as the Smoke Baseline

- a small, repeatable backend flow that proves auth and readiness still work together
- a stable CLI/compose validation command for local verification
- `docker compose config` as the structural compose sanity check

## Exit Criteria

- every delivery gate is named and testable
- smoke tests are small enough to run frequently
- test failures point to a single layer instead of being ambiguous
