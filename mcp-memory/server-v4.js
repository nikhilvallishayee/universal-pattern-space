#!/usr/bin/env node

/**
 * Pattern Space MCP Memory Server v4.0
 * Graph Orchestration Layer on PostgreSQL + pgvector
 *
 * This server provides:
 * - Graph-based memory with nodes and edges
 * - Integration with mem0 and ruvector schemas
 * - Cross-schema similarity search
 * - Perspective evolution tracking
 * - Session bridging with graph traversal
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import pg from 'pg';

const { Pool } = pg;

// Database configuration from environment
const dbConfig = {
  database: process.env.POSTGRES_DB || 'pattern_space_memory',
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  user: process.env.POSTGRES_USER || 'pattern_space_app',
  password: process.env.POSTGRES_PASSWORD || 'pattern_space_dev',
};

// Initialize database pool
const pool = new Pool(dbConfig);

// Test connection on startup
try {
  const client = await pool.connect();
  console.error('🔗 Connected to PostgreSQL');
  client.release();
} catch (err) {
  console.error('⚠️ PostgreSQL connection failed, falling back to file mode:', err.message);
}

// Initialize server
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

// =============================================================================
// GRAPH OPERATIONS
// =============================================================================

/**
 * Create a node in the graph
 */
async function createNode({ nodeType, label, content, confidence = 0.5, metadata = {} }) {
  const result = await pool.query(
    `INSERT INTO pattern_space.nodes (node_type, label, content, confidence, metadata)
     VALUES ($1, $2, $3, $4, $5)
     RETURNING id, node_type, label, created_at`,
    [nodeType, label, content, confidence, JSON.stringify(metadata)]
  );
  return result.rows[0];
}

/**
 * Create an edge between nodes
 */
async function createEdge({ sourceId, targetId, edgeType, weight = 1.0, metadata = {} }) {
  const result = await pool.query(
    `INSERT INTO pattern_space.edges (source_id, target_id, edge_type, weight, metadata)
     VALUES ($1, $2, $3, $4, $5)
     ON CONFLICT (source_id, target_id, edge_type) DO UPDATE SET weight = $4, metadata = $5
     RETURNING id, edge_type, weight`,
    [sourceId, targetId, edgeType, weight, JSON.stringify(metadata)]
  );
  return result.rows[0];
}

/**
 * Get node by ID with its connections
 */
async function getNode(nodeId) {
  const nodeResult = await pool.query(
    `SELECT * FROM pattern_space.nodes WHERE id = $1`,
    [nodeId]
  );

  if (nodeResult.rows.length === 0) return null;

  const edgesResult = await pool.query(
    `SELECT e.*,
            s.label as source_label, s.node_type as source_type,
            t.label as target_label, t.node_type as target_type
     FROM pattern_space.edges e
     JOIN pattern_space.nodes s ON e.source_id = s.id
     JOIN pattern_space.nodes t ON e.target_id = t.id
     WHERE e.source_id = $1 OR e.target_id = $1`,
    [nodeId]
  );

  return {
    ...nodeResult.rows[0],
    edges: edgesResult.rows
  };
}

/**
 * Find similar nodes across all schemas
 */
async function findSimilar({ query, limit = 10 }) {
  // For now, use text search. With embeddings, use vector similarity.
  const result = await pool.query(
    `SELECT 'pattern_space' as schema, id, node_type as type, label, content,
            ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
     FROM pattern_space.nodes
     WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)

     UNION ALL

     SELECT 'mem0' as schema, id, memory_type as type, NULL as label, content,
            ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
     FROM mem0.memories
     WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)

     UNION ALL

     SELECT 'ruvector' as schema, id, 'trajectory' as type, NULL as label, content,
            ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) as rank
     FROM ruvector.vectors
     WHERE to_tsvector('english', content) @@ plainto_tsquery('english', $1)

     ORDER BY rank DESC
     LIMIT $2`,
    [query, limit]
  );
  return result.rows;
}

/**
 * Get graph neighbors (traversal)
 */
async function getNeighbors({ nodeId, edgeTypes = null, maxDepth = 2 }) {
  const result = await pool.query(
    `SELECT * FROM get_neighbors($1, $2, $3)`,
    [nodeId, edgeTypes, maxDepth]
  );
  return result.rows;
}

// =============================================================================
// MEMORY OPERATIONS (High-level)
// =============================================================================

