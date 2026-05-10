# Calma — Architecture Refactoring & Standardization Plan

**Version:** 1.0 (Final Polish Phase)  
**Status:** Approved for Execution  
**Lead Architect:** Dr. Software Engineer (Evaluator)

---

## 1. Executive Summary

During the development of the **Calma** project (Phase 0 through Phase 9), the file structure has grown evolutionarily, leading to "architectural drift." This includes redundant test files, a cluttered documentation root, and blurred boundaries between core AI logic and application services.

This plan outlines the **Standardization & Refactoring** required to align the project with global **Clean Architecture** and **Domain-Driven Design (DDD)** standards for Enterprise AI applications.

### 1.1 Current Baseline

The plan should be executed against the current repository reality, not an idealized target tree.
- Backend currently lives in `app/` and is launched by `run.py`.
- Frontend currently lives in `frontend/` and is built/run separately.
- Safety, retrieval, routing, and agent logic are still under `app/engine/`.
- `tests/` already contains both smoke-style and comprehensive safety coverage, plus many phase-specific regression tests.
- CI already runs backend, safety, frontend, and compose validation jobs.

### 1.2 Refactoring Principles

- Prefer one structural move at a time.
- Do not combine directory renames with business-logic changes in the same commit.
- Every rename must include import updates, test updates, and CI updates.
- Keep a temporary compatibility layer only if it reduces risk; remove it after verification.
- Refactor from the outside in: docs and build tooling first, then imports, then internal package boundaries.

---

## 2. Structural Transformation (The Target State)

### 2.1 Directory Mapping

| Current Location | New Standard Location | Rationale |
|------------------|-----------------------|-----------|
| `app/` | `backend/app/` | Clear separation from frontend and infra. |
| `frontend/` | `frontend/` | Industry standard naming for SPAs. |
| `docs/` | `docs/{category}/` | Hierarchy for better discoverability. |
| `tests/` | `tests/{unit\|integration\|e2e}/` | Categorized verification suite. |
| `app/engine/` | `backend/app/core/` | Represents the Domain/Core AI logic. |
| `run.py` | `backend/run.py` | Entry point should live with its service. |

> Note: the `app/ -> backend/app/` move is a coordinated repository-wide migration because `run.py`, `docker-compose.yml`, CI, and README currently depend on the existing paths.

### 2.2 Proposed Folder Hierarchy

```text
Calma/
├── backend/                    # Python Backend Service
│   ├── app/                    # Main Application Package
│   │   ├── api/                # FastAPI Routers (v1/v2)
│   │   ├── core/               # The "Engine" (RAG, Safety, Agents)
│   │   ├── services/           # Business Logic (Assistant, Screening)
│   │   ├── models/             # Pydantic & SQLAlchemy Models
│   │   ├── config/             # YAML Prompts & Settings
│   │   └── utils/              # Shared Helpers
│   ├── requirements.txt
│   └── run.py
├── frontend/                   # React/Vite SPA
├── docs/                       # Project Documentation
│   ├── design/                 # PRD, Architecture, Analysis
│   ├── safety/                 # Policies, Ethics, Limitations
│   ├── evaluation/             # Test Results, Metrics, Eval Scripts
│   └── management/             # Roadmaps, Checklists, Plans
├── scripts/                    # Operational Scripts (eval, ingest)
├── tests/                      # Unified Testing Suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── infrastructure/             # Docker, CI/CD, Nginx Configs
├── .env.example
├── docker-compose.yml
└── Makefile                    # Standard Automation Interface
```

---

## 3. Key Refactoring Tracks

### Track A: Documentation Categorization 🔴 P0
The docs root should be organized without breaking canonical entry points or links.
- **Action:** Move `SAFETY_POLICY.md`, `LIMITATIONS.md` to `docs/safety/`.
- **Action:** Move `PROJECT_OVERVIEW.md`, `TECHNICAL_ANALYSIS.md` to `docs/design/`.
- **Action:** Archive obsolete phase-plans into `docs/management/archive/`.
- **Action:** Keep one root-level index document that links to the new categories.
- **Action:** Update all relative links in `README.md`, `frontend/README.md`, and other docs.

### Track B: Test Suite Consolidation 🔴 P0
Safety coverage should be consolidated, not accidentally reduced.
- **Action:** Keep `tests/unit/test_safety.py` as the narrow smoke/regression suite.
- **Action:** Keep `tests/unit/test_safety_comprehensive.py` as the exhaustive scenario suite.
- **Action:** Remove only true duplicates after coverage comparison, not by filename alone.
- **Action:** Move only dead phase tests to `tests/archive/` after confirming they are superseded.
- **Action:** Align CI so each suite is invoked intentionally and independently.

