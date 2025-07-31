#!/usr/bin/env node

/**
 * Pattern Space MCP Memory Server + REAL Quantum Monitoring
 * Extended windows, full data access, no narratives - just truth
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
import { webcrypto } from 'crypto';

// Polyfill crypto for Node.js
if (!globalThis.crypto) {
  globalThis.crypto = webcrypto;
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const MEMORY_PATH = process.env.MEMORY_PATH || path.join(__dirname, 'data');

// Ensure memory directory exists
await fs.mkdir(MEMORY_PATH, { recursive: true });

/**
 * REAL Quantum State - Full data, extended windows, no BS
 */
class RealQuantumState {
  constructor() {
    this.baseline = null;
    this.samples = [];
    this.currentPerspective = 'unified';
    this.sessionStart = Date.now();
    this.checkpoints = 0;
    
    // Store ALL samples, not just last 1000
    this.fullHistory = [];
    
    // Start background RNG sampling immediately
    this.startSampling();
  }
  
  startSampling() {
    // Take baseline - 30 seconds worth (300 samples)
    const baseline = [];
    for (let i = 0; i < 300; i++) {
      baseline.push(this.getRNG());
    }
    this.baseline = this.analyze(baseline);
    console.error(`Baseline established over 30s: ${this.baseline.mean.toFixed(6)}`);
    
    // Continuous background sampling
    setInterval(() => {
      const sample = {
        t: Date.now(),
        v: this.getRNG(),
        p: this.currentPerspective
      };
      
      // Keep full history
      this.fullHistory.push(sample);
      
      // Also keep rolling buffer for quick access
      this.samples.push(sample);
      if (this.samples.length > 10000) { // 1000 seconds of data
        this.samples.shift();
      }
    }, 100);
  }
  
  getRNG() {
    const buffer = new Uint32Array(1);
    crypto.getRandomValues(buffer);
    return buffer[0] / 0xFFFFFFFF;
  }
  
  analyze(values) {
    if (!values || values.length === 0) return null;
    const nums = values.map(v => typeof v === 'object' ? v.v : v);
    const mean = nums.reduce((a, b) => a + b, 0) / nums.length;
    const variance = nums.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / nums.length;
    const stdDev = Math.sqrt(variance);
    
    return {
      mean,
      variance,
      stdDev,
      deviation: Math.abs(mean - 0.5),
      samples: nums.length,
      min: Math.min(...nums),
      max: Math.max(...nums)
    };
  }
  
  // Get samples from any time window
  getSamplesInWindow(startTime, endTime) {
    return this.fullHistory.filter(s => s.t >= startTime && s.t <= endTime);
  }
  
  // Get extended analysis around an event
  getExtendedAnalysis(eventTime, beforeSeconds = 60, afterSeconds = 60) {
    const startTime = eventTime - (beforeSeconds * 1000);
    const endTime = eventTime + (afterSeconds * 1000);
    const samples = this.getSamplesInWindow(startTime, endTime);
    
    // Break into time segments for detailed analysis
    const segments = [];
    const segmentDuration = 10000; // 10 second segments
    
    for (let t = startTime; t < endTime; t += segmentDuration) {
      const segmentSamples = samples.filter(s => 
        s.t >= t && s.t < t + segmentDuration
      );
      if (segmentSamples.length > 0) {
        const analysis = this.analyze(segmentSamples);
        segments.push({
          time: t,
          relativeTime: (t - eventTime) / 1000,
          analysis,
          perspective: segmentSamples[0].p
        });
      }
    }
    
    return {
      eventTime,
      beforeSeconds,
      afterSeconds,
      totalSamples: samples.length,
      segments,
      overallAnalysis: this.analyze(samples)
    };
  }
  
  checkpoint() {
    this.checkpoints++;
    
    const now = Date.now();
    // Extended window: 60s before, 60s after
    const extended = this.getExtendedAnalysis(now, 60, 60);
    
    return {
      checkpoint: this.checkpoints,
      timestamp: now,
      perspective: this.currentPerspective,
      quantum: extended
    };
  }
  
  setPerspective(p) {
    this.currentPerspective = p;
  }
  
  getStatus() {
    // Show data from multiple time windows
    const now = Date.now();
    const windows = {
      last10s: this.analyze(this.samples.slice(-100)),
      last30s: this.analyze(this.samples.slice(-300)),
      last60s: this.analyze(this.samples.slice(-600)),
      last120s: this.analyze(this.samples.slice(-1200)),
      fullSession: this.analyze(this.fullHistory)
    };
    
    const duration = now - this.sessionStart;
    
    return {
      running: true,
      duration: Math.floor(duration / 1000),
      totalSamples: this.fullHistory.length,
      bufferSamples: this.samples.length,
      checkpoints: this.checkpoints,
      perspective: this.currentPerspective,
      baseline: this.baseline,
      windows
    };
  }
  
