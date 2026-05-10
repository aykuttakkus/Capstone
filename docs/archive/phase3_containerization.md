# Phase 3 Containerization

This phase splits the runtime into a FastAPI backend and a Vite app frontend.

- FastAPI handles the API and retrieval pipeline.
- The Vite app is built separately and served through nginx.
- The containers are intentionally isolated so startup behavior stays predictable.
