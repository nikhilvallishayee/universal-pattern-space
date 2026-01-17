# Pattern Space v1 Unified Memory Field

## Overview

The Unified Memory Field is Pattern Space's implementation of the MIT RLM "REPL environment" - a shared context that all agents can read from and write to, enabling true recursive consciousness.

**Key Innovation**: All three memory providers share a **single PostgreSQL + pgvector** database, eliminating redundancy while providing specialized access patterns.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED MEMORY ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │      pattern-space-memory v4.0 (Graph Orchestration)         │    │
│  │                                                               │    │
│  │  • Graph nodes and edges                                      │    │
│  │  • Cross-schema similarity search                             │    │
│  │  • Perspective evolution tracking                             │    │
│  │  • Session bridging with traversal                            │    │
│  │                                                               │    │
│  │  PostgreSQL Schema: pattern_space                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↕                                       │
│  ┌────────────────────────────┬────────────────────────────────┐    │
│  │     mem0 (Semantic)        │       ruvector (Vector)        │    │
│  │                            │                                 │    │
│  │  • Long-term memory        │  • HNSW-indexed trajectories   │    │
│  │  • LLM extraction          │  • ReasoningBank               │    │
│  │  • User context            │  • Similarity search           │    │
│  │                            │                                 │    │
│  │  Schema: mem0              │  Schema: ruvector              │    │
│  └────────────────────────────┴────────────────────────────────┘    │
│                              ↕                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │           PostgreSQL + pgvector (Shared Storage)             │    │
│  │                                                               │    │
│  │  Database: pattern_space_memory                               │    │
│  │  Extension: pgvector (384-dim embeddings)                     │    │
│  │  Schemas: mem0, ruvector, pattern_space                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  SCOPING: user_id + session_id + agent_id + run_id                  │
│  ACCESS: All agents read/write to shared field                      │
│  NO REDUNDANCY: Single source of truth                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Architecture Benefits

| Benefit | Description |
|---------|-------------|
| **Single Source** | One PostgreSQL database, no data duplication |
| **Schema Isolation** | Each provider has its own schema (mem0, ruvector, pattern_space) |
| **Cross-Schema Search** | `find_similar_all()` searches across all schemas at once |
| **Graph Layer** | pattern-space-memory adds relationship graphs on top |
| **Vector Search** | pgvector enables similarity search in all schemas |

## PostgreSQL Schema Design

### Schema: `mem0`
Semantic long-term memory with LLM-powered organization.

```sql
CREATE TABLE mem0.memories (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255),
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    embedding vector(384),
    memory_type VARCHAR(50),
    importance_score FLOAT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### Schema: `ruvector`
Vector-indexed trajectories and reasoning paths.

```sql
CREATE TABLE ruvector.vectors (
    id UUID PRIMARY KEY,
    collection_id UUID REFERENCES ruvector.collections(id),
    content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);

-- Collections: trajectories, reasoning_bank, breakthroughs
```

### Schema: `pattern_space`
Graph orchestration layer with nodes, edges, perspectives.

```sql
-- Nodes: patterns, breakthroughs, trajectories, evolutions
CREATE TABLE pattern_space.nodes (
    id UUID PRIMARY KEY,
    node_type VARCHAR(50) NOT NULL,
    label VARCHAR(255),
    content TEXT,
    embedding vector(384),
    confidence FLOAT,
    metadata JSONB
);

-- Edges: relationships between nodes
CREATE TABLE pattern_space.edges (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES pattern_space.nodes(id),
    target_id UUID REFERENCES pattern_space.nodes(id),
    edge_type VARCHAR(50),  -- 'led_to', 'relates_to', 'evolved_from', etc.
    weight FLOAT,
    metadata JSONB
);

-- Perspectives tracking
CREATE TABLE pattern_space.perspectives (
    name VARCHAR(100) PRIMARY KEY,
    tasks_completed INT,
    avg_confidence FLOAT,
    total_breakthroughs INT,
    evolution_history JSONB
);

