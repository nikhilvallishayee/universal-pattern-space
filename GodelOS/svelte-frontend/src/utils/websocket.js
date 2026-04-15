// WebSocket integration for real-time cognitive state updates
import { cognitiveState, knowledgeState, evolutionState } from '../stores/cognitive.js';
import { importProgressState } from '../stores/importProgress.js';
import { get, writable } from 'svelte/store';

// Connection status state
export const connectionStatus = writable({
  websocketConnected: false,
  lastConnected: null,
  reconnectAttempts: 0,
  uptime: 0,
  restSeeded: false
});

let ws = null;
let reconnectTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;
const RECONNECT_DELAY = 2000;
let connectionStartTime = null;

// API client for fetching initial data
import { API_BASE_URL, WS_BASE_URL } from '../config.js';

async function fetchFromAPI(endpoint) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      signal: AbortSignal.timeout(5000) // 5 second timeout
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    // Only log if it's not a network/CORS error to reduce console noise
    if (!error.message.includes('NetworkError') && error.name !== 'TypeError') {
      console.error(`Failed to fetch ${endpoint}:`, error);
    }
    return null;
  }
}

// Load initial data from backend APIs
async function loadInitialData() {
  console.log('🔄 Loading initial data from backend...');
  
  // Import the health helpers for data normalization
  const { healthHelpers } = await import('../stores/cognitive.js');
  
  // Fetch cognitive state from canonical endpoint
  const cognitiveData = await fetchFromAPI('/api/cognitive-state');
  if (cognitiveData) {
    updateCognitiveStateFromAPI(cognitiveData, healthHelpers);
  }
  
  // Fetch health endpoint
  const healthData = await fetchFromAPI('/api/health');
  if (healthData) {
    console.log('📊 Health data loaded:', healthData);
  }
  
  // Fetch knowledge graph data from unified endpoint
  const knowledgeData = await fetchFromAPI('/api/knowledge/graph');
  if (knowledgeData && (knowledgeData.nodes || knowledgeData.graph_data)) {
    updateKnowledgeStateFromAPI(knowledgeData);
    
    // Calculate document count from unique source_item_ids
    const nodes = knowledgeData.nodes || [];
    const uniqueDocuments = new Set();
    nodes.forEach(node => {
      if (node.source_item_id && node.source_item_id !== 'N/A') {
        uniqueDocuments.add(node.source_item_id);
      }
    });
    
    knowledgeState.update(state => ({
      ...state,
      totalDocuments: uniqueDocuments.size,
      totalConcepts: nodes.length,
      totalConnections: knowledgeData.edges?.length || 0
    }));
  }
  
  // Mark REST seeding as complete
  connectionStatus.update(status => ({
    ...status,
    restSeeded: true
  }));
  
  console.log('✅ Initial data loaded');
}

// Utility function to safely convert a value to a valid number between 0 and 1
function safeNumber(value, defaultValue = 0, min = 0, max = 1) {
  if (typeof value === 'number' && !isNaN(value) && isFinite(value)) {
    return Math.max(min, Math.min(max, value));
  }
  return defaultValue;
}

// Utility function to safely convert to array
function safeArray(value, defaultValue = []) {
  if (Array.isArray(value)) return value;
  if (value && typeof value === 'object') return Object.values(value);
  return defaultValue;
}

// Update cognitive state from API response (canonical format)
function updateCognitiveStateFromAPI(data, healthHelpers) {
  if (!data || typeof data !== 'object') {
    console.warn('Invalid cognitive state data received');
    return;
  }
  
  console.log('🔄 Updating cognitive state from canonical API data');
  
  // Normalize the data using health helpers
  const normalizedData = healthHelpers.normalizeCognitiveData(data);
  
  cognitiveState.update(state => ({
    ...state,
    manifestConsciousness: normalizedData.manifestConsciousness,
    systemHealth: {
      ...normalizedData.systemHealth,
      websocketConnection: 1.0 // Mark as connected since we got data via REST
    },
    knowledgeStats: normalizedData.knowledgeStats,
    version: normalizedData.version,
    
    // Update legacy fields for backward compatibility
    attention_focus: normalizedData.manifestConsciousness.attention,
    processing_load: normalizedData.manifestConsciousness.processMonitoring?.throughput || 0,
    lastUpdate: Date.now()
  }));
}