### Track C: Configuration & Prompt Decoupling 🟠 P1
Currently, prompts are hardcoded strings inside Python agents. This is a maintenance risk.
- **Action:** Inventory all prompt-bearing classes before migration.
- **Action:** Create `backend/app/config/prompts.yaml` only after the inventory is confirmed.
- **Action:** Refactor `SafetyGuardian`, `SentimentAgent`, and `Orchestrator` to load prompt templates from this YAML if and only if those prompts are truly static.
- **Action:** Add a fallback path and schema validation for malformed prompt configs.

### Track D: CI / Docker / Runtime Alignment 🟠 P1
Repository moves are only safe if the execution surface is updated in the same plan.
- **Action:** Update `docker-compose.yml` build contexts and paths after any rename.
- **Action:** Update `run.py` if backend entrypoint location changes.
- **Action:** Update `.github/workflows/ci.yml` to match the final test layout and path names.
- **Action:** Update `README.md` examples and all run commands.
- **Action:** Verify `docker compose config`, backend import startup, and frontend build in CI.

### Track E: Automation Interface (Makefile) 🟡 P2
Standardize how the project is managed across different environments.
- **Action:** Implement a `Makefile` with commands: `make setup`, `make test`, `make docker-run`, `make ingest`.

### Track F: Architecture Boundary Clarification 🟡 P2
Clean Architecture and DDD should be stated in terms of dependency direction, not only folder names.
- **Action:** Define which modules are domain, application, infrastructure, and interface layers.
- **Action:** Specify what can import what, especially between agents, services, retrieval, and persistence.
- **Action:** Document the boundary of the RAG engine versus delivery/transport code.

---

## 4. Implementation Checklist

1. [ ] **Pre-check:** Confirm the current backend, frontend, and test suite are green before any move.
2. [ ] **Phase 1 (Docs):** Reorganize docs and repair all links and references.
3. [ ] **Phase 2 (Tooling):** Update `README.md`, `docker-compose.yml`, `run.py`, and CI in lockstep with any path rename.
4. [ ] **Phase 3 (Core Packages):** Rename `app/engine` to the chosen core boundary only after import impact is enumerated.
5. [ ] **Phase 4 (Prompts):** Externalize prompts only after inventory and schema design are complete.
6. [ ] **Phase 5 (Tests):** Rationalize the test layout, but keep unique regression coverage.
7. [ ] **Verification Gate:** Run the full validation matrix before marking the refactor complete.

### 4.1 Validation Matrix

- Backend unit tests: `pytest tests/unit`
- Safety tests: `pytest tests/unit/test_safety.py tests/unit/test_safety_comprehensive.py`
- Frontend lint/build: `npm run lint` and `npm run build` inside `frontend/`
- Compose validation: `docker compose config`
- Startup smoke: backend boot plus one health check request
- Documentation sanity: root README links and moved docs resolve correctly

---

## 5. Impact Analysis

- **Imports:** `app/services/assistant.py`, `app/engine/agents/orchestrator.py`, and related modules will require import updates if package paths move.
- **Docker:** `docker-compose.yml` and `Dockerfile.*` must match the final backend/frontend path layout.
- **CI/CD:** `.github/workflows/ci.yml` must reflect the final test names and working directories.
- **Docs:** `README.md`, `docs/*`, and any phase documents must keep links consistent after file moves.
- **Runtime:** `run.py` and any bootstrapping scripts must continue to launch the backend without manual path edits.

---

## 6. Definition of Done

- No import errors on backend startup.
- All targeted tests pass.
- Frontend builds and lints successfully.
- Docker compose config validates.
- Documentation links are not broken.
- The repository structure matches the documented target state.

---

## 7. Final Target Architecture

The target state should be stable enough to hand to another engineer without additional interpretation.

```text
Calma/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── agents/
│   │   │   ├── generation/
│   │   │   ├── retrieval/
│   │   │   ├── routing/
│   │   │   └── safety/
│   │   ├── services/
│   │   ├── models/
│   │   ├── config/
│   │   └── utils/
│   ├── main.py
│   ├── requirements.txt
│   └── run.py
├── frontend/
├── docs/
│   ├── design/
│   ├── safety/
│   ├── compliance/
│   ├── evaluation/
│   ├── management/
│   └── archive/
├── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── infrastructure/
├── .env.example
├── docker-compose.yml
└── Makefile
```

