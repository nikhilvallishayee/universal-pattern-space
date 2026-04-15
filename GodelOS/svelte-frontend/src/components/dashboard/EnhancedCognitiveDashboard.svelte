<script>
    import { onMount, onDestroy } from 'svelte';
    import { enhancedCognitiveState, autonomousLearningState, streamState, enhancedCognitive } from '../../stores/enhanced-cognitive.js';
    import { cognitiveState, healthHelpers } from '../../stores/cognitive.js';
    
    // Import monitoring components
    import StreamOfConsciousnessMonitor from '../core/StreamOfConsciousnessMonitor.svelte';
    import AutonomousLearningMonitor from '../core/AutonomousLearningMonitor.svelte';
    import CognitiveStateMonitor from '../core/CognitiveStateMonitor.svelte';
    
    // Component props
    export let layout = 'grid'; // 'grid', 'tabs', 'accordion'
    export let compactMode = false;
    export let showHealth = true;
    export let autoRefresh = true;

    // Local state
    let cognitiveStateData = null;
    let systemHealth = null;
    let healthProbes = null;
    let probesError = '';
    let activeTab = 'overview';
    let isConnected = false;
    let lastUpdate = null;
    let isLoading = true;
    let selectedProbe = null;  // For probe detail modal
    let showProbeModal = false;

    // Subscriptions
    let unsubscribe;

    import { API_BASE_URL } from '../../config.js';
    import { GödelOSAPI } from '../../utils/api.js';

    // State for vector DB management
    let vectorDbStats = null;
    let clearingVectorDb = false;
    let showClearConfirm = false;

    function fmtBool(v) { return typeof v === 'boolean' ? (v ? 'true' : 'false') : String(v); }
    function fmtTS(ts) {
        try {
            if (!ts) return '';
            const d = new Date(ts > 10_000_000_000 ? ts : ts * 1000);
            return d.toLocaleTimeString();
        } catch { return String(ts); }
    }

    async function fetchHealthProbes() {
        try {
            const res = await fetch(`${API_BASE_URL}/api/health`, { signal: AbortSignal.timeout(6000) });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            healthProbes = data?.probes || null;
            probesError = '';
        } catch (e) {
            probesError = String(e?.message || e);
            healthProbes = null;
        }
    }

    function getProbeStatusColor(probe) {
        const status = probe?.status || 'unknown';
        switch (status) {
            case 'healthy': return 'emerald';
            case 'warning': return 'amber';
            case 'error': case 'unavailable': return 'red';
            default: return 'gray';
        }
    }

    function openProbeModal(probeName, probeData) {
        selectedProbe = { name: probeName, data: probeData };
        showProbeModal = true;
    }

    function closeProbeModal() {
        showProbeModal = false;
        selectedProbe = null;
    }

    // Health badge logic - accepts both _labels and numeric health data
    function getHealthStatus() {
        if (!systemHealth) return { status: 'unknown', color: 'gray', score: 0 };
        
        // Check if we have _labels from canonical format
        if (systemHealth._labels) {
            const labels = systemHealth._labels;
            const healthyCount = Object.values(labels).filter(label => label === 'healthy').length;
            const totalCount = Object.keys(labels).length;
            const score = totalCount > 0 ? (healthyCount / totalCount) * 100 : 0;
            
            if (healthyCount === totalCount) return { status: 'excellent', color: 'emerald', score };
            if (score >= 75) return { status: 'good', color: 'amber', score };
            if (score >= 50) return { status: 'degraded', color: 'orange', score };
            return { status: 'critical', color: 'red', score };
        }
        
        // Fallback: derive from numeric values or legacy labels
        const components = [
            systemHealth?.inferenceEngine,
            systemHealth?.knowledgeStore,
            systemHealth?.autonomousLearning,
            systemHealth?.cognitiveStreaming
        ];
        
        const healthy = components.filter(c => c === 'healthy').length;
        const total = components.length;
        const score = total > 0 ? (healthy / total) * 100 : 0;
        
        if (healthy === total) return { status: 'excellent', color: 'emerald', score };
        if (healthy >= total * 0.75) return { status: 'good', color: 'amber', score };
        if (healthy >= total * 0.5) return { status: 'degraded', color: 'orange', score };
        return { status: 'critical', color: 'red', score };
    }

    // Get health status for a specific component
    function getComponentHealth(componentKey) {
        if (!systemHealth) return 'unknown';
        
        // Check _labels first (canonical format)
        if (systemHealth._labels && systemHealth._labels[componentKey]) {
            return systemHealth._labels[componentKey];
        }
        
        // Fallback to direct value
        const value = systemHealth[componentKey];
        if (typeof value === 'string') return value;
        if (typeof value === 'number') return healthHelpers.scoreToLabel(value);
        
        return 'unknown';
    }

    // Vector Database action handlers
    async function refreshVectorStats() {
        try {
            vectorDbStats = await GödelOSAPI.getVectorDbStats();
            // Also refresh the health probes to get latest data
            await fetchHealthProbes();
        } catch (error) {
            console.error('Failed to refresh vector stats:', error);
        }
    }

    function confirmClearVectorDb() {
        showClearConfirm = true;
    }

    async function clearVectorDb() {
        if (clearingVectorDb) return; // Prevent double-clicks
        
        clearingVectorDb = true;
        try {
            const result = await GödelOSAPI.clearVectorDb();
            console.log('Vector DB cleared:', result);
            
            // Refresh stats and health after clearing
            await refreshVectorStats();
            showClearConfirm = false;
            
            // Optionally show a success notification
            alert('Vector database cleared successfully!');
        } catch (error) {
            console.error('Failed to clear vector DB:', error);
            alert(`Failed to clear vector database: ${error.message}`);
        } finally {
            clearingVectorDb = false;
        }
    }

    function cancelClearVectorDb() {
        showClearConfirm = false;
    }

    onMount(() => {
        // Subscribe to both enhanced and canonical cognitive state
        unsubscribe = cognitiveState.subscribe(state => {
            cognitiveStateData = state;
            systemHealth = state.systemHealth;
            isConnected = state.systemHealth?.websocketConnection > 0 || false;
            lastUpdate = new Date();
            isLoading = false;
        });

        // Initialize enhanced cognitive systems - REMOVED to prevent duplicate initialization
        // (App.svelte already handles initialization)
        
        // Start automatic data fetching
        startAutoRefresh();
        fetchHealthProbes();
        
        // Initialize vector database stats
        refreshVectorStats();
        
        // Provide fallback system health if not available after 3 seconds
        setTimeout(() => {
            if (!systemHealth) {
                systemHealth = {
                    websocketConnection: 0.8,
                    pipeline: 0.9, 
                    knowledgeStore: 0.85,
                    vectorIndex: 0.7,
                    _labels: {
                        websocketConnection: 'healthy',
                        pipeline: 'healthy',
                        knowledgeStore: 'healthy',
                        vectorIndex: 'healthy'
                    }
                };
            }
        }, 3000);
    });
    
    function startAutoRefresh() {
        console.log('� Dashboard auto-refresh enabled');
        
        // Initial fetch
        refreshAllSystems();
        
        // Enable periodic refresh
        if (autoRefresh) {
            const interval = setInterval(() => {
                if (autoRefresh) {
                    refreshAllSystems();
                }
            }, 30000); // 30 second intervals
            
            // Store interval ID for cleanup
            return () => clearInterval(interval);
        }
    }

    onDestroy(() => {
        if (unsubscribe) unsubscribe();
    });

    function formatUptime(seconds) {
        if (!seconds || isNaN(seconds)) return null; // Return null so we can handle fallback in template
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }

    function refreshAllSystems() {
        isLoading = true;
        
        // Call all the enhanced cognitive store update methods
        enhancedCognitive.refreshSystemHealth();
        enhancedCognitive.refreshAutonomousState();
        enhancedCognitive.refreshStreamingState();
        
        // Also manually call the update methods
        enhancedCognitive.updateHealthStatus();
        enhancedCognitive.updateAutonomousLearningState();
        enhancedCognitive.updateStreamingStatus();
        fetchHealthProbes();
        setTimeout(() => isLoading = false, 1000);
    }

    $: healthStatus = getHealthStatus();
