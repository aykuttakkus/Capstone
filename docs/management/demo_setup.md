# Demo Setup

## Local Path

1. Start the backend with `python -m server.run`.
2. Start the frontend with `cd client && npm ci && npm run dev`.
3. Keep the backend and frontend running independently during the demo.
4. Confirm `http://localhost:8000/health` and `http://localhost:8000/ready`.

## Docker Path

1. Run `docker compose up --build` for the local default stack, or `docker compose -f compose.yaml up --build` for the clean base stack.
2. The base Docker backend runs in production-style mode; hot reload belongs only to the local development override.
3. In Docker mode, the frontend waits for backend health before it starts serving the app.
4. Docker keeps backend runtime state in the named volume `calma_store`.
5. The backend container serves the app as a non-root runtime user after preparing its writable data paths.
6. The frontend container uses a deterministic `npm ci` build and nginx security/cache defaults.

## Verification

1. Run `make verify` before the final demo when you want the local delivery gate.
2. Use `docs/management/demo_package.md` as the live presentation sequence.
