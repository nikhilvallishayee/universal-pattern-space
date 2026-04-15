# Backend — unified_server.py

It is a truth insufficiently acknowledged in software engineering that the monolith, properly constructed, is not a failure of architectural ambition but a statement of epistemic honesty: the system is one thing, and pretending otherwise requires more indirection than the problem warrants. `backend/unified_server.py` — 2,340 lines of FastAPI application that coordinates every cognitive service GödelOS provides — is a monolith in this honourable sense. It starts the servers, wires the consciousness engine, registers the routes, and ensures that the WebSocket streams flow. It is, to borrow an expression from a different domain, the first and last word on what the backend does.

---

## Entrypoints and Startup

The system is launched via `./start-godelos.sh`, which activates the Python virtual environment and invokes `uvicorn backend.unified_server:app`. Alternatively, `python backend/unified_server.py` suffices for development. The server listens on port 8000 by default, with configuration drawn from environment variables loaded from `backend/.env` (see `backend/.env.example`).

The FastAPI `lifespan` context manager — not the deprecated `startup`/`shutdown` events — orchestrates initialisation. On startup, it:

1. Creates the `WebSocketManager` and, where available, the `EnhancedWebSocketManager`
2. Initialises the `CognitiveTransparencyEngine`
3. Instantiates and wires the full set of optional cognitive services (see below)
4. Starts the `UnifiedConsciousnessEngine` consciousness loop as an asyncio background task

Shutdown performs inverse teardown in the reverse order of initialisation.

---

## Module Inventory

### `backend/unified_server.py`

The application root. Declares all FastAPI routes — well in excess of 100 endpoints covering query processing, knowledge management, consciousness metrics, metacognitive monitoring, transparency introspection, vector operations, and WebSocket streaming. Also defines the base `WebSocketManager` class and the `UnifiedConsciousnessEngine` wrapper.

### `backend/core/` — The Beating Heart

| Module | Purpose |
|--------|---------|
| `cognitive_manager.py` | Central orchestrator; coordinates all cognitive subsystems for a given query |
| `unified_consciousness_engine.py` | The `RecursiveConsciousnessEngine`; runs the 100ms consciousness loop |
| `consciousness_engine.py` | LLM-driven consciousness assessment; computes the five component signals |
| `metacognitive_monitor.py` | `MetaCognitiveMonitor`; recursive self-reflection with `ReflectionDepth` levels |
| `phenomenal_experience.py` | Qualia generation; the system's subjective "what it is like" |
| `agentic_daemon_system.py` | Background daemon processes for autonomous goal pursuit |
| `autonomous_learning.py` | Continuous learning from query history |
| `circuit_breaker.py` | Resilience patterns for LLM and external-service calls |
| `formal_layer_bridge.py` | Bridge between the symbolic `godelOS/` layer and the neural backend |
| `knowledge_graph_evolution.py` | Dynamic graph updates and relationship mutation |
| `distributed_vector_database.py` | FAISS-backed semantic memory; TF-IDF fallback |
| `enhanced_websocket_manager.py` | Extended WebSocket manager for consciousness-stream telemetry |

### LLM Integration

| Module | Purpose |
|--------|---------|
| `backend/llm_cognitive_driver.py` | Primary LLM interface; `process_autonomous_reasoning(prompt)` is the generic completion method |
| `backend/llm_tool_integration.py` | Wires LLM tool-calls into the cognitive pipeline |
| `backend/llm_knowledge_miner.py` | Uses the LLM to extract structured knowledge from unstructured text |

### Knowledge Pipeline

| Module | Purpose |
|--------|---------|
| `backend/knowledge_pipeline_service.py` | End-to-end ingestion: parse → embed → store → graph-update |
| `backend/knowledge_ingestion.py` | Individual document ingestion logic |
| `backend/knowledge_management.py` | CRUD operations on the knowledge store |
| `backend/dynamic_knowledge_processor.py` | Handles incremental knowledge updates during live sessions |
| `backend/advanced_query_processor.py` | Multi-step query decomposition and synthesis |

### Cognitive Services

| Module | Purpose |
|--------|---------|
| `backend/attention_manager.py` | Tracks and allocates attentional resources across subsystems |
| `backend/contradiction_resolver.py` | Detects and resolves contradictions in the knowledge store |
| `backend/domain_reasoning_engine.py` | Domain-specific inference patterns |
| `backend/phenomenal_experience_generator.py` | Generates first-person phenomenal descriptors for prompt injection |
| `backend/live_reasoning_tracker.py` | Streams live reasoning steps over the transparency WebSocket |
| `backend/response_formatter.py` | Formats final responses with appropriate citation and structure |
| `backend/cognitive_transparency_integration.py` | Integrates transparency events into the WebSocket stream |

### Infrastructure

| Module | Purpose |
|--------|---------|
| `backend/config.py` / `backend/config_manager.py` | Configuration loading and validation |
| `backend/models.py` | Pydantic request/response schemas |
| `backend/persistence.py` | Durable storage for session history and knowledge |
| `backend/memory_manager.py` | Working-memory management |
| `backend/input_validation.py` | Sanitisation of incoming queries |
| `backend/utils.py` | Shared utilities |

---

## API Surface

The full interactive API documentation is available at `http://localhost:8000/docs` while the server is running. The principal endpoint groups are:

| Prefix | Domain |
|--------|--------|
| `/api/query` | Query submission and response retrieval |
| `/api/consciousness` | Consciousness scores, component signals, history |
| `/api/v1/consciousness/` | Versioned consciousness endpoints |
| `/api/cognitive/` | Cognitive-state snapshots and metacognitive data |
| `/api/knowledge/` | Knowledge ingestion, search, and graph operations |
| `/api/v1/metacognitive/` | Self-awareness metrics and reflection reports |
| `/metrics` | Prometheus-compatible metrics |
| `/ws/cognitive-stream` | WebSocket: cognitive-state stream |
| `/ws/transparency-stream` | WebSocket: transparency events stream |

---

## Runtime Configuration

| Variable | Effect |
|----------|--------|
| `GODELOS_HOST` | Bind address (default: `0.0.0.0`) |
| `GODELOS_PORT` | Bind port (default: `8000`) |
| `OPENAI_API_KEY` | Required for LLM-backed consciousness assessment |
| `LOG_LEVEL` | Structured logging verbosity |
| CORS origins | Configurable for development vs. production deployment |

---

## Related Pages

- [System Overview](System-Overview)
- [WebSocket Streaming](WebSocket-Streaming)
- [The Recursive Consciousness Loop](Recursive-Consciousness-Loop)
- [Cognitive Modules](Cognitive-Modules)