</script>

<main class="modern-dashboard">
    <!-- Hero Header with Gradient Background -->
    <header class="dashboard-hero">
        <div class="hero-content">
            <div class="hero-title-section">
                <div class="title-icon">🧠</div>
                <div class="title-text">
                    <h1 class="hero-title">GödelOS Cognitive Dashboard</h1>
                    <p class="hero-subtitle">Real-time consciousness monitoring and enhanced cognitive analytics</p>
                </div>
            </div>
            <div class="hero-stats">
                <div class="stat-card" class:pulse={isConnected}>
                    <div class="stat-icon">🌐</div>
                    <div class="stat-content">
                        <div class="stat-value">{isConnected ? 'Connected' : 'Offline'}</div>
                        <div class="stat-label">WebSocket Status</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">💚</div>
                    <div class="stat-content">
                        <div class="stat-value">{healthStatus.score.toFixed(0)}%</div>
                        <div class="stat-label">System Health</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-content">
                        <div class="stat-value">{formatUptime(systemHealth?.uptime) || 'Starting...'}</div>
                        <div class="stat-label">Uptime</div>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Dashboard Grid -->
    <section class="dashboard-grid">
        <!-- Cognitive Monitors Row -->
        <div class="monitor-grid">
            <div class="monitor-card stream-monitor">
                <div class="card-header">
                    <h3 class="card-title">🌊 Stream of Consciousness</h3>
                    <div class="card-badge">Live</div>
                </div>
                <div class="card-content">
                    <StreamOfConsciousnessMonitor {compactMode} showFilters={true} formatJson={false} />
                </div>
            </div>

            <div class="monitor-card learning-monitor">
                <div class="card-header">
                    <h3 class="card-title">🎯 Autonomous Learning</h3>
                    <div class="card-badge learning">Active</div>
                </div>
                <div class="card-content">
                    <AutonomousLearningMonitor {compactMode} showDetails={true} />
                </div>
            </div>

            <div class="monitor-card state-monitor">
                <div class="card-header">
                    <h3 class="card-title">⚡ Cognitive State</h3>
                    <div class="card-badge state">Monitoring</div>
                </div>
                <div class="card-content">
                    <CognitiveStateMonitor {compactMode} />
                </div>
            </div>
        </div>

        <!-- System Health Section -->
        <div class="health-section">
            <div class="section-header">
                <h2 class="section-title">🏥 System Health Overview</h2>
                <button class="refresh-btn" on:click={refreshAllSystems} disabled={isLoading}>
                    <span class="refresh-icon" class:spinning={isLoading}>🔄</span>
                    Refresh
                </button>
            </div>
            
            <div class="health-grid">
                <div class="health-card websocket" class:healthy={getComponentHealth('websocketConnection') === 'healthy'}>
                    <div class="health-icon">🔌</div>
                    <div class="health-info">
                        <h4>WebSocket Connection</h4>
                        <div class="health-status">{getComponentHealth('websocketConnection')}</div>
                    </div>
                    <div class="health-indicator" class:active={getComponentHealth('websocketConnection') === 'healthy'}></div>
                </div>

                <div class="health-card pipeline" class:healthy={getComponentHealth('pipeline') === 'healthy'}>
                    <div class="health-icon">⚙️</div>
                    <div class="health-info">
                        <h4>Processing Pipeline</h4>
                        <div class="health-status">{getComponentHealth('pipeline')}</div>
                    </div>
                    <div class="health-indicator" class:active={getComponentHealth('pipeline') === 'healthy'}></div>
                </div>

                <div class="health-card knowledge" class:healthy={getComponentHealth('knowledgeStore') === 'healthy'}>
                    <div class="health-icon">📚</div>
                    <div class="health-info">
                        <h4>Knowledge Store</h4>
                        <div class="health-status">{getComponentHealth('knowledgeStore')}</div>
                    </div>
                    <div class="health-indicator" class:active={getComponentHealth('knowledgeStore') === 'healthy'}></div>
                </div>

                <div class="health-card vector" class:healthy={getComponentHealth('vectorIndex') === 'healthy'}>
                    <div class="health-icon">🧮</div>
                    <div class="health-info">
                        <h4>Vector Index</h4>
                        <div class="health-status">{getComponentHealth('vectorIndex')}</div>
                    </div>
                    <div class="health-indicator" class:active={getComponentHealth('vectorIndex') === 'healthy'}></div>
                </div>
            </div>
        </div>

        <!-- System Probes Section -->
        {#if showHealth && healthProbes}
            <div class="probes-section">
                <div class="section-header">
                    <h2 class="section-title">🔍 System Probes</h2>
                    <div class="probe-stats">
                        {Object.keys(healthProbes).length} probes active
                    </div>
                </div>
                
                <div class="probes-grid">
                    {#each Object.entries(healthProbes) as [probeName, probeData]}
                        <div class="probe-card" 
                             class:clickable={true}
                             class:healthy={probeData?.status === 'healthy'}
                             class:warning={probeData?.status === 'warning'}
                             class:error={probeData?.status === 'error'}
                             class:vector-db-card={probeName === 'vector_database'}
                             on:click={() => openProbeModal(probeName, probeData)}
                             on:keydown={(e) => e.key === 'Enter' && openProbeModal(probeName, probeData)}
                             tabindex="0"
                             role="button">
                            <div class="probe-header">
                                <h4 class="probe-name">
                                    {probeName === 'vector_database' ? '🧮 Vector Database' : probeName}
                                </h4>
                                <div class="probe-status status-{getProbeStatusColor(probeData)}">
                                    <div class="status-dot"></div>
                                    <span>{probeData?.status || 'unknown'}</span>
                                </div>
                            </div>
                            <div class="probe-details">
                                {#if probeName === 'vector_database'}
                                    <!-- Special vector database info -->
                                    {#if probeData?.total_vectors !== undefined}
                                        <div class="probe-detail">
                                            <span class="detail-label">Total Vectors:</span>
                                            <span class="detail-value">{probeData.total_vectors.toLocaleString()}</span>
                                        </div>
                                    {/if}
                                    {#if probeData?.production_db !== undefined}
                                        <div class="probe-detail">
                                            <span class="detail-label">Production DB:</span>
                                            <span class="detail-value">{probeData.production_db ? '✅' : '❌'}</span>
                                        </div>
                                    {/if}
                                    <!-- Vector DB Actions -->
                                    <div class="probe-actions">
                                        <button 
                                            class="action-btn refresh-btn"
                                            on:click|stopPropagation={refreshVectorStats}
                                            title="Refresh vector stats"
                                        >
                                            🔄
                                        </button>
                                        <button 
                                            class="action-btn clear-btn"
                                            on:click|stopPropagation={confirmClearVectorDb}
                                            title="Clear all vectors"
                                        >
                                            🗑️
                                        </button>
                                    </div>
                                {:else}
                                    <!-- Standard probe details for non-vector DB probes -->
                                    {#if probeData?.timestamp}
                                        <div class="probe-detail">
                                            <span class="detail-label">Last Check:</span>
                                            <span class="detail-value">{fmtTS(probeData.timestamp)}</span>
                                        </div>
                                    {/if}
                                    {#if probeData?.responseTime}
                                        <div class="probe-detail">
                                            <span class="detail-label">Response:</span>
                                            <span class="detail-value">{probeData.responseTime}ms</span>
                                        </div>
                                    {/if}
                                {/if}
                                {#if probeData?.timestamp}
                                    <div class="probe-detail">
                                        <span class="detail-label">Last Check:</span>
                                        <span class="detail-value">{fmtTS(probeData.timestamp)}</span>
                                    </div>
                                {/if}
                                {#if probeData?.responseTime}
                                    <div class="probe-detail">
                                        <span class="detail-label">Response:</span>
                                        <span class="detail-value">{probeData.responseTime}ms</span>
                                    </div>
                                {/if}
                            </div>
                            <div class="probe-hover-hint">Click for details</div>
                        </div>
                    {/each}
                </div>
            </div>
        {:else if probesError}
            <div class="error-section">
                <div class="error-icon">⚠️</div>
                <div class="error-message">Failed to load system probes: {probesError}</div>
            </div>
        {/if}
    </section>
</main>

<!-- Probe Detail Modal -->
{#if showProbeModal && selectedProbe}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal-overlay" on:click={closeProbeModal}>
        <div class="modal-content" on:click|stopPropagation>
            <div class="modal-header">
                <h2>Probe Details: {selectedProbe.name}</h2>
                <button class="modal-close" on:click={closeProbeModal} aria-label="Close modal">×</button>
            </div>
            <div class="modal-body">
                <div class="probe-status-banner status-{getProbeStatusColor(selectedProbe.data)}">
                    <div class="status-dot"></div>
                    <span>Status: {selectedProbe.data.status || 'unknown'}</span>
                </div>
                
                <div class="probe-details-grid">
                    {#each Object.entries(selectedProbe.data) as [key, value]}
                        <div class="detail-row">
                            <div class="detail-label">{key}:</div>
                            <div class="detail-value">
                                {#if key === 'timestamp'}
                                    <code>{fmtTS(value)}</code>
                                {:else if typeof value === 'boolean'}
                                    <code class="bool-{value}">{fmtBool(value)}</code>
                                {:else if typeof value === 'object' && value !== null}
                                    <details>
                                        <summary>View object</summary>
                                        <pre>{JSON.stringify(value, null, 2)}</pre>
                                    </details>
                                {:else}
                                    <code>{value}</code>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>
{/if}

<!-- Vector DB Clear Confirmation Modal -->
{#if showClearConfirm}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal-overlay" on:click={cancelClearVectorDb}>
        <div class="modal-content confirm-modal" on:click|stopPropagation>
            <div class="modal-header">
                <h2>⚠️ Clear Vector Database</h2>
                <button class="modal-close" on:click={cancelClearVectorDb} aria-label="Close modal">×</button>
            </div>
            <div class="modal-body">
                <div class="warning-banner">
                    <div class="warning-icon">🚨</div>
                    <div class="warning-text">
                        <p><strong>This action cannot be undone!</strong></p>
                        <p>All vectors and metadata will be permanently deleted from the database.</p>
                    </div>
                </div>
                
                {#if vectorDbStats?.total_vectors}
                    <div class="impact-stats">
                        <p>This will delete <strong>{vectorDbStats.total_vectors.toLocaleString()} vectors</strong> across all models.</p>
                    </div>
                {/if}
                
                <div class="action-buttons">
                    <button 
                        class="btn btn-secondary" 
                        on:click={cancelClearVectorDb}
                        disabled={clearingVectorDb}
                    >
                        Cancel
                    </button>
                    <button 
                        class="btn btn-danger" 
                        on:click={clearVectorDb}
                        disabled={clearingVectorDb}
                    >
                        {clearingVectorDb ? 'Clearing...' : 'Clear Database'}
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    /* --- Base & Typography --- */
    .modern-dashboard {
        background: #0D1117;
        color: #C9D1D9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
        padding: 2rem;
        min-height: 100vh;
        max-height: 100vh;
        overflow-y: auto;
        overflow-x: hidden;
    }

    h1, h2, h3, h4 {
        color: #F0F6FC;
        font-weight: 600;
    }

    /* Custom scrollbar for the main dashboard */
    .modern-dashboard::-webkit-scrollbar {
        width: 8px;
    }

    .modern-dashboard::-webkit-scrollbar-track {
        background: #21262D;
        border-radius: 4px;
    }

    .modern-dashboard::-webkit-scrollbar-thumb {
        background: #30363D;
        border-radius: 4px;
    }

    .modern-dashboard::-webkit-scrollbar-thumb:hover {
        background: #484F58;
    }

    /* --- Hero Header --- */
    .dashboard-hero {
        background: linear-gradient(135deg, rgba(31, 111, 235, 0.1) 0%, rgba(88, 80, 234, 0.1) 100%);
        border: 1px solid #30363D;
        border-radius: 16px;
        padding: 1.5rem; /* Reduced from 2.5rem */
        margin-bottom: 1.5rem; /* Reduced from 2rem */
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }

    .hero-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1.5rem; /* Reduced from 2rem */
    }

    .hero-title-section {
        display: flex;
        align-items: center;
        gap: 1rem; /* Reduced from 1.5rem */
    }

    .title-icon {
        font-size: 2.5rem; /* Reduced from 3rem */
    }

    .hero-title {
        font-size: 1.75rem; /* Reduced from 2rem */
        margin: 0 0 0.25rem 0;
    }

    .hero-subtitle {
        font-size: 1rem;
        color: #8B949E;
        margin: 0;
    }

    .hero-stats {
        display: flex;
        gap: 1rem;
    }

    .stat-card {
        background: rgba(13, 17, 23, 0.5);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 0.75rem 1rem; /* Reduced padding */
        display: flex;
        align-items: center;
        gap: 0.75rem; /* Reduced gap */
        min-width: 150px; /* Reduced from 180px */
        transition: all 0.2s ease-in-out;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .stat-icon {
        font-size: 1.5rem;
    }

    .stat-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #F0F6FC;
    }

    .stat-label {
        font-size: 0.875rem;
        color: #8B949E;
    }

    .stat-card.pulse {
        animation: pulse-border 2s infinite;
    }

    @keyframes pulse-border {
        0% { border-color: #3882F6; }
        50% { border-color: #1F6FEB; }
        100% { border-color: #3882F6; }
    }

    /* --- Main Dashboard Grid --- */
    .dashboard-grid {
        display: grid;
        gap: 2rem;
    }

    /* --- Monitor Grid --- */
    .monitor-grid {
        display: grid;
        grid-template-columns: 1fr; /* Full width columns instead of auto-fit */
        gap: 2rem;
    }

    .monitor-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        transition: all 0.2s ease-in-out;
        width: 100%; /* Ensure full width */
    }
    .monitor-card:hover {
        border-color: #8B949E;
    }

    .monitor-card .card-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #30363D;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .card-title {
        font-size: 1.25rem;
        margin: 0;
    }

    .card-badge {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.75rem;
        border-radius: 2rem;
        background: #21262D;
        color: #8B949E;
    }
    .card-badge.learning { background: #3882F630; color: #58A6FF; }
    .card-badge.state { background: #A371F730; color: #BC8CFF; }

    .monitor-card .card-content {
        padding: 1rem; /* Reduced from 1.5rem */
        flex-grow: 1;
        overflow: hidden; /* Ensure content doesn't overflow the card */
        width: 100%; /* Ensure full width usage */
    }

    /* --- Section Header --- */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.5rem;
        margin: 0;
    }

    .refresh-btn {
        background: #21262D;
        border: 1px solid #30363D;
        color: #C9D1D9;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }
    .refresh-btn:hover {
        background: #30363D;
    }
    .refresh-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .refresh-icon.spinning {
        animation: spin 1s linear infinite;
    }

    /* --- Health Section --- */
    .health-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
    }

    .health-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        position: relative;
        overflow: hidden;
    }

    .health-icon {
        font-size: 2rem;
    }

    .health-info h4 {
        margin: 0 0 0.25rem 0;
        font-size: 1rem;
    }

    .health-status {
        font-size: 0.875rem;
        color: #8B949E;
        text-transform: capitalize;
    }

    .health-indicator {
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        width: 4px;
        background: #30363D;
        transition: background-color 0.3s ease;
    }

    .health-card.healthy .health-indicator { background-color: #238636; }
    .health-card.healthy .health-status { color: #3FB950; }

    /* --- Probes Section --- */
    .probes-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
    }

    .probe-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.2s ease-in-out;
        position: relative;
        overflow: hidden;
    }
    .probe-card.clickable { cursor: pointer; }
    .probe-card.clickable:hover {
        transform: translateY(-4px);
        border-color: #58A6FF;
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }

    .probe-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .probe-name {
        font-size: 1rem;
        font-weight: 600;
        color: #F0F6FC;
    }

    .probe-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        font-weight: 500;
        padding: 0.25rem 0.75rem;
        border-radius: 2rem;
    }
    .probe-status .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    .probe-status.status-emerald { background: #23863630; color: #3FB950; }
    .probe-status.status-emerald .status-dot { background: #3FB950; }
    .probe-status.status-amber { background: #BB800930; color: #D29922; }
    .probe-status.status-amber .status-dot { background: #D29922; }
    .probe-status.status-red { background: #DA363330; color: #F85149; }
    .probe-status.status-red .status-dot { background: #F85149; }
    .probe-status.status-gray { background: #21262D; color: #8B949E; }
    .probe-status.status-gray .status-dot { background: #8B949E; }

    .probe-details {
        font-size: 0.875rem;
        color: #8B949E;
    }
    .probe-detail {
        display: flex;
        justify-content: space-between;
    }
    .detail-value {
        color: #C9D1D9;
        font-weight: 500;
    }

    .probe-hover-hint {
        position: absolute;
        bottom: -20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.75rem;
        color: #58A6FF;
        opacity: 0;
        transition: all 0.2s ease-in-out;
    }
    .probe-card.clickable:hover .probe-hover-hint {
        bottom: 10px;
        opacity: 1;
    }

    /* --- Modal --- */
    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(13, 17, 23, 0.8);
        backdrop-filter: blur(5px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .modal-content {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        max-width: 700px;
        width: 90%;
        max-height: 85vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 16px 48px rgba(0,0,0,0.4);
    }

    .modal-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #30363D;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .modal-header h2 { font-size: 1.25rem; margin: 0; }

    .modal-close {
        background: none;
        border: none;
        color: #8B949E;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.5rem;
        line-height: 1;
    }
    .modal-close:hover { color: #F0F6FC; }

    .modal-body {
        padding: 1.5rem;
        overflow-y: auto;
    }

    .probe-status-banner {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }

    .probe-details-grid {
        display: grid;
        gap: 0.75rem;
    }

    .detail-row {
        display: grid;
        grid-template-columns: 150px 1fr;
        gap: 1rem;
        padding: 0.75rem;
        background: #0D1117;
        border-radius: 6px;
    }

    .detail-label {
        font-weight: 500;
        color: #8B949E;
    }

    .detail-value code {
        background: #21262D;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-family: "SF Mono", "Consolas", "Liberation Mono", Menlo, Courier, monospace;
        font-size: 0.875rem;
    }
    .detail-value pre {
        background: #0D1117;
        border: 1px solid #30363D;
        padding: 1rem;
        border-radius: 6px;
        overflow-x: auto;
    }

    /* --- Vector DB Specific Styles --- */
    .vector-db-card {
        border-color: #58A6FF;
        background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    }

    .probe-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid #30363D;
    }

    .action-btn {
        background: #21262D;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 0.5rem;
        color: #F0F6FC;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.875rem;
        min-width: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .action-btn:hover {
        background: #30363D;
        border-color: #58A6FF;
        transform: translateY(-1px);
    }

    .refresh-btn:hover {
        color: #58A6FF;
    }

    .clear-btn:hover {
        color: #F85149;
        border-color: #F85149;
    }

    /* --- Confirmation Modal Styles --- */
    .confirm-modal {
        max-width: 500px;
    }

    .warning-banner {
        display: flex;
        gap: 1rem;
        padding: 1rem;
        background: #DA363330;
        border: 1px solid #F85149;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }

    .warning-icon {
        font-size: 1.5rem;
        flex-shrink: 0;
    }

    .warning-text p {
        margin: 0 0 0.5rem 0;
        color: #F0F6FC;
    }

    .warning-text p:last-child {
        margin-bottom: 0;
    }

    .impact-stats {
        background: #21262D;
        border: 1px solid #30363D;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        text-align: center;
        color: #8B949E;
    }

    .action-buttons {
        display: flex;
        gap: 1rem;
        justify-content: flex-end;
    }

    .btn {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
        font-size: 0.875rem;
    }

    .btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .btn-secondary {
        background: #21262D;
        color: #F0F6FC;
        border: 1px solid #30363D;
    }

    .btn-secondary:hover:not(:disabled) {
        background: #30363D;
    }

    .btn-danger {
        background: #DA3633;
        color: #F0F6FC;
        border: 1px solid #F85149;
    }

    .btn-danger:hover:not(:disabled) {
        background: #F85149;
        transform: translateY(-1px);
    }

    /* --- Animations --- */
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* --- Responsive --- */
    @media (max-width: 768px) {
        .modern-dashboard { padding: 1rem; }
        .dashboard-hero { padding: 1.5rem; }
        .hero-title { font-size: 1.5rem; }
        .hero-subtitle { font-size: 0.875rem; }
        .hero-stats { flex-direction: column; align-items: stretch; width: 100%; }
    }
</style>
