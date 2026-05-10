# Phase 6: Source Transparency

## Goal

Make every grounded answer easy to inspect and explain.

## What Changed

1. Source metadata now includes `source_kind`, `language`, `confidence`, `section`, and `page`.
2. Retrieval diagnostics now expose the same metadata.
3. Responses now include `source_highlight` for the top evidence card.
4. The frontend shows the primary evidence separately from the source list.

## Keep / Replace / Remove

### Keep

1. Source cards.
2. Retrieval diagnostics.
3. Clinical nugget display.

### Replace

1. Minimal source tags with richer metadata cards.
2. Hidden top evidence with an explicit primary evidence highlight.

### Remove

1. Source-less default presentation when evidence exists.
2. Ambiguous source cards that do not show confidence or origin.

## Validation

The phase was validated with the following tests:

```bash
pytest tests/integration/api/test_chat_api.py tests/integration/api/test_config_api.py tests/unit/services/test_assistant_service.py tests/unit/core/test_safety_policy.py tests/unit/core/test_generation.py tests/unit/core/test_reranker.py
```

Result:

- 21 passed

## Notes

1. The UI now exposes the strongest source first.
2. Metadata remains visible for auditability and debugging.
