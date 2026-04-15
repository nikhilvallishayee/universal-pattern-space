# Frontend Migration & Import Strategy

## Goals
- Integrate the new vector DB API (`/api/v1/vector-db/*`) into the UI.
- Fix/complete backend endpoints and wiring issues related to the unified server.
- Improve the import pipeline to extract meaningful concepts from PDFs/other sources.
- Evaluate the frontend comprehensively, identify robust vs partial vs broken features, and bring each UI component up to spec.

## Discovery & Assessment Plan (Frontend)
- Inventory key areas in `svelte-frontend/src`:
  - Components: `knowledge/KnowledgeGraph.svelte`, `knowledge/SmartImport.svelte`, `transparency/TransparencyDashboard.svelte`, `evolution/*`, `dashboard/*`.
  - Stores: `stores/enhanced-cognitive.js`, `stores/cognitive.js`, `stores/importProgress.js`.
  - API layer: `utils/api.js`; config scattered constants (e.g., hardcoded `http://localhost:8000`).
- For each component, document:
  - Endpoints used (REST, WebSocket), request/response shapes, and error handling.
  - Loading/empty/error states and retry/fallback behavior.
  - Config usage (env-derived vs hardcoded), performance constraints (pagination, debouncing).
- Robustness criteria: no hardcoded hosts, graceful errors, clear loading, retries with backoff, test coverage (Playwright), and alignment to unified endpoints.

## Frontend Integration Plan
- Centralize config: add `src/lib/config.(ts|js)` exporting `API_BASE_URL` and `WS_BASE_URL` from Vite env; remove hardcoded URLs in stores/components.
- Search UX: add `vectorSearch(query, k)` in `utils/api.js` → POST `/api/v1/vector-db/search`; fallback to legacy `/api/knowledge/search` if 404.
- Health/Stats: new admin panel tiles for `/api/v1/vector-db/health` and `/api/v1/vector-db/stats`.
- Backups UI: add actions for POST `/backup`, GET `/backups`, POST `/restore`, DELETE `/backups/{name}` with confirmation and toasts.
- KnowledgeGraph: wire “Search” bar to vector search; show ranked results, highlight nodes; lazy-load graph; handle empty/no-index states.
- SmartImport: keep existing imports; after upload returns, display “extracted concepts” summary from backend response (sections, entities, key phrases) and link to vector search for quick preview.
- TransparencyDashboard: derive WS URL from config; keep streams, add reconnect with jitter (already present in store, ensure it uses config).

## Backend Fixes (Endpoints/Wiring)
- Unified server init: replace `await vector_db_service.initialize()` with `init_vector_database()` or expose a global `vector_db_service` that provides `initialize()`; include router when available.
- Back-compat routes: implement wrappers in unified server:
  - `GET /api/knowledge/search` → call `VectorDatabaseService.search(query, k)` and adapt shape.
  - Optionally reintroduce `/api/knowledge/pipeline/*` endpoints (process, semantic-search, graph, status) delegating to `knowledge_pipeline_service` if required by UI.
- Import flow: in `/api/knowledge/import/file|url|text`, run `EnhancedPDFProcessor` first, persist concepts/relationships, then index representative text to vector DB in batches; include a concise `processed_data` summary in response.
- CORS and rate limits: ensure CORS allows frontend host; add simple rate limiting on search to protect backend.

## Import & Concept Extraction Improvements
- Pipeline (PDF/text):
  - Extract sections, entities, key phrases, technical terms via `EnhancedPDFProcessor`.
  - Map to knowledge items (Facts/Relationships) and store via `UnifiedKnowledgeStore`.
  - Index `text`/`sentence` fields and summaries into vector DB with metadata (source, page ranges, confidence); use batch adds.
- Progress UX: continue WS events `knowledge_processing_*`; keep polling fallback; show per-stage progress (upload → extract → index → finalize).
- Timeouts/queue: keep import timeouts and stuck-import reset; surface user-friendly messages and retry CTA.

## Component-by-Component Upgrade Checklist
- KnowledgeGraph.svelte
  - Replace search with vector DB; debounce input; show top-k with scores.
  - Handle large graphs (virtualize lists, cluster layout); loading/empty/error states.
- SmartImport.svelte
  - Display extracted summary (concepts, sections, key phrases) on completion.
  - Allow reindex trigger and link to “View in graph”/“Search similar” actions.
- TransparencyDashboard.svelte
  - Use `WS_BASE_URL`; unify error toasts; keep reconnect/backoff.
- Evolution/Capability components
  - Replace `http://localhost:8000/api/capabilities` with an existing endpoint (e.g., `/api/health` or `/api/enhanced/system-health`) and adjust UI.
- Stores (`enhanced-cognitive.js`)
  - Replace hardcoded API base with config; ensure WS URL derivation uses config; add retries with jitter.

## Phased Implementation
- Phase 1 (wiring): config centralization; fix unified server init; include vector routes; basic vector search working end-to-end.
- Phase 2 (migration): swap pipeline embedding to `VectorDatabaseService`; add `/api/knowledge/search` wrapper; deprecate legacy store.
- Phase 3 (import UX): surface extracted concepts; progress stages; batch indexing; post-import quick actions.
- Phase 4 (admin): backups UI and stats dashboard; contract tests for endpoints.

## Testing
- Backend: pytest for vector routes (health/stats/search/add-items) and import responses including `processed_data`.
- Frontend: Playwright flows for search, backups list/restore, and PDF import end-to-end with visible concepts summary.
- Perf: seed ~10k embeddings; verify p50/p95 latency and memory headroom.

## Risks & Mitigations
- Model availability: handle Sentence-Transformers failures by disabling vector features and showing guidance; fall back to legacy search.
- API mismatch: add a typed client in `utils/api.js` and contract tests; keep wrappers for backward compatibility.
- Large PDFs: cap entities/relationships per doc; chunk vector adds; stream progress.