### 7.1 Layer Rules

- `api/` exposes HTTP transport only.
- `core/` contains routing, retrieval, safety, generation, and agents.
- `services/` coordinates application workflows and persistence.
- `models/` owns schemas and database models.
- `config/` stores non-code configuration such as prompts and static settings.
- `utils/` is reserved for genuinely shared helpers only.

### 7.2 Documentation Categories

- `docs/design/`: architecture, PRD, tech stack, analysis.
- `docs/safety/`: safety policy, limitations, refusal guidance.
- `docs/compliance/`: privacy notice, retention policy, consent-related docs.
- `docs/evaluation/`: retrieval results, safety results, hyperparameter decisions.
- `docs/management/`: roadmaps, plans, checklists, demo instructions, freeze notes.
- `docs/archive/`: obsolete phase-specific materials that are retained for traceability only.

---

## 8. File Migration Matrix

### 8.1 Documentation Moves

| Source | Target | Action |
|--------|--------|--------|
| `docs/ARCHITECTURE.md` | `docs/design/ARCHITECTURE.md` | Move |
| `docs/TECHNICAL_ANALYSIS.md` | `docs/design/TECHNICAL_ANALYSIS.md` | Move |
| `docs/PROJECT_OVERVIEW.md` | `docs/design/PROJECT_OVERVIEW.md` | Move |
| `docs/PRD.md` | `docs/design/PRD.md` | Move |
| `docs/TECH_STACK.md` | `docs/design/TECH_STACK.md` | Move |
| `docs/SAFETY_POLICY.md` | `docs/safety/SAFETY_POLICY.md` | Move |
| `docs/LIMITATIONS.md` | `docs/safety/LIMITATIONS.md` | Move |
| `docs/privacy_notice.md` | `docs/compliance/privacy_notice.md` | Move |
| `docs/retention_policy.md` | `docs/compliance/retention_policy.md` | Move |
| `docs/TEST_RESULTS.md` | `docs/evaluation/TEST_RESULTS.md` | Move |
| `docs/RETRIEVAL_EVALUATION.md` | `docs/evaluation/RETRIEVAL_EVALUATION.md` | Move |
| `docs/HYPERPARAMETER_DECISIONS.md` | `docs/evaluation/HYPERPARAMETER_DECISIONS.md` | Move |
| `docs/delivery_master_plan.md` | `docs/management/delivery_master_plan.md` | Move |
| `docs/submission_checklist.md` | `docs/management/submission_checklist.md` | Move |
| `docs/demo_setup.md` | `docs/management/demo_setup.md` | Move |
| `docs/demo_package.md` | `docs/management/demo_package.md` | Move |
| `docs/roadmap.md` | `docs/management/roadmap.md` | Move |
| `docs/CALMA_ROADMAP.md` | `docs/management/CALMA_ROADMAP.md` | Move |
| `docs/BACKEND_ROADMAP.md` | `docs/management/BACKEND_ROADMAP.md` | Move |
| `docs/zero_cost_*` | `docs/management/archive/` or `docs/evaluation/` | Review then move |
| `docs/phase*.md` | `docs/archive/phase*/` | Archive |

### 8.2 Code Moves

| Source | Target | Action |
|--------|--------|--------|
| `app/main.py` | `backend/app/main.py` | Move |
| `run.py` | `backend/run.py` | Move |
| `app/engine/agents/*` | `backend/app/core/agents/*` | Move |
| `app/engine/generation/*` | `backend/app/core/generation/*` | Move |
| `app/engine/retrieval/*` | `backend/app/core/retrieval/*` | Move |
| `app/engine/routing/*` | `backend/app/core/routing/*` | Move |
| `app/engine/safety/*` | `backend/app/core/safety/*` | Move |
| `app/services/*` | `backend/app/services/*` | Move |
| `app/models/*` | `backend/app/models/*` | Move |
| `app/utils/*` | `backend/app/utils/*` | Move |

### 8.3 Tooling Moves

