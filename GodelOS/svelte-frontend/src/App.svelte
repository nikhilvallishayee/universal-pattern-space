<script>
  import { onMount, onDestroy } from 'svelte';
  import { cognitiveState, knowledgeState, evolutionState, uiState, apiHelpers, systemHealthScore } from './stores/cognitive.js';
  import { enhancedCognitiveState, autonomousLearningState, streamState, enhancedCognitive } from './stores/enhanced-cognitive.js';
  import { setupWebSocket, connectToCognitiveStream } from './utils/websocket.js';
  import { GödelOSAPI } from './utils/api.js';
  import { initializeMobileEnhancements } from './utils/mobile.js';
  
  // Core UI Components (keeping lightweight ones loaded immediately)
  // import CognitiveStateMonitor from './components/core/CognitiveStateMonitor.svelte'; // LAZY LOADED - 1,442 lines
  import QueryInterface from './components/core/QueryInterface.svelte';
  import ResponseDisplay from './components/core/ResponseDisplay.svelte';
  import HumanInteractionPanel from './components/core/HumanInteractionPanel.svelte';
  
  // Enhanced Metacognition Components
  // import StreamOfConsciousnessMonitor from './components/core/StreamOfConsciousnessMonitor.svelte'; // LAZY LOADED - 1,062 lines
  // import AutonomousLearningMonitor from './components/core/AutonomousLearningMonitor.svelte'; // LAZY LOADED - 1,447 lines
  import EnhancedCognitiveDashboard from './components/dashboard/EnhancedCognitiveDashboard.svelte';
  
  // Transparency Components (keeping lightweight ones loaded immediately)
  import ReflectionVisualization from './components/transparency/ReflectionVisualization.svelte';
  import ResourceAllocation from './components/transparency/ResourceAllocation.svelte';
  import ProcessInsight from './components/transparency/ProcessInsight.svelte';
  // import TransparencyDashboard from './components/transparency/TransparencyDashboard.svelte'; // LAZY LOADED - 2,011 lines
  // ReasoningSessionViewer removed — redundant with TransparencyPanel reasoning trace tab; called non-existent endpoints
  // ProvenanceTracker removed — called non-existent /api/transparency/provenance/* endpoints
  import TransparencyPanel from './components/transparency/TransparencyPanel.svelte';
  
  // Knowledge Management - LAZY LOADED to improve startup performance
  // import KnowledgeGraph from './components/knowledge/KnowledgeGraph.svelte'; // LAZY LOADED - 3,632 lines
  import ConceptEvolution from './components/knowledge/ConceptEvolution.svelte';
  // import SmartImport from './components/knowledge/SmartImport.svelte'; // LAZY LOADED - 2,468 lines
  
  // Evolution Tracking
  import CapabilityDashboard from './components/evolution/CapabilityDashboard.svelte';
  import ArchitectureTimeline from './components/evolution/ArchitectureTimeline.svelte';
  
  // UI Components
  import Modal from './components/ui/Modal.svelte';
  import ConnectionStatus from './components/ui/ConnectionStatus.svelte';
  
  let activeView = 'enhanced'; // Start with enhanced dashboard by default
  let websocketConnected = false;
  let sidebarCollapsed = false;
  let fullscreenMode = false;
  let pollInterval;
  let mobileEnhancer;
  let isMobileDevice = false;
  let systemHealthCollapsed = false;

  // Check URL parameters for direct view access
  onMount(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const viewParam = urlParams.get('view');
    if (viewParam && viewConfig[viewParam]) {
      activeView = viewParam;
      console.log(`🎯 Direct navigation to view: ${viewParam}`);
    }
    
    // Debug navigation sections
    console.log('🧭 Available view sections:', Object.keys(viewSections));
    console.log('🧭 Enhanced section views:', Object.keys(viewSections.enhanced?.views || {}));
    console.log('🧭 Total views available:', Object.keys(viewConfig).length);
  });
  
  // Modal state management
  let showProcessInsightModal = false;
  let showKnowledgeGraphModal = false;
  let showSmartImportModal = false;
  let showCapabilityDashboardModal = false;
  let showArchitectureTimelineModal = false;
  let showAdaptiveJobsModal = false;
  
  // New modal variables for lazy-loaded heavy components
  let showCognitiveStateModal = false;
  let showStreamMonitorModal = false;
  let showAutonomousLearningModal = false;
  let showTransparencyModal = false;
  let showConsciousnessModal = false;
  
  onMount(async () => {
    try {
      console.log('🚀 Initializing GödelOS cognitive interface...');
      
      // Detect mobile device first and set initial state
      isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
      
      // Initialize mobile enhancements first
      mobileEnhancer = initializeMobileEnhancements();
      
      // Set sidebar collapsed on mobile by default
      if (isMobileDevice) {
        sidebarCollapsed = true;
        console.log('📱 Mobile device detected - sidebar collapsed');
      }
      
      // Initialize enhanced cognitive features
      await initializeEnhancedCognitive();
      
      // Setup WebSocket connection (enhanced store will handle its own WebSocket)
      try {
        await setupWebSocket();
        websocketConnected = true;
        console.log('✅ Basic WebSocket connection established');
      } catch (error) {
        console.log('⚠️ Basic WebSocket unavailable, enhanced store will handle streaming');
        websocketConnected = false;
      }
      
      // Start real-time data polling as fallback with less aggressive interval
      try {
        pollInterval = await GödelOSAPI.pollForUpdates(handleDataUpdate, 30000); // Reduced from 5s to 30s
        console.log('✅ Background data polling started');
      } catch (error) {
        console.log('⚠️ Background polling unavailable');
      }

      // Initialize knowledge state from backend
      try {
        await apiHelpers.updateKnowledgeFromBackend();
        console.log('✅ Knowledge stats loaded from backend');
        
        // Set up periodic knowledge stats updates
        setInterval(() => {
          apiHelpers.updateKnowledgeFromBackend().catch(err => 
            console.warn('Knowledge stats update failed:', err)
          );
        }, 60000); // Update every minute
      } catch (error) {
        console.log('⚠️ Knowledge stats initialization failed:', error);
      }
      
      console.log('✅ GödelOS cognitive interface initialized');
    } catch (error) {
      console.warn('GödelOS initialization completed with warnings:', error);
      // Application should still be usable in fallback mode
    }
  });

  onDestroy(() => {
    // Clean up polling interval
    if (pollInterval) {
      clearInterval(pollInterval);
    }
    
    // Clean up enhanced cognitive systems
    try {
      enhancedCognitive.disableCognitiveStreaming();
    } catch (error) {
      // Ignore cleanup errors
    }
    
    console.log('🛑 GödelOS interface cleaned up');
  });

  function handleDataUpdate(data) {
    try {
      // Handle real-time data updates from WebSocket
      if (data.type === 'system_health') {
        systemHealth = data.data;
      } else if (data.type === 'cognitive_state') {
        // Update enhanced cognitive state if available
        if (typeof enhancedCognitive !== 'undefined') {
          enhancedCognitive.updateFromWebSocket(data.data);
        }
      }
      console.log('🔄 Data update processed:', data.type);
    } catch (error) {
      console.error('Error handling data update:', error, 'Data:', data);
    }
  }
  
  // Query event handlers
  function handleQuerySubmitted(event) {
    console.log('Query submitted:', event.detail);
    // Could add loading states or other UI updates here
  }
  
  function handleQueryResponse(event) {
    console.log('Query response received:', event.detail);
    // The ResponseDisplay component will handle displaying the response
    // We could add additional processing here if needed
  }
  
  // Enhanced view configuration with better UX organization
  const viewSections = {
    core: {
      title: 'Core Features',
      icon: '⭐',
      views: {
        dashboard: {
          icon: '🏠',
          title: 'Dashboard',
          description: 'System overview and key metrics',
          component: 'dashboard'
        },
        cognitive: {
          icon: '🧠',
          title: 'Cognitive State',
          description: 'Real-time cognitive processing monitor',
          modal: 'cognitive' // Use modal trigger instead of direct component
        },
        knowledge: {
          icon: '🕸️',
          title: 'Knowledge Graph',
          description: 'Interactive knowledge visualization',
          modal: 'knowledge' // Use modal trigger instead of direct component
        },
        query: {
          icon: '💬',
          title: 'Query Interface',
          description: 'Natural language interaction',
          component: QueryInterface
        },
        interaction: {
          icon: '🤝',
          title: 'Human Interaction',
          description: 'Human-system communication dashboard',
          component: HumanInteractionPanel,
          featured: true
        }
      }
    },
    enhanced: {
      title: 'Enhanced Cognition',
      icon: '🚀',
      badge: 'NEW',
      views: {
        enhanced: {
          icon: '🚀',
          title: 'Enhanced Dashboard',
          description: 'Unified cognitive enhancement overview',
          component: EnhancedCognitiveDashboard,
          featured: true
        },
        consciousness: {
          icon: '🧠',
          title: 'Unified Consciousness',
          description: 'Real-time consciousness state and emergence monitoring',
          modal: 'consciousness',
          featured: true,
          badge: 'BREAKTHROUGH'
        },
        stream: {
          icon: '🌊',
          title: 'Stream of Consciousness',
          description: 'Real-time cognitive event streaming',
          modal: 'stream', // Use modal trigger instead of direct component
          featured: true
        },
        autonomous: {
          icon: '🤖',
          title: 'Autonomous Learning',
          description: 'Self-directed knowledge acquisition',
          modal: 'autonomous', // Use modal trigger instead of direct component
          featured: true
        }
      }
    },
    analysis: {
      title: 'Analysis & Tools',
      icon: '🔬',
      views: {
        transparency: {
          icon: '🔍',
          title: 'Transparency',
          description: 'Cognitive transparency and reasoning insights',
          component: TransparencyPanel
        },
        reflection: {
          icon: '🪞',
          title: 'Reflection',
          description: 'System introspection and analysis',
          component: ReflectionVisualization
        }
      }
    },
    system: {
      title: 'System Management',
      icon: '⚙️',
      views: {
        jobs: {
          icon: '📥',
          title: 'Ingestion Jobs',
          description: 'Adaptive knowledge ingestion pipeline',
          modal: 'jobs',
          featured: true,
          badge: 'NEW'
        },
        import: {
          icon: '📁',
          title: 'Knowledge Import',
          description: 'Import and process documents',
          modal: 'import' // Use modal trigger instead of direct component
        },
        capabilities: {
          icon: '📈',
          title: 'Capabilities',
          description: 'System capabilities and evolution',
          component: CapabilityDashboard
        },
        resources: {
          icon: '⚡',
          title: 'Resources',
          description: 'Resource allocation and performance',
          component: ResourceAllocation
        }
      }
    }
  };

  // Flatten views for backward compatibility
  const viewConfig = {};
  Object.values(viewSections).forEach(section => {
    Object.assign(viewConfig, section.views);
  });

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
  }

  function toggleFullscreen() {
    fullscreenMode = !fullscreenMode;
    if (fullscreenMode) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
  }

  function toggleSystemHealth() {
    systemHealthCollapsed = !systemHealthCollapsed;
    console.log(`🔧 System health panel toggled: ${systemHealthCollapsed ? 'collapsed' : 'expanded'}`);
  }

  function getHealthColor(value) {
    if (value >= 0.8) return '#66bb6a';
    if (value >= 0.6) return '#ffa726';
    if (value >= 0.4) return '#ff7043';
    return '#ef5350';
  }
  
  async function initializeEnhancedCognitive() {
    try {
      console.log('🧠 Initializing enhanced cognitive features...');
      
      // Use the enhanced cognitive store initialization
      await enhancedCognitive.initializeEnhancedSystems();
      
      // Subscribe to enhanced cognitive state updates
      enhancedCognitive.subscribe(state => {
        if (state.systemHealth) {
          console.log('🧠 Enhanced cognitive system health updated');
        }
        if (state.autonomousLearning) {
          console.log('🧠 Autonomous learning state updated');
        }
      });
      
      console.log('✅ Enhanced cognitive features initialized');
      
    } catch (error) {
      console.warn('Enhanced cognitive initialization had issues:', error);
      // Enhanced cognitive store will handle fallback mode internally
    }
  }
