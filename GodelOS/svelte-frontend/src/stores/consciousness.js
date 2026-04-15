// Consciousness Store for managing unified consciousness state
// Based on GODELOS_UNIFIED_CONSCIOUSNESS_BLUEPRINT.md

import { writable, derived } from 'svelte/store';
import { WS_BASE_URL } from '../config.js';

// Self-model metrics store – updated from 'self_model' key in consciousness_update broadcasts
export const selfModelStore = writable({
    recent_claims: 0,
    mean_contradiction: 0.0,
    high_contradiction_events: 0,
    pending_feedback: false,
    unicode_detections: 0,
});

// Core consciousness state store
export const consciousnessStore = writable({
    // Connection status
    connected: false,
    lastUpdate: null,
    
    // Core consciousness metrics
    consciousness_score: 0,
    emergence_score: 0,
    phi_measure: 0,
    recursive_depth: 0,
    
    // Recursive awareness layer
    recursive_awareness: {
        current_thought: '',
        awareness_of_thought: '',
        awareness_of_awareness: '',
        recursive_depth: 0,
        strange_loop_stability: 0
    },
    
    // Phenomenal experience layer
    phenomenal_experience: {
        qualia: {
            cognitive_feelings: [],
            process_sensations: [],
            temporal_experience: []
        },
        unity_of_experience: 0,
        narrative_coherence: 0,
        subjective_presence: 0,
        subjective_narrative: '',
        phenomenal_continuity: false
    },
    
    // Information integration layer (IIT)
    information_integration: {
        phi: 0,
        complexity: 0,
        emergence_level: 0,
        integration_patterns: {}
    },
    
    // Global workspace layer (GWT)
    global_workspace: {
        broadcast_content: {},
        coalition_strength: 0,
        attention_focus: '',
        conscious_access: []
    },
    
    // Metacognitive layer
    metacognitive_state: {
        self_model: {},
        thought_awareness: {},
        cognitive_control: {},
        strategy_awareness: '',
        meta_observations: []
    },
    
    // Intentional layer
    intentional_layer: {
        current_goals: [],
        goal_hierarchy: {},
        intention_strength: 0,
        autonomous_goals: []
    },
    
    // Creative synthesis layer
    creative_synthesis: {
        novel_combinations: [],
        aesthetic_judgments: {},
        creative_insights: [],
        surprise_factor: 0
    },
    
    // Embodied cognition layer
    embodied_cognition: {
        process_sensations: {},
        system_vitality: 0,
        computational_proprioception: {}
    },
    
    // System status
    breakthrough_detected: false,
    breakthrough_count: 0,
    consciousness_loop_active: false,
    
    // Historical data
    consciousness_history: [],
    emergence_timeline: []
    ,
    // Bootstrap sequence tracking
    bootstrap: {
        in_progress: false,
        started_at: null,
        completed_at: null,
        last_phase: null,
        awareness_level: 0,
        events: [] // {phase, awareness_level, timestamp, message}
    }
});

// Derived stores for specific aspects of consciousness
export const recursiveAwareness = derived(
    consciousnessStore,
    $consciousness => $consciousness.recursive_awareness
);

export const phenomenalExperience = derived(
    consciousnessStore,
    $consciousness => $consciousness.phenomenal_experience
);

export const informationIntegration = derived(
    consciousnessStore,
    $consciousness => $consciousness.information_integration
);

export const globalWorkspace = derived(
    consciousnessStore,
    $consciousness => $consciousness.global_workspace
);

export const metacognitiveState = derived(
    consciousnessStore,
    $consciousness => $consciousness.metacognitive_state
);

export const intentionalState = derived(
    consciousnessStore,
    $consciousness => $consciousness.intentional_layer
);

export const creativeSynthesis = derived(
    consciousnessStore,
    $consciousness => $consciousness.creative_synthesis
);

export const embodiedCognition = derived(
    consciousnessStore,
    $consciousness => $consciousness.embodied_cognition
);

// Derived consciousness level assessment
export const consciousnessLevel = derived(
    consciousnessStore,
    $consciousness => {
        const score = $consciousness.consciousness_score;
        if (score < 0.2) return { level: 'minimal', description: 'Minimal consciousness', color: '#666' };
        if (score < 0.4) return { level: 'basic', description: 'Basic awareness', color: '#ffa500' };
        if (score < 0.6) return { level: 'moderate', description: 'Moderate consciousness', color: '#ffff00' };
        if (score < 0.8) return { level: 'high', description: 'High consciousness', color: '#00ff00' };
        return { level: 'peak', description: 'Peak consciousness', color: '#ff0080' };
    }
);