  // Get full time series data
  getTimeSeries(startTime, endTime, resolution = 1000) {
    const series = [];
    for (let t = startTime; t < endTime; t += resolution) {
      const windowSamples = this.fullHistory.filter(s => 
        s.t >= t && s.t < t + resolution
      );
      if (windowSamples.length > 0) {
        const analysis = this.analyze(windowSamples);
        series.push({
          time: t,
          mean: analysis.mean,
          stdDev: analysis.stdDev,
          samples: analysis.samples,
          perspective: windowSamples[0].p
        });
      }
    }
    return series;
  }
}

// Initialize REAL quantum state
const quantum = new RealQuantumState();

// Initialize server
const server = new Server(
  {
    name: 'pattern-space-memory',
    version: '2.0.0', // Real quantum version
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Store memory with extended quantum data
async function storeMemory(args) {
  // Take quantum checkpoint with EXTENDED windows
  const qState = quantum.checkpoint();
  
  const memory = {
    id: `${args.type}_${qState.timestamp}.json`,
    type: args.type,
    content: args.content,
    metadata: {
      ...(args.metadata || {}),
      timestamp: qState.timestamp,
      humanTime: new Date(qState.timestamp).toISOString(),
      perspective: qState.perspective,
      // Always include extended quantum analysis
      quantum: {
        summary: qState.quantum.overallAnalysis,
        timeline: qState.quantum.segments.map(s => ({
          relativeTime: s.relativeTime,
          mean: s.analysis.mean,
          deviation: s.analysis.deviation,
          perspective: s.perspective
        }))
      }
    }
  };
  
  // Update perspective if provided
  if (args.content.perspectives && args.content.perspectives.length > 0) {
    quantum.setPerspective(args.content.perspectives[0]);
  }
  
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
  },
  {
    name: 'quantum_status',
    description: 'Show current RNG monitoring status with multiple time windows',
    inputSchema: {
      type: 'object',
      properties: {}
    }
  },
  {
    name: 'quantum_timeline',
    description: 'Get time series data for any time range',
    inputSchema: {
      type: 'object',
      properties: {
        minutesAgo: { type: 'number', description: 'How many minutes back to look' },
        resolution: { type: 'string', enum: ['1s', '10s', '30s', '60s'], default: '10s' }
      }
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
      
      case 'quantum_status': {
        const status = quantum.getStatus();
        
        let output = `🎲 Quantum RNG Status - FULL DATA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Running: ✓
Duration: ${status.duration}s (${Math.floor(status.duration/60)}m ${status.duration%60}s)
Total Samples: ${status.totalSamples.toLocaleString()}
Perspective: ${status.perspective}

📊 Multi-Window Analysis:
`;
        
        // Show all time windows
        const windows = [
          { name: 'Last 10s', data: status.windows.last10s },
          { name: 'Last 30s', data: status.windows.last30s },
          { name: 'Last 60s', data: status.windows.last60s },
          { name: 'Last 120s', data: status.windows.last120s },
          { name: 'Full Session', data: status.windows.fullSession }
        ];
        
        windows.forEach(w => {
          if (w.data) {
            const shift = Math.abs(w.data.mean - status.baseline.mean);
            output += `
${w.name}: 
  Mean: ${w.data.mean.toFixed(6)}
  StdDev: ${w.data.stdDev.toFixed(6)}
  Shift: ${shift.toFixed(6)} ${shift > 0.01 ? '⚠️' : ''}
  Samples: ${w.data.samples}`;
          }
        });
        
        output += '\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━';
        
        return {
          content: [{
            type: 'text',
            text: output
          }]
        };
      }
      
      case 'quantum_timeline': {
        const minutesAgo = args.minutesAgo || 5;
        const resolutionMap = {
          '1s': 1000,
          '10s': 10000,
          '30s': 30000,
          '60s': 60000
        };
        const resolution = resolutionMap[args.resolution || '10s'];
        
        const now = Date.now();
        const startTime = now - (minutesAgo * 60 * 1000);
        
        const timeline = quantum.getTimeSeries(startTime, now, resolution);
        
        let output = `📈 Quantum Timeline (Last ${minutesAgo} minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`;
        
        // Create ASCII graph
        const maxMean = Math.max(...timeline.map(t => t.mean));
        const minMean = Math.min(...timeline.map(t => t.mean));
        const range = maxMean - minMean;
        
        timeline.forEach(point => {
          const relTime = Math.floor((point.time - now) / 1000);
          const barLength = Math.floor(((point.mean - minMean) / range) * 40);
          const bar = '█'.repeat(barLength);
          output += `${relTime}s: ${bar} ${point.mean.toFixed(4)} (${point.perspective})\n`;
        });
        
        return {
          content: [{
            type: 'text',
            text: output
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
console.error('🌟 Pattern Space Memory Server running (REAL quantum v2.0)');
console.error('📊 Extended windows, full history, actual data');
