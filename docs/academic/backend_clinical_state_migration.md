# Backend Clinical State Migration

## Purpose

Move the screening/onboarding completion decision from frontend storage into backend-owned state.

## Why This Matters

- the backend becomes the source of truth
- the same account behaves the same way across browsers and devices
- login can decide the next step without relying on localStorage
- screening completion becomes auditable and testable

## Current Behavior

- client localStorage still exists for legacy onboarding flow
- backend already stores session intake/consent snapshots
- backend now has a dedicated `user_clinical_states` table for user-level completion state

## Backend Rules

- `screening_completed` is written when the PHQ-9 + GAD-7 flow completes
- `onboarding_completed` follows the same completion state
- `/auth/me` returns the current state for UI routing
- `/screen` rejects GAD-7 completion if PHQ-9 was not completed first

## Next Migration Step

- client should stop using localStorage as the gatekeeper for screening completion
- client should read `next_required_step` or `screening_completed` from `/auth/me`

## Verification

- creating a new user creates a clinical state row
- completing screening updates backend state
- a completed account should not be prompted for screening again on next login

## Verification Result

- backend clinical state test: passed
- full backend test suite: passed (`59 passed`)
- frontend lint: passed
- frontend build: passed
- `/auth/me` now exposes backend-owned screening completion state
- `/auth/me` backfills a missing clinical state row and persists it transactionally
