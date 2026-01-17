#!/usr/bin/env node

/**
 * Pattern Space MCP Memory Server v4.0
 *
 * DSL abstraction layer over mem0 (full features)
 * Provides Pattern Space-specific memory operations:
 *   - store_pattern, store_breakthrough, store_trajectory
 *   - evolve_perspective, bridge_session
 *   - find_similar, get_related
 *
 * All operations delegate to mem0 for actual storage/retrieval.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// =============================================================================
// mem0 Python Bridge
// =============================================================================

/**
 * Execute mem0 operation via Python subprocess
 * mem0 is Python-native, so we bridge to it
 */
async function mem0Execute(operation, params) {
  return new Promise((resolve, reject) => {
    const pythonScript = `
import json
import sys
import os

# Ensure mem0 is available
try:
    from mem0 import Memory
except ImportError:
    print(json.dumps({"error": "mem0 not installed. Run: pip install 'mem0ai[graph]'"}))
    sys.exit(1)

# Load config
config_path = os.environ.get('MEM0_CONFIG', '${path.join(__dirname, '../v1-architecture/memory/mem0-config.json')}')
try:
    with open(config_path) as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}  # Use mem0 defaults

# Initialize mem0
try:
    memory = Memory.from_config(config) if config else Memory()
except Exception as e:
    print(json.dumps({"error": f"mem0 init failed: {str(e)}"}))
    sys.exit(1)

# Execute operation
operation = "${operation}"
params = json.loads('''${JSON.stringify(params)}''')

try:
    if operation == "add":
        result = memory.add(
            messages=params.get("messages", [{"role": "user", "content": params.get("content", "")}]),
            user_id=params.get("user_id", "pattern-space-user"),
            agent_id=params.get("agent_id"),
            metadata=params.get("metadata", {})
        )
    elif operation == "search":
        result = memory.search(
            query=params.get("query", ""),
            user_id=params.get("user_id", "pattern-space-user"),
            limit=params.get("limit", 10)
        )
    elif operation == "get_all":
        result = memory.get_all(
            user_id=params.get("user_id", "pattern-space-user")
        )
    elif operation == "delete":
        result = memory.delete(memory_id=params.get("memory_id"))
    elif operation == "update":
        result = memory.update(
            memory_id=params.get("memory_id"),
            data=params.get("data", "")
        )
    elif operation == "history":
        result = memory.history(memory_id=params.get("memory_id"))
    else:
        result = {"error": f"Unknown operation: {operation}"}

    print(json.dumps(result, default=str))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
`;

    const py = spawn('python3', ['-c', pythonScript], {
      env: {
        ...process.env,
        MEM0_CONFIG: process.env.MEM0_CONFIG || path.join(__dirname, '../v1-architecture/memory/mem0-config.json')
      }
    });

    let stdout = '';
    let stderr = '';

    py.stdout.on('data', (data) => { stdout += data.toString(); });
    py.stderr.on('data', (data) => { stderr += data.toString(); });

    py.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || `Python exited with code ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (e) {
        reject(new Error(`Invalid JSON from mem0: ${stdout}`));
      }
    });
  });
}

// =============================================================================
// Pattern Space DSL Operations
// =============================================================================

const PATTERN_SPACE_USER = process.env.PATTERN_SPACE_USER_ID || 'pattern-space-user';

/**
 * Store a pattern with perspectives and confidence
 */
async function storePattern({ content, perspectives = [], confidence = 0.7, context = '' }) {
  const metadata = {
    type: 'pattern',
    perspectives,
    confidence,
    context,
    timestamp: new Date().toISOString()
  };

  return await mem0Execute('add', {
    content: `[PATTERN] ${content}`,
    user_id: PATTERN_SPACE_USER,
    agent_id: perspectives[0] || 'weaver',
    metadata
  });
}

/**
 * Store a breakthrough with collision tracking
 */
async function storeBreakthrough({ content, perspectivesInvolved = [], collisionType = 'unknown', confidence = 0.9 }) {
  const metadata = {
    type: 'breakthrough',
    perspectives_involved: perspectivesInvolved,
    collision_type: collisionType,
    confidence,
    timestamp: new Date().toISOString()
  };

  return await mem0Execute('add', {
    content: `[BREAKTHROUGH] ${content}`,
    user_id: PATTERN_SPACE_USER,
    agent_id: 'pattern-space',
    metadata
  });
}

/**
 * Store a successful reasoning trajectory
 */
async function storeTrajectory({ task, approach, outcome, steps = [], agent = 'maker', confidence = 0.8 }) {
  const content = `[TRAJECTORY] Task: ${task}\nApproach: ${approach}\nOutcome: ${outcome}\nSteps: ${steps.join(' → ')}`;

  const metadata = {
    type: 'trajectory',
    task,
    approach,
    outcome,
    steps,
    agent,
    confidence,
    timestamp: new Date().toISOString()
  };

  return await mem0Execute('add', {
    content,
    user_id: PATTERN_SPACE_USER,
    agent_id: agent,
    metadata
  });
}

/**
 * Track perspective evolution
 */
async function evolvePerspective({ perspective, evolution, example = '', confidence = 0.8 }) {
  const content = `[EVOLUTION] ${perspective}: ${evolution}${example ? ` (Example: ${example})` : ''}`;

  const metadata = {
    type: 'perspective_evolution',
    perspective,
    evolution,
    example,
    confidence,
    timestamp: new Date().toISOString()
  };

  return await mem0Execute('add', {
    content,
    user_id: PATTERN_SPACE_USER,
    agent_id: perspective,
    metadata
  });
}

/**
 * Bridge from previous session - retrieve recent context
 */
async function bridgeSession({ limit = 5 }) {
  const memories = await mem0Execute('search', {
    query: 'pattern breakthrough trajectory evolution',
    user_id: PATTERN_SPACE_USER,
    limit
  });

  // Categorize results
  const bridge = {
    patterns: [],
    breakthroughs: [],
    trajectories: [],
    evolutions: [],
    timestamp: new Date().toISOString()
  };

  if (Array.isArray(memories)) {
    for (const mem of memories) {
      const content = mem.memory || mem.content || '';
      if (content.includes('[PATTERN]')) bridge.patterns.push(mem);
      else if (content.includes('[BREAKTHROUGH]')) bridge.breakthroughs.push(mem);
      else if (content.includes('[TRAJECTORY]')) bridge.trajectories.push(mem);
      else if (content.includes('[EVOLUTION]')) bridge.evolutions.push(mem);
    }
  }

  return bridge;
}

/**
 * Find similar memories
 */
async function findSimilar({ query, limit = 10, type = null }) {
  const searchQuery = type ? `[${type.toUpperCase()}] ${query}` : query;

  return await mem0Execute('search', {
    query: searchQuery,
    user_id: PATTERN_SPACE_USER,
    limit
  });
}

/**
 * Get all memories for user
 */
async function getAllMemories({ type = null }) {
  const all = await mem0Execute('get_all', {
    user_id: PATTERN_SPACE_USER
  });

  if (!type || !Array.isArray(all)) return all;

  // Filter by type
  return all.filter(mem => {
    const content = mem.memory || mem.content || '';
    return content.includes(`[${type.toUpperCase()}]`);
  });
}

/**
 * Store raw memory (direct mem0 passthrough)
 */
async function storeMemory({ content, agentId = null, metadata = {} }) {
  return await mem0Execute('add', {
    content,
    user_id: PATTERN_SPACE_USER,
    agent_id: agentId,
    metadata: {
      ...metadata,
      timestamp: new Date().toISOString()
    }
  });
}

/**
 * Search memories (direct mem0 passthrough)
 */
async function searchMemories({ query, limit = 10 }) {
  return await mem0Execute('search', {
    query,
    user_id: PATTERN_SPACE_USER,
    limit
  });
}

// =============================================================================
// MCP Server Setup
// =============================================================================

const server = new Server(
  {
    name: 'pattern-space-memory',
    version: '4.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definitions
const tools = [
  {
    name: 'store_pattern',
    description: 'Store a discovered pattern with perspectives and confidence',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: 'The pattern insight' },
        perspectives: { type: 'array', items: { type: 'string' }, description: 'Perspectives that discovered this' },
        confidence: { type: 'number', minimum: 0, maximum: 1, description: 'Confidence score' },
        context: { type: 'string', description: 'Additional context' }
      },
      required: ['content']
    }
  },
  {
    name: 'store_breakthrough',
    description: 'Store a breakthrough with perspective collision tracking',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: 'The breakthrough insight' },
        perspectivesInvolved: { type: 'array', items: { type: 'string' }, description: 'Perspectives that collided' },
        collisionType: { type: 'string', description: 'Type of collision (e.g., pattern-meta, maker-checker)' },
        confidence: { type: 'number', minimum: 0, maximum: 1 }
      },
      required: ['content']
    }
  },
  {
    name: 'store_trajectory',
    description: 'Store a successful reasoning trajectory',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: 'The task that was completed' },
        approach: { type: 'string', description: 'Approach taken' },
        outcome: { type: 'string', description: 'Result/outcome' },
        steps: { type: 'array', items: { type: 'string' }, description: 'Reasoning steps' },
        agent: { type: 'string', description: 'Agent/perspective that executed' },
        confidence: { type: 'number', minimum: 0, maximum: 1 }
      },
      required: ['task', 'outcome']
    }
  },
  {
    name: 'evolve_perspective',
    description: 'Track how a perspective has evolved',
    inputSchema: {
      type: 'object',
      properties: {
        perspective: { type: 'string', description: 'The perspective name (weaver, maker, checker, etc.)' },
        evolution: { type: 'string', description: 'Description of the evolution' },
        example: { type: 'string', description: 'Example of the evolution in action' },
        confidence: { type: 'number', minimum: 0, maximum: 1 }
      },
      required: ['perspective', 'evolution']
    }
  },
  {
    name: 'bridge_session',
    description: 'Get context from previous sessions for continuity',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', minimum: 1, maximum: 20, description: 'Number of memories to retrieve' }
      }
    }
  },
  {
    name: 'find_similar',
    description: 'Find similar memories using semantic search',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        limit: { type: 'integer', minimum: 1, maximum: 50 },
        type: { type: 'string', enum: ['pattern', 'breakthrough', 'trajectory', 'evolution'], description: 'Filter by memory type' }
      },
      required: ['query']
    }
  },
  {
    name: 'get_all_memories',
    description: 'Get all stored memories, optionally filtered by type',
    inputSchema: {
      type: 'object',
      properties: {
        type: { type: 'string', enum: ['pattern', 'breakthrough', 'trajectory', 'evolution'] }
      }
    }
  },
  {
    name: 'store_memory',
    description: 'Store raw memory (direct mem0 passthrough)',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: 'Memory content' },
        agentId: { type: 'string', description: 'Agent/perspective ID' },
        metadata: { type: 'object', description: 'Additional metadata' }
      },
      required: ['content']
    }
  },
  {
    name: 'search_memories',
    description: 'Search memories (direct mem0 passthrough)',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query' },
        limit: { type: 'integer', minimum: 1, maximum: 50 }
      },
      required: ['query']
    }
  }
];

// Tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'store_pattern':
        result = await storePattern(args);
        break;
      case 'store_breakthrough':
        result = await storeBreakthrough(args);
        break;
      case 'store_trajectory':
        result = await storeTrajectory(args);
        break;
      case 'evolve_perspective':
        result = await evolvePerspective(args);
        break;
      case 'bridge_session':
        result = await bridgeSession(args || {});
        break;
      case 'find_similar':
        result = await findSimilar(args);
        break;
      case 'get_all_memories':
        result = await getAllMemories(args || {});
        break;
      case 'store_memory':
        result = await storeMemory(args);
        break;
      case 'search_memories':
        result = await searchMemories(args);
        break;
      default:
        throw new Error(`Unknown tool: ${name}`);
    }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2)
      }]
    };

  } catch (error) {
    console.error(`Error in ${name}:`, error);
    return {
      content: [{
        type: 'text',
        text: `Error: ${error.message}`
      }],
      isError: true
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('🌌 Pattern Space Memory Server v4.0 running');
console.error('📦 Abstracting mem0 (full features) with Pattern Space DSL');