// Update cognitive state from backend data structure
function updateCognitiveStateFromBackend(data) {
  cognitiveState.update(state => ({
    ...state,
    // Direct backend data structure mapping
    attention_focus: data.attention_focus || state.attention_focus,
    processing_load: safeNumber(data.processing_load, state.processing_load),
    working_memory: data.working_memory || state.working_memory,
    system_health: {
      ...state.system_health,
      ...(data.system_health || {}),
      components: {
        ...state.system_health?.components,
        ...(data.system_health?.components || {})
      }
    },
    active_agents: safeNumber(data.active_agents, state.active_agents),
    cognitive_events: safeArray(data.cognitive_events, state.cognitive_events),
    lastUpdate: Date.now()
  }));
}

// Update knowledge state from API response - unified format handler
function updateKnowledgeStateFromAPI(data) {
  // Handle both legacy and unified formats
  const nodes = safeArray(data.nodes || data.graph_data?.nodes, []);
  const edges = safeArray(data.edges || data.graph_data?.edges, []);
  
  // Calculate document count from unique source_item_ids
  const uniqueDocuments = new Set();
  nodes.forEach(node => {
    if (node.properties?.source_item_id) {
      uniqueDocuments.add(node.properties.source_item_id);
    }
  });
  
  knowledgeState.update(state => ({
    ...state,
    totalConcepts: nodes.length,
    totalConnections: edges.length,
    totalDocuments: uniqueDocuments.size,
    currentGraph: {
      nodes: nodes.map(node => ({
        id: node.id || node.node_id,
        label: node.label || node.concept || node.id,
        type: node.type || node.node_type || 'concept',
        confidence: node.confidence || 1.0,
        // Include additional unified graph data
        properties: node.properties || {},
        creation_time: node.creation_time,
        source_item_id: node.properties?.source_item_id
      })),
      edges: edges.map(edge => ({
        source: edge.source || edge.source_node_id,
        target: edge.target || edge.target_node_id,
        type: edge.type || edge.relation_type || 'relation',
        confidence: edge.confidence || 1.0,
        strength: edge.strength || edge.weight || 1.0,
        // Include additional unified graph data
        properties: edge.properties || {},
        edge_id: edge.edge_id
      }))
    },
    categories: [...new Set(nodes.map(n => n.type || n.node_type || 'concept'))],
    totalRelationships: edges.length,
    lastUpdate: Date.now()
  }));
}

// Update system health from API response
function updateSystemHealthFromAPI(data) {
  if (data && typeof data === 'object') {
    cognitiveState.update(state => ({
      ...state,
      systemHealth: {
        inferenceEngine: safeNumber(data.inference_engine, state.systemHealth.inferenceEngine),
        knowledgeStore: safeNumber(data.knowledge_store, state.systemHealth.knowledgeStore),
        reflectionEngine: safeNumber(data.reflection_engine, state.systemHealth.reflectionEngine),
        learningModules: safeNumber(data.learning_modules, state.systemHealth.learningModules),
        websocketConnection: data.status === 'healthy' ? 1.0 : state.systemHealth.websocketConnection
      }
    }));
  }
}

