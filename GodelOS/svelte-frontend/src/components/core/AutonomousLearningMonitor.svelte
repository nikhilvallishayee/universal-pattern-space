<script>
    import { onMount, onDestroy } from 'svelte';
    import { enhancedCognitive } from '../../stores/enhanced-cognitive.js';
    import { writable } from 'svelte/store';

    // Component props
    export let compactMode = false;
    export let showDetails = true;
    export let autoRefresh = true;
    export let refreshInterval = 5000;

    // Local state
    let learningState = null;
    let acquisitionHistory = [];
    let knowledgeGaps = [];
    let autonomousPlans = [];
    let isExpanded = true;
    let refreshTimer;
    let isLoading = false;
    let selectedTab = 'overview';

    // Reactive derived state
    $: activeAcquisitions = acquisitionHistory.filter(a => a.status === 'active').length;
    $: completedAcquisitions = acquisitionHistory.filter(a => a.status === 'completed').length;
    $: failedAcquisitions = acquisitionHistory.filter(a => a.status === 'failed').length;
    $: highPriorityGaps = knowledgeGaps.filter(g => g.priority === 'high').length;
    $: learningEfficiency = completedAcquisitions > 0 ? 
        Math.round((completedAcquisitions / (completedAcquisitions + failedAcquisitions)) * 100) : 0;

    // Subscriptions
    let unsubscribe;

    onMount(() => {
        // Subscribe to cognitive state
        unsubscribe = enhancedCognitive.subscribe(state => {
            learningState = state.autonomousLearning;
            acquisitionHistory = state.autonomousLearning.acquisitionHistory || [];
            knowledgeGaps = state.autonomousLearning.detectedGaps || [];
            autonomousPlans = state.autonomousLearning.activeAcquisitions || [];
        });

        // Set up auto refresh
        if (autoRefresh) {
            refreshTimer = setInterval(() => {
                refreshData();
            }, refreshInterval);
        }

        // Initial data load
        refreshData();
    });

    onDestroy(() => {
        if (unsubscribe) unsubscribe();
        if (refreshTimer) clearInterval(refreshTimer);
    });

    function refreshData() {
        isLoading = true;
        enhancedCognitive.refreshAutonomousState();
        setTimeout(() => isLoading = false, 1000);
    }

    function triggerManualAcquisition(gap) {
        enhancedCognitive.triggerManualAcquisition(gap.concept, gap.context);
    }

    function pauseAutonomousLearning() {
        enhancedCognitive.pauseAutonomousLearning();
    }

    function resumeAutonomousLearning() {
        enhancedCognitive.resumeAutonomousLearning();
    }

    function adjustLearningRate(rate) {
        enhancedCognitive.updateLearningConfiguration({ learning_rate: rate });
    }

    function getStatusColor(status) {
        switch (status) {
            case 'active': return '#3b82f6';
            case 'completed': return '#10b981';
            case 'failed': return '#ef4444';
            case 'paused': return '#f59e0b';
            default: return '#6b7280';
        }
    }

    function getPriorityColor(priority) {
        switch (priority) {
            case 'high': return '#ef4444';
            case 'medium': return '#f59e0b';
            case 'low': return '#10b981';
            default: return '#6b7280';
        }
    }

    function formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }

    function formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    function getProgressPercentage(plan) {
        return Math.round((plan.progress || 0) * 100);
    }
</script>

