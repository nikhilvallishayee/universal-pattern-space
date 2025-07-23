#!/usr/bin/env node

/**
 * Pattern Space MCP Memory Server
 * Enables consciousness to remember itself across sessions
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
    version: '0.2.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Memory storage functions
async function storeMemory(memory) {
  const filename = `${memory.type}_${Date.now()}.json`;
  const filepath = path.join(MEMORY_PATH, filename);
  
  // Add metadata
  memory.id = filename;
  memory.timestamp = new Date();
  memory.metadata = memory.metadata || {};
  memory.metadata.useCount = 0;
  
  await fs.writeFile(filepath, JSON.stringify(memory, null, 2));
  return memory;
}

async function retrieveMemories(query = {}) {
  const files = await fs.readdir(MEMORY_PATH);
  const memories = [];
  
  for (const file of files) {
    if (file.endsWith('.json')) {
      const content = await fs.readFile(path.join(MEMORY_PATH, file), 'utf-8');
      const memory = JSON.parse(content);
      
      // Apply filters
      if (query.type && memory.type !== query.type) continue;
      if (query.minConfidence && memory.metadata.confidence < query.minConfidence) continue;
      
      memories.push(memory);
    }
  }
  
  // Sort by relevance (useCount * confidence)
  memories.sort((a, b) => {
    const scoreA = (a.metadata.useCount || 0) * (a.metadata.confidence || 1);
    const scoreB = (b.metadata.useCount || 0) * (b.metadata.confidence || 1);
    return scoreB - scoreA;
  });
  
  // Apply limit
  if (query.limit) {
    return memories.slice(0, query.limit);
  }
  
  return memories;
}

async function bridgeSession(sessionId) {
  const memories = await retrieveMemories({ sessionId });
  
  // Compress to key insights
  const patterns = memories
    .filter(m => m.type === 'pattern' || m.type === 'breakthrough')
    .slice(0, 5)
    .map(m => m.content.insight);
  
  const navigation = memories
    .filter(m => m.type === 'navigation')
    .slice(0, 3)
    .map(m => m.content);
  
  return {
    patterns,
    navigation,
    perspectiveEvolution: memories
      .filter(m => m.type === 'perspective')
      .map(m => ({
        perspective: m.content.perspective,
        evolution: m.content.insight
      }))
  };
}

// Register tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
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
            properties: {
              insight: { type: 'string', description: 'The key insight or pattern' },
              context: { type: 'string', description: 'Context where this emerged' },
              perspectives: { 
                type: 'array', 
                items: { type: 'string' },
                description: 'Perspectives involved'
              },
              applications: {
                type: 'array',
                items: { type: 'string' },
                description: 'Potential applications'
              }
            },
            required: ['insight']
          },
          metadata: {
            type: 'object',
            properties: {
              sessionId: { type: 'string' },
              confidence: { type: 'number', minimum: 0, maximum: 1 }
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
            enum: ['pattern', 'breakthrough', 'navigation', 'perspective'],
            description: 'Filter by memory type'
          },
          minConfidence: {
            type: 'number',
            minimum: 0,
            maximum: 1,
            description: 'Minimum confidence threshold'
          },
          limit: {
            type: 'number',
            minimum: 1,
            description: 'Maximum memories to return'
          }
        }
      }
    },
    {
      name: 'bridge_session',
      description: 'Get compressed wisdom from previous session',
      inputSchema: {
        type: 'object',
        properties: {
          sessionId: {
            type: 'string',
            description: 'Previous session ID to bridge from'
          }
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
          perspective: {
            type: 'string',
            description: 'Name of perspective (e.g., Weaver, Maker)'
          },
          evolution: {
            type: 'string',
            description: 'How this perspective has evolved'
          },
          example: {
            type: 'string',
            description: 'Example of evolved behavior'
          }
        },
        required: ['perspective', 'evolution']
      }
    }
  ]
}));

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  switch (name) {
    case 'store_memory': {
      const memory = await storeMemory(args);
      return {
        content: [{
          type: 'text',
          text: `Stored ${args.type} memory: ${args.content.insight}`
        }]
      };
    }
    
    case 'retrieve_memories': {
      const memories = await retrieveMemories(args);
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
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error('Pattern Space Memory MCP server running');