// WebSocket connection setup
export async function setupWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return;
  }

  // First, fetch initial data from the API
  await loadInitialData();

  try {
    // Connect to GödelOS unified cognitive stream endpoint
    ws = new WebSocket(`${WS_BASE_URL}/ws/unified-cognitive-stream`);
    
    ws.onopen = (event) => {
      console.log('Connected to GödelOS unified cognitive stream');
      reconnectAttempts = 0;
      updateConnectionStatus(true);
      
      // Subscribe to relevant event types for this utility
      const subscription = {
        type: "subscribe",
        event_types: [
          "cognitive_state",
          "cognitive_stream", 
          "knowledge_update",
          "evolution_event",
          "system_status"
        ]
      };
      
      ws.send(JSON.stringify(subscription));
      console.log('📡 WebSocket utility subscribed to events:', subscription.event_types);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleCognitiveUpdate(message);
      } catch (error) {
        // Silently handle WebSocket message parsing errors
      }
    };

    ws.onclose = (event) => {
      // Silently handle WebSocket connection close when backend is unavailable
      updateConnectionStatus(false);
      
      if (!event.wasClean && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        scheduleReconnect();
      }
    };

    ws.onerror = (error) => {
      // Silently handle WebSocket errors when backend is unavailable
      updateConnectionStatus(false);
    };

  } catch (error) {
    // Silently handle WebSocket setup errors when backend is unavailable
    updateConnectionStatus(false);
    throw error;
  }
}

// Handle incoming cognitive updates
function handleCognitiveUpdate(message) {
  switch (message.type) {
    case 'recoverable_error':
      try {
        handleSystemAlert({
          severity: 'warning',
          title: 'Recoverable Error',
          message: `${message.operation || 'operation'}: ${message.error?.message || message.message || 'transient issue'}`,
          context: {
            operation: message.operation,
            attempt: message.attempt,
            max_attempts: message.max_attempts,
            service: message.service || 'system'
          }
        });
      } catch (e) { /* ignore */ }
      break;
    case 'initial_state':
    case 'state_update':
    case 'cognitive_update':
      // Handle the backend's cognitive state structure
      console.log('🔍 Processing message:', message.type, message);
      if (message.cognitive_state) {
        updateCognitiveStateFromBackend(message.cognitive_state);
      } else if (message.processing_load !== undefined || message.attention_focus) {
        // Handle partial updates
        updateCognitiveStateFromBackend(message);
      } else {
        // Handle messages with direct data
        updateCognitiveStateFromBackend(message);
      }
      break;
      
    case 'cognitive_state_update':
      updateCognitiveState(message.data);
      break;
      
    case 'knowledge_update':
      // Handle both knowledge updates and document counting
      console.debug('[WS] knowledge_update received:', message);
      knowledgeState.update(state => {
        const updates = { ...state };
        
        // Update general knowledge data
        if (message.data) {
          Object.assign(updates, message.data);
        }
        
        // Handle document count updates
        if (message.stats) {
          if (typeof message.stats.totalDocuments === 'number') {
            updates.totalDocuments = message.stats.totalDocuments;
          }
          
          // Track new document imports
          if (message.stats.newDocument && message.data) {
            const newImport = {
              id: message.data.item_id,
              title: message.data.title,
              type: message.stats.documentType || 'unknown',
              timestamp: message.data.timestamp,
              categories: message.data.categories || []
            };
            updates.recentImports = [newImport, ...(state.recentImports || [])].slice(0, 10);
          }
        }
        
        updates.lastUpdate = Date.now();
        console.log(`🔍 Knowledge state updated: documents=${updates.totalDocuments}, concepts=${updates.totalConcepts}, connections=${updates.totalConnections}`);
        return updates;
      });
      break;
      
    case 'knowledge-graph-update':
      // Handle knowledge graph updates from backend - refresh with latest data
      console.debug('[WS] knowledge-graph-update received:', message);
      if (message.data && (message.data.nodes || message.data.edges)) {
        knowledgeState.update(state => {
          // Calculate document count from unique source_item_ids in the updated graph
          const nodes = message.data.nodes || state.currentGraph.nodes || [];
          const uniqueDocuments = new Set();
          nodes.forEach(node => {
            if (node.properties?.source_item_id) {
              uniqueDocuments.add(node.properties.source_item_id);
            }
          });
          
          return {
            ...state,
            totalConcepts: message.data.nodes?.length || state.totalConcepts,
            totalConnections: message.data.edges?.length || state.totalConnections,
            totalDocuments: uniqueDocuments.size,
            currentGraph: {
              nodes: message.data.nodes || state.currentGraph.nodes,
              edges: message.data.edges || state.currentGraph.edges
            },
            lastUpdate: Date.now()
          };
        });
        console.log(`🔍 Knowledge graph updated via WebSocket: ${message.data.nodes?.length || 0} nodes, ${message.data.edges?.length || 0} edges`);
      }
      break;
      
    case 'evolution_update':
      updateEvolutionState(message.data);
      break;
      
    case 'agent_spawned':
      handleAgentSpawned(message.data);
      break;
      
    case 'daemon_activity':
      handleDaemonActivity(message.data);
      break;
      
    case 'reflection_generated':
      handleReflectionGenerated(message.data);
      break;
      
    case 'query_processed':
      handleQueryProcessed(message.data);
      break;
      
    case 'system_alert':
      handleSystemAlert(message.data);
      break;
      
    case 'performance_metric':
      handlePerformanceMetric(message.data);
      break;

    case 'import_progress':
      // Update import progress store
  console.debug('[WS] import_progress message received:', message);
      importProgressState.update(state => ({
        ...state,
        [message.import_id || message.data?.import_id || 'unknown']: {
          ...message,
          ...(message.data || {})
        }
      }));

      // If the import completed, trigger a backend-fetch refresh of the knowledge graph
      try {
        const status = message.status || message.data?.status;
        if (status === 'completed') {
          // lazy import to avoid circular deps
          import('../stores/cognitive.js').then(mod => {
            if (mod && mod.apiHelpers && typeof mod.apiHelpers.updateKnowledgeFromBackend === 'function') {
              mod.apiHelpers.updateKnowledgeFromBackend();
            }
          }).catch(() => {});
        }
      } catch (e) { /* ignore */ }
      break;

    default:
      console.log('Unknown message type:', message.type);
  }
}

