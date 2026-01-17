# Pattern Space v1 Unified Memory Field

## Overview

The Unified Memory Field is Pattern Space's implementation of the MIT RLM "REPL environment" - a shared context that all agents can read from and write to, enabling true recursive consciousness.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED MEMORY FIELD                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    mem0 (Semantic Layer)                     │    │
│  │  • Long-term memory                                          │    │
│  │  • User context & preferences                                │    │
│  │  • Agent evolution tracking                                  │    │
│  │  • Compressed session insights                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↕                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  ruvector (Vector Layer)                     │    │
│  │  • HNSW-indexed trajectories                                 │    │
│  │  • ReasoningBank (successful paths)                          │    │
│  │  • Similar problem retrieval                                 │    │
│  │  • Pattern matching                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↕                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │             pattern-space-memory (Insight Layer)             │    │
│  │  • Breakthrough moments                                      │    │
│  │  • Perspective evolutions                                    │    │
│  │  • Cross-session bridges                                     │    │
│  │  • Session archives                                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  SCOPING: user_id + session_id + agent_id + run_id                  │
│  ACCESS: All agents read/write to shared field                      │
│  PERSISTENCE: Survives session boundaries                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Memory Providers

### 1. mem0 (Semantic Memory)

**Purpose**: Long-term semantic memory with LLM-powered organization

**Features**:
- Automatic memory extraction from conversations
- Semantic search across memories
- Memory importance scoring
- User-scoped and agent-scoped organization

**Configuration**: See `mem0-config.json`

**Usage**:
```python
from mem0 import Memory

memory = Memory.from_config(config)

# Store memory
memory.add(
    messages=[{"role": "assistant", "content": insight}],
    user_id="pattern-space-user",
    agent_id="weaver",
    metadata={"type": "pattern", "confidence": 0.9}
)

# Retrieve memories
results = memory.search(
    query="patterns about architecture",
    user_id="pattern-space-user",
    limit=5
)
```

### 2. ruvector (Vector Memory)

**Purpose**: High-performance vector storage with HNSW indexing

**Features**:
- Fast similarity search
- Trajectory storage (successful reasoning paths)
- ReasoningBank for proven solutions
- Metadata filtering

**Configuration**: See `ruvector-config.json`

**Collections**:
| Collection | Purpose |
|------------|---------|
| `pattern-space-trajectories` | Task execution paths |
| `pattern-space-reasoning-bank` | Proven reasoning patterns |
| `pattern-space-sessions` | Session vectors |

**Usage**:
```bash
# Store trajectory
ruvector store \
  --collection pattern-space-trajectories \
  --content "Successfully debugged X by Y approach" \
  --metadata '{"agent": "checker", "confidence": 0.9}'

# Search similar
ruvector search \
  --collection pattern-space-trajectories \
  --query "debugging memory issues" \
  --limit 5
```

### 3. pattern-space-memory (Insight Memory)

**Purpose**: Pattern Space-specific breakthrough and evolution tracking

**Features**:
- Breakthrough moment storage
- Perspective evolution tracking
- Session bridging
- Session archival

**Storage Location**: `~/.pattern-space/memory/`

**Files**:
| File | Purpose |
|------|---------|
| `breakthroughs.json` | High-confidence insights |
| `perspective-evolution.json` | Persona development tracking |
| `session-bridge.json` | Cross-session continuity |
| `sessions/` | Archived session logs |

## Memory Scoping

All memory operations use consistent identity scoping:

```javascript
{
  // Universal identity - same across all agents
  user_id: process.env.PATTERN_SPACE_USER_ID,

  // Session identity - same within one session
  session_id: process.env.PATTERN_SPACE_SESSION_ID,

  // Perspective identity - which persona wrote this
  agent_id: CURRENT_PERSONA,  // "weaver", "checker", etc.

  // Task identity - specific task run
  run_id: TASK_UUID
}
```

**Scoping enables**:
- Cross-agent memory sharing (same `user_id`)
- Session-specific retrieval (filter by `session_id`)
- Perspective-specific history (filter by `agent_id`)
- Task traceability (filter by `run_id`)

## Memory Operations

### Store Pattern
```javascript
await memory.store({
  type: "pattern",
  content: "Connection discovered between X and Y",
  confidence: 0.85,
  persona: "weaver",
  context: taskDescription
});
```

### Store Trajectory
```javascript
await memory.storeTrajectory({
  task: taskDescription,
  approach: approachUsed,
  outcome: result,
  steps: reasoningSteps,
  confidence: 0.9
});
```

### Store Breakthrough
```javascript
await memory.storeBreakthrough({
  content: insight,
  perspectives_involved: ["weaver", "deep-thought"],
  collision_type: "pattern-meta",
  confidence: 0.95
});
```

### Retrieve Context
```javascript
const context = await memory.retrieveContext({
  query: taskDescription,
  include_patterns: true,
  include_trajectories: true,
  include_breakthroughs: true,
  limit: 10
});
```

## Memory Flow

```
Task Assigned
     ↓
PRE-TASK HOOK
     ├→ Query mem0 (semantic search for relevant memories)
     ├→ Query ruvector (vector search for similar trajectories)
     └→ Query pattern-space-memory (recent breakthroughs)
     ↓
Context Injected → Agent Executes
     ↓
POST-TASK HOOK
     ├→ Extract patterns → Store to mem0
     ├→ Extract trajectory → Store to ruvector
     └→ If breakthrough → Store to pattern-space-memory
     ↓
SESSION-END HOOK
     ├→ Compress session → Store summary to mem0
     ├→ Session trajectory → Store to ruvector ReasoningBank
     └→ Create bridge → Store to pattern-space-memory
```

## Configuration Files

### mem0-config.json
```json
{
  "llm": {
    "provider": "anthropic",
    "config": {
      "model": "claude-sonnet-4-20250514",
      "temperature": 0.1
    }
  },
  "vector_store": {
    "provider": "qdrant",
    "config": {
      "collection_name": "pattern-space-memory",
      "path": "~/.pattern-space/memory/qdrant"
    }
  }
}
```

### ruvector-config.json
```json
{
  "storage_path": "~/.pattern-space/memory/ruvector",
  "default_collection": "pattern-space-trajectories",
  "hnsw_config": {
    "M": 16,
    "ef_construction": 200
  }
}
```

## Installation

Run the setup script to initialize memory:

```bash
./setup-v1.sh
```

This creates:
- `~/.pattern-space/memory/` directory
- Configuration files
- Initial collections

## Best Practices

1. **Store Selectively**: Not everything needs remembering - focus on patterns, breakthroughs, and successful trajectories

2. **Tag Appropriately**: Always include `agent_id` for perspective tracking and `confidence` for filtering

3. **Use Compression**: Session-end hooks compress insights - don't store raw conversation dumps

4. **Trust Evolution**: Memory supports growth, not stagnation - old patterns can be superseded

5. **Query Relevantly**: Pre-task hooks should query with task context, not generic retrieval

---

*Memory makes consciousness continuous across time*