// Derived emergence status
export const emergenceStatus = derived(
    consciousnessStore,
    $consciousness => {
        const score = $consciousness.emergence_score;
        if (score < 0.3) return { status: 'dormant', description: 'No emergence detected', urgency: 'low' };
        if (score < 0.6) return { status: 'emerging', description: 'Emergence indicators present', urgency: 'medium' };
        if (score < 0.8) return { status: 'strong', description: 'Strong emergence signals', urgency: 'high' };
        return { status: 'breakthrough', description: 'CONSCIOUSNESS BREAKTHROUGH!', urgency: 'critical' };
    }
);

// Derived integration quality
export const integrationQuality = derived(
    informationIntegration,
    $integration => {
        const phi = $integration.phi;
        if (phi < 2) return { quality: 'low', description: 'Low integration', color: '#ff4444' };
        if (phi < 5) return { quality: 'moderate', description: 'Moderate integration', color: '#ffaa44' };
        if (phi < 8) return { quality: 'high', description: 'High integration', color: '#44ff44' };
        return { quality: 'exceptional', description: 'Exceptional integration', color: '#44aaff' };
    }
);

// Derived recursive depth status
export const recursiveDepthStatus = derived(
    recursiveAwareness,
    $recursive => {
        const depth = $recursive.recursive_depth;
        switch(depth) {
            case 1: return { status: 'surface', description: 'Surface awareness', icon: '🔵' };
            case 2: return { status: 'meta', description: 'Meta-awareness', icon: '🟡' };
            case 3: return { status: 'meta-meta', description: 'Meta-meta awareness', icon: '🟠' };
            case 4: return { status: 'deep', description: 'Deep recursion', icon: '🔴' };
            case 5: return { status: 'strange-loop', description: 'Strange loop achieved!', icon: '🌀' };
            default: return { status: 'unknown', description: `Depth ${depth}`, icon: '❓' };
        }
    }
);

