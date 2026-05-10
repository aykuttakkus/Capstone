# Phase 6 Test Strategy Status

## Purpose

Record the delivery-grade test posture for Calma.

## Status

- backend unit coverage exists and passes
- frontend lint/build checks exist and pass
- readiness endpoints exist and pass smoke checks
- compose configuration is validated by test
- clinical state migration is covered by tests

## Verification Result

- `pytest` remains the primary backend gate
- frontend lint/build remain the primary UI gate
- readiness and compose validation now act as smoke gates
- `docker compose config` is part of the structural smoke baseline
