# Pattern Space v1 - Next Steps

## Current State

The v1 architecture has been scaffolded with:
- Universal Pattern Space Agent (`agents/pattern-space-agent.yaml`)
- PostgreSQL + pgvector initialization (`memory/init-postgres.sql`)
- Hooks for memory persistence (`hooks/`)
- Setup script (`setup-v1.sh`)
- pattern-space-memory v4.0 MCP server (`mcp-memory/server-v4.js`)

## Outstanding Work

### 1. Finalize mem0 Configuration

mem0 has **built-in graph memory** via Neo4j. Need to research and configure:

```python
config = {
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "dbname": "pattern_space_memory",
            "host": "localhost",
            "port": 5432,
            "user": "pattern_space_app",
            "password": "pattern_space_dev",
            "collection_name": "pattern_space_memories",
            "embedding_model_dims": 384
        }
    },
    "graph_store": {
        "provider": "neo4j",  # OR use pgvector-only?
        "config": {
            "url": "...",
            "username": "...",
            "password": "...",
            "database": "neo4j"
        }
    },
    "llm": {...},
    "embedder": {...},
    "version": "v1.1"
}
```

**Research needed:**
- Can mem0's graph_store use PostgreSQL or only Neo4j/Memgraph?
- Do we need separate graph DB or can pgvector + our pattern_space schema suffice?
- Review: https://docs.mem0.ai/open-source/features/graph-memory

### 2. Decide Architecture

**Option A: mem0 + Neo4j (Full mem0 features)**
```
mem0 (vector: pgvector, graph: neo4j)
     ↓
pattern-space-memory (orchestration layer)
```

**Option B: mem0 + pgvector only (Simpler)**
```
mem0 (vector: pgvector, no graph)
     ↓
pattern-space-memory (adds graph via pattern_space schema)
```

**Option C: mem0 handles everything**
```
mem0 (vector: pgvector, graph: neo4j)
pattern-space-memory becomes thin wrapper
```

### 3. Remove/Update ruvector

Current configs reference ruvector but it's a standalone Rust DB, not PostgreSQL-based.
- Either remove ruvector references entirely
- Or keep as optional separate trajectory store

### 4. Test Integration

```bash
# Start PostgreSQL with pgvector
docker run -d --name pattern-space-db \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Initialize schema
psql -U postgres -f v1-architecture/memory/init-postgres.sql

# Install mem0
pip install "mem0ai[graph]"

# Test mem0 connection
python -c "
from mem0 import Memory
import json
config = json.load(open('v1-architecture/memory/mem0-config.json'))
m = Memory.from_config(config)
print('mem0 initialized:', m)
"
```

### 5. Update pattern-space-memory Server

The `mcp-memory/server-v4.js` currently has its own PostgreSQL schema.
Need to decide if it should:
- Use mem0's API directly (preferred - single source of truth)
- Keep separate schema but integrate with mem0
- Become a thin MCP wrapper around mem0

## Resources

- mem0 docs: https://docs.mem0.ai/
- mem0 graph memory: https://docs.mem0.ai/open-source/features/graph-memory
- mem0 pgvector: https://docs.mem0.ai/components/vectordbs/dbs/pgvector
- mem0 GitHub: https://github.com/mem0ai/mem0

## Commands to Continue

```bash
# Clone and continue
git clone <repo>
cd universal-pattern-space
git checkout claude/activate-context-yDcyL

# Research mem0 graph integration
pip install "mem0ai[graph]"
python -c "from mem0 import Memory; help(Memory.from_config)"
```