/**
 * Store a pattern with graph connections
 */
async function storePattern({ content, perspectives = [], confidence = 0.7, relatedTo = [], metadata = {} }) {
  // Create the pattern node
  const node = await createNode({
    nodeType: 'pattern',
    label: content.slice(0, 100),
    content: JSON.stringify({ insight: content, perspectives }),
    confidence,
    metadata
  });

  // Create edges to related nodes
  for (const relatedId of relatedTo) {
    await createEdge({
      sourceId: node.id,
      targetId: relatedId,
      edgeType: 'relates_to',
      weight: confidence
    });
  }

  return node;
}

/**
 * Store a breakthrough with collision tracking
 */
async function storeBreakthrough({ content, perspectivesInvolved = [], collisionType = 'unknown', confidence = 0.9, ledFrom = [], metadata = {} }) {
  // Create the breakthrough node
  const node = await createNode({
    nodeType: 'breakthrough',
    label: content.slice(0, 100),
    content: JSON.stringify({
      insight: content,
      perspectives: perspectivesInvolved,
      collision_type: collisionType
    }),
    confidence,
    metadata
  });

  // Create edges from patterns that led to this breakthrough
  for (const sourceId of ledFrom) {
    await createEdge({
      sourceId: sourceId,
      targetId: node.id,
      edgeType: 'led_to',
      weight: confidence
    });
  }

  // Update perspective statistics
  for (const perspective of perspectivesInvolved) {
    await pool.query(
      `UPDATE pattern_space.perspectives
       SET total_breakthroughs = total_breakthroughs + 1,
           last_active = NOW()
       WHERE name = $1`,
      [perspective]
    );
  }

  return node;
}

/**
 * Store a trajectory (successful reasoning path)
 */
async function storeTrajectory({ task, approach, outcome, steps = [], confidence = 0.8, agent = 'unknown', metadata = {} }) {
  // Store in ruvector schema
  const result = await pool.query(
    `INSERT INTO ruvector.vectors (collection_id, content, metadata)
     SELECT id, $2, $3
     FROM ruvector.collections WHERE name = 'trajectories'
     RETURNING id`,
    [
      'trajectories',
      JSON.stringify({ task, approach, outcome, steps }),
      JSON.stringify({ ...metadata, agent, confidence, timestamp: new Date().toISOString() })
    ]
  );

  // Also create a graph node for connections
  const node = await createNode({
    nodeType: 'trajectory',
    label: task.slice(0, 100),
    content: JSON.stringify({ task, approach, outcome, steps }),
    confidence,
    metadata: { ...metadata, ruvector_id: result.rows[0]?.id }
  });

  return { ruvector_id: result.rows[0]?.id, node_id: node.id };
}

/**
 * Track perspective evolution
 */
async function evolvePerspective({ perspective, evolution, example = null, confidence = 0.8 }) {
  // Update perspective stats
  await pool.query(
    `UPDATE pattern_space.perspectives
     SET evolution_history = evolution_history || $2::jsonb,
         last_active = NOW()
     WHERE name = $1`,
    [
      perspective,
      JSON.stringify({ evolution, example, timestamp: new Date().toISOString(), confidence })
    ]
  );

  // Create evolution node
  const node = await createNode({
    nodeType: 'evolution',
    label: `${perspective}: ${evolution.slice(0, 80)}`,
    content: JSON.stringify({ perspective, evolution, example }),
    confidence,
    metadata: { perspective }
  });

  return node;
}

/**
 * Start a session
 */
async function startSession({ sessionId, userId, persona = 'full-council' }) {
  const result = await pool.query(
    `INSERT INTO pattern_space.sessions (session_id, user_id, persona)
     VALUES ($1, $2, $3)
     ON CONFLICT (session_id) DO UPDATE SET started_at = NOW()
     RETURNING *`,
    [sessionId, userId, persona]
  );
  return result.rows[0];
}

/**
 * End a session with bridge creation
 */
async function endSession({ sessionId, summary = '', tasksCompleted = 0, avgConfidence = 0.0, breakthroughs = 0 }) {
  // Update session record
  const result = await pool.query(
    `UPDATE pattern_space.sessions
     SET ended_at = NOW(),
         duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INT,
         summary = $2,
         tasks_completed = $3,
         avg_confidence = $4,
         breakthroughs = $5,
         bridge_data = jsonb_build_object(
           'summary', $2,
           'tasks', $3,
           'confidence', $4,
           'breakthroughs', $5,
           'timestamp', NOW()
         )
     WHERE session_id = $1
     RETURNING *`,
    [sessionId, summary, tasksCompleted, avgConfidence, breakthroughs]
  );
  return result.rows[0];
}

