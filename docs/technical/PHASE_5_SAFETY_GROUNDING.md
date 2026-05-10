# Phase 5: Safety and Groundedness

## Goal

Keep the assistant bounded, deterministic, and evidence-grounded.

## What Changed

1. Added an explicit `risk_clarification` response path.
2. Safety refusals remain deterministic for diagnosis, medication, prompt injection, crisis, and off-domain requests.
3. The assistant short-circuits before retrieval/generation when safety mode is not normal.
4. Grounded answers still fall back to evidence refusal when the model is unavailable.

## Keep / Replace / Remove

### Keep

1. Keyword safety engine.
2. LLM safety guardian.
3. Evidence gate.
4. Grounded generation fallback.

### Replace

1. Generic safety fallback with explicit mode-based responses.
2. Ambiguous distress handling with a dedicated clarification path.

### Remove

1. Any hidden safety mode that does not map to a user-facing explanation.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/unit/core/test_safety_policy.py tests/unit/core/test_generation.py tests/unit/services/test_assistant_service.py tests/unit/core/test_routing.py tests/integration/api/test_chat_api.py
```

Result:

- 23 passed

## Notes

1. Crisis and diagnosis requests still refuse immediately.
2. Ambiguous distress now uses a clarification response instead of a generic refusal.
3. Evidence refusal remains the fallback when retrieval is too weak or the model is unavailable.
