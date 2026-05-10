# Redundancy Analysis & Cleanup Report
**Prepared by:** Prof. Dr. Software Engineer (Antigravity AI)
**Project:** Calma Refactoring — Phase 2
**Date:** May 9, 2026

## 1. Executive Summary
This report analyzes the root directory and project structure for redundant files. The goal is to minimize clutter and ensure every file has a clear, professional purpose. We distinguish between "temporary junk" (to be deleted) and "professional boilerplate" (to be kept).

---

## 2. Redundancy Audit (Root Directory)

| File / Folder | Status | Recommendation | Rationale |
| :--- | :--- | :--- | :--- |
| **`run.py` (root)** | 🗑️ Redundant | **Delete** | We now have `Makefile` and `server/run.py`. This root file is a "duplicate entry point" that causes confusion. |
| **`.DS_Store`** | 🗑️ Junk | **Delete** | macOS system file. Should be handled by `.gitignore`. |
| **`__pycache__/`** | 🗑️ Junk | **Delete** | Python bytecode cache. Should be in `.gitignore`. |
| **`.pytest_cache/`** | 🗑️ Junk | **Delete** | Test cache. Should be in `.gitignore`. |
| **`infra/`** | 🗑️ Redundant | **Delete** | Currently an empty directory. If we need Nginx/K8s configs later, we can recreate it. |
| **`Dockerfile.server`** | ✅ Active | Keep | Backend container for the `/server` runtime. |
| **`client/Dockerfile`** | ✅ Active | Keep | Frontend container for the `/client` runtime. |

---

## 3. Professional Assets (TO BE KEPT)
Some files might *look* like clutter but are essential for enterprise-grade repositories:

| File | Status | Purpose |
| :--- | :--- | :--- |
| **`requirements-dev.txt`** | ✅ **Essential** | Contains tools for developers only (pytest, black, flake8). This keeps the production environment (`requirements.txt`) lightweight and secure. |
| **`.env.example`** | ✅ **Essential** | A template for other developers. It shows what environment variables are needed without leaking your private keys/passwords. |
| **`pytest.ini`** | ✅ **Essential** | Configures how tests are run. Essential for a stable testing pipeline. |
| **`Makefile`** | ✅ **Essential** | The "remote control" for the project. Standardizes commands across different developer machines. |

---

## 4. Logical Cleanup Roadmap

### Step 1: Root Cleanup
- Remove the empty `infra/` folder.
- Remove root `run.py`.
- Clean up system junk (`.DS_Store`, `__pycache__`).

### Step 2: Naming Standardization
- Standardize Dockerfiles to `Dockerfile.server` and `client/Dockerfile`.

### Step 3: Test Refactoring (Future)
- The files in `tests/unit` starting with `test_phaseX...` should eventually be renamed to functional names (e.g., `test_auth.py`, `test_sessions.py`) to move away from "milestone-based" naming to "feature-based" naming.

---

## 5. Future Usage Analysis
- **`scripts/evaluate_retrieval.py`**: Keep. This will be the foundation for your automated RAG evaluation (LLM-as-a-Judge).
- **`data/processed/versions`**: Keep. This allows "time-traveling" through your knowledge base versions, a key feature for RAG transparency.

---
> [!IMPORTANT]
> A clean root directory is the first thing a technical reviewer (or professor) sees. It signals a mature, organized engineering mindset.