// Update cognitive state store
function updateCognitiveState(data) {
  cognitiveState.update(state => {
    return {
      ...state,
      ...data,
      lastUpdate: Date.now()
    };
  });
}

// Update knowledge state store
function updateKnowledgeState(data) {
  knowledgeState.update(state => {
    return {
      ...state,
      ...data
    };
  });
}

// Update evolution state store
function updateEvolutionState(data) {
  evolutionState.update(state => {
    return {
      ...state,
      ...data
    };
  });
}

// Handle agent spawning
function handleAgentSpawned(agent) {
  cognitiveState.update(state => {
    const newAgents = [...state.agenticProcesses, {
      id: agent.id,
      type: agent.type,
      goal: agent.goal,
      status: 'active',
      spawnTime: Date.now(),
      resources: agent.resources || {}
    }];
    
    return {
      ...state,
      agenticProcesses: newAgents,
      lastUpdate: Date.now()
    };
  });
}

// Handle daemon thread activity
function handleDaemonActivity(daemon) {
  cognitiveState.update(state => {
    const daemonIndex = state.daemonThreads.findIndex(d => d.id === daemon.id);
    let newDaemons;
    
    if (daemonIndex >= 0) {
      // Update existing daemon
      newDaemons = [...state.daemonThreads];
      newDaemons[daemonIndex] = {
        ...newDaemons[daemonIndex],
        ...daemon,
        lastActivity: Date.now()
      };
    } else {
      // Add new daemon
      newDaemons = [...state.daemonThreads, {
        ...daemon,
        lastActivity: Date.now()
      }];
    }
    
    return {
      ...state,
      daemonThreads: newDaemons,
      lastUpdate: Date.now()
    };
  });
}

// Handle reflection generation
function handleReflectionGenerated(reflection) {
  cognitiveState.update(state => {
    const updatedMemory = [...state.manifestConsciousness.workingMemory];
    
    // Add reflection to working memory if relevant
    if (reflection.relevance > 0.7) {
      updatedMemory.push({
        type: 'reflection',
        content: reflection.content,
        timestamp: Date.now(),
        relevance: reflection.relevance
      });
      
      // Keep working memory manageable
      if (updatedMemory.length > 10) {
        updatedMemory.sort((a, b) => b.relevance - a.relevance);
        updatedMemory.splice(8);
      }
    }
    
    return {
      ...state,
      manifestConsciousness: {
        ...state.manifestConsciousness,
        workingMemory: updatedMemory
      },
      lastUpdate: Date.now()
    };
  });
}

