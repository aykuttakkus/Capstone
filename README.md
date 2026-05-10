# Calma

**A psychology-oriented, safety-aware, source-grounded mental health RAG assistant.**

Calma provides guided psychoeducational support through trusted-source retrieval, structured interaction, and strict clinical safety boundaries. It is designed as an academic capstone demonstrating responsible AI design in a high-sensitivity domain.

> ⚠️ **Calma is an educational tool, not a clinical product.** It does not diagnose, prescribe, or replace professional mental health care.

---

## Key Technical Contributions

- **Dual-layer safety architecture** — Deterministic keyword engine (fast path) + LLM-based SafetyGuardian (nuanced path) with negation-aware matching
- **EvidenceGate** — Abstention mechanism that prevents hallucination by refusing to generate when retrieval confidence is below threshold
- **Hybrid retrieval** — FAISS semantic search (70%) + keyword BM25 (30%) + knowledge graph contextual boost
- **Corrective RAG (CRAG)** — `RetrievalGrader` agent validates retrieved evidence before passing to generation
- **PHQ-9 / GAD-7 clinical screening** integration for structured intake
- **6-tier safety priority chain** — Crisis → Distress → Medication → Diagnosis → Off-domain → Normal

---

## Architecture

See [docs/technical/ARCHITECTURE.md](docs/technical/ARCHITECTURE.md) for full system diagrams (flow, data layer, sequence, deployment).

---

## Evaluation Results

- Safety routing accuracy: see [docs/academic/TEST_RESULTS.md](docs/academic/TEST_RESULTS.md)
- Retrieval quality (Precision@5, nDCG@5): see [docs/academic/RETRIEVAL_EVALUATION.md](docs/academic/RETRIEVAL_EVALUATION.md)
- Automated behavior-driven coverage lives under `tests/unit`, `tests/integration`, and `tests/eval`

---

## Limitations

See [docs/technical/LIMITATIONS.md](docs/technical/LIMITATIONS.md) for full disclosure including linguistic bias, cultural limitations, and deployment constraints.

---

## Structure

- `client/` frontend application
- `server/` backend launcher and package root
- `server/app/` canonical backend application package
- `server/app/core/` canonical core package
- `server/app/services/` canonical service package
- `data/` corpus, indexes, secure DB
- `scripts/` maintenance scripts
- `Makefile` standard commands
- `docs/` categorized project docs
- `docs/archive/` archived phase notes and status docs

## Run

Backend:

```bash
python -m server.run
```

Frontend:

```bash
cd client
npm ci
npm run dev
```

Both apps now run independently. `python -m server.run` starts only the backend, and the frontend is started from `client/`.

## Docker

Full stack:

```bash
docker compose up --build
```

Default local `docker compose up --build` uses `compose.yaml` plus `compose.override.yaml`.
The clean production/demo path is `docker compose -f compose.yaml up --build`.
The base backend image starts in production-style mode, while hot reload lives only in the local override file.
The frontend service waits for the backend healthcheck before starting, while deeper application readiness remains available at `/ready`.
The backend persists its runtime database and FAISS index in the named Docker volume `calma_store`.
The backend mounts `data/raw` and `data/processed` read-only in the base stack, and prepares writable runtime state under `/app/data/store`.
The frontend image installs dependencies with `npm ci` and serves the build through nginx using a runtime upstream variable so it can support both full-stack and standalone modes.

Clean base stack:

```bash
docker compose -f compose.yaml up --build
```

Backend only:

```bash
docker compose up --build backend
```

Frontend only, with an external backend:

```bash
docker compose -f compose.yaml -f compose.frontend-standalone.yaml up --build frontend
```

Stop the stack:

```bash
docker compose down
```

Reset the stack and volume:

```bash
docker compose down -v
```

Default ports:

- backend: `http://localhost:8000`
- frontend: `http://localhost:8080`

## Makefile

- `make install` installs backend and frontend dependencies
- `make test-unit` runs the fast offline unit/service suite
- `make test-integration` runs API, database, and retrieval integration tests
- `make test` runs both backend test tiers
- `make test-eval` runs the separate evaluation contract and benchmark script
- `make verify` runs the full local validation gate
- `make run-stack` starts the full stack with Docker Compose
- `make docker-dev` starts the default local Docker development stack
- `make docker-prod` starts the clean base Docker stack
- `make docker-frontend-standalone` starts the frontend against an external backend
- `make docker-init-store` seeds the named runtime volume from `data/store`
- `make ingest-pdfs` rebuilds the PDF corpus inputs
- `make build-index` rebuilds the index artifacts

Local verification gate:

```bash
make verify
```

This gate runs backend unit and integration tests, frontend `npm ci` + lint/build, and the full Docker Compose contract validation set.

Readiness:

- health: `http://localhost:8000/health`
- ready: `http://localhost:8000/ready`

## Notes

- Copy `.env.example` to `.env` when you want local overrides.
- Docker Compose can start with its built-in defaults even when `.env` is absent.
- `FRONTEND_API_UPSTREAM` controls the nginx API upstream at runtime and is what enables the standalone frontend mode.
- `data/store/` and `data/processed/` contain generated artifacts.
- `data/raw/` should contain only real source PDFs.
- The local development override binds `data/raw`, `data/processed`, and `data/store` from the host for inspection and iteration.
- If you want to pre-seed the named store volume before a clean base run, use `make docker-init-store`.

## Demo

- See `docs/management/demo_package.md` for the advisor demo flow, architecture, and seed PDF guidance.