</script>

<main class="godelos-interface" class:fullscreen={fullscreenMode} data-testid="app-container">
  <!-- Modern Header -->
  <header class="interface-header">
    <div class="header-content">
      <div class="header-left">
        <button class="sidebar-toggle" on:click={toggleSidebar}>
          <span class="toggle-icon">{sidebarCollapsed ? '▶️' : '◀️'}</span>
        </button>
        <h1 class="system-title">
          <span class="logo">🦉</span>
          <span class="title-text">GödelOS</span>
          <span class="subtitle">Cognitive Interface</span>
        </h1>
      </div>
      
      <div class="header-center">
        <div class="current-view-indicator">
          <span class="view-icon">{viewConfig[activeView]?.icon}</span>
          <div class="view-info">
            <div class="view-title">{viewConfig[activeView]?.title}</div>
            <div class="view-description">{viewConfig[activeView]?.description}</div>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <div class="health-chip" data-testid="system-health" title="System health score">
          {Math.round($systemHealthScore * 100)}%
        </div>
        <ConnectionStatus />
        <button class="fullscreen-toggle" on:click={toggleFullscreen}>
          <span>{fullscreenMode ? '🗗' : '⛶'}</span>
        </button>
      </div>
    </div>
  </header>

  <!-- Main application layout -->
  <div class="app-layout">
    <!-- Enhanced Sidebar Navigation -->
    <nav class="sidebar" class:collapsed={sidebarCollapsed} data-testid="sidebar-nav">
      {#if !sidebarCollapsed}
        <div class="sidebar-header">
          <h3>🧭 Navigation</h3>
          <span class="nav-count">{Object.keys(viewConfig).length} views available</span>
        </div>
      {/if}
      
      <div class="nav-sections">
        {#each Object.entries(viewSections) as [sectionKey, section]}
          <div class="nav-section" data-testid="nav-section-{sectionKey}">
            {#if !sidebarCollapsed}
              <div class="section-header">
                <span class="section-icon">{section.icon}</span>
                <span class="section-title">{section.title}</span>
                {#if section.badge}
                  <span class="section-badge">{section.badge}</span>
                {/if}
              </div>
            {/if}
            
            <div class="section-items">
              {#each Object.entries(section.views) as [key, config]}
                <button
                  class="nav-item {activeView === key ? 'active' : ''} {config.featured ? 'featured' : ''}"
                  data-testid="nav-item-{key}"
                  data-nav="{key}"
                  on:click={() => {
                    console.log(`🧭 Navigation clicked: ${key} -> ${config.title}`);
                    activeView = key;
                    console.log(`🧭 Active view updated to: ${activeView}`);
                  }}
                  title={config.description}
                >
                  <span class="nav-icon">{config.icon}</span>
                  {#if !sidebarCollapsed}
                    <div class="nav-content">
                      <span class="nav-title">{config.title}</span>
                      {#if config.featured}
                        <span class="featured-indicator">✨</span>
                      {/if}
                    </div>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        {/each}
      </div>
      
      {#if !sidebarCollapsed}
        <!-- System Status in Sidebar -->
        <div class="sidebar-status">
          <div class="status-section">
            <div class="status-header">
              <h4>System Health</h4>
              <button class="collapse-btn" on:click={toggleSystemHealth} title={systemHealthCollapsed ? 'Expand' : 'Collapse'}>
                {systemHealthCollapsed ? '▼' : '▲'}
              </button>
            </div>
            {#if !systemHealthCollapsed}
              <div class="health-overview">
                {#each Object.entries($cognitiveState.systemHealth) as [module, health]}
                  {#if typeof health === 'number' && !isNaN(health) && health >= 0 && health <= 1}
                    <div class="health-item">
                      <span class="module-name">{module}</span>
                      <div class="health-bar">
                        <div class="health-fill" style="width: {health * 100}%; background: {getHealthColor(health)}"></div>
                      </div>
                      <span class="health-value" style="color: {getHealthColor(health)}">{Math.round(health * 100)}%</span>
                    </div>
                  {/if}
                {/each}
                
                <!-- Enhanced Cognitive Health -->
                {#if $enhancedCognitiveState.systemHealth}
                  {#each Object.entries($enhancedCognitiveState.systemHealth) as [module, status]}
                    {#if typeof status === 'string' && ['healthy', 'degraded', 'critical', 'connected', 'disconnected'].includes(status)}
                      <div class="health-item enhanced">
                        <span class="module-name enhanced-module">{module}</span>
                        <div class="status-badge {status}">
                          {status}
                        </div>
                      </div>
                    {/if}
                  {/each}
                {/if}
              </div>
            {/if}
          </div>
          
          <div class="status-section">
            <h4>Knowledge Stats</h4>
            <div class="knowledge-stats">
              <div class="stat">
                <span class="stat-value">{$knowledgeState.totalConcepts}</span>
                <span class="stat-label">Concepts</span>
              </div>
              <div class="stat">
                <span class="stat-value">{$knowledgeState.totalConnections}</span>
                <span class="stat-label">Connections</span>
              </div>
              <div class="stat">
                <span class="stat-value">{$knowledgeState.totalDocuments}</span>
                <span class="stat-label">Documents</span>
              </div>
              
              <!-- Enhanced Learning Stats -->
              {#if $enhancedCognitiveState.autonomousLearning}
                <div class="stat enhanced">
                  <span class="stat-value">{$enhancedCognitiveState.autonomousLearning.detectedGaps?.length || 0}</span>
                  <span class="stat-label">Knowledge Gaps</span>
                </div>
                <div class="stat enhanced">
                  <span class="stat-value">{$enhancedCognitiveState.autonomousLearning.statistics?.totalAcquisitions || 0}</span>
                  <span class="stat-label">Acquisitions</span>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}
    </nav>

    <!-- Main Content Area -->
    <section class="main-content">
      {#if activeView === 'dashboard'}
        <!-- Enhanced Dashboard View -->
        <div class="dashboard-layout" data-testid="dashboard-view">
          <div class="dashboard-top">
            <div class="query-panel">
              <QueryInterface 
                on:query-submitted={handleQuerySubmitted}
                on:query-response={handleQueryResponse}
              />
            </div>
            <div class="response-panel">
              <ResponseDisplay />
            </div>
          </div>
          
          <div class="dashboard-middle">
            <div class="cognitive-panel">
              <div class="cognitive-placeholder">
                <h3>Cognitive State Monitor</h3>
                <button 
                  class="btn btn-primary"
                  on:click={() => showCognitiveStateModal = true}
                >
                  Open Cognitive Monitor
                </button>
                <p class="text-sm text-gray-600 mt-2">
                  Lazy-loaded for optimal performance
                </p>
              </div>
            </div>
            <div class="interaction-panel">
              <HumanInteractionPanel compactMode={true} />
            </div>
          </div>
          
          <div class="dashboard-bottom">
            <div class="evolution-panel">
              <ConceptEvolution />
            </div>
            <div class="insights-panel">
              <div class="panel-header">
                <h3>Process Insights</h3>
                <button class="expand-btn" on:click={() => showProcessInsightModal = true}>
                  Expand 🗗
                </button>
              </div>
              <div class="insights-preview">
                <ProcessInsight />
              </div>
            </div>
            
            <div class="knowledge-preview-panel">
              <div class="panel-header">
                <h3>Knowledge Graph</h3>
                <button class="expand-btn" on:click={() => activeView = 'knowledge'}>
                  Open Graph 🕸️
                </button>
              </div>
              <div class="knowledge-preview">
                <div class="graph-stats">
                  <div class="stat-item">
                    <span class="value">{$knowledgeState.totalConcepts}</span>
                    <span class="label">Concepts</span>
                  </div>
                  <div class="stat-item">
                    <span class="value">{$knowledgeState.totalConnections}</span>
                    <span class="label">Connections</span>
                  </div>
                  <div class="stat-item">
                    <span class="value">{$knowledgeState.totalVectors}</span>
                    <span class="label">Vectors</span>
                  </div>
                  <div class="stat-item">
                    <span class="value">{$knowledgeState.totalDocuments}</span>
                    <span class="label">Documents</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
      {:else if activeView === 'query'}
        <!-- Enhanced Query Interface -->
        <div class="expanded-view">
          <div class="query-layout">
            <div class="query-main">
              <QueryInterface 
                on:query-submitted={handleQuerySubmitted}
                on:query-response={handleQueryResponse}
              />
            </div>
            <div class="query-sidebar">
              <ResponseDisplay />
            </div>
          </div>
        </div>

      {:else if activeView === 'enhanced'}
        <!-- Enhanced Cognitive Dashboard -->
        <div class="enhanced-dashboard-wrapper" data-testid="enhanced-view">
          <EnhancedCognitiveDashboard />
        </div>
        
      {:else if viewConfig[activeView]?.modal}
        <!-- Modal-based Views -->
        <div class="expanded-view" data-testid="{activeView}-view">
          <div class="view-header">
            <h2>{viewConfig[activeView].title}</h2>
            <p class="view-description">{viewConfig[activeView].description}</p>
          </div>
          <div class="component-container">
            <button class="btn btn-primary" on:click={() => {
              if (viewConfig[activeView].modal === 'knowledge') {
                showKnowledgeGraphModal = true;
              } else if (viewConfig[activeView].modal === 'cognitive') {
                showCognitiveStateModal = true;
              } else if (viewConfig[activeView].modal === 'stream') {
                showStreamMonitorModal = true;
              } else if (viewConfig[activeView].modal === 'consciousness') {
                showConsciousnessModal = true;
              } else if (viewConfig[activeView].modal === 'autonomous') {
                showAutonomousLearningModal = true;
              } else if (viewConfig[activeView].modal === 'import') {
                showSmartImportModal = true;
              } else if (viewConfig[activeView].modal === 'jobs') {
                showAdaptiveJobsModal = true;
              }
            }}>
              {viewConfig[activeView].icon} Open {viewConfig[activeView].title}
            </button>
          </div>
        </div>
        
      {:else if viewConfig[activeView]?.component && typeof viewConfig[activeView].component !== 'string'}
        <!-- Standard Component Views -->
        <div class="expanded-view" data-testid="{activeView}-view">
          <div class="view-header">
            <h2>{viewConfig[activeView].title}</h2>
            <p class="view-description">{viewConfig[activeView].description}</p>
          </div>
          <div class="component-container">
            <svelte:component this={viewConfig[activeView].component} />
          </div>
        </div>
      {:else}
        <!-- Fallback for unmatched views -->
        <div class="expanded-view" data-testid="fallback-view">
          <div class="view-header">
            <h2>View Not Found</h2>
            <div class="debug-info" style="background: rgba(255,0,0,0.1); padding: 1rem; border-radius: 8px;">
              <p>⚠️ Debug: Could not render view "{activeView}"</p>
              <p>Component: {JSON.stringify(viewConfig[activeView]?.component)}</p>
              <p>Available views: {Object.keys(viewConfig).join(', ')}</p>
            </div>
          </div>
        </div>
      {/if}
    </section>
  </div>

  <!-- Alert notifications -->
  {#if $cognitiveState.alerts.length > 0}
    <div class="alert-overlay">
      {#each $cognitiveState.alerts as alert}
        <div class="alert alert-{alert.severity}">
          <span class="alert-icon">⚠️</span>
          <div class="alert-content">
            <div class="alert-title">{alert.title}</div>
            <div class="alert-message">{alert.message}</div>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Modal Components -->
  <Modal 
    bind:show={showProcessInsightModal} 
    title="Process Insights & Analysis"
    size="large"
    on:close={() => showProcessInsightModal = false}
  >
    <ProcessInsight />
  </Modal>

  <Modal 
    bind:show={showKnowledgeGraphModal} 
    title="Knowledge Graph Visualization"
    size="fullscreen"
    on:close={() => showKnowledgeGraphModal = false}
  >
    {#if showKnowledgeGraphModal}
      {#await import('./components/knowledge/KnowledgeGraph.svelte')}
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Knowledge Graph...</p>
        </div>
      {:then module}
        <svelte:component this={module.default} />
      {:catch error}
        <div class="error-container">
          <p>Failed to load Knowledge Graph: {error.message}</p>
        </div>
      {/await}
    {/if}
  </Modal>

  {#if showSmartImportModal}
    {#await import('./components/knowledge/SmartImport.svelte')}
      <div class="modal-backdrop">
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Smart Import...</p>
        </div>
      </div>
    {:then module}
      <svelte:component this={module.default} bind:show={showSmartImportModal} on:close={() => showSmartImportModal = false} />
    {:catch error}
      <div class="modal-backdrop">
        <div class="error-container">
          <p>Failed to load Smart Import: {error.message}</p>
        </div>
      </div>
    {/await}
  {/if}

  {#if showAdaptiveJobsModal}
    {#await import('./components/knowledge/AdaptiveJobsUI.svelte')}
      <div class="modal-backdrop">
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Adaptive Jobs UI...</p>
        </div>
      </div>
    {:then module}
      <Modal bind:show={showAdaptiveJobsModal} size="extra-large">
        <svelte:component this={module.default} />
      </Modal>
    {:catch error}
      <div class="modal-backdrop">
        <div class="error-container">
          <p>Failed to load Adaptive Jobs UI: {error.message}</p>
        </div>
      </div>
    {/await}
  {/if}

  <!-- New Lazy-loaded Modals -->
  <Modal 
    bind:show={showCognitiveStateModal} 
    title="Cognitive State Monitor"
    size="large"
    on:close={() => showCognitiveStateModal = false}
  >
    {#if showCognitiveStateModal}
      {#await import('./components/core/CognitiveStateMonitor.svelte')}
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Cognitive State Monitor...</p>
        </div>
      {:then module}
        <svelte:component this={module.default} />
      {:catch error}
        <div class="error-container">
          <p>Failed to load Cognitive State Monitor: {error.message}</p>
        </div>
      {/await}
    {/if}
  </Modal>

  <Modal 
    bind:show={showStreamMonitorModal} 
    title="Stream of Consciousness Monitor"
    size="large"
    on:close={() => showStreamMonitorModal = false}
  >
    {#if showStreamMonitorModal}
      {#await import('./components/core/StreamOfConsciousnessMonitor.svelte')}
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Stream Monitor...</p>
        </div>
      {:then module}
        <svelte:component this={module.default} />
      {:catch error}
        <div class="error-container">
          <p>Failed to load Stream Monitor: {error.message}</p>
        </div>
      {/await}
    {/if}
  </Modal>

  <Modal 
    bind:show={showAutonomousLearningModal} 
    title="Autonomous Learning Monitor"
    size="large"
    on:close={() => showAutonomousLearningModal = false}
  >
    {#if showAutonomousLearningModal}
      {#await import('./components/core/AutonomousLearningMonitor.svelte')}
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Autonomous Learning Monitor...</p>
        </div>
      {:then module}
        <svelte:component this={module.default} />
      {:catch error}
        <div class="error-container">
          <p>Failed to load Autonomous Learning Monitor: {error.message}</p>
        </div>
      {/await}
    {/if}
  </Modal>

  <Modal 
    bind:show={showTransparencyModal} 
    title="Transparency Dashboard"
    size="fullscreen"
    on:close={() => showTransparencyModal = false}
  >
    {#if showTransparencyModal}
      {#await import('./components/transparency/TransparencyDashboard.svelte')}
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Loading Transparency Dashboard...</p>
        </div>
      {:then module}
        <svelte:component this={module.default} />
      {:catch error}
        <div class="error-container">
          <p>Failed to load Transparency Dashboard: {error.message}</p>
        </div>
      {/await}
    {/if}
  </Modal>

  <Modal 
    bind:show={showConsciousnessModal} 
    title="🧠 Unified Consciousness Dashboard"
    size="fullscreen"
    on:close={() => showConsciousnessModal = false}
  >
    {#if showConsciousnessModal}
      {#await import('./components/UnifiedConsciousnessDashboard.svelte')}
        <div class="loading-container">
          <div class="loading-spinner"></div>
          <p>Initializing consciousness monitoring systems...</p>
          <p class="consciousness-loading-subtitle">🧠 Connecting to unified consciousness stream...</p>
        </div>
      {:then module}
        <svelte:component this={module.default} />
      {:catch error}
        <div class="error-container">
          <p>Failed to load Unified Consciousness Dashboard: {error.message}</p>
          <p>⚠️ Consciousness monitoring temporarily unavailable</p>
        </div>
      {/await}
    {/if}
  </Modal>

  <Modal 
    bind:show={showCapabilityDashboardModal} 
    title="Capability Dashboard"
    size="large"
    on:close={() => showCapabilityDashboardModal = false}
  >
    <CapabilityDashboard />
  </Modal>

  <Modal 
    bind:show={showArchitectureTimelineModal} 
    title="Architecture Timeline"
    size="large"
    on:close={() => showArchitectureTimelineModal = false}
  >
    <ArchitectureTimeline />
  </Modal>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    color: #e1e5e9;
    overflow: hidden;
  }

  :global(html) {
    /* CSS custom property for viewport height */
    --vh: 1vh;
  }

  :global(*) {
    box-sizing: border-box;
  }

  .godelos-interface {
    height: 100vh;
    height: calc(var(--vh, 1vh) * 100); /* Use CSS custom property for mobile */
    display: flex;
    flex-direction: column;
    background: transparent;
  }

  .godelos-interface.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 9999;
  }

  /* Enhanced Header */
  .interface-header {
    background: rgba(20, 25, 40, 0.95);
    border-bottom: 1px solid rgba(100, 120, 150, 0.2);
    backdrop-filter: blur(20px);
    z-index: 100;
    padding: 0.5rem 0;
    min-height: 60px;
    flex-shrink: 0;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2rem;
    max-width: none;
    margin: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .sidebar-toggle {
    background: rgba(100, 181, 246, 0.1);
    border: 1px solid rgba(100, 181, 246, 0.3);
    color: #64b5f6;
    padding: 0.5rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .sidebar-toggle:hover {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
  }

  .system-title {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #64b5f6;
  }

  .logo {
    font-size: 2rem;
  }

  .title-text {
    font-size: 1.5rem;
    font-weight: 700;
  }

  .subtitle {
    font-size: 0.9rem;
    opacity: 0.7;
    font-weight: 400;
  }

  .header-center {
    flex: 1;
    display: flex;
    justify-content: center;
  }

  .current-view-indicator {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(0, 0, 0, 0.3);
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    border: 1px solid rgba(100, 181, 246, 0.2);
  }

  .view-icon {
    font-size: 1.5rem;
  }

  .view-info {
    display: flex;
    flex-direction: column;
  }

  .view-title {
    font-weight: 600;
    color: #e1e5e9;
  }

  .view-description {
    font-size: 0.8rem;
    opacity: 0.7;
    margin: 0;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .health-chip {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    font-weight: 600;
    font-size: 0.9rem;
    min-width: 48px;
    text-align: center;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(100, 120, 150, 0.2);
  }

  .connection-status.connected {
    border-color: rgba(129, 199, 132, 0.4);
    background: rgba(129, 199, 132, 0.1);
  }

  .connection-status.disconnected {
    border-color: rgba(229, 115, 115, 0.4);
    background: rgba(229, 115, 115, 0.1);
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #f44336;
    animation: pulse 2s infinite;
  }

  .connection-status.connected .status-indicator {
    background: #4CAF50;
  }

  .status-text {
    font-size: 0.9rem;
    font-weight: 500;
  }

  .fullscreen-toggle {
    background: rgba(100, 181, 246, 0.1);
    border: 1px solid rgba(100, 181, 246, 0.3);
    color: #64b5f6;
    padding: 0.5rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .fullscreen-toggle:hover {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
  }

  /* Main Layout */
  .app-layout {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  /* Sidebar */
  .sidebar {
    width: 280px;
    background: rgba(15, 20, 35, 0.95);
    border-right: 1px solid rgba(100, 120, 150, 0.2);
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
    backdrop-filter: blur(10px);
    height: 100%;
    overflow: hidden;
  }

  .sidebar.collapsed {
    width: 70px;
  }

  .sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid rgba(100, 120, 150, 0.2);
    text-align: center;
  }

  .sidebar-header h3 {
    margin: 0 0 0.5rem 0;
    color: #64b5f6;
    font-size: 1.1rem;
  }

  .nav-count {
    font-size: 0.8rem;
    color: rgba(225, 229, 233, 0.7);
    background: rgba(100, 181, 246, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
  }

  .nav-sections {
    flex: 1;
    padding: 1rem 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(100, 181, 246, 0.3) transparent;
  }

  .nav-sections::-webkit-scrollbar {
    width: 6px;
  }

  .nav-sections::-webkit-scrollbar-track {
    background: transparent;
  }

  .nav-sections::-webkit-scrollbar-thumb {
    background: rgba(100, 181, 246, 0.3);
    border-radius: 3px;
  }

  .nav-sections::-webkit-scrollbar-thumb:hover {
    background: rgba(100, 181, 246, 0.5);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    color: #e1e5f9;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
    min-height: 60px;
  }

  .nav-item:hover {
    background: rgba(100, 181, 246, 0.1);
    border-color: rgba(100, 181, 246, 0.3);
  }

  .nav-item.active {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
    color: #64b5f6;
  }

  /* Navigation Sections */
  .nav-section {
    margin-bottom: 1rem;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    background: rgba(100, 181, 246, 0.05);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #64b5f6;
  }

  .section-icon {
    font-size: 1.1rem;
  }

  .section-title {
    flex: 1;
  }

  .section-badge {
    background: linear-gradient(135deg, #ff6b35, #f7931e);
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .section-items {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding-left: 0.5rem;
  }

  .nav-item.featured {
    background: linear-gradient(135deg, rgba(100, 181, 246, 0.1), rgba(156, 39, 176, 0.1));
    border: 1px solid rgba(100, 181, 246, 0.4);
    position: relative;
    overflow: hidden;
  }

  .nav-item.featured::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    transition: left 0.5s ease;
  }

  .nav-item.featured:hover::before {
    left: 100%;
  }

  .nav-item.featured:hover {
    background: linear-gradient(135deg, rgba(100, 181, 246, 0.2), rgba(156, 39, 176, 0.2));
    border-color: rgba(100, 181, 246, 0.6);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(100, 181, 246, 0.3);
  }

  .featured-indicator {
    font-size: 0.8rem;
    animation: sparkle 1.5s infinite;
  }

  @keyframes sparkle {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.2); }
  }

  .nav-icon {
    font-size: 1.5rem;
    min-width: 1.5rem;
  }

  .nav-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .nav-title {
    font-weight: 600;
    font-size: 1rem;
  }

  .sidebar-status {
    padding: 1rem;
    border-top: 1px solid rgba(100, 120, 150, 0.2);
  }

  .status-section {
    margin-bottom: 1.5rem;
  }

  .status-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }

  .status-section h4 {
    margin: 0;
    font-size: 0.9rem;
    color: #64b5f6;
    font-weight: 600;
  }

  .collapse-btn {
    background: rgba(100, 181, 246, 0.1);
    border: 1px solid rgba(100, 181, 246, 0.3);
    color: #64b5f6;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s ease;
  }

  .collapse-btn:hover {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
  }

  .health-overview {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .health-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
  }

  .module-name {
    flex: 1;
    min-width: 60px;
  }

  .health-bar {
    flex: 2;
    height: 4px;
    background: rgba(100, 181, 246, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .health-fill {
    height: 100%;
    background: linear-gradient(90deg, #f44336 0%, #ff9800 50%, #4CAF50 100%);
    transition: width 0.3s ease;
  }

  .health-value {
    min-width: 35px;
    text-align: right;
    font-weight: 500;
  }

  .knowledge-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }

  .stat {
    text-align: center;
    background: rgba(0, 0, 0, 0.3);
    padding: 0.5rem;
    border-radius: 6px;
  }

  .stat-value {
    display: block;
    font-size: 1.1rem;
    font-weight: 600;
    color: #64b5f6;
  }

  .stat-label {
    display: block;
    font-size: 0.7rem;
    opacity: 0.7;
    margin-top: 0.25rem;
  }

  /* Main Content */
  .main-content {
    flex: 1;
    padding: 0.75rem;
    overflow: hidden;
    background: rgba(10, 15, 25, 0.8);
    border-radius: 8px;
    margin: 0.25rem 0.5rem 0.5rem 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  /* Dashboard Layout */
  .dashboard-layout {
    display: grid;
    grid-template-rows: minmax(180px, auto) 1fr minmax(200px, auto);
    gap: 1.5rem;
    height: 100%;
    overflow: hidden;
  }

  .dashboard-top {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    min-height: 180px;
  }

  .dashboard-middle {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    min-height: 200px;
  }

  .dashboard-bottom {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    min-height: 200px;
  }

  .query-panel, .response-panel, .cognitive-panel, .evolution-panel,
  .insights-panel, .knowledge-preview-panel, .interaction-panel {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 16px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(10px);
    min-height: 0;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
  }

  .panel-header h3 {
    margin: 0;
    color: #64b5f6;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .expand-btn {
    background: rgba(100, 181, 246, 0.1);
    border: 1px solid rgba(100, 181, 246, 0.3);
    color: #64b5f6;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
  }

  .expand-btn:hover {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
  }

  /* Expanded Views */
  .expanded-view {
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  .view-header {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
  }

  .view-header h2 {
    margin: 0 0 0.5rem 0;
    color: #64b5f6;
    font-size: 1.8rem;
    font-weight: 700;
  }

  .component-container {
    flex: 1;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    overflow: auto;
    min-height: 0;
    max-height: 100%;
  }

  .enhanced-dashboard-wrapper {
    width: 100%;
    min-height: 100vh;
    padding: 0;
    margin: 0;
    overflow: hidden;
  }

  .query-layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
    height: 100%;
    min-height: 0;
  }

  .query-main, .query-sidebar {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    overflow: auto;
    min-height: 0;
    max-height: 100%;
  }

  /* Knowledge Preview */
  .graph-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 1rem;
  }

  .stat-item {
    text-align: center;
    background: rgba(0, 0, 0, 0.3);
    padding: 1rem;
    border-radius: 10px;
  }

  .stat-item .value {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: #64b5f6;
    margin-bottom: 0.25rem;
  }

  .stat-item .label {
    font-size: 0.9rem;
    opacity: 0.7;
  }

  /* Alert overlay */
  .alert-overlay {
    position: fixed;
    top: 100px;
    right: 2rem;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .alert {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
    background: rgba(20, 25, 40, 0.95);
    border-radius: 8px;
    border-left: 4px solid;
    backdrop-filter: blur(20px);
    max-width: 400px;
    animation: slideIn 0.3s ease;
  }

  .alert-warning {
    border-left-color: #ffa726;
  }

  .alert-error {
    border-left-color: #ef5350;
  }

  .alert-info {
    border-left-color: #64b5f6;
  }

  .alert-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
  }

  .alert-title {
    font-weight: 600;
    color: #e1e5e9;
    margin-bottom: 0.25rem;
  }

  .alert-message {
    font-size: 0.9rem;
    color: #a0a9b8;
  }

  /* Insights and Knowledge Preview Content */
  .insights-preview, .knowledge-preview {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: hidden;
  }

  .insights-preview {
    background: rgba(100, 181, 246, 0.05);
    border-radius: 12px;
    padding: 1rem;
    border: 1px dashed rgba(100, 181, 246, 0.2);
  }

  /* Empty state styling */
  .insights-preview:empty::before {
    content: "💭 Process insights will appear here when system is processing...";
    color: rgba(225, 229, 233, 0.6);
    font-style: italic;
    text-align: center;
    display: block;
    padding: 2rem;
  }

  /* Animations */
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes fadeInContent {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Loading and transition effects */
  .nav-item, .expand-btn, .sidebar-toggle, .fullscreen-toggle {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .dashboard-layout, .expanded-view, .query-layout {
    opacity: 0;
    animation: fadeInContent 0.3s ease forwards;
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .dashboard-top, .dashboard-middle, .dashboard-bottom {
      grid-template-columns: 1fr;
      gap: 1rem;
    }
    
    .dashboard-layout {
      gap: 1rem;
    }
    
    .query-layout {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr 1fr;
      gap: 1rem;
    }

    .main-content {
      padding: 0.5rem;
    }
  }

  /* Enhanced Mobile Styles */
  @media (max-width: 768px) {
    .godelos-interface {
      /* Enable smooth scrolling for mobile */
      scroll-behavior: smooth;
      overflow-x: hidden;
    }

    /* Mobile sidebar - full screen overlay when open */
    .sidebar {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      z-index: 200;
      /* Mobile overlay background */
      background: rgba(15, 20, 35, 0.98);
      backdrop-filter: blur(20px);
      /* Smooth slide animation */
      transform: translateX(0);
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .sidebar.collapsed {
      /* Hide sidebar completely off-screen */
      transform: translateX(-100%);
      pointer-events: none;
    }

    /* Ensure sidebar content is properly scrollable on mobile */
    .nav-sections {
      max-height: calc(100vh - 200px); /* Account for header and status */
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
    }
    
    /* Mobile-optimized header */
    .interface-header {
      padding: 0.25rem 0;
      min-height: 56px; /* Standard mobile header height */
      position: sticky;
      top: 0;
      z-index: 150;
    }
    
    .header-content {
      padding: 0 1rem;
      gap: 0.5rem;
    }
    
    .header-left {
      gap: 0.5rem;
    }

    .system-title {
      font-size: 1.2rem;
      gap: 0.5rem;
    }

    .logo {
      font-size: 1.5rem;
    }

    .subtitle {
      display: none; /* Hide subtitle on mobile to save space */
    }
    
    /* Hide view indicator on mobile to save space */
    .header-center {
      display: none;
    }
    
    /* Improved mobile navigation */
    .nav-sections {
      padding: 0.5rem;
      gap: 0.25rem;
    }

    .nav-item {
      padding: 1rem 0.75rem;
      min-height: 48px; /* Touch-friendly minimum height */
      border-radius: 8px;
      /* Add larger touch target */
      touch-action: manipulation;
      -webkit-tap-highlight-color: rgba(100, 181, 246, 0.2);
    }

    .nav-item:active {
      transform: scale(0.98);
      background: rgba(100, 181, 246, 0.3);
    }

    .section-header {
      padding: 0.5rem 0.75rem;
      font-size: 0.85rem;
    }

    .section-items {
      padding-left: 0.25rem;
    }
    
    /* Mobile-optimized main content */
    .main-content {
      padding: 0.5rem;
      margin: 0;
      border-radius: 0;
      /* Enable momentum scrolling on iOS */
      -webkit-overflow-scrolling: touch;
      overflow-y: auto;
      width: 100%;
    }

    /* Fix dashboard layout for mobile - single column */
    .dashboard-layout {
      gap: 0.75rem;
      /* Optimize for vertical scrolling on mobile */
      display: flex;
      flex-direction: column;
      height: auto;
      overflow: visible;
    }

    .dashboard-top, .dashboard-middle, .dashboard-bottom {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      width: 100%;
    }
    
    .query-panel, .response-panel, .cognitive-panel, .evolution-panel,
    .insights-panel, .knowledge-preview-panel, .interaction-panel {
      padding: 0.75rem;
      border-radius: 12px;
      /* Ensure touch-friendly interaction */
      touch-action: manipulation;
      width: 100%;
      box-sizing: border-box;
    }

    .panel-header {
      margin-bottom: 0.75rem;
      padding-bottom: 0.5rem;
    }

    .panel-header h3 {
      font-size: 1rem;
    }

    .expand-btn {
      padding: 0.5rem 0.75rem;
      font-size: 0.85rem;
      border-radius: 6px;
      /* Touch-friendly button */
      min-height: 44px; /* iOS recommended touch target size */
      min-width: 44px;
    }

    /* Mobile-specific component container optimization */
    .component-container {
      padding: 1rem;
      border-radius: 12px;
      /* Enable smooth scrolling within components */
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
    }

    /* Query layout mobile optimization */
    .query-layout {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      height: auto;
    }

    .query-main, .query-sidebar {
      width: 100%;
    }

    /* Optimize buttons for touch */
    button, .nav-item, .expand-btn, .sidebar-toggle, .fullscreen-toggle {
      min-height: 44px; /* iOS recommended touch target size */
      /* Improve touch responsiveness */
      touch-action: manipulation;
      -webkit-tap-highlight-color: rgba(100, 181, 246, 0.2);
    }

    button:active, .nav-item:active {
      transform: scale(0.96);
      transition: transform 0.1s ease;
    }

    /* Mobile-specific sidebar status optimization */
    .sidebar-status {
      padding: 0.75rem;
    }

    .status-section {
      margin-bottom: 1rem;
    }

    .knowledge-stats {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.5rem;
    }

    .stat {
      padding: 0.5rem 0.25rem;
    }

    .stat-value {
      font-size: 1rem;
    }

    .stat-label {
      font-size: 0.65rem;
    }

    /* Alert optimization for mobile */
    .alert-overlay {
      top: 60px;
      right: 0.5rem;
      left: 0.5rem;
      max-width: none;
    }

    .alert {
      margin-bottom: 0.5rem;
      padding: 0.75rem;
    }
  }

  /* Ultra-small mobile screens */
  @media (max-width: 480px) {
    .header-content {
      padding: 0 0.5rem;
    }

    .system-title {
      font-size: 1.1rem;
    }

    .main-content {
      padding: 0.25rem;
    }

    .query-panel, .response-panel, .cognitive-panel, .evolution-panel,
    .insights-panel, .knowledge-preview-panel, .interaction-panel {
      padding: 0.5rem;
    }

    .knowledge-stats {
      grid-template-columns: 1fr;
      gap: 0.5rem;
    }

    .dashboard-layout {
      gap: 0.5rem;
    }

    /* Smaller text for ultra-small screens */
    .nav-title {
      font-size: 0.9rem;
    }

    .section-header {
      font-size: 0.8rem;
      padding: 0.4rem 0.5rem;
    }
  }

  /* Touch device optimizations */
  @media (hover: none) and (pointer: coarse) {
    .nav-item:hover {
      /* Remove hover effects on touch devices */
      background: transparent;
      border-color: transparent;
    }

    .nav-item:hover::before {
      /* Disable shimmer effect on touch */
      left: -100%;
    }

    .expand-btn:hover,
    .sidebar-toggle:hover,
    .fullscreen-toggle:hover {
      /* Simplify hover states for touch */
      background: rgba(100, 181, 246, 0.1);
    }

    /* Add better touch feedback */
    .nav-item:active,
    .expand-btn:active,
    button:active {
      background: rgba(100, 181, 246, 0.3);
      transform: scale(0.95);
    }

    /* Touch-specific active states */
    .touch-active {
      background: rgba(100, 181, 246, 0.25) !important;
      transform: scale(0.96) !important;
      transition: all 0.1s ease !important;
    }

    /* Larger touch targets for interactive elements */
    .nav-item, button, .expand-btn {
      min-height: 48px;
      padding: 0.75rem 1rem;
    }

    /* Improve touch scrolling performance */
    .nav-sections,
    .main-content,
    .component-container {
      -webkit-overflow-scrolling: touch;
      overscroll-behavior: contain;
    }
  }

  /* Touch-friendly utility classes */
  .touch-friendly {
    min-width: 44px;
    min-height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    touch-action: manipulation;
    -webkit-tap-highlight-color: rgba(100, 181, 246, 0.2);
  }

  /* Mobile device specific styles */
  :global(body.mobile-device) {
    /* Improve mobile performance */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  :global(body.mobile-device .sidebar) {
    /* Ensure mobile sidebar is properly layered */
    z-index: 1000;
  }

  :global(body.mobile-device .sidebar.collapsed) {
    /* Completely hide collapsed sidebar on mobile */
    visibility: hidden;
  }

  :global(body.mobile-device .sidebar:not(.collapsed)) {
    /* Show mobile sidebar overlay */
    visibility: visible;
  }

  /* Network status indicators */
  body.offline .connection-status {
    border-color: rgba(255, 152, 0, 0.6) !important;
    background: rgba(255, 152, 0, 0.1) !important;
  }

  body.offline .connection-status .status-indicator {
    background: #ff9800 !important;
  }

  body.slow-connection::before {
    content: "Slow connection detected";
    position: fixed;
    top: 70px;
    right: 1rem;
    background: rgba(255, 152, 0, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.8rem;
    z-index: 1001;
  }

  /* High DPI mobile screens */
  @media (-webkit-min-device-pixel-ratio: 2) and (max-width: 768px) {
    .interface-header {
      /* Optimize for high DPI mobile screens */
      border-bottom: 0.5px solid rgba(100, 120, 150, 0.2);
    }

    .nav-item {
      border-width: 0.5px;
    }

    .query-panel, .response-panel, .cognitive-panel, .evolution-panel,
    .insights-panel, .knowledge-preview-panel {
      border-width: 0.5px;
    }
  }

  /* Enhanced Cognitive Features Styling */
  
  /* Enhanced connection indicator */
  .status-indicator.enhanced-connected {
    background: linear-gradient(45deg, #4caf50, #8bc34a);
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
    animation: enhanced-pulse 2s infinite;
  }

  @keyframes enhanced-pulse {
    0%, 100% { 
      box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
    }
    50% { 
      box-shadow: 0 0 16px rgba(76, 175, 80, 0.7);
    }
  }

  .fallback-indicator {
    margin-left: 0.5rem;
    opacity: 0.8;
    font-size: 0.8rem;
    animation: fallback-blink 3s infinite;
  }

  @keyframes fallback-blink {
    0%, 90%, 100% { opacity: 0.8; }
    95% { opacity: 0.3; }
  }

  /* Enhanced health items */
  .health-item.enhanced {
    background: rgba(76, 175, 80, 0.05);
    border: 1px solid rgba(76, 175, 80, 0.1);
    border-radius: 6px;
    padding: 0.5rem;
    margin: 0.25rem 0;
  }

  .enhanced-module {
    color: #8bc34a !important;
    font-weight: 500;
  }

  .status-badge {
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .status-badge.healthy {
    background: rgba(76, 175, 80, 0.2);
    color: #4caf50;
  }

  .status-badge.degraded {
    background: rgba(255, 193, 7, 0.2);
    color: #ffc107;
  }

  .status-badge.critical {
    background: rgba(244, 67, 54, 0.2);
    color: #f44336;
  }

  .status-badge.connected {
    background: rgba(76, 175, 80, 0.2);
    color: #4caf50;
  }

  .status-badge.disconnected {
    background: rgba(158, 158, 158, 0.2);
    color: #9e9e9e;
  }

  /* Enhanced stats */
  .stat.enhanced {
    background: rgba(76, 175, 80, 0.05);
    border: 1px solid rgba(76, 175, 80, 0.1);
    border-radius: 6px;
    position: relative;
    overflow: hidden;
  }

  .stat.enhanced::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #4caf50, #8bc34a);
  }

  .stat.enhanced .stat-label {
    color: #8bc34a;
  }

  /* Enhanced view indicators */
  .nav-item.featured {
    position: relative;
    background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(139, 195, 74, 0.1));
    border: 1px solid rgba(76, 175, 80, 0.2);
  }

  .nav-item.featured::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #4caf50, #8bc34a);
  }

  .featured-indicator {
    font-size: 0.8rem;
    margin-left: 0.25rem;
    animation: sparkle 2s infinite;
  }

  @keyframes sparkle {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
  }

  /* Enhanced section badges */
  .section-badge {
    background: linear-gradient(45deg, #4caf50, #8bc34a);
    color: white;
    padding: 0.1rem 0.4rem;
    border-radius: 8px;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-left: auto;
    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
  }

  /* Connection status improvements */
  .connection-status {
    transition: all 0.3s ease;
  }

  .connection-status.connected .status-indicator {
    background: #4caf50;
  }

  .connection-status.disconnected .status-indicator {
    background: #9e9e9e;
  }

  /* Enhanced responsive adjustments */
  @media (max-width: 768px) {
    .fallback-indicator {
      display: none; /* Hide on mobile to save space */
    }
    
    .status-badge {
      font-size: 0.6rem;
      padding: 0.15rem 0.4rem;
    }
    
    .enhanced-module {
      font-size: 0.8rem;
    }
  }

  /* Loading states for lazy-loaded components */
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    min-height: 200px;
    color: var(--text-primary);
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border-color);
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error-container {
    padding: 2rem;
    text-align: center;
    color: var(--error-color, #ff6b6b);
    background: rgba(255, 107, 107, 0.1);
    border-radius: 8px;
    margin: 1rem;
  }

  /* Consciousness-specific styles */
  .consciousness-loading-subtitle {
    font-size: 0.9rem;
    color: #00d4ff;
    margin-top: 0.5rem;
    animation: consciousness-pulse 2s infinite;
  }

  @keyframes consciousness-pulse {
    0%, 100% { opacity: 1; color: #00d4ff; }
    50% { opacity: 0.7; color: #7b2cbf; }
  }

  /* Consciousness navigation item styling */
  .nav-item[data-view="consciousness"] {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(123, 44, 191, 0.1));
    border: 1px solid rgba(0, 212, 255, 0.3);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.2);
  }

  .nav-item[data-view="consciousness"]:hover {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(123, 44, 191, 0.2));
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
    transform: translateY(-2px);
  }

  .nav-item[data-view="consciousness"] .badge {
    background: linear-gradient(45deg, #ff006e, #7b2cbf);
    color: white;
    animation: breakthrough-glow 2s infinite;
  }

  @keyframes breakthrough-glow {
    0%, 100% { box-shadow: 0 0 10px rgba(255, 0, 110, 0.5); }
    50% { box-shadow: 0 0 20px rgba(255, 0, 110, 0.8); }
  }
</style>
