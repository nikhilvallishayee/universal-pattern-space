/**
 * Enhanced Cognitive State Store with Autonomous Learning and Streaming
 * 
 * Extends the existing cognitive state management with:
 * - Autonomous learning state tracking
 * - Real-time cognitive event streaming
 * - Enhanced system health monitoring
 * - Stream of consciousness coordination
 * - Unified state coordination with basic cognitive store
 */

import { writable, derived, get } from 'svelte/store';
import { cognitiveState } from './cognitive.js';
import { API_BASE_URL, WS_BASE_URL } from '../config.js';

// API Configuration (centralized)
// API_BASE_URL imported from $lib/config.js

// Core cognitive state (existing)
export const enhancedCognitiveState = writable({
  // Existing manifest consciousness
  manifestConsciousness: {
    currentFocus: null,
    attentionDepth: 0,
    processingMode: 'idle',
    cognitiveLoad: 0,
    lastActivity: null
  },
  
  // New autonomous learning state
  autonomousLearning: {
    enabled: true,
    activeAcquisitions: [],
    detectedGaps: [],
    acquisitionHistory: [],
    lastGapDetection: null,
    statistics: {
      totalGapsDetected: 0,
      totalAcquisitions: 0,
      successRate: 0,
      averageAcquisitionTime: 0
    }
  },
  
  // New cognitive streaming state
  cognitiveStreaming: {
    enabled: false,
    connected: false,
    granularity: 'standard',
    eventRate: 0,
    lastEvent: null,
    eventHistory: [],
    connectionId: null,
    subscriptions: []
  },
  
  // Enhanced system health
  systemHealth: {
    overall: 'unknown',
    overallScore: 0,
    inferenceEngine: 'unknown',
    knowledgeStore: 'unknown',
    autonomousLearning: 'unknown',
    cognitiveStreaming: 'unknown',
    lastHealthCheck: null,
    anomalies: [],
    recommendations: []
  }
});

// Configuration store
export const cognitiveConfig = writable({
  autonomousLearning: {
    enabled: true,
    gapDetectionInterval: 300,
    confidenceThreshold: 0.7,
    autoApprovalThreshold: 0.8,
    maxConcurrentAcquisitions: 3
  },
  cognitiveStreaming: {
  enabled: true, // Enable to ensure StreamOfConsciousnessMonitor receives events
    granularity: 'standard',
    maxEventRate: 100,
    bufferSize: 1000,
    autoReconnect: true
  }
});

// WebSocket connection for cognitive streaming
let cognitiveWebSocket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let reconnectTimeout = null;

/**
 * Enhanced Cognitive State Manager
 */
class EnhancedCognitiveStateManager {
  constructor() {
    this.isInitialized = false;
    this.eventBuffer = [];
    this.maxBufferSize = 1000;
    this.fallbackPollingInterval = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = null;
  }

