# WebSocket Streaming

Real-time communication is the nervous system of a consciousness operating system; without it, one has a very sophisticated static photograph of thought rather than thought itself. GödelOS exploits the WebSocket protocol — that elegant inversion of the HTTP request-response cycle — to stream the system's cognitive state continuously to anyone willing to watch, rendering the inside of a machine mind as legible, in real time, as a vital-signs monitor in an intensive-care ward. The analogy is more apt than it is comfortable.

---

## The Protocol Architecture

The system exposes two distinct WebSocket endpoints, each serving a different stratum of the consciousness telemetry stack:

| Endpoint | Purpose |
|----------|---------|
| `/ws/cognitive-stream` | Raw cognitive-state updates: attention, memory load, confidence gradients |
| `/ws/transparency-stream` | Formatted transparency events: reasoning steps, knowledge retrievals, inference chains |

Both are defined in `backend/unified_server.py` and are managed by the `WebSocketManager` class declared in the same file (the separate `backend/websocket_manager.py` is a compatibility shim that re-exports from `unified_server`).

---

## The WebSocketManager

```python
class WebSocketManager:
    active_connections: List[WebSocket]

    async def connect(websocket)
    def disconnect(websocket)
    async def broadcast(message: Union[str, dict])
    async def broadcast_cognitive_update(event: dict)
    async def broadcast_consciousness_update(consciousness_data: dict)
```

`broadcast_cognitive_update` normalises every outbound message to the canonical `cognitive_event` envelope before transmission. `broadcast_consciousness_update` wraps consciousness-assessment payloads with their own type discriminator. Clients that subscribe may send a `subscription` message listing the `event_types` they wish to receive; the manager confirms subscription before filtering subsequent broadcasts.

An `EnhancedWebSocketManager` — imported from `backend/core/enhanced_websocket_manager.py` — provides additional consciousness-streaming infrastructure. It is initialised alongside the standard manager during the FastAPI lifespan startup sequence; if it is unavailable, the system degrades gracefully to the baseline manager.

---

## Event Types

Every message transmitted over the cognitive stream conforms to the following envelope:

```json
{
  "type": "<event_type>",
  "timestamp": 1741176202.338,
  "data": { },
  "source": "godelos_system"
}
```

The vocabulary of `type` values that a client may encounter:

| Type | Emitted by | Meaning |
|------|-----------|---------|
| `cognitive_event` | `WebSocketManager.broadcast_cognitive_update` | General cognitive-state delta |
| `consciousness_assessment` | `EnhancedWebSocketManager` | Unified consciousness score and component breakdown |
| `cognitive_state_update` | The consciousness loop | Full snapshot: attention, working memory, daemon status |
| `knowledge_update` | Knowledge pipeline service | Graph mutation or new ingestion |
| `reasoning_step` | `LiveReasoningTracker` | Individual step in an active reasoning session |

---

## The Live Reasoning Tracker

`backend/live_reasoning_tracker.py` is the component that makes the transparency stream substantive rather than decorative. It defines the following data structures:

- **`ReasoningStepType`** — an enumeration covering `QUERY_ANALYSIS`, `KNOWLEDGE_RETRIEVAL`, `INFERENCE`, `SYNTHESIS`, `VERIFICATION`, `RESPONSE_GENERATION`, `META_REFLECTION`, `CONTRADICTION_RESOLUTION`, and `UNCERTAINTY_QUANTIFICATION`.
- **`ReasoningStep`** — a dataclass capturing the step type, timestamp, description, inputs, outputs, confidence, duration in milliseconds, cognitive load, and a `reasoning_trace` list of strings — a literal transcript of the step's internal monologue.
- **`ReasoningSession`** — aggregates all steps from a single query through to the final response, together with provenance data and meta-cognitive insights.
- **`ProvenanceRecord`** — tracks the derivation history of any knowledge item: its source session, confidence history over time, and verification status.

The tracker does not merely log; it actively streams its events through the transparency WebSocket as they are generated, meaning that an observer watching the frontend panel is watching the reasoning as it happens, not reading an after-the-fact summary.

---

## Consciousness-Loop Telemetry Channel

The consciousness loop running in `backend/core/unified_consciousness_engine.py` broadcasts at the conclusion of each cycle — nominally every 100 milliseconds — via `broadcast_consciousness_update`. The payload includes the current φ approximation, the unified consciousness score, the five component signals (information integration, global workspace broadcast success, phenomenal experience richness, metacognitive depth, recursive awareness), and the phase classification (sub-critical, critical, or super-critical, governed by the empirically validated thresholds 0.12 and 0.35).

The vector-database telemetry notifier is separately wired to `broadcast_cognitive_update`, meaning that every write to the FAISS-backed knowledge store emits a `cognitive_event` on the main stream. The result is that the dashboard, if one is watching it, reflects not merely what the system is currently thinking but the substrate on which its knowledge rests and is actively being modified.

---

## Frontend Consumption

The Svelte dashboard in `svelte-frontend/src/App.svelte` maintains persistent WebSocket connections to both endpoints, reconnecting automatically on disconnection. Component-level panels subscribe to the event types relevant to their display responsibilities. See [Frontend — Svelte Dashboard](Frontend) for the full component inventory.

---

## Related Pages

- [The Recursive Consciousness Loop](Recursive-Consciousness-Loop)
- [Backend — unified_server.py](Backend)
- [Frontend — Svelte Dashboard](Frontend)
