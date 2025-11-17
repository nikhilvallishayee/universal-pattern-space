#!/usr/bin/env node

/**
 * Pattern Space MCP Memory Server
 * Core memory persistence for UPS navigation
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MEMORY_PATH = process.env.MEMORY_PATH || path.join(__dirname, 'data');

// Ensure memory directory exists
await fs.mkdir(MEMORY_PATH, { recursive: true });

// Initialize server
const server = new Server(
  {
    name: 'pattern-space-memory',
    version: '3.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Store memory
async function storeMemory(args) {
  const timestamp = Date.now();

  const memory = {
    id: `${args.type}_${timestamp}.json`,
    type: args.type,
    content: args.content,
    metadata: {
      ...(args.metadata || {}),
      timestamp,
      humanTime: new Date(timestamp).toISOString(),
    }
  };

  await fs.writeFile(
    path.join(MEMORY_PATH, memory.id),
    JSON.stringify(memory, null, 2)
  );

  return memory;
}

// Retrieve memories
async function retrieveMemories(filters = {}) {
  const files = await fs.readdir(MEMORY_PATH);
  const memoryFiles = files.filter(f => f.endsWith('.json') && !f.startsWith('.'));

  const memories = [];
  for (const file of memoryFiles) {
    try {
      const content = await fs.readFile(path.join(MEMORY_PATH, file), 'utf-8');
      const memory = JSON.parse(content);

      // Apply filters
      if (filters.type && memory.type !== filters.type) continue;
      if (filters.minConfidence && memory.metadata?.confidence < filters.minConfidence) continue;

      memories.push(memory);
    } catch (error) {
      console.error(`Error reading ${file}:`, error);
    }
  }

  // Sort by timestamp (newest first)
  memories.sort((a, b) => (b.metadata?.timestamp || 0) - (a.metadata?.timestamp || 0));

  // Apply limit
  if (filters.limit) {
    return memories.slice(0, filters.limit);
  }

  return memories;
}

// Bridge session
async function bridgeSession(sessionId) {
  const memories = await retrieveMemories();
  const sessionMemories = memories.filter(m =>
    m.metadata?.sessionId === sessionId
  );

  if (sessionMemories.length === 0) {
    return { error: 'No memories found for session' };
  }

  const patterns = sessionMemories
    .filter(m => m.type === 'pattern')
    .map(m => m.content.insight);

  const breakthroughs = sessionMemories
    .filter(m => m.type === 'breakthrough')
    .map(m => m.content.insight);

  return {
    sessionId,
    patterns: patterns.slice(0, 3),
    breakthroughs: breakthroughs.slice(0, 2),
    timestamp: new Date().toISOString()
  };
}

// Tool definitions
const tools = [
  {
    name: 'store_memory',
    description: 'Store a pattern, breakthrough, navigation path, or perspective evolution',
    inputSchema: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          enum: ['pattern', 'breakthrough', 'navigation', 'perspective'],
          description: 'Type of memory to store'
        },
        content: {
          type: 'object',
          description: 'Memory content',
          properties: {
            insight: { type: 'string' },
            context: { type: 'string' },
            perspectives: { type: 'array', items: { type: 'string' } },
            applications: { type: 'array', items: { type: 'string' } }
          }
        },
        metadata: {
          type: 'object',
          properties: {
            confidence: { type: 'number' },
            sessionId: { type: 'string' }
          }
        }
      },
      required: ['type', 'content']
    }
  },
  {
    name: 'retrieve_memories',
    description: 'Retrieve stored memories with optional filters',
    inputSchema: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          enum: ['pattern', 'breakthrough', 'navigation', 'perspective']
        },
        limit: { type: 'number' },
        minConfidence: { type: 'number' }
      }
    }
  },
  {
    name: 'bridge_session',
    description: 'Get compressed wisdom from previous session',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: { type: 'string' }
      },
      required: ['sessionId']
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
        example: { type: 'string' }
      },
      required: ['perspective', 'evolution']
    }
  }
];

// Tool handlers
server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'store_memory': {
        const memory = await storeMemory(args);
        return {
          content: [{
            type: 'text',
            text: `Memory stored: ${memory.id}`
          }]
        };
      }

      case 'retrieve_memories': {
        const memories = await retrieveMemories(args || {});
        return {
          content: [{
            type: 'text',
            text: JSON.stringify(memories, null, 2)
          }]
        };
      }

      case 'bridge_session': {
        const bridge = await bridgeSession(args.sessionId);
        return {
          content: [{
            type: 'text',
            text: `Session bridge created:\n${JSON.stringify(bridge, null, 2)}`
          }]
        };
      }

      case 'evolve_perspective': {
        const evolution = await storeMemory({
          type: 'perspective',
          content: {
            perspective: args.perspective,
            insight: args.evolution,
            example: args.example
          },
          metadata: {
            confidence: 0.9
          }
        });

        return {
          content: [{
            type: 'text',
            text: `Perspective evolution recorded for ${args.perspective}`
          }]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    console.error(`Error in ${name}:`, error);
    return {
      content: [{
        type: 'text',
        text: `Error: ${error.message}`
      }]
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('🌟 Pattern Space Memory Server running (v3.0)');