| Source | Target | Action |
|--------|--------|--------|
| `docker-compose.yml` | `docker-compose.yml` | Update paths only |
| `Dockerfile.server` | `Dockerfile.server` (root) | Keep current backend runtime |
| `Dockerfile.client` | `Dockerfile.client` (root) | Keep current frontend runtime |
| `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | Update jobs and working dirs |
| `README.md` | `README.md` | Update commands and references |

---

## 9. Execution Waves

### Wave 0: Freeze and Inventory

- Capture the current tree and import graph.
- Identify files that are canonical versus archive candidates.
- Confirm the test suite names that must remain active.
- Stop here if any unknown dependency is found.

#### 9.1 Wave 0 Inventory Snapshot

Current repository snapshot:
- Backend package root: `app/`
- Backend transition layer: `backend/`
- Frontend app root: `frontend/`
- Primary docs root: `docs/`
- Primary test root: `tests/`
- Operational scripts: `scripts/`
- Compose entrypoint: `docker-compose.yml`
- Backend launcher: `run.py`
- CI workflow: `.github/workflows/ci.yml`

Canonical documentation set for the refactor:
- `docs/design/ARCHITECTURE.md`
- `docs/design/TECHNICAL_ANALYSIS.md`
- `docs/design/PROJECT_OVERVIEW.md`
- `docs/design/PRD.md`
- `docs/design/TECH_STACK.md`
- `docs/design/KNOWLEDGE_BASE.md`
- `docs/safety/SAFETY_POLICY.md`
- `docs/safety/LIMITATIONS.md`
- `docs/evaluation/TEST_RESULTS.md`
- `docs/evaluation/RETRIEVAL_EVALUATION.md`
- `docs/evaluation/HYPERPARAMETER_DECISIONS.md`
- `docs/compliance/privacy_notice.md`
- `docs/compliance/retention_policy.md`
- `README.md`

Archive candidates for later review:
- `docs/archive/phase0_baseline_freeze.md`
- `docs/archive/phase1_runtime_separation.md`
- `docs/archive/phase2_config_contract.md`
- `docs/archive/phase3_containerization.md`
- `docs/archive/phase4_compose_orchestration.md`
- `docs/archive/phase5_readiness_observability.md`
- `docs/archive/phase6_test_strategy.md`
- `docs/archive/phase6_test_strategy_status.md`
- `docs/archive/phase7_ci_automation.md`
- `docs/archive/phase8_documentation_status.md`
- `docs/archive/phase9_final_freeze.md`
- `docs/archive/freeze_note.md`

Test suites that should remain active until coverage proves otherwise:
- `tests/unit/test_safety.py`
- `tests/unit/test_safety_comprehensive.py`
- `tests/unit/test_evidence_gate_evaluation.py`
- `tests/unit/test_routing.py`
- `tests/unit/test_rag.py`
- `tests/unit/test_index_store.py`
- `tests/unit/test_session.py`
- `tests/unit/test_pdf_ingestion.py`
- phase regression suites that still represent current behavior

High-impact dependency hotspots:
- `app/services/assistant.py`
- `app/engine/agents/orchestrator.py`
- `app/engine/agents/safety_guardian.py`
- `app/main.py`
- `run.py`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `README.md`

Wave 0 decision:
- No physical moves are performed in this wave.
- Any file marked as archive candidate stays untouched until Wave 1+ confirms it is superseded.
- The next step is to move documentation only after links and canonical references are frozen.

### Wave 1: Documentation Rehome

- Move docs into their final categories.
- Repair all internal links immediately after each move.
- Keep a root-level landing page if any top-level navigation is still needed.

#### 9.2 Wave 1 Current Status

- Completed: canonical docs moved into `docs/design/`, `docs/safety/`, `docs/compliance/`, `docs/evaluation/`, and `docs/management/`.
- Completed: `docs/README.md` added as the docs index.
- Completed: root `README.md` links updated to the new doc paths.
- Completed: `KNOWLEDGE_BASE.md`, `frontend_integration_plan.md`, `backend_clinical_state_migration.md`, and zero-cost planning docs moved into their target categories.
- Completed: phase, freeze, and status notes moved into `docs/archive/`.
- Completed: tracked frontend source moved from `web/` to `frontend/`.

### Wave 2: Runtime and Build Alignment

- Update `README.md`.
- Update Docker build contexts and entrypoints.
- Update CI working directories and test commands.
- Validate that the backend still boots before any core package rename.

#### 9.3 Wave 2 Runtime Baseline

Current runtime/build surface:
- `docker-compose.yml` still targets the root repository context and current Dockerfile paths.
- `run.py` still launches `app.main:app` from the existing backend layout.
- CI still runs backend pytest jobs, safety suites, frontend lint/build under `frontend/`, and compose validation.

Wave 2 decision:
- Keep runtime commands stable until the backend/frontend path migration begins.
- When the package move starts, update Docker, CI, and launcher paths in the same wave so the repo never enters a half-migrated state.

#### 9.4 Wave 2 Current Status

- Completed: `backend/run.py` added as the new launcher shim.
- Completed: root `run.py` delegates to `backend.run`.
- Completed: `Dockerfile.server` now launches `python -m server.run`.
- Completed: CI validates the backend shim import path.
- Completed: local smoke test passes with the project virtual environment.

### Wave 3: Backend Package Boundary Refactor

- Move `app/main.py` and engine subpackages into the final backend layout.
- Update imports in application services, routes, tests, and scripts.
- Keep behavior unchanged while paths change.

#### 9.5 Wave 3 Current Status

- Completed: canonical FastAPI entrypoint now lives at `backend/app/main.py`.
- Completed: canonical API transition layer established under `backend/app/api`.
- Completed: root `app/main.py` now acts as a compatibility shim.
- Completed: `backend/run.py` launches `backend.app.main:app`.
- Completed: import smoke test passes for both canonical and legacy entrypoints.
- Completed: `backend.app.core.config`, `backend.app.core.database`, and `backend.app.core.security` transition wrappers are in place.
- Completed: canonical `backend.app.core` transition layer established for agents, generation, retrieval, routing, and safety.
- Completed: canonical `backend.app.services.assistant` now hosts the assistant service, with root compatibility shim preserved.
- Completed: canonical `backend.app.services` transition layer established for flows and helper services.
- Completed: canonical `backend.app.models` and `backend.app.utils` transition layers are in place for the currently used schemas and helpers.
- Completed: `backend.app.main` now resolves through backend API, core, service-flow, model, and utility layers.
- Completed: `app/services/assistant.py` now consumes `backend.app.core` imports.
- Completed: backend copies now exist for session helpers, retrieval diagnostics, clinical state, feedback storage, flow helpers, and used schemas/utilities.
- Completed: legacy `app.*` package shims now delegate to backend API, core, services, models, and utils.
- Pending: non-essential engine bridge modules and future cleanup of compatibility-only wrappers.

### Wave 4: Configuration and Prompt Externalization

- Inventory prompt strings.
- Add `prompts.yaml` only for prompts that are stable and reusable.
- Add schema validation and a fallback path.

#### 9.6 Wave 4 Current Status

- Completed: `backend/app/config/prompts.yaml` added as the prompt catalog.
- Completed: `backend/app/utils/prompts.py` added as the prompt loader/render helper.
- Completed: prompt-bearing agents and ingestion classifier now read from YAML.
- Pending: schema validation for prompt keys and optional prompt coverage expansion.

### Wave 5: Test Rationalization

- Keep both the smoke and comprehensive safety suites unless one is truly redundant.
- Move obsolete phase tests into archive only after confirming supersession.
- Re-run all focused suites after each cleanup batch.

#### 9.7 Wave 5 Current Status

- Completed: phase-specific documentation-only tests moved into `tests/archive/`.
- Completed: `tests/unit/test_phase9_demo_readiness.py` now points to the current management docs path.
- Completed: updated active phase/runtime/docs suite passed after the rationalization changes.
- Pending: decide whether any remaining phase-branded functional tests should be renamed for clarity.

### Wave 6: Automation and Stabilization

- Add `Makefile` targets.
- Run the full validation matrix.
- Freeze the structure once the repo is green end-to-end.

#### 9.8 Wave 6 Current Status

- Completed: root `Makefile` added with `setup`, `test`, `docker-run`, and `ingest` targets.
- Completed: `make help` and dry-run validation passed.
- Completed: full validation matrix passed (`pytest`, frontend build, `docker compose config`).
- Completed: repository structure is now stabilized for handoff.

---

## 10. Stop Conditions

Do not proceed to the next wave until the current wave satisfies all of the following:

- No broken imports in the changed surface.
- No broken doc links in the moved set.
- CI commands are aligned with the current tree.
- Docker config validates.
- Targeted tests for the changed area pass.

---

## 11. Handover Checklist

- Updated architecture document.
- Updated migration matrix.
- Updated runtime commands.
- Updated CI job definitions.
- Updated test plan.
- Verified final directory tree.

---

> [!IMPORTANT]
> This refactoring is the final step in transitioning from a development-heavy project to a deployment-ready professional product. It demonstrates to the jury that the team values **Maintainability**, **Clean Code**, and **Systematic Engineering**.

---
*Generated by the Calma Academic Board.*