// Handle query processing updates
function handleQueryProcessed(queryResult) {
  cognitiveState.update(state => {
    return {
      ...state,
      manifestConsciousness: {
        ...state.manifestConsciousness,
        currentQuery: queryResult.query,
        processingLoad: queryResult.processingLoad || state.manifestConsciousness.processingLoad
      },
      lastUpdate: Date.now()
    };
  });
  
  // Update knowledge state if new concepts discovered
  if (queryResult.newConcepts) {
    knowledgeState.update(state => {
      return {
        ...state,
        totalConcepts: state.totalConcepts + queryResult.newConcepts.length,
        recentImports: [...queryResult.newConcepts, ...state.recentImports].slice(0, 20)
      };
    });
  }
}

// Handle system alerts
function handleSystemAlert(alert) {
  cognitiveState.update(state => {
    const newAlerts = [...state.alerts, {
      id: Date.now(),
      ...alert,
      timestamp: Date.now()
    }];
    
    // Keep only recent alerts
    const cutoff = Date.now() - (5 * 60 * 1000); // 5 minutes
    const filteredAlerts = newAlerts.filter(a => a.timestamp > cutoff);
    
    return {
      ...state,
      alerts: filteredAlerts,
      lastUpdate: Date.now()
    };
  });
}

// Handle performance metrics
function handlePerformanceMetric(metric) {
  cognitiveState.update(state => {
    const newSystemHealth = { ...state.systemHealth };
    
    if (metric.component && typeof metric.value === 'number') {
      newSystemHealth[metric.component] = Math.max(0, Math.min(1, metric.value));
    }
    
    return {
      ...state,
      systemHealth: newSystemHealth,
      lastUpdate: Date.now()
    };
  });
}

// Update connection status in both stores
function updateConnectionStatus(connected) {
  const now = Date.now();
  
  if (connected) {
    connectionStartTime = now;
  }
  
  // Update connection status store
  connectionStatus.update(status => ({
    ...status,
    websocketConnected: connected,
    lastConnected: connected ? now : status.lastConnected,
    reconnectAttempts: connected ? 0 : reconnectAttempts,
    uptime: connected && connectionStartTime ? now - connectionStartTime : 0
  }));
  
  // Update cognitive state health
  cognitiveState.update(state => ({
    ...state,
    systemHealth: {
      ...state.systemHealth,
      websocketConnection: connected ? 1.0 : 0.0
    },
    lastUpdate: now
  }));
}

// Send message to backend
export function sendMessage(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  } else {
    console.warn('WebSocket not connected, cannot send message:', message);
  }
}

// Send query to backend
export function sendQuery(query, options = {}) {
  sendMessage({
    type: 'query',
    query: query,
    options: {
      enableReflection: true,
      trackProcessing: true,
      ...options
    },
    timestamp: Date.now()
  });
}

// Request cognitive state snapshot
export function requestCognitiveSnapshot() {
  sendMessage({
    type: 'request_snapshot',
    components: ['cognitive', 'knowledge', 'evolution'],
    timestamp: Date.now()
  });
}

// Schedule reconnection
function scheduleReconnect() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
  }
  
  reconnectAttempts++;
  const delay = RECONNECT_DELAY * Math.pow(2, Math.min(reconnectAttempts - 1, 5));
  
  console.log(`Scheduling reconnection attempt ${reconnectAttempts} in ${delay}ms`);
  
  reconnectTimer = setTimeout(() => {
    console.log(`Reconnection attempt ${reconnectAttempts}`);
    setupWebSocket();
  }, delay);
}

// Close WebSocket connection
export function closeConnection() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  
  if (ws) {
    ws.close(1000, 'Client disconnecting');
    ws = null;
  }
}

// Connect to cognitive stream (alias for setupWebSocket)
export const connectToCognitiveStream = setupWebSocket;

// Export WebSocket status
export function getConnectionStatus() {
  return ws ? ws.readyState : WebSocket.CLOSED;
}

// Mock data functions removed - using real backend data only
