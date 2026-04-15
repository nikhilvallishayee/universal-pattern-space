<!-- Enhanced Dashboard Component with Better Space Utilization -->
<script>
  import { onMount } from 'svelte';
  import { cognitiveState, knowledgeState, apiHelpers } from '../../stores/cognitive.js';
  import CognitiveStateMonitor from '../core/CognitiveStateMonitor.svelte';
  import QueryInterface from '../core/QueryInterface.svelte';
  import ResponseDisplay from '../core/ResponseDisplay.svelte';
  import ConceptEvolution from '../knowledge/ConceptEvolution.svelte';
  import ProcessInsight from '../transparency/ProcessInsight.svelte';

  let selectedMetric = 'overview';
  let autoRefresh = true;
  let refreshInterval;

  const metrics = [
    { id: 'overview', name: 'System Overview', icon: '🏠' },
    { id: 'cognitive', name: 'Cognitive Health', icon: '🧠' },
    { id: 'knowledge', name: 'Knowledge Stats', icon: '📚' },
    { id: 'performance', name: 'Performance', icon: '⚡' },
    { id: 'evolution', name: 'Evolution', icon: '📈' }
  ];

  onMount(() => {
    // Start real-time updates if auto-refresh is enabled
    if (autoRefresh) {
      refreshInterval = apiHelpers.startRealTimeUpdates(3000);
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  });

  // Safe calculation functions
  function safePercentage(value, fallback = 0) {
    if (typeof value === 'number' && !isNaN(value) && isFinite(value)) {
      return Math.round(Math.max(0, Math.min(100, value * 100)));
    }
    return fallback;
  }
  
  function safeNumber(value, fallback = 0) {
    if (typeof value === 'number' && !isNaN(value) && isFinite(value)) {
      return value;
    }
    return fallback;
  }
  
  function safeLength(arr, fallback = 0) {
    if (Array.isArray(arr)) {
      return arr.length;
    }
    return fallback;
  }

  function safeAverage(values) {
    const validValues = values.filter(val => typeof val === 'number' && !isNaN(val) && isFinite(val));
    return validValues.length > 0 ? validValues.reduce((sum, val) => sum + val, 0) / validValues.length : 0;
  }

  $: systemHealthScore = safeAverage(Object.values($cognitiveState.systemHealth));
  $: overallCapabilities = safeAverage(Object.values($cognitiveState.capabilities));
</script>

<div class="enhanced-dashboard">
  <!-- Dashboard Header with Metrics Toggle -->
  <div class="dashboard-header">
    <div class="header-left">
      <h2>GödelOS Dashboard</h2>
      <div class="auto-refresh-toggle">
        <label class="toggle-switch">
          <input type="checkbox" bind:checked={autoRefresh} />
          <span class="slider"></span>
        </label>
        <span class="toggle-label">Auto Refresh</span>
      </div>
    </div>
    
    <div class="metrics-selector">
      {#each metrics as metric}
        <button 
          class="metric-button {selectedMetric === metric.id ? 'active' : ''}"
          on:click={() => selectedMetric = metric.id}
        >
          <span class="metric-icon">{metric.icon}</span>
          <span class="metric-name">{metric.name}</span>
        </button>
      {/each}
    </div>
  </div>

  <!-- Main Dashboard Content -->
  <div class="dashboard-content">
    {#if selectedMetric === 'overview'}
      <!-- System Overview Layout -->
      <div class="overview-layout">
        <!-- Top Stats Row -->
        <div class="stats-grid">
          <div class="stat-card primary">
            <div class="stat-header">
              <span class="stat-icon">🧠</span>
              <span class="stat-title">System Health</span>
            </div>
            <div class="stat-value">{safePercentage(systemHealthScore)}%</div>
            <div class="stat-trend positive">↗ +2.3%</div>
          </div>
          
          <div class="stat-card secondary">
            <div class="stat-header">
              <span class="stat-icon">📚</span>
              <span class="stat-title">Knowledge Base</span>
            </div>
            <div class="stat-value">{$knowledgeState.totalConcepts.toLocaleString()}</div>
            <div class="stat-subtitle">Concepts</div>
          </div>
          
          <div class="stat-card secondary">
            <div class="stat-header">
              <span class="stat-icon">🔗</span>
              <span class="stat-title">Connections</span>
            </div>
            <div class="stat-value">{$knowledgeState.totalConnections.toLocaleString()}</div>
            <div class="stat-subtitle">Active Links</div>
          </div>
          
          <div class="stat-card accent">
            <div class="stat-header">
              <span class="stat-icon">⚡</span>
              <span class="stat-title">Processing</span>
            </div>
            <div class="stat-value">{safePercentage($cognitiveState.manifestConsciousness?.processingLoad)}%</div>
            <div class="stat-subtitle">Load</div>
          </div>
        </div>

        <!-- Interactive Components Row -->
        <div class="components-grid">
          <div class="component-card large">
            <div class="card-header">
              <h3>Query Interface</h3>
              <div class="card-actions">
                <button class="action-btn" title="Expand">🗗</button>
              </div>
            </div>
            <div class="card-content">
              <QueryInterface />
            </div>
          </div>
          
          <div class="component-card large">
            <div class="card-header">
              <h3>System Response</h3>
              <div class="card-actions">
                <button class="action-btn" title="Expand">🗗</button>
              </div>
            </div>
            <div class="card-content">
              <ResponseDisplay />
            </div>
          </div>
        </div>

        <!-- Bottom Analysis Row -->
        <div class="analysis-grid">
          <div class="component-card">
            <div class="card-header">
              <h3>Cognitive State</h3>
              <div class="card-actions">
                <button class="action-btn" title="Details">📊</button>
              </div>
            </div>
            <div class="card-content">
              <CognitiveStateMonitor />
            </div>
          </div>
          
          <div class="component-card">
            <div class="card-header">
              <h3>Concept Evolution</h3>
              <div class="card-actions">
                <button class="action-btn" title="Timeline">📈</button>
              </div>
            </div>
            <div class="card-content">
              <ConceptEvolution />
            </div>
          </div>
          
          <div class="component-card">
            <div class="card-header">
              <h3>Process Insights</h3>
              <div class="card-actions">
                <button class="action-btn" title="Detailed View">🔍</button>
              </div>
            </div>
            <div class="card-content">
              <ProcessInsight />
            </div>
          </div>
        </div>
      </div>

    {:else if selectedMetric === 'cognitive'}
      <!-- Cognitive Health Detailed View -->
      <div class="cognitive-layout">
        <div class="cognitive-main">
          <CognitiveStateMonitor />
        </div>
        <div class="cognitive-sidebar">
          <div class="health-metrics">
            <h4>Health Breakdown</h4>
            {#each Object.entries($cognitiveState.systemHealth) as [module, health]}
              <div class="health-item">
                <span class="module-name">{module}</span>
                <div class="health-bar">
                  <div class="health-fill" style="width: {safePercentage(health)}%"></div>
                </div>
                <span class="health-percentage">{safePercentage(health)}%</span>
              </div>
            {/each}
          </div>
        </div>
      </div>

    {:else if selectedMetric === 'knowledge'}
      <!-- Knowledge Statistics View -->
      <div class="knowledge-layout">
        <div class="knowledge-stats-grid">
          <div class="stat-card-large">
            <h4>Total Concepts</h4>
            <div class="large-number">{$knowledgeState.totalConcepts.toLocaleString()}</div>
          </div>
          <div class="stat-card-large">
            <h4>Total Connections</h4>
            <div class="large-number">{$knowledgeState.totalConnections.toLocaleString()}</div>
          </div>
          <div class="stat-card-large">
            <h4>Documents</h4>
            <div class="large-number">{$knowledgeState.totalDocuments.toLocaleString()}</div>
          </div>
        </div>
        <div class="knowledge-evolution">
          <ConceptEvolution />
        </div>
      </div>

    {:else if selectedMetric === 'performance'}
      <!-- Performance Metrics View -->
      <div class="performance-layout">
        <div class="performance-cards">
          <div class="perf-card">
            <h4>Processing Load</h4>
            <div class="perf-gauge">
              <div class="gauge-fill" style="transform: rotate({safeNumber($cognitiveState.manifestConsciousness?.processingLoad, 0) * 180}deg)"></div>
              <div class="gauge-value">{safePercentage($cognitiveState.manifestConsciousness?.processingLoad)}%</div>
            </div>
          </div>
          
          <div class="perf-card">
            <h4>Active Agents</h4>
            <div class="agent-count">{$cognitiveState.agenticProcesses.length}</div>
          </div>
          
          <div class="perf-card">
            <h4>Memory Usage</h4>
            <div class="memory-bar">
              <div class="memory-fill" style="width: {Math.min(100, (safeLength($cognitiveState.manifestConsciousness?.workingMemory) / 12) * 100)}%"></div>
            </div>
            <div class="memory-text">{safeLength($cognitiveState.manifestConsciousness?.workingMemory)}/12</div>
          </div>
        </div>
      </div>

    {:else if selectedMetric === 'evolution'}
      <!-- Evolution and Growth View -->
      <div class="evolution-layout">
        <ConceptEvolution />
      </div>
    {/if}
  </div>
</div>

<style>
  .enhanced-dashboard {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 2rem;
    padding: 1rem;
  }

  /* Dashboard Header */
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 16px;
    backdrop-filter: blur(10px);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 2rem;
  }

  .header-left h2 {
    margin: 0;
    color: #64b5f6;
    font-size: 1.8rem;
    font-weight: 700;
  }

  .auto-refresh-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .toggle-switch {
    position: relative;
    width: 50px;
    height: 24px;
  }

  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(100, 181, 246, 0.3);
    transition: .4s;
    border-radius: 24px;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: #64b5f6;
    transition: .4s;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: rgba(100, 181, 246, 0.6);
  }

  input:checked + .slider:before {
    transform: translateX(26px);
  }

  .toggle-label {
    font-size: 0.9rem;
    color: #e1e5e9;
  }

  .metrics-selector {
    display: flex;
    gap: 0.5rem;
  }

  .metric-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 12px;
    color: #e1e5e9;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .metric-button:hover {
    background: rgba(100, 181, 246, 0.1);
    border-color: rgba(100, 181, 246, 0.4);
  }

  .metric-button.active {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
    color: #64b5f6;
  }

  .metric-icon {
    font-size: 1.2rem;
  }

  .metric-name {
    font-weight: 500;
    font-size: 0.9rem;
  }

  /* Dashboard Content */
  .dashboard-content {
    flex: 1;
    overflow: auto;
  }

  /* Overview Layout */
  .overview-layout {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    height: 100%;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 1.5rem;
    min-height: 120px;
  }

  .stat-card {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(10px);
  }

  .stat-card.primary {
    background: linear-gradient(135deg, rgba(100, 181, 246, 0.1) 0%, rgba(0, 0, 0, 0.3) 100%);
    border-color: rgba(100, 181, 246, 0.4);
  }

  .stat-card.secondary {
    background: rgba(15, 20, 35, 0.8);
  }

  .stat-card.accent {
    background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(0, 0, 0, 0.3) 100%);
    border-color: rgba(255, 193, 7, 0.4);
  }

  .stat-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .stat-icon {
    font-size: 1.5rem;
  }

  .stat-title {
    font-weight: 600;
    color: #e1e5e9;
    font-size: 0.9rem;
    opacity: 0.8;
  }

  .stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #64b5f6;
    margin-bottom: 0.5rem;
  }

  .stat-trend {
    font-size: 0.9rem;
    font-weight: 500;
  }

  .stat-trend.positive {
    color: #4CAF50;
  }

  .stat-subtitle {
    font-size: 0.8rem;
    opacity: 0.7;
    margin-top: 0.5rem;
  }

  .components-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    min-height: 300px;
  }

  .analysis-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 2rem;
    min-height: 400px;
  }

  .component-card {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(10px);
  }

  .component-card.large {
    min-height: 300px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 1.5rem 1rem 1.5rem;
    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
  }

  .card-header h3 {
    margin: 0;
    color: #64b5f6;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .card-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    background: rgba(100, 181, 246, 0.1);
    border: 1px solid rgba(100, 181, 246, 0.3);
    color: #64b5f6;
    padding: 0.5rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9rem;
  }

  .action-btn:hover {
    background: rgba(100, 181, 246, 0.2);
    border-color: rgba(100, 181, 246, 0.5);
  }

  .card-content {
    flex: 1;
    padding: 1.5rem;
    overflow: auto;
  }

  /* Responsive Design */
  @media (max-width: 1400px) {
    .stats-grid {
      grid-template-columns: 1fr 1fr;
      grid-template-rows: auto auto;
    }
    
    .analysis-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 900px) {
    .components-grid {
      grid-template-columns: 1fr;
    }
    
    .stats-grid {
      grid-template-columns: 1fr;
    }
    
    .dashboard-header {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }
    
    .metrics-selector {
      overflow-x: auto;
      padding-bottom: 0.5rem;
    }
  }
</style>