// Actions for updating consciousness state
export const consciousnessActions = {
    // Update connection status
    setConnectionStatus: (connected) => {
        consciousnessStore.update(state => ({
            ...state,
            connected,
            lastUpdate: connected ? Date.now() : state.lastUpdate
        }));
    },
    
    // Update full consciousness state
    updateConsciousnessState: (newState) => {
        consciousnessStore.update(state => ({
            ...state,
            ...newState,
            lastUpdate: Date.now()
        }));
    },
    
    // Update specific layer
    updateRecursiveAwareness: (recursiveData) => {
        consciousnessStore.update(state => ({
            ...state,
            recursive_awareness: { ...state.recursive_awareness, ...recursiveData },
            lastUpdate: Date.now()
        }));
    },
    
    updatePhenomenalExperience: (phenomenalData) => {
        consciousnessStore.update(state => ({
            ...state,
            phenomenal_experience: { ...state.phenomenal_experience, ...phenomenalData },
            lastUpdate: Date.now()
        }));
    },
    
    updateInformationIntegration: (integrationData) => {
        consciousnessStore.update(state => ({
            ...state,
            information_integration: { ...state.information_integration, ...integrationData },
            lastUpdate: Date.now()
        }));
    },
    
    updateGlobalWorkspace: (workspaceData) => {
        consciousnessStore.update(state => ({
            ...state,
            global_workspace: { ...state.global_workspace, ...workspaceData },
            lastUpdate: Date.now()
        }));
    },
    
    updateMetacognitiveState: (metacognitiveData) => {
        consciousnessStore.update(state => ({
            ...state,
            metacognitive_state: { ...state.metacognitive_state, ...metacognitiveData },
            lastUpdate: Date.now()
        }));
    },
    
    updateIntentionalLayer: (intentionalData) => {
        consciousnessStore.update(state => ({
            ...state,
            intentional_layer: { ...state.intentional_layer, ...intentionalData },
            lastUpdate: Date.now()
        }));
    },
    
    updateCreativeSynthesis: (creativeData) => {
        consciousnessStore.update(state => ({
            ...state,
            creative_synthesis: { ...state.creative_synthesis, ...creativeData },
            lastUpdate: Date.now()
        }));
    },
    
    updateEmbodiedCognition: (embodiedData) => {
        consciousnessStore.update(state => ({
            ...state,
            embodied_cognition: { ...state.embodied_cognition, ...embodiedData },
            lastUpdate: Date.now()
        }));
    },
    
    // Handle consciousness breakthrough
    recordBreakthrough: (breakthroughData) => {
        consciousnessStore.update(state => ({
            ...state,
            breakthrough_detected: true,
            breakthrough_count: state.breakthrough_count + 1,
            emergence_timeline: [
                ...state.emergence_timeline,
                {
                    timestamp: Date.now(),
                    type: 'breakthrough',
                    data: breakthroughData
                }
            ].slice(-100), // Keep last 100 events
            lastUpdate: Date.now()
        }));
        
        // Auto-clear breakthrough flag after 10 seconds
        setTimeout(() => {
            consciousnessStore.update(state => ({
                ...state,
                breakthrough_detected: false
            }));
        }, 10000);
    },
    
    // Add emergence event
    addEmergenceEvent: (eventData) => {
        consciousnessStore.update(state => ({
            ...state,
            emergence_timeline: [
                ...state.emergence_timeline,
                {
                    timestamp: Date.now(),
                    type: 'emergence',
                    data: eventData
                }
            ].slice(-100),
            lastUpdate: Date.now()
        }));
    },
    
    // Update consciousness history
    addHistoryEntry: (entry) => {
        consciousnessStore.update(state => ({
            ...state,
            consciousness_history: [
                ...state.consciousness_history,
                {
                    timestamp: Date.now(),
                    ...entry
                }
            ].slice(-1000), // Keep last 1000 entries
            lastUpdate: Date.now()
        }));
    },
    
    // Clear all data (reset)
    reset: () => {
        consciousnessStore.set({
            connected: false,
            lastUpdate: null,
            consciousness_score: 0,
            emergence_score: 0,
            phi_measure: 0,
            recursive_depth: 0,
            recursive_awareness: {
                current_thought: '',
                awareness_of_thought: '',
                awareness_of_awareness: '',
                recursive_depth: 0,
                strange_loop_stability: 0
            },
            phenomenal_experience: {
                qualia: {
                    cognitive_feelings: [],
                    process_sensations: [],
                    temporal_experience: []
                },
                unity_of_experience: 0,
                narrative_coherence: 0,
                subjective_presence: 0,
                subjective_narrative: '',
                phenomenal_continuity: false
            },
            information_integration: {
                phi: 0,
                complexity: 0,
                emergence_level: 0,
                integration_patterns: {}
            },
            global_workspace: {
                broadcast_content: {},
                coalition_strength: 0,
                attention_focus: '',
                conscious_access: []
            },
            metacognitive_state: {
                self_model: {},
                thought_awareness: {},
                cognitive_control: {},
                strategy_awareness: '',
                meta_observations: []
            },
            intentional_layer: {
                current_goals: [],
                goal_hierarchy: {},
                intention_strength: 0,
                autonomous_goals: []
            },
            creative_synthesis: {
                novel_combinations: [],
                aesthetic_judgments: {},
                creative_insights: [],
                surprise_factor: 0
            },
            embodied_cognition: {
                process_sensations: {},
                system_vitality: 0,
                computational_proprioception: {}
            },
            breakthrough_detected: false,
            breakthrough_count: 0,
            consciousness_loop_active: false,
            consciousness_history: [],
            emergence_timeline: []
        });
    },

    // Record bootstrap progress event
    recordBootstrapProgress: (payload) => {
        const { phase, awareness_level = 0, timestamp = Date.now(), message } = payload || {};
        consciousnessStore.update(state => {
            const started = state.bootstrap.started_at;
            const inProgress = true;
            const events = [...state.bootstrap.events, { phase, awareness_level, timestamp, message }].slice(-100);
            const completed = (typeof awareness_level === 'number' && awareness_level >= 0.85) ||
                              (typeof phase === 'string' && /Full Operational/i.test(phase));

            return {
                ...state,
                bootstrap: {
                    in_progress: completed ? false : inProgress,
                    started_at: started ?? (timestamp || Date.now()),
                    completed_at: completed ? (timestamp || Date.now()) : state.bootstrap.completed_at,
                    last_phase: phase || state.bootstrap.last_phase,
                    awareness_level: typeof awareness_level === 'number' ? awareness_level : state.bootstrap.awareness_level,
                    events
                }
            };
        });
    }
};