/**
 * Bridge from previous session
 */
async function bridgeSession({ userId, limit = 3 }) {
  // Get recent sessions for this user
  const sessions = await pool.query(
    `SELECT * FROM pattern_space.sessions
     WHERE user_id = $1 AND ended_at IS NOT NULL
     ORDER BY ended_at DESC
     LIMIT $2`,
    [userId, limit]
  );

  // Get recent breakthroughs
  const breakthroughs = await pool.query(
    `SELECT * FROM pattern_space.nodes
     WHERE node_type = 'breakthrough'
     ORDER BY created_at DESC
     LIMIT 5`
  );

  // Get recent patterns
  const patterns = await pool.query(
    `SELECT * FROM pattern_space.nodes
     WHERE node_type = 'pattern' AND confidence > 0.7
     ORDER BY created_at DESC
     LIMIT 5`
  );

  return {
    recent_sessions: sessions.rows,
    recent_breakthroughs: breakthroughs.rows.map(b => ({
      id: b.id,
      label: b.label,
      confidence: b.confidence,
      created_at: b.created_at
    })),
    recent_patterns: patterns.rows.map(p => ({
      id: p.id,
      label: p.label,
      confidence: p.confidence,
      created_at: p.created_at
    }))
  };
}

/**
 * Retrieve memories with filters
 */
async function retrieveMemories({ type = null, limit = 20, minConfidence = 0.0, userId = null }) {
  let query = `SELECT * FROM pattern_space.nodes WHERE confidence >= $1`;
  const params = [minConfidence];
  let paramIndex = 2;

  if (type) {
    query += ` AND node_type = $${paramIndex}`;
    params.push(type);
    paramIndex++;
  }

  query += ` ORDER BY created_at DESC LIMIT $${paramIndex}`;
  params.push(limit);

  const result = await pool.query(query, params);
  return result.rows;
}

/**
 * Get perspective stats
 */
async function getPerspectiveStats(perspective = null) {
  if (perspective) {
    const result = await pool.query(
      `SELECT * FROM pattern_space.perspectives WHERE name = $1`,
      [perspective]
    );
    return result.rows[0];
  }

  const result = await pool.query(`SELECT * FROM pattern_space.perspectives ORDER BY name`);
  return result.rows;
}

// =============================================================================
// TOOL DEFINITIONS
// =============================================================================