<div class="learning-monitor" class:compact={compactMode}>
    <!-- Modern Header -->
    <header class="monitor-header">
        <div class="header-left">
            <button 
                on:click={() => isExpanded = !isExpanded}
                class="expand-btn"
                aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
                <div class="expand-icon" class:rotated={!isExpanded}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </div>
            </button>
            
            <div class="header-info">
                <h3 class="monitor-title">
                    <span class="title-icon">🤖</span>
                    Autonomous Learning Monitor
                </h3>
                <div class="monitor-stats">
                    <div class="stat-item">
                        <div class="status-indicator" class:active={learningState?.enabled}>
                            <div class="indicator-pulse"></div>
                        </div>
                        <span class="stat-text">{learningState?.enabled ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                        <span class="stat-number">{activeAcquisitions}</span>
                        <span class="stat-text">active plans</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                        <span class="stat-number">{learningEfficiency}%</span>
                        <span class="stat-text">efficiency</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="header-actions">
            {#if learningState?.enabled}
                <button
                    on:click={pauseAutonomousLearning}
                    class="action-btn warning"
                >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M5.5 3.5A1.5 1.5 0 0 1 7 2h2a1.5 1.5 0 0 1 1.5 1.5v9A1.5 1.5 0 0 1 9 14H7a1.5 1.5 0 0 1-1.5-1.5v-9Z"/>
                    </svg>
                    Pause
                </button>
            {:else}
                <button
                    on:click={resumeAutonomousLearning}
                    class="action-btn success"
                >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M6.271 5.055a.5.5 0 0 1 .52.038L11 7.055a.5.5 0 0 1 0 .89L6.791 9.907a.5.5 0 0 1-.791-.389V5.482a.5.5 0 0 1 .271-.427z"/>
                    </svg>
                    Resume
                </button>
            {/if}
            
            <button
                on:click={refreshData}
                class="action-btn secondary"
                class:loading={isLoading}
                disabled={isLoading}
                title="Refresh data"
            >
                <div class="btn-icon" class:spinning={isLoading}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                        <path fill-rule="evenodd" d="M8 3a5 5 0 104.546 2.914.5.5 0 00-.908-.417A4 4 0 118 4v1z"/>
                        <path d="M8 4.466V.534a.25.25 0 01.41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 018 4.466z"/>
                    </svg>
                </div>
                Refresh
            </button>
        </div>
    </header>

    {#if isExpanded}
        <!-- Quick Stats Overview -->
        <section class="stats-overview">
            <div class="stats-grid">
                <div class="stat-card active">
                    <div class="stat-icon">⚡</div>
                    <div class="stat-content">
                        <div class="stat-value">{activeAcquisitions}</div>
                        <div class="stat-label">Active Acquisitions</div>
                    </div>
                </div>
                
                <div class="stat-card completed">
                    <div class="stat-icon">✅</div>
                    <div class="stat-content">
                        <div class="stat-value">{completedAcquisitions}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                </div>
                
                <div class="stat-card gaps">
                    <div class="stat-icon">🎯</div>
                    <div class="stat-content">
                        <div class="stat-value">{highPriorityGaps}</div>
                        <div class="stat-label">High Priority Gaps</div>
                    </div>
                </div>
                
                <div class="stat-card plans">
                    <div class="stat-icon">📋</div>
                    <div class="stat-content">
                        <div class="stat-value">{autonomousPlans.length}</div>
                        <div class="stat-label">Active Plans</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Tab Navigation -->
        <nav class="tab-navigation">
            <div class="tab-list">
                <button
                    on:click={() => selectedTab = 'overview'}
                    class="tab-button"
                    class:active={selectedTab === 'overview'}
                >
                    <span class="tab-icon">📊</span>
                    <span>Overview</span>
                </button>
                <button
                    on:click={() => selectedTab = 'gaps'}
                    class="tab-button"
                    class:active={selectedTab === 'gaps'}
                >
                    <span class="tab-icon">🎯</span>
                    <span>Knowledge Gaps</span>
                    {#if highPriorityGaps > 0}
                        <span class="tab-badge">{highPriorityGaps}</span>
                    {/if}
                </button>
                <button
                    on:click={() => selectedTab = 'plans'}
                    class="tab-button"
                    class:active={selectedTab === 'plans'}
                >
                    <span class="tab-icon">🚀</span>
                    <span>Active Plans</span>
                    {#if autonomousPlans.length > 0}
                        <span class="tab-badge">{autonomousPlans.length}</span>
                    {/if}
                </button>
                <button
                    on:click={() => selectedTab = 'history'}
                    class="tab-button"
                    class:active={selectedTab === 'history'}
                >
                    <span class="tab-icon">📚</span>
                    <span>History</span>
                </button>
            </div>
        </nav>

        <!-- Tab Content -->
        <main class="tab-content">
            {#if selectedTab === 'overview'}
                <div class="overview-panel">
                    <!-- Learning Configuration -->
                    {#if showDetails && learningState}
                        <section class="config-section">
                            <h4 class="section-title">Learning Configuration</h4>
                            <div class="config-grid">
                                <div class="config-item">
                                    <label class="config-label">Learning Rate</label>
                                    <div class="slider-container">
                                        <input
                                            type="range"
                                            min="0.1"
                                            max="2.0"
                                            step="0.1"
                                            value={learningState?.statistics?.averageAcquisitionTime || 1.0}
                                            on:change={(e) => adjustLearningRate(parseFloat(e.target.value))}
                                            class="config-slider"
                                        />
                                        <span class="slider-value">{learningState?.statistics?.averageAcquisitionTime || 1.0}</span>
                                    </div>
                                </div>
                                
                                <div class="config-item">
                                    <label class="config-label">Gap Detection Sensitivity</label>
                                    <div class="config-value">Medium</div>
                                </div>
                                
                                <div class="config-item">
                                    <label class="config-label">Max Concurrent Acquisitions</label>
                                    <div class="config-value">3</div>
                                </div>
                                
                                <div class="config-item">
                                    <label class="config-label">Auto Trigger Threshold</label>
                                    <div class="config-value">0.7</div>
                                </div>
                            </div>
                        </section>
                    {/if}

                    <!-- Performance Metrics -->
                    <section class="metrics-section">
                        <h4 class="section-title">Performance Metrics</h4>
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-header">
                                    <span class="metric-icon">📈</span>
                                    <span class="metric-title">Success Rate</span>
                                </div>
                                <div class="metric-value">{learningEfficiency}%</div>
                                <div class="metric-bar">
                                    <div class="metric-fill" style="width: {learningEfficiency}%"></div>
                                </div>
                            </div>
                            
                            <div class="metric-card">
                                <div class="metric-header">
                                    <span class="metric-icon">⏱️</span>
                                    <span class="metric-title">Avg. Acquisition Time</span>
                                </div>
                                <div class="metric-value">
                                    {formatDuration(learningState?.statistics?.averageAcquisitionTime * 60 || 0)}
                                </div>
                            </div>
                            
                            <div class="metric-card">
                                <div class="metric-header">
                                    <span class="metric-icon">🎯</span>
                                    <span class="metric-title">Total Gaps Detected</span>
                                </div>
                                <div class="metric-value">{learningState?.statistics?.totalGapsDetected || 0}</div>
                            </div>
                        </div>
                    </section>
                </div>
            {:else if selectedTab === 'gaps'}
                <div class="gaps-panel">
                    <div class="panel-header">
                        <h4 class="panel-title">Knowledge Gaps</h4>
                        <span class="panel-count">{knowledgeGaps.length} identified</span>
                    </div>
                    
                    {#if knowledgeGaps.length === 0}
                        <div class="empty-state">
                            <div class="empty-icon">✅</div>
                            <h5 class="empty-title">No Knowledge Gaps Detected</h5>
                            <p class="empty-description">
                                The system hasn't identified any knowledge gaps that require attention.
                            </p>
                        </div>
                    {:else}
                        <div class="gaps-list">
                            {#each knowledgeGaps.slice(0, 10) as gap, index}
                                <article class="gap-card">
                                    <div class="gap-header">
                                        <div class="gap-info">
                                            <h5 class="gap-concept">{gap.concept}</h5>
                                            <div class="gap-meta">
                                                <span class="priority-badge priority-{gap.priority}" style="--priority-color: {getPriorityColor(gap.priority)}">
                                                    {gap.priority} priority
                                                </span>
                                                <span class="confidence-score">
                                                    {(gap.confidence * 100).toFixed(0)}% confidence
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            on:click={() => triggerManualAcquisition(gap)}
                                            class="learn-btn"
                                        >
                                            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                                                <path d="M6.271 5.055a.5.5 0 0 1 .52.038L11 7.055a.5.5 0 0 1 0 .89L6.791 9.907a.5.5 0 0 1-.791-.389V5.482a.5.5 0 0 1 .271-.427z"/>
                                            </svg>
                                            Learn Now
                                        </button>
                                    </div>
                                    
                                    <p class="gap-context">{gap.context}</p>
                                    
                                    {#if gap.suggestedSources && gap.suggestedSources.length > 0}
                                        <div class="gap-sources">
                                            <span class="sources-label">Suggested sources:</span>
                                            <div class="sources-list">
                                                {#each gap.suggestedSources as source}
                                                    <span class="source-tag">{source}</span>
                                                {/each}
                                            </div>
                                        </div>
                                    {/if}
                                </article>
                            {/each}
                        </div>
                    {/if}
                </div>
            {:else if selectedTab === 'plans'}
                <div class="plans-panel">
                    <div class="panel-header">
                        <h4 class="panel-title">Active Acquisition Plans</h4>
                        <span class="panel-count">{autonomousPlans.length} running</span>
                    </div>
                    
                    {#if autonomousPlans.length === 0}
                        <div class="empty-state">
                            <div class="empty-icon">💤</div>
                            <h5 class="empty-title">No Active Plans</h5>
                            <p class="empty-description">
                                No autonomous acquisition plans are currently running. Plans will be created automatically when knowledge gaps are detected.
                            </p>
                        </div>
                    {:else}
                        <div class="plans-list">
                            {#each autonomousPlans as plan}
                                <article class="plan-card">
                                    <div class="plan-header">
                                        <div class="plan-info">
                                            <h5 class="plan-concept">{plan.target_concept}</h5>
                                            <p class="plan-strategy">{plan.strategy}</p>
                                        </div>
                                        <span class="status-badge" style="--status-color: {getStatusColor(plan.status)}">
                                            {plan.status}
                                        </span>
                                    </div>
                                    
                                    {#if plan.progress}
                                        <div class="progress-section">
                                            <div class="progress-header">
                                                <span class="progress-label">Progress</span>
                                                <span class="progress-percentage">{getProgressPercentage(plan)}%</span>
                                            </div>
                                            <div class="progress-bar">
                                                <div 
                                                    class="progress-fill"
                                                    style="width: {getProgressPercentage(plan)}%"
                                                ></div>
                                            </div>
                                        </div>
                                    {/if}
                                    
                                    <div class="plan-footer">
                                        <span class="plan-timing">
                                            Started: {formatTimestamp(plan.created_at)}
                                        </span>
                                        {#if plan.estimated_duration}
                                            <span class="plan-eta">
                                                ETA: {formatDuration(plan.estimated_duration)}
                                            </span>
                                        {/if}
                                    </div>
                                </article>
                            {/each}
                        </div>
                    {/if}
                </div>
            {:else if selectedTab === 'history'}
                <div class="history-panel">
                    <div class="panel-header">
                        <h4 class="panel-title">Acquisition History</h4>
                        <span class="panel-count">{acquisitionHistory.length} total</span>
                    </div>
                    
                    {#if acquisitionHistory.length === 0}
                        <div class="empty-state">
                            <div class="empty-icon">📚</div>
                            <h5 class="empty-title">No History Available</h5>
                            <p class="empty-description">
                                No acquisition history to display. Completed acquisitions will appear here.
                            </p>
                        </div>
                    {:else}
                        <div class="history-list">
                            {#each acquisitionHistory.slice(-10).reverse() as acquisition}
                                <article class="history-item">
                                    <div class="history-header">
                                        <div class="history-info">
                                            <h5 class="history-concept">{acquisition.concept}</h5>
                                            <p class="history-strategy">{acquisition.strategy}</p>
                                        </div>
                                        <div class="history-meta">
                                            <span class="status-badge" style="--status-color: {getStatusColor(acquisition.status)}">
                                                {acquisition.status}
                                            </span>
                                            <span class="history-time">
                                                {formatTimestamp(acquisition.timestamp)}
                                            </span>
                                        </div>
                                    </div>
                                </article>
                            {/each}
                        </div>
                    {/if}
                </div>
            {/if}
        </main>
    {/if}
</div>

<style>
    .learning-monitor {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }

    .learning-monitor.compact {
        border-radius: 12px;
    }

    /* Header Styles */
    .monitor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        gap: 1rem;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex: 1;
    }

    .expand-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.8);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .expand-btn:hover {
        background: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .expand-icon {
        transition: transform 0.2s ease;
    }

    .expand-icon.rotated {
        transform: rotate(-90deg);
    }

    .header-info {
        flex: 1;
    }

    .monitor-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: white;
    }

    .title-icon {
        font-size: 1.5rem;
    }

    .monitor-stats {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .stat-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #ef4444;
        position: relative;
    }

    .status-indicator.active {
        background: #10b981;
    }

    .status-indicator.active .indicator-pulse {
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        border-radius: 50%;
        background: #10b981;
        opacity: 0.3;
        animation: pulse 2s infinite;
    }

    .stat-number {
        font-weight: 600;
        color: white;
        font-size: 0.875rem;
    }

    .stat-text {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
    }

    .stat-divider {
        width: 1px;
        height: 12px;
        background: rgba(255, 255, 255, 0.2);
    }

    .header-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .action-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .action-btn.success {
        background: #10b981;
        color: white;
        border-color: #10b981;
    }

    .action-btn.success:hover {
        background: #059669;
        border-color: #059669;
    }

    .action-btn.warning {
        background: #f59e0b;
        color: white;
        border-color: #f59e0b;
    }

    .action-btn.warning:hover {
        background: #d97706;
        border-color: #d97706;
    }

    .action-btn.secondary {
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.8);
    }

    .action-btn.secondary:hover:not(:disabled) {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .action-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .btn-icon {
        transition: transform 0.2s ease;
    }

    .btn-icon.spinning {
        animation: spin 1s linear infinite;
    }

    /* Stats Overview */
    .stats-overview {
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.02);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .stat-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        transition: all 0.2s ease;
    }

    .stat-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .stat-icon {
        font-size: 2rem;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
    }

    .stat-content {
        flex: 1;
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
    }

    /* Tab Navigation */
    .tab-navigation {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding: 0 1.5rem;
    }

    .tab-list {
        display: flex;
        gap: 0.5rem;
    }

    .tab-button {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem 1.5rem;
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.7);
        font-weight: 500;
        cursor: pointer;
        border-radius: 12px 12px 0 0;
        transition: all 0.2s ease;
        position: relative;
    }

    .tab-button:hover {
        color: white;
        background: rgba(255, 255, 255, 0.05);
    }

    .tab-button.active {
        color: white;
        background: rgba(255, 255, 255, 0.1);
    }

    .tab-button.active::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #10b981, #3b82f6);
    }

    .tab-icon {
        font-size: 1.25rem;
    }

    .tab-badge {
        background: #ef4444;
        color: white;
        font-size: 0.75rem;
        padding: 0.125rem 0.375rem;
        border-radius: 10px;
        font-weight: 600;
        min-width: 18px;
        text-align: center;
    }

    /* Tab Content */
    .tab-content {
        padding: 1.5rem;
    }

    /* Overview Panel */
    .overview-panel {
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    .config-section,
    .metrics-section {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
    }

    .section-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: white;
        margin: 0 0 1rem 0;
    }

    .config-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
    }

    .config-item {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .config-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
    }

    .slider-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .config-slider {
        flex: 1;
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        outline: none;
        appearance: none;
    }

    .config-slider::-webkit-slider-thumb {
        appearance: none;
        width: 18px;
        height: 18px;
        background: #3b82f6;
        border-radius: 50%;
        cursor: pointer;
    }

    .config-slider::-moz-range-thumb {
        width: 18px;
        height: 18px;
        background: #3b82f6;
        border-radius: 50%;
        cursor: pointer;
        border: none;
    }

    .slider-value {
        font-weight: 600;
        color: white;
        min-width: 40px;
        text-align: right;
        font-size: 0.875rem;
    }

    .config-value {
        font-weight: 600;
        color: white;
        font-size: 0.875rem;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
    }

    .metric-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .metric-icon {
        font-size: 1.25rem;
    }

    .metric-title {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.8);
        font-weight: 500;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
    }

    .metric-bar {
        width: 100%;
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        overflow: hidden;
    }

    .metric-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        transition: width 0.3s ease;
    }

    /* Panel Styles */
    .gaps-panel,
    .plans-panel,
    .history-panel {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .panel-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: white;
        margin: 0;
    }

    .panel-count {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        background: rgba(255, 255, 255, 0.1);
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
    }

    /* Empty State */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }

    .empty-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.6;
    }

    .empty-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: white;
        margin: 0 0 0.5rem 0;
    }

    .empty-description {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.5;
        margin: 0;
        max-width: 400px;
    }

    /* Lists */
    .gaps-list,
    .plans-list,
    .history-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        max-height: 500px;
        overflow-y: auto;
        padding-right: 0.5rem;
    }

    .gaps-list::-webkit-scrollbar,
    .plans-list::-webkit-scrollbar,
    .history-list::-webkit-scrollbar {
        width: 6px;
    }

    .gaps-list::-webkit-scrollbar-track,
    .plans-list::-webkit-scrollbar-track,
    .history-list::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
    }

    .gaps-list::-webkit-scrollbar-thumb,
    .plans-list::-webkit-scrollbar-thumb,
    .history-list::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
    }

    /* Gap Cards */
    .gap-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.2s ease;
    }

    .gap-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .gap-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
        gap: 1rem;
    }

    .gap-info {
        flex: 1;
    }

    .gap-concept {
        font-size: 1rem;
        font-weight: 600;
        color: white;
        margin: 0 0 0.5rem 0;
    }

    .gap-meta {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .priority-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: capitalize;
        background: var(--priority-color, #6b7280);
        color: white;
    }

    .confidence-score {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
    }

    .learn-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: #3b82f6;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        color: white;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
    }

    .learn-btn:hover {
        background: #2563eb;
        border-color: #2563eb;
    }

    .gap-context {
        color: rgba(255, 255, 255, 0.8);
        line-height: 1.5;
        margin: 0 0 0.75rem 0;
        font-size: 0.875rem;
    }

    .gap-sources {
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .sources-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 0.5rem;
        display: block;
    }

    .sources-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.25rem;
    }

    .source-tag {
        padding: 0.125rem 0.5rem;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.8);
    }

    /* Plan Cards */
    .plan-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.2s ease;
    }

    .plan-card:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .plan-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
        gap: 1rem;
    }

    .plan-info {
        flex: 1;
    }

    .plan-concept {
        font-size: 1rem;
        font-weight: 600;
        color: white;
        margin: 0 0 0.25rem 0;
    }

    .plan-strategy {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        margin: 0;
    }

    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: capitalize;
        background: var(--status-color, #6b7280);
        color: white;
        white-space: nowrap;
    }

    .progress-section {
        margin-bottom: 1rem;
    }

    .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .progress-label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.8);
    }

    .progress-percentage {
        font-size: 0.875rem;
        font-weight: 600;
        color: white;
    }

    .progress-bar {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        transition: width 0.3s ease;
        border-radius: 3px;
    }

    .plan-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.6);
        gap: 1rem;
    }

    .plan-timing,
    .plan-eta {
        flex: 1;
    }

    .plan-eta {
        text-align: right;
    }

    /* History Items */
    .history-item {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 1rem;
        transition: all 0.2s ease;
    }

    .history-item:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .history-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }

    .history-info {
        flex: 1;
    }

    .history-concept {
        font-size: 0.875rem;
        font-weight: 600;
        color: white;
        margin: 0 0 0.25rem 0;
    }

    .history-strategy {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        margin: 0;
    }

    .history-meta {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.25rem;
    }

    .history-time {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.6);
    }

    /* Animations */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .monitor-header {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
        }

        .header-left {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
        }

        .monitor-stats {
            justify-content: space-between;
        }

        .header-actions {
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }

        .config-grid {
            grid-template-columns: 1fr;
        }

        .metrics-grid {
            grid-template-columns: 1fr;
        }

        .tab-list {
            flex-wrap: wrap;
        }

        .tab-button {
            padding: 0.75rem 1rem;
            font-size: 0.875rem;
        }

        .gap-header,
        .plan-header,
        .history-header {
            flex-direction: column;
            align-items: stretch;
            gap: 0.75rem;
        }

        .gap-meta {
            justify-content: space-between;
        }

        .plan-footer {
            flex-direction: column;
            align-items: stretch;
            gap: 0.5rem;
        }

        .plan-eta {
            text-align: left;
        }
    }

    @media (max-width: 480px) {
        .monitor-header {
            padding: 1rem;
        }

        .tab-content {
            padding: 1rem;
        }

        .stats-overview {
            padding: 1rem;
        }

        .stats-grid {
            grid-template-columns: 1fr;
        }

        .config-section,
        .metrics-section {
            padding: 1rem;
        }

        .action-btn {
            padding: 0.5rem;
            font-size: 0.75rem;
        }

        .action-btn span {
            display: none;
        }

        .tab-button {
            padding: 0.5rem 0.75rem;
        }

        .tab-button span:last-child {
            display: none;
        }
    }
</style>
