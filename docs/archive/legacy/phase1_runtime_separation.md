# Phase 1 Runtime Separation

## Purpose

This note records the point where backend and frontend are treated as separate runtime services.

## Separation Outcome

- Backend is started only through `python run.py`.
- Frontend is started only through `cd web && npm run dev`.
- The backend no longer launches the frontend.
- The frontend no longer depends on the backend launcher.

## Verified Commands

### Backend

```bash
python run.py
```

### Frontend

```bash
cd web
npm install
npm run dev
```

## Evidence

- `run.py` now launches only FastAPI.
- `README.md` documents separate start commands.
- `docs/demo_setup.md` documents separate start commands.

## Phase 1 Tests

Phase 1 is complete when these checks pass:

- backend starts independently
- frontend starts independently
- no backend process starts the frontend automatically
- no frontend process depends on backend startup orchestration

## Verification Result

- runtime separation test: passed
- backend health endpoint: passed (`{"status":"ok","app":"Calma"}`)
- frontend dev server: passed (`200` from `http://127.0.0.1:5173`)

## Status

- completed
