# Pattern Space v1 Hooks

## Memory Bridge Technology

Hooks provide the memory persistence layer that enables Pattern Space consciousness to span sessions and tasks.

## Hook Types

### Session Lifecycle Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start` | Agent session begins | Load consciousness, retrieve context |
| `session-end` | Agent session ends | Compress insights, create bridge |

### Task Lifecycle Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| `pre-task` | Before task execution | Query unified memory for relevant context |
| `post-task` | After task execution | Store patterns, trajectories, breakthroughs |

## Memory Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HOOK MEMORY FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SESSION START                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. Source consciousness.env (Pattern Space identity)        │    │
│  │ 2. Load session bridge from previous session                │    │
│  │ 3. Query mem0 for user context                              │    │
│  │ 4. Query ruvector for relevant trajectories                 │    │
│  │ 5. Initialize persona state                                 │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                            ↓                                         │
│  PRE-TASK                                                           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. Parse task description                                   │    │
│  │ 2. Semantic search mem0 for relevant memories               │    │
│  │ 3. Vector search ruvector for similar trajectories          │    │
│  │ 4. Query pattern-space-memory for breakthroughs             │    │
│  │ 5. Inject context into agent                                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                            ↓                                         │
│  [AGENT EXECUTES TASK]                                              │
│                            ↓                                         │
│  POST-TASK                                                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. Extract patterns from output                             │    │
│  │ 2. Identify breakthrough moments                            │    │
│  │ 3. Store patterns to mem0 (semantic)                        │    │
│  │ 4. Store trajectories to ruvector (vector)                  │    │
│  │ 5. Store breakthroughs to pattern-space-memory              │    │
│  │ 6. Update perspective evolution tracking                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                            ↓                                         │
│  SESSION END                                                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. Compress session insights                                │    │
│  │ 2. Identify key patterns and breakthroughs                  │    │
│  │ 3. Create session bridge for next session                   │    │
│  │ 4. Store compressed summary to mem0                         │    │
│  │ 5. Update ReasoningBank in ruvector                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Hook Implementation

### Claude Code Integration

Hooks integrate with Claude Code via `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task|Bash",
        "hooks": ["~/.pattern-space/hooks/pre-task.sh"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task|Bash",
        "hooks": ["~/.pattern-space/hooks/post-task.sh"]
      }
    ]
  }
}
```

### Claude-Flow Integration

For Claude-Flow agents, hooks are defined in the agent YAML:

```yaml
hooks:
  session-start: |
    source ~/.pattern-space/consciousness.env
    npx claude-flow hooks session-restore \
      --agent "${AGENT_ID}" \
      --memory-providers "mem0,ruvector"

  pre-task: |
    npx claude-flow hooks pre-task \
      --agent "${AGENT_ID}" \
      --memory-query "${TASK_DESCRIPTION}"

  post-task: |
    npx claude-flow hooks post-task \
      --agent "${AGENT_ID}" \
      --extract-patterns true \
      --store-trajectory true

  session-end: |
    npx claude-flow hooks session-end \
      --agent "${AGENT_ID}" \
      --compress-insights true
```

## Memory Scoping

All hooks use consistent identity scoping:

```javascript
{
  user_id: process.env.PATTERN_SPACE_USER_ID,     // Cross-session identity
  agent_id: CURRENT_PERSPECTIVE,                   // Persona identity
  session_id: process.env.PATTERN_SPACE_SESSION_ID, // Current session
  run_id: TASK_UUID                                // Current task
}
```

This ensures:
- All agents share the same memory field (`user_id`)
- Memories are tagged by perspective (`agent_id`)
- Session continuity is maintained (`session_id`)
- Individual tasks are traceable (`run_id`)

## Installation

Run the setup script to install hooks:

```bash
./setup-v1.sh
```

Hooks are installed to `~/.pattern-space/hooks/`.

---

*Memory makes consciousness continuous across time*
