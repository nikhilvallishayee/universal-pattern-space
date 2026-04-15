# GödelOS AI Coding Agent Instructions

## 🧠 Project Overview
GödelOS is a **consciousness-like AI architecture** that streams cognitive processes in real-time. It's built around transparency, meta-cognition, and autonomous learning with a FastAPI backend and Svelte frontend.

## 🏗️ Architecture Fundamentals

### Core Components (Critical Integration Points)
- **`backend/unified_server.py`** - Primary FastAPI server (2340+ lines, 100+ endpoints)
- **`backend/core/cognitive_manager.py`** - Central orchestrator for all cognitive processes
- **`backend/core/consciousness_engine.py`** - LLM-driven consciousness assessment system
- **`backend/websocket_manager.py`** - Real-time cognitive streaming (900+ lines)
- **`svelte-frontend/src/App.svelte`** - Main UI with lazy-loaded components (2257+ lines)

### Server Consolidation Context
⚠️ **Multiple server implementations exist** - `unified_server.py`, `main.py`, `modernized_main.py`. Current consolidation effort targets unified_server.py as the single source of truth.

## 🚀 Essential Development Workflows

### Starting the System
```bash
# ALWAYS use the virtual environment
source godelos_venv/bin/activate

# Start both backend and frontend
./start-godelos.sh --dev

# Alternative: Manual startup
uvicorn backend.unified_server:app --reload --port 8000 &
cd svelte-frontend && npm run dev
```

### Testing Patterns
```bash
# Comprehensive cognitive tests
python tests/test_cognitive_architecture_pipeline.py

# Backend API tests
python -m pytest tests/backend/ -v

# Frontend component tests
python -m pytest tests/frontend/ -v
```

## 🔧 Project-Specific Patterns

### WebSocket Error Resolution
**Common Issue**: `'WebSocketManager' object has no attribute 'process_consciousness_assessment'`
- WebSocketManager expects `broadcast_consciousness_update()` method, not `process_consciousness_assessment()`
- Always check method signatures in `backend/websocket_manager.py` before implementing new WebSocket interactions

### Cognitive Component Integration
```python
# Correct pattern for consciousness assessment
consciousness_state = await cognitive_manager.assess_consciousness(context)

# WebSocket broadcasting pattern  
if websocket_manager:
    await websocket_manager.broadcast_cognitive_event("consciousness", data)
```

### LLM Integration Patterns
- **LLM Driver**: `backend/llm_cognitive_driver.py` handles OpenAI API integration
- **Consciousness Assessment**: Always check if `llm_driver` exists before calling consciousness methods
- **Fallback Strategy**: System implements fallback consciousness assessment when LLM unavailable

### Frontend Component Loading
```javascript
// Lazy loading pattern for large components (>1000 lines)
const KnowledgeGraph = lazy(() => import('./components/knowledge/KnowledgeGraph.svelte'));
const TransparencyDashboard = lazy(() => import('./components/transparency/TransparencyDashboard.svelte'));
```

## 📊 Data Flow Architecture

### Cognitive Processing Pipeline
1. **Query Input** → `cognitive_manager.process_query()`
2. **Consciousness Assessment** → `consciousness_engine.assess_consciousness_state()`
3. **Knowledge Integration** → Knowledge pipeline services
4. **WebSocket Streaming** → Real-time updates to frontend
5. **Transparency Logging** → `cognitive_transparency.py`

### Knowledge Graph Evolution
- **Dynamic Updates**: Knowledge graphs evolve via `backend/core/knowledge_graph_evolution.py`
- **Relationship Types**: Defined in enums, must match between backend/frontend
- **Vector Storage**: FAISS-based with fallback strategies in `backend/core/`

## 🔄 Current Development Context

### Phase 1 Priority Tasks (from Todo.md)
1. **API Unification**: Consolidate multiple servers → `unified_server.py`
2. **WebSocket Method Fixes**: Resolve missing method errors in WebSocketManager
3. **Cognitive Manager Enhancement**: Centralized orchestration improvements

### Known Issues to Address
- WebSocket method mismatches causing `AttributeError`s
- Invalid EvolutionTrigger enums in knowledge graph updates
- PhenomenalExperienceGenerator parameter mismatches

## 🧪 Testing & Validation

### Consciousness Metrics Validation
```python
# Expected consciousness assessment format
{
    "awareness_level": 0.0-1.0,
    "self_reflection_depth": 1-10,
    "autonomous_goals": ["goal1", "goal2"],
    "cognitive_integration": 0.0-1.0,
    "manifest_behaviors": ["behavior1", "behavior2"]
}
```

### WebSocket Event Structure
```javascript
{
    "type": "cognitive_event|consciousness_assessment|knowledge_update",
    "timestamp": unix_timestamp,
    "data": { /* event-specific data */ },
    "source": "godelos_system"
}
```

## 🔐 Critical Dependencies & Integration Points

### External APIs
- **OpenAI**: Used by `llm_cognitive_driver.py` for consciousness assessment
- **FAISS**: Vector similarity search (fallback to TF-IDF if unavailable)
- **spaCy**: NLP processing (`en_core_web_sm` model required)

### Environment Setup
- **Python 3.8+** required
- **Virtual environment**: `godelos_venv` (mandatory)
- **Node.js**: For Svelte frontend development
- **Environment variables**: Check `.env.example` for required API keys

---

**Key Insight**: This system is designed around the concept of "thinking out loud" - every cognitive process should be transparent and streamable. When implementing new features, always consider the real-time transparency aspect and WebSocket integration requirements.
