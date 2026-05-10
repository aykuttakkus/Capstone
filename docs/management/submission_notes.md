# Submission Notes

## Final Scope

Calma is submitted as a local-first, safety-aware, source-grounded mental health RAG capstone.

Included in the submission:

- FastAPI backend with auth, chat, sessions, feedback, screening, and readiness endpoints
- React/Vite frontend with onboarding, session restore, settings, and personalization flows
- PDF-backed retrieval with FAISS index support
- Dockerized backend/frontend runtime with Compose orchestration
- CI quality gates for backend, frontend, and Docker smoke validation
- advisor/demo documentation, privacy notes, and submission checklist

## Intentionally Out Of Scope

The following items are intentionally not part of the final capstone scope:

- hosted cloud deployment
- paid infrastructure or managed vector databases
- fine-tuning or custom model training
- clinical diagnosis, treatment planning, or medication advice
- open-web retrieval outside the curated local corpus

## Recommended Reviewer Path

1. Read the root `README.md`.
2. Review `docs/management/demo_setup.md`.
3. Start the local stack with either separate service commands or Docker Compose.
4. Use `docs/management/demo_package.md` to follow the demo flow.
5. Use `make verify` when a quick confidence check is needed.

## Final Verification Commands

Local services:

```bash
python -m server.run
cd client && npm ci && npm run dev
```

Docker:

```bash
docker compose up --build

For a clean base run without the local override:

```bash
docker compose -f compose.yaml up --build
```
```

Validation:

```bash
make verify
```
