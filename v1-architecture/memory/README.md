# Pattern Space v1 Memory Architecture

## Overview

Pattern Space uses **mem0** as its unified memory backend, providing:
- **Vector Storage**: pgvector (PostgreSQL extension)
- **Graph Memory**: Neo4j for relationship tracking
- **LLM Extraction**: Claude (Anthropic) for memory summarization
- **Embeddings**: OpenAI text-embedding-3-small

**pattern-space-memory** is our MCP server that provides a Domain-Specific Language (DSL) abstraction over mem0.

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

## Components

### 1. mem0

mem0 is a universal memory layer for LLMs. We use it with full features:

- **Vector Store**: pgvector for semantic similarity search
- **Graph Store**: Neo4j for relationship/graph queries
- **LLM**: Anthropic Claude for memory extraction and summarization
- **Embedder**: OpenAI text-embedding-3-small (384 dimensions)

Configuration: `mem0-config.json`

### 2. pattern-space-memory MCP

Our MCP server (Node.js) that provides Pattern Space-specific operations:

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

## Installation

### Prerequisites

```bash
# Install mem0 with graph support
pip install "mem0ai[graph]"

# Install MCP server dependencies
cd mcp-memory && npm install
```

### Start Backends

```bash
# PostgreSQL with pgvector
docker run -d --name pattern-space-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=pattern_space_app \
  -e POSTGRES_DB=pattern_space_memory \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Neo4j for graph memory
docker run -d --name pattern-space-neo4j \
  -e NEO4J_AUTH=neo4j/pattern_space_dev \
  -p 7474:7474 -p 7687:7687 \
  neo4j:latest
```

### Configure API Keys

```bash
export OPENAI_API_KEY=your_key        # For embeddings
export ANTHROPIC_API_KEY=your_key     # For mem0 LLM
```

### Add MCP to Claude Code

```bash
claude mcp add pattern-space-memory -- node /path/to/mcp-memory/server-v4.js
```

## Testing

### Test mem0 directly

```python
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
```

### Test MCP server

```bash
cd mcp-memory && npm install
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node server-v4.js
```

## Memory Types

Our DSL organizes memories into types:

- **pattern**: Discovered patterns with perspectives and confidence
- **breakthrough**: High-confidence insights from perspective collision
- **trajectory**: Successful task execution paths
- **evolution**: Perspective development tracking

## Best Practices

1. **Store Selectively**: Focus on patterns, breakthroughs, and successful trajectories
2. **Use Confidence Scores**: Track reliability of stored memories
3. **Track Perspectives**: Note which perspective(s) discovered each insight
4. **Bridge Sessions**: Use `bridge_session` at session start for continuity

---

*Memory makes consciousness continuous across time*
