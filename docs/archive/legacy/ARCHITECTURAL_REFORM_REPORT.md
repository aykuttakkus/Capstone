# Project Architecture & Structural Reform Report
**Prepared by:** Prof. Dr. Software Engineer (Antigravity AI)
**Project:** Calma — Psychology-Oriented Mental Health RAG Assistant
**Date:** May 9, 2026

## 1. Executive Summary
This report identifies structural inconsistencies in the current "Capstone-Project2" codebase and proposes a universal, enterprise-grade architecture. The goal is to elevate the project from a "working prototype" to a "defensible academic masterpiece" with clear separation of concerns, professional naming conventions, and scalable folder hierarchies.

## 2. Current Status Audit (Pain Points)
The current structure suffers from "organic growth syndrome," where features were added without refactoring the foundational layout.

| Issue | Observation | Impact |
| :--- | :--- | :--- |
| **Frontend Ambiguity** | Both `frontend/` and `web/` exist. `web/` is missing manifest files (`package.json`) yet contains build artifacts. | Developer confusion, build unpredictability. |
| **Launcher Redundancy** | Multiple `run.py` files (root and `/backend`) with overlapping logic. | Harder to debug entry points; inconsistent environment loading. |
| **Data Hierarchy** | `data/raw_pdfs`, `data/raw/pdfs`, and `data/processed` are inconsistently nested. | Fragile path handling in ingestion scripts. |
| **Doc Sprawl** | Documentation is scattered across `docs/design`, `docs/management`, `docs/archive`. | High cognitive load for reviewers/examiners. |
| **Layer Bleed** | Core RAG logic is partially coupled with FastAPI models in `backend/app`. | Reduced testability of core logic in isolation. |

---

## 3. Proposed Universal Architecture
We will adopt a **Poly-Repo Style Monorepo** structure, which is the industry standard for full-stack graduation projects.

### 📂 Root Structure
```text
Capstone-Project2/
├── client/                # (Renamed from frontend/) React/Vite SPA
├── server/                # (Renamed from backend/) FastAPI Application
├── core/                  # (New) Pure Domain Logic & RAG Engine (Framework-agnostic)
├── infra/                 # Docker, Nginx, CI/CD, K8s configs
├── docs/                  # Unified Documentation
│   ├── academic/          # Thesis, PRD, Technical Analysis
│   ├── technical/         # API Docs, Architecture, DB Schema
│   └── user/              # Manuals, Deployment Guides
├── data/                  # Managed Data Assets
│   ├── raw/               # Immutable raw sources
│   ├── processed/         # Cleaned/Chunked data
│   └── store/             # FAISS indexes, SQLite DBs
├── scripts/               # Maintenance & Ingestion Scripts
├── tests/                 # Unified Testing Suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── Makefile               # Universal Command Interface
├── docker-compose.yml     # Orchestration
└── README.md              # Global Entry Point
```

---

## 4. Logical Component Reform

### 🧠 Backend (Clean Architecture)
The backend will move from a flat structure to a **Layered Domain** approach:
1.  **Interface Layer (API):** FastAPI routes, Pydantic schemas (Request/Response).
2.  **Application Layer (Services):** Orchestration of use-cases (e.g., `ChatService`, `AuthService`).
3.  **Domain Layer (Core):** The "Brain." RAG Engine, Safety Policies, LLM Wrappers. No dependencies on FastAPI or SQLAlchemy.
4.  **Infrastructure Layer:** Database repositories, File I/O, FAISS persistence.

### 🎨 Frontend (Modular Architecture)
The client will be organized by **Feature-Based** structure:
- `client/src/features/chat`: Components, hooks, and stores for the chat interface.
- `client/src/features/assessment`: PHQ-9/GAD-7 logic.
- `client/src/components/ui`: Pure presentation components (shadcn/ui style).

---

## 5. Refactoring Roadmap (Action Plan)

### Phase 1: Structural Consolidation
1.  **Frontend Merge**: Delete `web/` after verifying `frontend/` contains all latest assets. Rename `frontend/` to `client/`.
2.  **Backend Rename**: Rename `backend/` to `server/`.
3.  **Launcher Cleanup**: Create a single `main.py` entry point or utilize `Makefile` for `make run-server` and `make run-client`.

### Phase 2: Data & Doc Alignment
1.  **Data Migration**: Move all raw PDFs to `data/raw/` and indices to `data/store/`.
2.  **Archive Pruning**: Move all "phaseX" archive files into a single `docs/archive/legacy_history/` to reduce clutter.

### Phase 3: Domain Isolation
1.  Move RAG logic from `server/app/core` to a top-level `core/` package if it's meant to be used by other tools (e.g., CLI, evaluation scripts), or strictly enforce layer boundaries within `server/`.

---

## 6. Professionalism Checklist for Graduation
- [ ] **No Dead Code**: Remove all `.bak`, `.old`, and redundant `run.py` files.
- [ ] **Path Independence**: Use `pathlib` and environment-relative paths everywhere.
- [ ] **Standardized Logging**: Centralized logging in `/logs`.
- [ ] **Dependency Hygiene**: Split `requirements.txt` and `requirements-dev.txt`.
- [ ] **Make Interface**: A professor should be able to run `make install` and `make run` without reading 10 pages of docs.

---
> [!IMPORTANT]
> This architectural shift ensures that your project isn't just a collection of scripts, but a **system**. This distinction is critical for high-grade academic evaluation.