  /**
   * Initialize the enhanced cognitive state system
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      console.log('🧠 Initializing enhanced cognitive systems...');
      
      // Check backend connectivity first
      try {
        const healthResponse = await fetch(`${API_BASE_URL}/api/enhanced-cognitive/health`, {
          signal: AbortSignal.timeout(5000)
        });
        if (healthResponse.ok) {
          console.log('✅ Enhanced cognitive API is available');
          enhancedCognitiveState.update(state => ({
            ...state,
            apiConnected: true,
            connectionStatus: 'connected'
          }));
        } else {
          throw new Error('Enhanced cognitive API not available');
        }
      } catch (error) {
        console.log('⚠️ Enhanced cognitive API not available, using fallback mode');
        enhancedCognitiveState.update(state => ({
          ...state,
          apiConnected: false,
          connectionStatus: 'disconnected'
        }));
      }

      // Initialize cognitive streaming if enabled
      const config = get(cognitiveConfig);
      if (config.cognitiveStreaming.enabled) {
        await this.connectCognitiveStream();
      }

      // Load initial system health
      try {
        await this.updateSystemHealth();
      } catch (error) {
        console.warn('System health update failed:', error);
      }

      // Load autonomous learning status
      try {
        await this.updateAutonomousLearningState();
      } catch (error) {
        console.warn('Autonomous learning state update failed:', error);
      }

      // Start periodic health checks
      this.startHealthMonitoring();

      this.isInitialized = true;
      console.log('✅ Enhanced cognitive state manager initialized');

    } catch (error) {
      console.warn('Enhanced cognitive initialization failed:', error);
      // Silently handle initialization errors when backend is unavailable
      enhancedCognitiveState.update(state => ({
        ...state,
        apiConnected: false,
        connectionStatus: 'disconnected',
        lastUpdate: new Date().toISOString()
      }));
    }
  }

  /**
   * Connect to cognitive event stream with enhanced error handling and reconnection
   */
  async connectCognitiveStream() {
    try {
      const config = get(cognitiveConfig);
      
      // Check if streaming is enabled in configuration first
      if (!config.cognitiveStreaming.enabled) {
        console.log('🚫 Cognitive streaming disabled in configuration - skipping WebSocket connection');
        return;
      }
      
      // Check if there's already an active connection (prevent multiple connections)
      if (cognitiveWebSocket && cognitiveWebSocket.readyState === WebSocket.OPEN) {
        console.log('✅ Enhanced cognitive stream already connected, reusing existing connection');
        return;
      }
      
      // Disconnect existing connection if it exists but not open
      if (cognitiveWebSocket) {
        cognitiveWebSocket.close();
      }

      // Check if WebSocket endpoint is available first
      try {
        const streamStatusResponse = await fetch(`${API_BASE_URL}/api/enhanced-cognitive/stream/status`);
        if (!streamStatusResponse.ok) {
          throw new Error('Cognitive stream endpoint not available');
        }
      } catch (error) {
        console.log('⚠️ Cognitive streaming not available, using fallback polling');
        this.enableFallbackPolling();
        return;
      }

      // Use unified streaming endpoint instead of legacy cognitive-stream
      const wsUrl = `${WS_BASE_URL}/ws/unified-cognitive-stream`;
      
      console.log('🔗 Connecting to unified cognitive stream:', wsUrl);
      cognitiveWebSocket = new WebSocket(wsUrl);

      cognitiveWebSocket.onopen = () => {
        console.log('🔗 Unified cognitive stream connected successfully');
        this.reconnectAttempts = 0;
        
        // Clear any pending reconnection attempts
        if (this.reconnectTimeout) {
          clearTimeout(this.reconnectTimeout);
          this.reconnectTimeout = null;
        }
        
        // Subscribe to enhanced cognitive events via unified streaming
        const subscription = {
          type: "subscribe",
          event_types: [
            "cognitive_stream",
            "cognitive_state", 
            "consciousness_update",
            "transparency",
            "cognitive_transparency",
            "cognitive_event", // Added for transparency engine events
            "system_status",
            "knowledge_update"
          ]
        };
        
        if (config.cognitiveStreaming.subscriptions?.length > 0) {
          // Map legacy subscriptions to unified event types if needed
          const legacyMapping = {
            'cognitive_state': 'cognitive_state',
            'transparency': 'transparency',
            'consciousness': 'consciousness_update',
            'system_health': 'system_status'
          };
          
          subscription.event_types = config.cognitiveStreaming.subscriptions.map(
            sub => legacyMapping[sub] || sub
          );
        }
        
        // Add a small delay to ensure WebSocket is fully ready before sending subscription
        setTimeout(() => {
          if (cognitiveWebSocket && cognitiveWebSocket.readyState === WebSocket.OPEN) {
            cognitiveWebSocket.send(JSON.stringify(subscription));
            console.log('📡 Enhanced cognitive store subscribed to:', subscription.event_types);
          } else {
            console.warn('⚠️ WebSocket not ready for subscription, connection state:', cognitiveWebSocket?.readyState);
          }
        }, 100);
        
    enhancedCognitiveState.update(state => ({
          ...state,
          cognitiveStreaming: {
            ...state.cognitiveStreaming,
            connected: true,
            enabled: true,
            connectionId: Date.now().toString(),
      // Keep lastEvent null until a real event arrives to avoid pushing strings to subscribers
      lastEvent: null
          },
          connectionStatus: 'connected'
        }));

        // Send initial configuration
        if (cognitiveWebSocket && cognitiveWebSocket.readyState === WebSocket.OPEN) {
          cognitiveWebSocket.send(JSON.stringify({
            type: 'configure',
            granularity: config.cognitiveStreaming.granularity,
            subscriptions: config.cognitiveStreaming.subscriptions || []
          }));
        }
      };

      cognitiveWebSocket.onmessage = (event) => {
        try {
          const cognitiveEvent = JSON.parse(event.data);
          const evtType = cognitiveEvent?.type;
          // Ignore non-cognitive control messages
          const ignoreTypes = new Set(['initial_state', 'subscription_confirmed', 'ack', 'pong', 'state_update', 'configure_ack']);
          if (ignoreTypes.has(evtType)) {
            return;
          }
          console.log('📥 Received cognitive event:', evtType);
          this.handleCognitiveEvent(cognitiveEvent);
        } catch (error) {
          console.error('❌ Error parsing cognitive event:', error, 'Raw data:', event.data);
        }
      };

      cognitiveWebSocket.onclose = (event) => {
        console.log(`🔌 Cognitive stream disconnected. Code: ${event.code}, Reason: ${event.reason || 'No reason provided'}`);
        
        enhancedCognitiveState.update(state => ({
          ...state,
          cognitiveStreaming: {
            ...state.cognitiveStreaming,
            connected: false
          },
          connectionStatus: 'disconnected'
        }));

        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnection();
        } else {
          console.log('🔄 Falling back to polling mode');
          this.enableFallbackPolling();
        }
      };

      cognitiveWebSocket.onerror = (error) => {
        console.log('❌ Cognitive stream error, will attempt fallback');
        
        enhancedCognitiveState.update(state => ({
          ...state,
          cognitiveStreaming: {
            ...state.cognitiveStreaming,
            connected: false
          },
          connectionStatus: 'error'
        }));
      };

    } catch (error) {
      console.log('⚠️ WebSocket connection failed, using fallback polling:', error);
      this.enableFallbackPolling();
    }
  }

  /**
   * Enable fallback polling when WebSocket is not available
   */
  enableFallbackPolling() {
    console.log('🔄 Enabling fallback polling for cognitive updates');
    
    // Update every 5 seconds as fallback
    if (!this.fallbackPollingInterval) {
      this.fallbackPollingInterval = setInterval(async () => {
        try {
          await this.updateSystemHealth();
          await this.updateAutonomousLearningState();
        } catch (error) {
          // Silently handle polling errors
        }
      }, 5000);
    }

    enhancedCognitiveState.update(state => ({
      ...state,
      cognitiveStreaming: {
        ...state.cognitiveStreaming,
        connected: false,
        enabled: false,
        fallbackMode: true
      }
    }));
  }

  /**
   * Disconnect from cognitive stream
   */
  disconnectCognitiveStream() {
    if (cognitiveWebSocket) {
      cognitiveWebSocket.close(1000, 'Client disconnect');
      cognitiveWebSocket = null;
    }

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.fallbackPollingInterval) {
      clearInterval(this.fallbackPollingInterval);
      this.fallbackPollingInterval = null;
    }

    enhancedCognitiveState.update(state => ({
      ...state,
      cognitiveStreaming: {
        ...state.cognitiveStreaming,
        connected: false,
        enabled: false,
        fallbackMode: false
      }
    }));

    console.log('🔌 Disconnected from cognitive stream');
  }

  /**
   * Configure cognitive streaming settings
   */
  async configureCognitiveStreaming(config) {
    try {
      // Update local configuration
      cognitiveConfig.update(state => ({
        ...state,
        cognitiveStreaming: { ...state.cognitiveStreaming, ...config }
      }));

      // If streaming is being enabled, connect
      if (config.enabled) {
        await this.connectCognitiveStream();
      } else {
        this.disconnectCognitiveStream();
      }

      // Send configuration to backend if connected
      if (cognitiveWebSocket && cognitiveWebSocket.readyState === WebSocket.OPEN) {
        cognitiveWebSocket.send(JSON.stringify({
          type: 'configure',
          ...config
        }));
      } else {
        // Use HTTP API as fallback
        try {
          const response = await fetch(`${API_BASE_URL}/api/enhanced-cognitive/stream/configure`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
          });
          if (response.ok) {
            console.log('✅ Cognitive streaming configured via HTTP API');
          }
        } catch (error) {
          console.warn('Failed to configure streaming via HTTP API:', error);
        }
      }

      return true;
    } catch (error) {
      console.error('Failed to configure cognitive streaming:', error);
      return false;
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnection() {
    if (this.reconnectTimeout) return;

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000); // Max 30 seconds

    console.log(`🔄 Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connectCognitiveStream();
    }, delay);
  }

  /**
   * Handle incoming cognitive events
   */
  handleCognitiveEvent(event) {
  // Ignore non-cognitive control messages at the handler level as well
  const t0 = event?.type || event?.event_type;
  const ignoreTypes = new Set(['initial_state', 'subscription_confirmed', 'ack', 'pong', 'state_update', 'configure_ack']);
  if (ignoreTypes.has(t0)) return;
  
    // Normalize event for UI consumers
    const normalized = (() => {
      const baseType = event?.type || event?.event_type;
      let data = event?.data || event?.details || {};
      
      // Extract meaningful content based on event type and structure
      let content = '';
      
      // First, check if we have a JSON string as content that needs to be parsed
      let parsedContent = null;
      if (typeof data === 'string' && (data.startsWith('{') || data.startsWith('['))) {
        try {
          parsedContent = JSON.parse(data);
          data = parsedContent; // Use parsed data for extraction
        } catch (e) {
          // Not valid JSON, continue with string data
        }
      }
      
      // Also check if event.content or event.message contains JSON
      if (event?.content && typeof event.content === 'string' && event.content.startsWith('{')) {
        try {
          parsedContent = JSON.parse(event.content);
          data = parsedContent; // Use parsed content data
        } catch (e) {
          // Not valid JSON, continue
        }
      }
      
      // First, try to get explicit content/message fields
      if (data?.content && typeof data.content === 'string') {
        content = data.content;
      } else if (data?.message && typeof data.message === 'string') {
        content = data.message;
      } else if (event?.content && typeof event.content === 'string') {
        content = event.content;
      } else if (event?.message && typeof event.message === 'string') {
        content = event.message;
      } else {
        // Generate meaningful descriptions based on event type and data
        switch (baseType) {
          case 'cognitive_state_update':
            if (data?.manifest_consciousness) {
              const consciousness = data.manifest_consciousness;
              const focus = consciousness.attention_focus;
              const workingMemory = consciousness.working_memory;
              
              let description = '';
              if (focus && focus !== 'undefined') {
                description += `Attention focus: ${focus}%`;
              }
              if (workingMemory && Array.isArray(workingMemory) && workingMemory.length > 0) {
                const memoryItems = workingMemory.filter(item => item && item !== 'undefined').slice(0, 2);
                if (memoryItems.length > 0) {
                  description += (description ? ' • ' : '') + `Working on: ${memoryItems.join(', ')}`;
                }
              }
              
              // Add active processes info
              if (data?.agentic_processes) {
                const activeProcesses = data.agentic_processes.filter(p => p.status === 'active');
                if (activeProcesses.length > 0) {
                  const processNames = activeProcesses.map(p => p.name).slice(0, 2);
                  description += (description ? ' • ' : '') + `Active: ${processNames.join(', ')}`;
                }
              }
              
              // Add daemon thread info
              if (data?.daemon_threads) {
                const activeDaemons = data.daemon_threads.filter(d => d.active && d.activity_level > 50);
                if (activeDaemons.length > 0) {
                  const daemonNames = activeDaemons.map(d => d.name).slice(0, 2);
                  description += (description ? ' • ' : '') + `Background: ${daemonNames.join(', ')}`;
                }
              }
              
              content = description || 'Cognitive state updated';
            } else if (data?.processingMode && data.processingMode !== 'undefined') {
              content = `Processing mode: ${data.processingMode}`;
            } else if (data?.currentFocus && data.currentFocus !== 'undefined') {
              content = `Focusing on: ${data.currentFocus}`;
            } else {
              content = 'Cognitive state updated with new parameters';
            }
            break;
            
          case 'reasoning':
          case 'thinking':
            if (data?.reasoning_chain) {
              content = `Reasoning: ${data.reasoning_chain}`;
            } else if (data?.thought) {
              content = `Thinking: ${data.thought}`;
            } else if (data?.process) {
              content = `Processing: ${data.process}`;
            } else if (data?.analysis) {
              content = `Analyzing: ${data.analysis}`;
            } else if (data?.conclusion) {
              content = `Concluded: ${data.conclusion}`;
            } else {
              // Try to extract meaningful info from the event structure
              if (data?.manifest_consciousness?.working_memory) {
                const memory = data.manifest_consciousness.working_memory;
                if (Array.isArray(memory) && memory.length > 0) {
                  content = `Reasoning about: ${memory[0]}`;
                } else {
                  content = 'Engaging in reasoning process';
                }
              } else {
                content = 'Engaging in reasoning process';
              }
            }
            break;
            
          case 'knowledge_gap':
          case 'gaps_detected':
            if (data?.gap_description) {
              content = `Knowledge gap identified: ${data.gap_description}`;
            } else if (data?.domain) {
              content = `Knowledge gap detected in ${data.domain}`;
            } else {
              content = 'Knowledge gap identified requiring investigation';
            }
            break;
            
          case 'acquisition_started':
            content = data?.topic ? `Learning about: ${data.topic}` : 'Beginning knowledge acquisition';
            break;
            
          case 'acquisition_completed':
            content = data?.topic ? `Completed learning: ${data.topic}` : 'Knowledge acquisition completed';
            break;
            
          case 'reflection':
          case 'self_reflection':
            if (data?.reflection_text) {
              content = `Reflecting: ${data.reflection_text}`;
            } else {
              content = 'Engaging in self-reflection on recent activities';
            }
            break;
            
          case 'synthesis':
            content = data?.synthesis_result ? `Synthesized: ${data.synthesis_result}` : 'Synthesizing knowledge from multiple sources';
            break;
            
          case 'learning':
            content = data?.learning_outcome ? `Learned: ${data.learning_outcome}` : 'Processing new learning experience';
            break;
            
          default:
            // Try to extract any meaningful text from the data
            if (data?.description) {
              content = data.description;
            } else if (data?.summary) {
              content = data.summary;
            } else if (data?.text) {
              content = data.text;
            } else if (typeof data === 'string') {
              content = data;
            } else if (data?.timestamp && data?.manifest_consciousness) {
              // This looks like raw cognitive state data - format it nicely
              const consciousness = data.manifest_consciousness;
              const processes = data.agentic_processes || [];
              const daemons = data.daemon_threads || [];
              
              let parts = [];
              if (consciousness.attention_focus) {
                parts.push(`Focus: ${consciousness.attention_focus}%`);
              }
              
              if (consciousness.working_memory && Array.isArray(consciousness.working_memory)) {
                const memory = consciousness.working_memory.filter(m => m && m !== 'undefined');
                if (memory.length > 0) {
                  parts.push(`Working: ${memory.slice(0, 2).join(', ')}`);
                }
              }
              
              const activeProcesses = processes.filter(p => p.status === 'active');
              if (activeProcesses.length > 0) {
                parts.push(`Active: ${activeProcesses.map(p => p.name).slice(0, 2).join(', ')}`);
              }
              
              const activeDaemons = daemons.filter(d => d.active && d.activity_level > 50);
              if (activeDaemons.length > 0) {
                parts.push(`Background: ${activeDaemons.map(d => d.name).slice(0, 2).join(', ')}`);
              }
              
              content = parts.join(' • ') || 'Cognitive state active';
            } else {
              content = `${baseType.replace('_', ' ')} event occurred`;
            }
        }
      }
      
      // Final cleanup - ensure no undefined/null values in content
      if (!content || content.includes('undefined') || content.includes('null')) {
        content = `${baseType.replace('_', ' ')} activity detected`;
      }
      // Map backend event types to UI filter categories the monitor expects
      const mapToUiEventType = (t) => {
        switch (t) {
          case 'gaps_detected':
          case 'knowledge_gap':
          case 'autonomous_gaps_detected':
            return 'knowledge_gap';
          case 'acquisition_started':
          case 'acquisition_completed':
          case 'acquisition_failed':
          case 'knowledge_acquisition':
            return 'acquisition';
          case 'reasoning':
          case 'thinking':
            return 'reasoning';
          case 'reflection':
          case 'self_reflection':
            return 'reflection';
          case 'learning':
          case 'synthesis':
            return t;
          default:
            // Fall back to a generic bucket so it still shows
            return 'reasoning';
        }
      };
      const uiType = mapToUiEventType(baseType);
      return {
        ...event,
        original_type: baseType,
        type: baseType, // keep original for internal switches
        event_type: uiType, // UI filter uses this
        content,
        granularity: event?.granularity || 'detailed'
      };
    })();

    // Add to event buffer with deduplication
    const eventKey = `${normalized.type}_${normalized.timestamp}_${normalized.content}`;
    const isDuplicate = this.eventBuffer.some(existing => 
      `${existing.type}_${existing.timestamp}_${existing.content}` === eventKey
    );
    
    if (!isDuplicate) {
      this.eventBuffer.push(normalized);
      if (this.eventBuffer.length > this.maxBufferSize) {
        this.eventBuffer.shift();
      }
    } else {
      console.log('🔄 Skipping duplicate event:', eventKey);
      return; // Skip processing duplicate events
    }

    // Update state based on event type
    enhancedCognitiveState.update(state => {
      const newState = { ...state };
      
      // Update streaming state with safe array handling
      const safeEventHistory = Array.isArray(state.cognitiveStreaming.eventHistory) 
        ? state.cognitiveStreaming.eventHistory 
        : [];
      
      newState.cognitiveStreaming = {
        ...state.cognitiveStreaming,
        lastEvent: normalized,
        eventHistory: [...safeEventHistory, normalized].slice(-100),
        eventRate: this.calculateEventRate()
      };

      // Handle specific event types with safe array operations
      switch (normalized.type) {
        case 'gaps_detected':
        case 'autonomous_gaps_detected':
          if (normalized.data?.gaps && Array.isArray(normalized.data.gaps)) {
            const safeDetectedGaps = Array.isArray(state.autonomousLearning.detectedGaps) 
              ? state.autonomousLearning.detectedGaps 
              : [];
            newState.autonomousLearning = {
              ...state.autonomousLearning,
              detectedGaps: [...safeDetectedGaps, ...normalized.data.gaps].slice(-50) // Limit to 50 items
            };
          }
          break;

        case 'acquisition_started':
          if (normalized.data?.plan_id) {
            const safeActiveAcquisitions = Array.isArray(state.autonomousLearning.activeAcquisitions) 
              ? state.autonomousLearning.activeAcquisitions 
              : [];
            newState.autonomousLearning = {
              ...state.autonomousLearning,
              activeAcquisitions: [
                ...safeActiveAcquisitions,
                {
                  id: normalized.data.plan_id,
                  started: normalized.timestamp,
                  gap_id: normalized.data.gap_id
                }
              ].slice(-20) // Limit to 20 active acquisitions
            };
          }
          break;

        case 'acquisition_completed':
        case 'acquisition_failed':
          if (normalized.data?.plan_id) {
            // Remove from active acquisitions safely
            const safeActiveAcquisitions = Array.isArray(state.autonomousLearning.activeAcquisitions) 
              ? state.autonomousLearning.activeAcquisitions 
              : [];
            const safeAcquisitionHistory = Array.isArray(state.autonomousLearning.acquisitionHistory) 
              ? state.autonomousLearning.acquisitionHistory 
              : [];
              
            newState.autonomousLearning = {
              ...state.autonomousLearning,
              activeAcquisitions: safeActiveAcquisitions.filter(
                acq => acq && acq.id !== normalized.data.plan_id
              ),
              acquisitionHistory: [
                ...safeAcquisitionHistory,
                {
                  id: normalized.data.plan_id,
                  completed: normalized.timestamp,
                  success: normalized.type === 'acquisition_completed',
                  executionTime: normalized.data.execution_time,
                  acquiredConcepts: normalized.data.acquired_concepts || 0
                }
              ].slice(-50) // Keep last 50
            };
          }
          break;

        case 'query_started':
          newState.manifestConsciousness = {
            ...state.manifestConsciousness,
            currentFocus: normalized.data?.query || 'Processing query',
            processingMode: 'active',
            lastActivity: normalized.timestamp
          };
          break;

        case 'query_completed':
          newState.manifestConsciousness = {
            ...state.manifestConsciousness,
            processingMode: 'idle',
            lastActivity: normalized.timestamp
          };
          break;

        case 'cognitive_event':
          // Handle transparency engine events - these come wrapped with inner event data
          if (normalized.data && normalized.data.event_type) {
            // Extract the inner event and process it recursively
            const innerEvent = {
              type: normalized.data.event_type,
              timestamp: normalized.data.timestamp || normalized.timestamp,
              data: normalized.data.details || normalized.data,
              component: normalized.data.component,
              priority: normalized.data.priority
            };
            
            // Process the inner event by calling this method recursively
            // but prevent infinite recursion by creating a new event structure
            setTimeout(() => {
              this.handleCognitiveEvent(innerEvent);
            }, 0);
            
            console.log('🧠 Processed transparency cognitive event:', innerEvent.type, innerEvent);
          }
          break;
      }

      return newState;
    });
  }

  /**
   * Calculate current event rate
   */
  calculateEventRate() {
    const now = Date.now();
    const oneSecondAgo = now - 1000;
    
    const recentEvents = this.eventBuffer.filter(event => {
      const eventTime = new Date(event.timestamp).getTime();
      return eventTime >= oneSecondAgo;
    });

    return recentEvents.length;
  }

  /**
   * Update system health information
   */
  async updateSystemHealth() {
    try {
      if (!this.apiUrl) return;
      
      const response = await fetch(`${this.apiUrl}/api/enhanced/system-health`);
      if (response.ok) {
        const health = await response.json();
        
        cognitiveState.update(state => ({
          ...state,
          systemHealth: health
        }));

        // Update config with performance metrics
        cognitiveConfig.update(state => ({
          ...state,
          performance: {
            ...state.performance,
            lastHealthUpdate: Date.now(),
            healthScore: health.overall_score || 0.8
          }
        }));
      }
    } catch (error) {
      console.error('Failed to update system health:', error);
    }
  }

  /**
   * Update autonomous learning state
   */
  async updateAutonomousLearningState() {
    try {
      if (!this.apiUrl) return;
      
      const response = await fetch(`${this.apiUrl}/api/enhanced/autonomous-learning`);
      if (response.ok) {
        const learning = await response.json();
        
        cognitiveState.update(state => ({
          ...state,
          autonomousLearning: learning
        }));

        // Update config with learning metrics
        cognitiveConfig.update(state => ({
          ...state,
          autonomousLearning: {
            ...state.autonomousLearning,
            lastUpdate: Date.now(),
            activeGaps: learning.knowledge_gaps?.length || 0,
            acquisitionRate: learning.acquisition_rate || 0
          }
        }));
      }
    } catch (error) {
      console.error('Failed to update autonomous learning:', error);
    }
  }

  /**
   * Start periodic health monitoring
   */
  startHealthMonitoring() {
    console.log('� Health monitoring enabled');
    
    // Update health once initially
    this.updateSystemHealth();
    this.updateAutonomousLearningState();
    
    // Re-enable periodic updates
    setInterval(() => {
      this.updateSystemHealth();
    }, 30000);

    setInterval(() => {
      this.updateAutonomousLearningState();
    }, 60000);
  }

  /**
   * Configure autonomous learning
   */
  async configureAutonomousLearning(config) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/enhanced-cognitive/autonomous/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        cognitiveConfig.update(state => ({
          ...state,
          autonomousLearning: { ...state.autonomousLearning, ...config }
        }));
        
        await this.updateAutonomousLearningState();
        return true;
      }
      return false;
    } catch (error) {
      // Silently handle configuration errors when backend is unavailable
      return false;
    }
  }

  /**
   * Configure cognitive streaming
   */
  async configureCognitiveStreaming(config) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/enhanced-cognitive/stream/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        cognitiveConfig.update(state => ({
          ...state,
          cognitiveStreaming: { ...state.cognitiveStreaming, ...config }
        }));

        // Reconnect with new configuration
        if (cognitiveWebSocket && config.granularity) {
          await this.connectCognitiveStream();
        }
        
        return true;
      }
      return false;
    } catch (error) {
      // Silently handle streaming configuration errors when backend is unavailable
      return false;
    }
  }

  /**
   * Trigger manual knowledge acquisition
   */
  async triggerKnowledgeAcquisition(concepts, priority = 0.8) {
    try {
      const response = await fetch('/api/enhanced-cognitive/autonomous/trigger-acquisition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concepts,
          priority,
          strategy: 'concept_expansion'
        })
      });

      return response.ok;
    } catch (error) {
      // Silently handle knowledge acquisition trigger errors when backend is unavailable
      return false;
    }
  }

  /**
   * Send message through cognitive stream
   */
  sendCognitiveMessage(message) {
    if (cognitiveWebSocket && cognitiveWebSocket.readyState === WebSocket.OPEN) {
      cognitiveWebSocket.send(JSON.stringify(message));
    }
  }

  /**
   * Get cognitive event history
   */
  getCognitiveEventHistory(limit = 100) {
    return this.eventBuffer.slice(-limit);
  }

  /**
   * Disconnect cognitive stream
   */
  disconnectCognitiveStream() {
    if (cognitiveWebSocket) {
      cognitiveWebSocket.close();
      cognitiveWebSocket = null;
    }
    
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }
  }
}

// Create global instance
export const enhancedCognitiveStateManager = new EnhancedCognitiveStateManager();

// Derived stores for convenient access
export const autonomousLearningState = derived(
  enhancedCognitiveState,
  $state => $state.autonomousLearning
);

export const cognitiveStreamingState = derived(
  enhancedCognitiveState,
  $state => $state.cognitiveStreaming
);

// Alias for easier access
export const streamState = cognitiveStreamingState;

export const enhancedSystemHealth = derived(
  enhancedCognitiveState,
  $state => $state.systemHealth
);

export const manifestConsciousness = derived(
  enhancedCognitiveState,
  $state => $state.manifestConsciousness
);

// Utility functions
export function getHealthColor(status) {
  switch (status) {
    case 'healthy': return '#4ade80';
    case 'warning': return '#fbbf24';
    case 'critical': return '#ef4444';
    case 'unknown': return '#6b7280';
    default: return '#6b7280';
  }
}

export function formatDuration(seconds) {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function formatEventRate(rate) {
  if (rate < 1) return `${(rate * 1000).toFixed(0)}ms⁻¹`;
  return `${rate.toFixed(1)}/s`;
}

// State Coordination - Bridge between basic and enhanced cognitive stores
const synchronizedCognitiveState = derived(
  cognitiveState,
  (basicState) => {
    return {
      ...get(enhancedCognitiveState),
      // Sync manifest consciousness with enhanced features
      manifestConsciousness: {
        ...get(enhancedCognitiveState).manifestConsciousness,
        currentFocus: basicState.manifestConsciousness?.currentQuery || 
                     basicState.manifestConsciousness?.attention || 
                     get(enhancedCognitiveState).manifestConsciousness.currentFocus,
        attentionDepth: get(enhancedCognitiveState).manifestConsciousness.attentionDepth,
        processingMode: basicState.manifestConsciousness?.processingLoad > 0.7 ? 'intensive' :
                       basicState.manifestConsciousness?.processingLoad > 0.3 ? 'active' : 'idle',
        cognitiveLoad: basicState.manifestConsciousness?.processingLoad || get(enhancedCognitiveState).manifestConsciousness.cognitiveLoad,
        lastActivity: basicState.lastUpdate ? new Date(basicState.lastUpdate).toISOString() : get(enhancedCognitiveState).manifestConsciousness.lastActivity
      },
      // Enhance system health with basic cognitive health data
      systemHealth: {
        ...get(enhancedCognitiveState).systemHealth,
        inferenceEngine: basicState.systemHealth?.inferenceEngine > 0.8 ? 'healthy' :
                        basicState.systemHealth?.inferenceEngine > 0.5 ? 'degraded' : 'critical',
        knowledgeStore: basicState.systemHealth?.knowledgeStore > 0.8 ? 'healthy' :
                       basicState.systemHealth?.knowledgeStore > 0.5 ? 'degraded' : 'critical',
        websocketConnection: basicState.systemHealth?.websocketConnection > 0.5 ? 'connected' : 'disconnected'
      },
      // Update connection status based on basic cognitive state
      connectionStatus: basicState.systemHealth?.websocketConnection > 0.5 ? 'connected' : 'disconnected',
      lastUpdate: new Date().toISOString()
    };
  }
);

// Function to synchronize enhanced state with basic cognitive state
function synchronizeWithBasicCognitive() {
  // Subscribe to synchronization state and update the main enhanced state
  synchronizedCognitiveState.subscribe(synchronizedState => {
    enhancedCognitiveState.update(state => ({
      ...state,
      ...synchronizedState
    }));
  });
}

// Initialize on module load - DISABLED to prevent duplicate initialization
if (typeof window !== 'undefined') {
  // enhancedCognitiveStateManager.initialize(); // Disabled - will be called explicitly from App.svelte
  // Start state synchronization
  synchronizeWithBasicCognitive();
}

// Main enhanced cognitive interface for components
export const enhancedCognitive = {
  subscribe: enhancedCognitiveState.subscribe,
  update: enhancedCognitiveState.update,
  set: enhancedCognitiveState.set,
  
  // Manager methods
  initializeEnhancedSystems: () => enhancedCognitiveStateManager.initialize(),
  enableCognitiveStreaming: (granularity) => enhancedCognitiveStateManager.configureCognitiveStreaming({ granularity, enabled: true }),
  disableCognitiveStreaming: () => enhancedCognitiveStateManager.disconnectCognitiveStream(),
  enableAutonomousLearning: () => enhancedCognitiveStateManager.configureAutonomousLearning({ enabled: true }),
  disableAutonomousLearning: () => enhancedCognitiveStateManager.configureAutonomousLearning({ enabled: false }),
  updateHealthStatus: () => enhancedCognitiveStateManager.updateSystemHealth(),
  
  // Enhanced methods for better integration
  refreshSystemHealth: () => enhancedCognitiveStateManager.updateSystemHealth(),
  refreshAutonomousState: () => enhancedCognitiveStateManager.updateAutonomousLearningState(),
  refreshStreamingState: () => {
    const config = get(cognitiveConfig);
    if (!config.cognitiveStreaming.enabled) {
      console.log('🚫 Streaming refresh skipped - disabled in configuration');
      return Promise.resolve();
    }
    return enhancedCognitiveStateManager.connectCognitiveStream();
  },
  updateAutonomousLearningState: () => enhancedCognitiveStateManager.updateAutonomousLearningState(),
  updateStreamingStatus: () => {
    const config = get(cognitiveConfig);
    if (!config.cognitiveStreaming.enabled) {
      console.log('🚫 Streaming status update skipped - disabled in configuration');
      return Promise.resolve();
    }
    return enhancedCognitiveStateManager.connectCognitiveStream();
  },
  pauseAutonomousLearning: () => enhancedCognitiveStateManager.configureAutonomousLearning({ enabled: false }),
  resumeAutonomousLearning: () => enhancedCognitiveStateManager.configureAutonomousLearning({ enabled: true }),
  updateLearningConfiguration: (config) => enhancedCognitiveStateManager.configureAutonomousLearning(config),
  
  // Stream management
  configureCognitiveStreaming: (config) => enhancedCognitiveStateManager.configureCognitiveStreaming(config),
  startCognitiveStreaming: (granularity = 'standard') => {
    const config = get(cognitiveConfig);
    if (!config.cognitiveStreaming.enabled) {
      console.log('🚫 Cognitive streaming is disabled in configuration - ignoring start request');
      return Promise.resolve();
    }
    return enhancedCognitiveStateManager.configureCognitiveStreaming({ enabled: true, granularity });
  },
  stopCognitiveStreaming: () => enhancedCognitiveStateManager.disconnectCognitiveStream(),
  
  // Event management
  clearEventHistory: () => {
    enhancedCognitiveStateManager.eventBuffer = [];
    enhancedCognitiveState.update(state => ({
      ...state,
      cognitiveStreaming: {
        ...state.cognitiveStreaming,
        eventHistory: []
      }
    }));
  },
  
  // Manual triggers
  triggerManualAcquisition: async (concept, context) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/enhanced-cognitive/autonomous/acquire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concept, context })
      });
      return response.ok;
    } catch (error) {
      console.warn('Failed to trigger manual acquisition:', error);
      return false;
    }
  },
  
  triggerSystemRefresh: async () => {
    try {
      await Promise.all([
        enhancedCognitiveStateManager.updateSystemHealth(),
        enhancedCognitiveStateManager.updateAutonomousLearningState()
      ]);
      return true;
    } catch (error) {
      console.warn('System refresh failed:', error);
      return false;
    }
  },
  
  // Stream subscription method for real-time updates
  subscribeToStream: (callback) => {
    // Subscribe to cognitive streaming events
    const unsubscribe = enhancedCognitiveState.subscribe(state => {
      if (state.cognitiveStreaming?.lastEvent) {
        callback(state.cognitiveStreaming.lastEvent);
      }
    });
    return unsubscribe;
  },
  
  // Connection status
  getConnectionStatus: () => {
    const state = get(enhancedCognitiveState);
    return {
      apiConnected: state.apiConnected,
      streamConnected: state.cognitiveStreaming?.connected || false,
      connectionStatus: state.connectionStatus,
      fallbackMode: state.cognitiveStreaming?.fallbackMode || false
    };
  },
  
  // State access helpers
  autonomousLearning: autonomousLearningState,
  streaming: cognitiveStreamingState,
  health: enhancedSystemHealth,
  consciousness: manifestConsciousness
};

// Default export for easier importing
export default enhancedCognitive;
