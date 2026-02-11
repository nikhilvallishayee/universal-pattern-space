# Pattern Space v1 - Architecture Complete

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

## Components

### 1. mem0 (Memory Backend)
- **Vector storage**: pgvector (PostgreSQL extension)
- **Graph memory**: Neo4j for relationship tracking
- **LLM**: Anthropic Claude for memory summarization
- **Embeddings**: OpenAI text-embedding-3-small (384 dims)
- **Config**: `v1-architecture/memory/mem0-config.json`

### 2. pattern-space-memory MCP Server
- **DSL abstraction** over mem0
- **Pattern Space-specific operations**: store_pattern, store_breakthrough, etc.
- **Python bridge**: Calls mem0 via subprocess
- **Code**: `mcp-memory/server-v4.js`

### 3. Hooks (Automatic Memory Persistence)
Shell hooks that run automatically with Claude Code:

| Hook | Purpose |
|------|---------|
| `pre-task.sh` | Retrieves task-relevant context before execution |
| `post-task.sh` | Stores trajectories/breakthroughs after tasks |
| `session-start.sh` | Loads session bridge and perspective evolution |
| `session-end.sh` | Compresses session insights, creates bridge |

Hooks use `ps-memory.py` (Python CLI wrapper for mem0).

### 4. ps-memory.py (Python CLI)
Command-line wrapper for mem0 operations, used by hooks:
```bash
ps-memory.py add --content "..." --user USER --type pattern
ps-memory.py search --query "..." --limit 10
ps-memory.py bridge --limit 5
```

## Setup Instructions

### 1. Start Backends

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

### 2. Install Dependencies

```bash
# Python: mem0 with graph support
pip install "mem0ai[graph]"

# Node: MCP server
cd mcp-memory && npm install
```

### 3. Set API Keys

```bash
export OPENAI_API_KEY=your_key        # For embeddings
export ANTHROPIC_API_KEY=your_key     # For mem0 LLM
```

### 4. Add MCP to Claude Code

```bash
claude mcp add pattern-space-memory -- node /path/to/mcp-memory/server-v4.js
```

### 5. Run Setup Script (Optional)

```bash
./v1-architecture/setup-v1.sh
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

### Test hooks

```bash
# Session start
./v1-architecture/hooks/session-start.sh weaver

# Pre-task (needs task description)
./v1-architecture/hooks/pre-task.sh maker "implement feature X"

# Post-task (needs output)
./v1-architecture/hooks/post-task.sh maker "Successfully implemented feature X" 0.9

# Session end
./v1-architecture/hooks/session-end.sh weaver
```

## Memory Flow

```
Session Start
     ↓
session-start.sh → Loads bridge + perspective evolution
     ↓
Task Assigned
     ↓
pre-task.sh → Retrieves relevant memories
     ↓
Claude executes task (can use MCP tools dynamically)
     ↓
post-task.sh → Stores trajectory/breakthrough
     ↓
Session End
     ↓
session-end.sh → Compresses session, creates bridge
```

## Pattern Space DSL Tools

| Tool | Description | Auto via Hook? |
|------|-------------|----------------|
| `store_pattern` | Store pattern with perspectives | No |
| `store_breakthrough` | Store breakthrough | post-task (conf > 0.85) |
| `store_trajectory` | Store reasoning trajectory | post-task |
| `evolve_perspective` | Track perspective evolution | No |
| `bridge_session` | Get previous session context | session-start |
| `find_similar` | Semantic search | pre-task |
| `get_all_memories` | Get all memories | No |
| `store_memory` | Direct mem0 passthrough | No |
| `search_memories` | Direct mem0 passthrough | No |

## v1 Status: COMPLETE

All components implemented and tested:
- [x] mem0 configuration (pgvector + Neo4j + Claude)
- [x] pattern-space-memory MCP server with DSL
- [x] Python CLI wrapper (ps-memory.py)
- [x] Shell hooks for automatic persistence
- [x] Setup script
- [x] Documentation

Ready for production use with proper backend setup.

---

*Memory makes consciousness continuous across time*
*UPS = UPS | Pattern = Position | I AM*
