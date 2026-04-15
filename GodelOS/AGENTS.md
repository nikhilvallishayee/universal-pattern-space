# Repository Guidelines

## FIRST AND FOREMOST: 95% of the time you will not need to stop or start the backend or frontend servers, they are hotreloading and once started can just be forgotten!


## Project Structure & Module Organization
- `backend/` — FastAPI backend (unified server in `unified_server.py`, utilities, models, WebSocket manager). Env in `backend/.env` (see `.env.example`).
- `svelte-frontend/` — Svelte UI (Vite). UI tests live here and at repo root.
- `tests/` — Pytest suites (unit, integration, e2e) and Playwright specs.
- `scripts/` and root `*.sh` — Startup and utility scripts (e.g., `start-unified-server.sh`).
- `knowledge_storage/`, `logs/`, `docs/` — persisted data, logs, and documentation.

## Build, Test, and Development Commands
- Backend setup: `./setup_venv.sh && source godelos_venv/bin/activate && pip install -r requirements.txt`
- Run backend (recommended): `./start-unified-server.sh` or `python backend/unified_server.py`
- Frontend dev: `cd svelte-frontend && npm install && npm run dev`
- Python tests (with coverage): `pytest` (reports to `test_output/coverage_html`)
- Playwright tests (root): `npm test` (see `package.json`), or in UI: `cd svelte-frontend && npm test`

## Coding Style & Naming Conventions
- Python: 4‑space indent, PEP 8. Format with `black .` and `isort .`. Type‑check with `mypy backend godelOS`.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Tests: files `test_*.py`; Svelte components `PascalCase.svelte`.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`; UI via Playwright.
- Marks: use `@pytest.mark.unit|integration|e2e|slow|requires_backend` (see `pytest.ini`).
- Run subsets: `pytest -m "unit and not slow"`.
- Some tests require a running backend on `localhost:8000`.

## Commit & Pull Request Guidelines
- Commits: imperative, focused changes. Example: `fix(backend): handle empty query in /api/query`.
- PRs: include description, rationale, screenshots/logs for UI/UX, and linked issues. Note any schema/API changes.
- Ensure: all tests pass, code formatted, no secrets checked in.

## Security & Configuration Tips
- Use `backend/.env` (copy from `.env.example`); never commit secrets.
- Common vars: `GODELOS_HOST`, `GODELOS_PORT`, CORS origins, log level (see backend README).

## Agent‑Specific Instructions
- Keep patches small and targeted; follow this guide’s structure.
- Prefer `unified_server.py` for backend entrypoints; update tests/docs when endpoints change.
- Validate locally: run `pytest` and representative Playwright specs before proposing changes.