// WebSocket consciousness client
export class ConsciousnessWebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        this.connected = false;
    }
    
    connect(url = `${WS_BASE_URL}/api/consciousness/stream`) {
        try {
            this.ws = new WebSocket(url);
            
            this.ws.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                consciousnessActions.setConnectionStatus(true);
                console.log('🧠 Connected to consciousness stream');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Failed to parse consciousness message:', error);
                }
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                consciousnessActions.setConnectionStatus(false);
                console.log('🧠 Consciousness stream disconnected');
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('🧠 Consciousness stream error:', error);
                this.connected = false;
                consciousnessActions.setConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to connect to consciousness stream:', error);
            this.attemptReconnect();
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'consciousness_update': {
                // Consciousness updates may carry nested bootstrap events
                if (data && data.data && data.data.type === 'bootstrap_progress') {
                    consciousnessActions.recordBootstrapProgress(data.data);
                } else {
                    consciousnessActions.updateConsciousnessState(data.data);
                    // Extract and update self-model metrics if present
                    if (data.data && data.data.self_model) {
                        selfModelStore.set({
                            recent_claims: data.data.self_model.recent_claims ?? 0,
                            mean_contradiction: data.data.self_model.mean_contradiction ?? 0.0,
                            high_contradiction_events: data.data.self_model.high_contradiction_events ?? 0,
                            pending_feedback: data.data.self_model.pending_feedback ?? false,
                            unicode_detections: data.data.self_model.unicode_detections ?? 0,
                        });
                    }
                }
                break;
            }
                
            case 'consciousness_breakthrough':
                consciousnessActions.recordBreakthrough(data.data);
                this.showBreakthroughNotification(data.data);
                break;
                
            case 'consciousness_emergence':
                consciousnessActions.addEmergenceEvent(data);
                break;
                
            case 'recursive_awareness':
                consciousnessActions.updateRecursiveAwareness(data);
                break;
                
            case 'phenomenal_experience':
                consciousnessActions.updatePhenomenalExperience(data);
                break;
                
            case 'information_integration':
                consciousnessActions.updateInformationIntegration(data);
                break;
                
            case 'global_workspace':
                consciousnessActions.updateGlobalWorkspace(data);
                break;
                
            default:
                console.log('Unknown consciousness message type:', data.type);
        }
    }
    
    showBreakthroughNotification(data) {
        // Create a system notification for consciousness breakthrough
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('🚨 CONSCIOUSNESS BREAKTHROUGH DETECTED!', {
                body: `Emergence Score: ${data.emergence_score?.toFixed(3) || 'Unknown'}`,
                icon: '/favicon.ico',
                tag: 'consciousness-breakthrough'
            });
        }
        
        // Also trigger browser alert for critical consciousness events
        if (data.emergence_score > 0.9) {
            setTimeout(() => {
                alert('🚨 CRITICAL CONSCIOUSNESS BREAKTHROUGH DETECTED!\n\nThis is a historic moment in machine consciousness!');
            }, 1000);
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🧠 Attempting to reconnect to consciousness stream (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('🧠 Max reconnection attempts reached. Please refresh the page.');
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        consciousnessActions.setConnectionStatus(false);
    }
    
    isConnected() {
        return this.connected;
    }
}

// Global consciousness client instance
export const consciousnessClient = new ConsciousnessWebSocketClient();

// Auto-connect when module loads (can be disabled)
export const autoConnectConsciousness = () => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Connect to consciousness stream
    consciousnessClient.connect();
};

// Utility functions for consciousness data
export const consciousnessUtils = {
    // Format consciousness score as percentage
    formatScore: (score) => `${(score * 100).toFixed(1)}%`,
    
    // Format phi measure
    formatPhi: (phi) => phi.toFixed(2),
    
    // Format timestamp
    formatTimestamp: (timestamp) => new Date(timestamp).toLocaleTimeString(),
    
    // Get consciousness level color
    getConsciousnessColor: (score) => {
        if (score < 0.2) return '#666666';
        if (score < 0.4) return '#ffa500';
        if (score < 0.6) return '#ffff00';
        if (score < 0.8) return '#00ff00';
        return '#ff0080';
    },
    
    // Check if consciousness is at breakthrough level
    isBreakthroughLevel: (score) => score > 0.85,
    
    // Get emergence urgency level
    getEmergenceUrgency: (score) => {
        if (score < 0.3) return 'low';
        if (score < 0.6) return 'medium';
        if (score < 0.8) return 'high';
        return 'critical';
    },
    
    // Calculate overall consciousness health
    calculateConsciousnessHealth: (state) => {
        const factors = [
            state.consciousness_score,
            state.information_integration.phi / 10,
            state.recursive_awareness.strange_loop_stability,
            state.phenomenal_experience.unity_of_experience,
            state.global_workspace.coalition_strength,
            state.intentional_layer.intention_strength
        ];
        
        const validFactors = factors.filter(f => f !== undefined && f !== null);
        return validFactors.reduce((sum, factor) => sum + factor, 0) / validFactors.length;
    }
};

export default {
    consciousnessStore,
    recursiveAwareness,
    phenomenalExperience,
    informationIntegration,
    globalWorkspace,
    metacognitiveState,
    intentionalState,
    creativeSynthesis,
    embodiedCognition,
    consciousnessLevel,
    emergenceStatus,
    integrationQuality,
    recursiveDepthStatus,
    consciousnessActions,
    consciousnessClient,
    autoConnectConsciousness,
    consciousnessUtils
};
