# Final Rehearsal Note

## Submission State

Calma is in final rehearsal state for capstone delivery.

The project is frozen around the current documented scope:

- local-first backend and frontend
- PDF-backed retrieval with FAISS state
- session restore and evidence-grounded response flow
- Docker and CI delivery artifacts
- privacy-aware demo boundaries

## Rehearsal Flow

1. Run `make verify`.
2. Start the local backend with `python -m server.run`.
3. Start the frontend with `cd client && npm ci && npm run dev`.
4. Confirm `/health` and `/ready`.
5. Use `docs/management/demo_package.md` for the live walkthrough.
6. Rehearse a grounded answer, a refusal boundary, and a reopened session.

## Docker Rehearsal Path

Use `docker compose up --build` for the local rehearsal path, or `docker compose -f compose.yaml up --build` for the clean base path.

Expected behaviors:

- backend starts in production-style mode
- frontend waits for backend health
- runtime state persists through `calma_store`

## Final Lock Rules

- no new features after this note
- only blocker-level bug fixes are acceptable
- documentation corrections are acceptable
- CI or packaging fixes are acceptable if they preserve the documented scope

## Reviewer Promise

A reviewer should be able to understand the scope from the docs alone, run `make verify`, and follow the demo path without guessing hidden setup steps.