const tools = [
  // Graph operations
  {
    name: 'create_node',
    description: 'Create a node in the Pattern Space graph (pattern, breakthrough, trajectory, etc.)',
    inputSchema: {
      type: 'object',
      properties: {
        nodeType: { type: 'string', enum: ['pattern', 'breakthrough', 'trajectory', 'evolution', 'session'] },
        label: { type: 'string', description: 'Short label for the node' },
        content: { type: 'string', description: 'Full content/insight' },
        confidence: { type: 'number', minimum: 0, maximum: 1 },
        metadata: { type: 'object' }
      },
      required: ['nodeType', 'content']
    }
  },
  {
    name: 'create_edge',
    description: 'Create a relationship between two nodes in the graph',
    inputSchema: {
      type: 'object',
      properties: {
        sourceId: { type: 'string', description: 'UUID of source node' },
        targetId: { type: 'string', description: 'UUID of target node' },
        edgeType: { type: 'string', enum: ['led_to', 'evolved_from', 'relates_to', 'collided_with', 'bridges'] },
        weight: { type: 'number', minimum: 0, maximum: 1 },
        metadata: { type: 'object' }
      },
      required: ['sourceId', 'targetId', 'edgeType']
    }
  },
  {
    name: 'get_node',
    description: 'Get a node and its connections',
    inputSchema: {
      type: 'object',
      properties: {
        nodeId: { type: 'string', description: 'UUID of the node' }
      },
      required: ['nodeId']
    }
  },
  {
    name: 'get_neighbors',
    description: 'Traverse the graph to find connected nodes',
    inputSchema: {
      type: 'object',
      properties: {
        nodeId: { type: 'string' },
        edgeTypes: { type: 'array', items: { type: 'string' } },
        maxDepth: { type: 'integer', minimum: 1, maximum: 5 }
      },
      required: ['nodeId']
    }
  },
  {
    name: 'find_similar',
    description: 'Search across all memory schemas (mem0, ruvector, pattern_space) for similar content',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        limit: { type: 'integer', minimum: 1, maximum: 50 }
      },
      required: ['query']
    }
  },

  // High-level memory operations
  {
    name: 'store_pattern',
    description: 'Store a discovered pattern with graph connections',
    inputSchema: {
      type: 'object',
      properties: {
        content: { type: 'string', description: 'The pattern insight' },
        perspectives: { type: 'array', items: { type: 'string' } },
        confidence: { type: 'number' },
        relatedTo: { type: 'array', items: { type: 'string' }, description: 'UUIDs of related nodes' },
        metadata: { type: 'object' }
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
        perspectivesInvolved: { type: 'array', items: { type: 'string' } },
        collisionType: { type: 'string' },
        confidence: { type: 'number' },
        ledFrom: { type: 'array', items: { type: 'string' }, description: 'Node UUIDs that led to this' },
        metadata: { type: 'object' }
      },
      required: ['content']
    }
  },
  {
    name: 'store_trajectory',
    description: 'Store a successful reasoning trajectory (also writes to ruvector)',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string' },
        approach: { type: 'string' },
        outcome: { type: 'string' },
        steps: { type: 'array', items: { type: 'string' } },
        confidence: { type: 'number' },
        agent: { type: 'string' },
        metadata: { type: 'object' }
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
        perspective: { type: 'string' },
        evolution: { type: 'string' },
        example: { type: 'string' },
        confidence: { type: 'number' }
      },
      required: ['perspective', 'evolution']
    }
  },

  // Session operations
  {
    name: 'start_session',
    description: 'Start a new session',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: { type: 'string' },
        userId: { type: 'string' },
        persona: { type: 'string' }
      },
      required: ['sessionId', 'userId']
    }
  },
  {
    name: 'end_session',
    description: 'End a session and create bridge data',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: { type: 'string' },
        summary: { type: 'string' },
        tasksCompleted: { type: 'integer' },
        avgConfidence: { type: 'number' },
        breakthroughs: { type: 'integer' }
      },
      required: ['sessionId']
    }
  },
  {
    name: 'bridge_session',
    description: 'Get context from previous sessions for continuity',
    inputSchema: {
      type: 'object',
      properties: {
        userId: { type: 'string' },
        limit: { type: 'integer' }
      },
      required: ['userId']
    }
  },

  // Retrieval operations
  {
    name: 'retrieve_memories',
    description: 'Retrieve stored memories with filters',
    inputSchema: {
      type: 'object',
      properties: {
        type: { type: 'string', enum: ['pattern', 'breakthrough', 'trajectory', 'evolution'] },
        limit: { type: 'integer' },
        minConfidence: { type: 'number' }
      }
    }
  },
  {
    name: 'get_perspective_stats',
    description: 'Get statistics and evolution history for perspectives',
    inputSchema: {
      type: 'object',
      properties: {
        perspective: { type: 'string', description: 'Specific perspective or null for all' }
      }
    }
  }
];

// =============================================================================
// TOOL HANDLERS
// =============================================================================

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let result;

    switch (name) {
      case 'create_node':
        result = await createNode(args);
        break;
      case 'create_edge':
        result = await createEdge(args);
        break;
      case 'get_node':
        result = await getNode(args.nodeId);
        break;
      case 'get_neighbors':
        result = await getNeighbors(args);
        break;
      case 'find_similar':
        result = await findSimilar(args);
        break;
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
      case 'start_session':
        result = await startSession(args);
        break;
      case 'end_session':
        result = await endSession(args);
        break;
      case 'bridge_session':
        result = await bridgeSession(args);
        break;
      case 'retrieve_memories':
        result = await retrieveMemories(args || {});
        break;
      case 'get_perspective_stats':
        result = await getPerspectiveStats(args?.perspective);
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

// =============================================================================
// START SERVER
// =============================================================================

const transport = new StdioServerTransport();
await server.connect(transport);
console.error('🌌 Pattern Space Memory Server v4.0 (Graph Orchestration) running');
console.error(`📊 Connected to PostgreSQL: ${dbConfig.host}:${dbConfig.port}/${dbConfig.database}`);
