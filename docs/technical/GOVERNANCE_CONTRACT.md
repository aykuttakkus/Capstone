# Governance Contract

## Purpose

This document defines the runtime and privacy contract for the current psychology assistant.

## Runtime Contract

1. Deployment mode defaults to `local`.
2. Retrieval backend is declared explicitly in config.
3. Model contract version is pinned and visible.
4. Sensitive log redaction is enabled by default.

## Privacy Contract

1. Clinical memory remains encrypted at rest.
2. Audit logs only keep a redacted query preview.
3. Retention settings are exposed in config and can be overridden by environment variables.
4. Debug logs must not become the main record of behavior.

## Retention Defaults

1. raw chat: 90 days
2. session summaries: 365 days
3. screening: 365 days
4. consent: 365 days
5. audit logs: 365 days

## Validation

This contract is validated by the config API and audit logger tests.