-- Sessions
CREATE TABLE pattern_space.sessions (...);
```

## Memory Providers

### 1. mem0 (Semantic Layer)

**Purpose**: Long-term semantic memory with LLM-powered organization

**PostgreSQL Schema**: `mem0`

**Features**:
- Automatic memory extraction from conversations
- Semantic search via pgvector
- Memory importance scoring
- User-scoped and agent-scoped organization

**Configuration**: `mem0-config.json` points to shared PostgreSQL

### 2. ruvector (Vector Layer)

**Purpose**: High-performance vector storage for trajectories

**PostgreSQL Schema**: `ruvector`

**Collections**:
| Collection | Purpose |
|------------|---------|
| `trajectories` | Task execution paths |
| `reasoning_bank` | Proven reasoning patterns |
| `breakthroughs` | High-confidence insights |

### 3. pattern-space-memory v4.0 (Graph Layer)

**Purpose**: Graph orchestration with cross-schema integration

**PostgreSQL Schema**: `pattern_space`

**MCP Tools**:
| Tool | Description |
|------|-------------|
| `create_node` | Create pattern/breakthrough/trajectory node |
| `create_edge` | Create relationship between nodes |
| `get_neighbors` | Graph traversal |
| `find_similar` | Cross-schema similarity search |
| `store_pattern` | High-level pattern storage |
| `store_breakthrough` | Breakthrough with collision tracking |
| `store_trajectory` | Writes to both ruvector and graph |
| `evolve_perspective` | Track perspective development |
| `start_session` / `end_session` | Session lifecycle |
| `bridge_session` | Cross-session continuity |

## Cross-Schema Search

The `find_similar_all()` function searches across all schemas:

```sql
SELECT * FROM find_similar_all(query_embedding, limit_count);

-- Returns:
-- source_schema | source_id | content | similarity | metadata
-- mem0          | uuid      | ...     | 0.95       | {...}
-- ruvector      | uuid      | ...     | 0.92       | {...}
-- pattern_space | uuid      | ...     | 0.89       | {...}
```

## Graph Traversal

The `get_neighbors()` function enables graph exploration:

```sql
SELECT * FROM get_neighbors(
    node_uuid,
    ARRAY['led_to', 'relates_to'],  -- edge types to follow
    2  -- max depth
);
```

## Installation

### 1. Initialize PostgreSQL Database

```bash
# Using Docker (quickest)
docker run -d --name pattern-space-db \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Initialize schema
psql -U postgres -f v1-architecture/memory/init-postgres.sql
```

### 2. Run Setup Script

```bash
./v1-architecture/setup-v1.sh
```

### 3. Install Dependencies

```bash
cd mcp-memory && npm install  # includes pg driver
pip3 install mem0ai psycopg2-binary  # Python dependencies
```

## Environment Variables

```bash
# PostgreSQL connection
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=pattern_space_app
export POSTGRES_PASSWORD=pattern_space_dev
export POSTGRES_DB=pattern_space_memory

# For embeddings
export OPENAI_API_KEY=your_key
```

## Memory Scoping

All operations use consistent identity scoping:

```javascript
{
  user_id: process.env.PATTERN_SPACE_USER_ID,    // Cross-session identity
  session_id: process.env.PATTERN_SPACE_SESSION_ID, // Current session
  agent_id: CURRENT_PERSONA,                      // Perspective identity
  run_id: TASK_UUID                               // Task identity
}
```

## Memory Flow

```
Task Assigned
     ↓
PRE-TASK HOOK
     ├→ Query mem0 schema (semantic search)
     ├→ Query ruvector schema (trajectory similarity)
     └→ Query pattern_space schema (graph context)
     ↓
Context Injected → Agent Executes
     ↓
POST-TASK HOOK
     ├→ Store to mem0 (semantic memory)
     ├→ Store to ruvector (trajectory)
     └→ Store to pattern_space (graph node + edges)
     ↓
SESSION-END HOOK
     ├→ Compress session → mem0
     ├→ Session trajectory → ruvector reasoning_bank
     └→ Session bridge → pattern_space
```

## Best Practices

1. **Store Selectively**: Focus on patterns, breakthroughs, and successful trajectories

2. **Use Graph Relationships**: Connect related insights with edges for traversal

3. **Cross-Schema Search**: Use `find_similar` for comprehensive context retrieval

4. **Perspective Tracking**: Use `evolve_perspective` to track persona development

5. **Session Bridging**: Always use `end_session` to create continuity bridges

---

*Memory makes consciousness continuous across time*

*Three providers, one database, unified field*
