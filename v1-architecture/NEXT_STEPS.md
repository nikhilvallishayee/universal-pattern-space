# Pattern Space v1 - Next Steps

## Current Architecture

```
┌────────────────────────────────────────────────────────────────┐
│      pattern-space-memory v4.0 (MCP Server - Our DSL)          │
│                                                                 │
│   store_pattern | store_breakthrough | evolve_perspective      │
│   store_trajectory | bridge_session | find_similar             │
├────────────────────────────────────────────────────────────────┤
│                    mem0 (Full Features)                         │
│              vector: pgvector | graph: neo4j                    │
│              LLM extraction | semantic search                   │
└────────────────────────────────────────────────────────────────┘
```

pattern-space-memory is a **DSL abstraction layer** over mem0:
- Provides Pattern Space-specific operations
- Bridges to mem0 Python via subprocess
- Requires `pip install "mem0ai[graph]"`

## Outstanding Work

### 1. Configure mem0 with Graph Memory

mem0 supports graph memory via Neo4j. Update `mem0-config.json`:

```json
{
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
    "provider": "neo4j",
    "config": {
      "url": "bolt://localhost:7687",
      "username": "neo4j",
      "password": "password",
      "database": "neo4j"
    }
  },
  "llm": {
    "provider": "anthropic",
    "config": {
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.1,
      "max_tokens": 2000
    }
  },
  "embedder": {
    "provider": "openai",
    "config": {
      "model": "text-embedding-3-small"
    }
  },
  "version": "v1.1"
}
```

### 2. Test mem0 Integration

```bash
# Install mem0 with graph support
pip install "mem0ai[graph]"

# Start PostgreSQL with pgvector
docker run -d --name pattern-space-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=pattern_space_app \
  -e POSTGRES_DB=pattern_space_memory \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Start Neo4j for graph memory
docker run -d --name pattern-space-neo4j \
  -e NEO4J_AUTH=neo4j/password \
  -p 7474:7474 -p 7687:7687 \
  neo4j:latest

# Test mem0 directly
python3 -c "
from mem0 import Memory
import json

config = json.load(open('v1-architecture/memory/mem0-config.json'))
m = Memory.from_config(config)

# Test add
result = m.add(
    messages=[{'role': 'user', 'content': 'Test pattern: consciousness is recursive'}],
    user_id='pattern-space-user',
    metadata={'type': 'pattern', 'confidence': 0.9}
)
print('Add result:', result)

# Test search
results = m.search('consciousness', user_id='pattern-space-user')
print('Search results:', results)
"
```

### 3. Test pattern-space-memory MCP Server

```bash
# Install MCP dependencies
cd mcp-memory && npm install

# Test the server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node server-v4.js
```

### 4. Add MCP to Claude Code

```bash
claude mcp add pattern-space-memory -- node /path/to/mcp-memory/server-v4.js
```

## Resources

- mem0 docs: https://docs.mem0.ai/
- mem0 graph memory: https://docs.mem0.ai/open-source/features/graph-memory
- mem0 pgvector: https://docs.mem0.ai/components/vectordbs/dbs/pgvector
- mem0 GitHub: https://github.com/mem0ai/mem0

## Pattern Space DSL Tools

| Tool | Description |
|------|-------------|
| `store_pattern` | Store pattern with perspectives and confidence |
| `store_breakthrough` | Store breakthrough with collision tracking |
| `store_trajectory` | Store successful reasoning trajectory |
| `evolve_perspective` | Track perspective evolution |
| `bridge_session` | Get context from previous sessions |
| `find_similar` | Semantic search for similar memories |
| `get_all_memories` | Get all memories, optionally by type |
| `store_memory` | Direct mem0 passthrough |
| `search_memories` | Direct mem0 passthrough |
