# Phase 0 Baseline Freeze

## Purpose

This note captures the current working state before any delivery-phase changes continue.

Phase 0 is complete only when the baseline is recorded and the current app still runs with the existing verification checks.

## Current Runtime Commands

### Backend

```bash
python run.py
```

`run.py` is backend-only and launches FastAPI on port `8000`.

### Frontend

```bash
cd web
npm install
npm run dev
```

The frontend runs independently on Vite port `5173`.

## Current Environment Contract

### Root `.env.example`

- `APP_NAME`
- `FRONTEND_ORIGINS`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `TOP_K`
- `EVIDENCE_MIN_SCORE`
- `EVIDENCE_MIN_CHUNKS`
- `EMBEDDING_MODEL`
- `RAW_CHAT_RETENTION_DAYS`
- `SESSION_SUMMARY_RETENTION_DAYS`
- `SCREENING_RETENTION_DAYS`
- `CONSENT_RETENTION_DAYS`
- `STREAMLIT_SERVER_PORT`

### `web/.env.example`

- `VITE_API_URL`

## Docs That Define Behavior

- `docs/delivery_master_plan.md`
- `docs/demo_setup.md`
- `docs/demo_package.md`
- `docs/freeze_note.md`
- `docs/submission_checklist.md`
- `docs/frontend_integration_plan.md`
- `docs/PROJECT_OVERVIEW.md`
- `docs/TECHNICAL_ANALYSIS.md`
- `docs/TECH_STACK.md`
- `docs/BACKEND_ROADMAP.md`
- `docs/PRD.md`
- `docs/roadmap.md`
- `docs/CALMA_ROADMAP.md`
- `docs/SAFETY_POLICY.md`
- `docs/privacy_notice.md`
- `docs/retention_policy.md`
- `docs/TEST_RESULTS.md`

## Tests That Define Behavior

### Unit and delivery tests

- `tests/unit/test_phase0_config.py`
- `tests/unit/test_phase1_sessions.py`
- `tests/unit/test_phase1_session_tools.py`
- `tests/unit/test_phase2_memory.py`
- `tests/unit/test_phase3_pdf_pipeline.py`
- `tests/unit/test_phase4_retrieval_quality.py`
- `tests/unit/test_phase6_response_style.py`
- `tests/unit/test_phase7_privacy_retention.py`
- `tests/unit/test_phase8_evaluation.py`
- `tests/unit/test_phase9_demo_readiness.py`
- `tests/unit/test_phase9_demo_smoke.py`
- `tests/unit/test_rag.py`
- `tests/unit/test_routing.py`
- `tests/unit/test_index_store.py`
- `tests/unit/test_session.py`
- `tests/unit/test_pdf_ingestion.py`
- `tests/unit/test_safety.py`

### Demo and freeze docs tests

- `tests/unit/test_zero_cost_phase2_corpus_versioning.py`
- `tests/unit/test_zero_cost_phase3_retrieval_transparency.py`
- `tests/unit/test_zero_cost_phase4_feedback_evaluation.py`
- `tests/unit/test_zero_cost_phase7_demo_docs.py`
- `tests/unit/test_zero_cost_phase8_freeze_docs.py`

### Eval runner

- `tests/eval/run_eval.py`

## Baseline Snapshot

- Backend and frontend are already separated at the command level.
- Backend CORS is controlled through `FRONTEND_ORIGINS`.
- Frontend API URL is controlled through `VITE_API_URL`.
- The main missing delivery pieces are containerization, compose orchestration, readiness endpoints, and CI.

## Phase 0 Verification

Run these checks before moving to Phase 1:

```bash
./.venv/bin/python -m pytest
cd web
npm run lint
npm run build
```

### Verification Result

- backend test suite: passed (`53 passed`)
- frontend lint: passed
- frontend build: passed
- baseline PDF ingestion test path was corrected to the current repository root

## Exit Criteria

- Baseline note is committed to the repo state.
- Current backend and frontend commands still work.
- Current automated checks still pass.
- No delivery-phase work starts until this baseline is verified.
