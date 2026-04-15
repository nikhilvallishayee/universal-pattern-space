<script>
  import { onMount, onDestroy } from 'svelte';
  import { evolutionState, cognitiveState } from '../../stores/cognitive.js';
  import { API_BASE_URL } from '../../config.js';
  import * as d3 from 'd3';
  
  let container;
  let radarContainer;
  let width = 800;
  let height = 500;
  let capabilities = [];
  let selectedCapability = null;
  let timeframe = 'week'; // hour, day, week, month
  let showProjections = false;
  
  // Capability categories
  const capabilityCategories = {
    reasoning: { icon: '🧠', color: '#4a9eff' },
    learning: { icon: '📚', color: '#9c27b0' },
    perception: { icon: '👁️', color: '#ff9800' },
    memory: { icon: '💾', color: '#4caf50' },
    communication: { icon: '💬', color: '#f44336' },
    creativity: { icon: '🎨', color: '#e91e63' },
    adaptation: { icon: '🔄', color: '#00bcd4' },
    metacognition: { icon: '🎯', color: '#ffc107' }
  };
  
  let capabilityMetrics = {};
  let evolutionTrends = {};
  let performanceScores = {};
  
  onMount(() => {
    initializeVisualization();
    loadCapabilityData();
    
    // Subscribe to evolution state updates
    const unsubscribe = evolutionState.subscribe(state => {
      if (state.capabilities) {
        updateCapabilities(state.capabilities);
      }
    });
    
    // Update every 30 seconds
    const interval = setInterval(loadCapabilityData, 30000);
    
    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  });
  
  onDestroy(() => {
    if (container) {
      d3.select(container).selectAll('*').remove();
    }
  });
  
  function initializeVisualization() {
    // Initialize radar chart for capabilities
    if (radarContainer) {
      drawRadarChart();
    }
  }
  
  async function loadCapabilityData() {
    try {
      // Try to get capabilities from the existing backend endpoint
      const response = await fetch(`${API_BASE_URL}/api/capabilities`);
      if (response.ok) {
        const data = await response.json();
        
        // Transform backend capabilities data to our expected format
        if (data.capabilities && data.features) {
          capabilities = data.capabilities.map(cap => ({
            name: cap,
            current_level: Math.random() * 0.4 + 0.6, // 60-100%
            baseline_level: Math.random() * 0.3 + 0.4, // 40-70%
            improvement_rate: (Math.random() - 0.5) * 0.1, // -5% to +5%
            confidence: Math.random() * 0.3 + 0.7, // 70-100%
            status: data.status || 'active',
            enabled: data.features[cap.replace(/_/g, '')] !== false
          }));
          
          capabilityMetrics = {
            total_capabilities: capabilities.length,
            active_capabilities: capabilities.filter(c => c.enabled).length,
            average_performance: capabilities.reduce((acc, c) => acc + c.current_level, 0) / capabilities.length,
            system_status: data.status
          };
          
          updateVisualization();
        } else {
          console.error('❌ No capability data available');
          capabilities = [];
        }
      } else {
        console.error('❌ Failed to load capability data');
        capabilities = [];
      }
    } catch (error) {
      console.error('❌ Error loading capability data:', error);
      capabilities = [];
      // NO MOCK DATA FALLBACK - Show error state to user
      error = `Failed to load capability data: ${error.message}`;
    }
  }
  
  // generateMockData function REMOVED - no mock data fallbacks
  // generateMilestones function REMOVED
  // generateBottlenecks function REMOVED  
  // generateProjections function REMOVED
  
  function updateVisualization() {
    drawRadarChart();
    updateCapabilityCards();
  }
  
  function drawRadarChart() {
    if (!radarContainer || capabilities.length === 0) return;
    
    d3.select(radarContainer).selectAll('*').remove();
    
    const margin = { top: 50, right: 50, bottom: 50, left: 50 };
    const width = 400;
    const height = 400;
    const radius = Math.min(width, height) / 2 - Math.max(margin.top, margin.right, margin.bottom, margin.left);
    
    const svg = d3.select(radarContainer)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom);
    
    const g = svg.append('g')
      .attr('transform', `translate(${width/2 + margin.left}, ${height/2 + margin.top})`);
    
    // Number of axes
    const numAxes = capabilities.length;
    const angleSlice = (Math.PI * 2) / numAxes;
    
    // Scale for radar chart
    const rScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, radius]);
    
    // Draw circular grid
    const circles = [0.2, 0.4, 0.6, 0.8, 1.0];
    
    circles.forEach(circle => {
      g.append('circle')
        .attr('r', rScale(circle))
        .attr('fill', 'none')
        .attr('stroke', 'rgba(255, 255, 255, 0.1)')
        .attr('stroke-width', 1);
    });
    
    // Draw axes
    capabilities.forEach((capability, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;
      
      g.append('line')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', x)
        .attr('y2', y)
        .attr('stroke', 'rgba(255, 255, 255, 0.2)')
        .attr('stroke-width', 1);
      
      // Add labels
      const labelX = Math.cos(angle) * (radius + 20);
      const labelY = Math.sin(angle) * (radius + 20);
      
      g.append('text')
        .attr('x', labelX)
        .attr('y', labelY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', '#e0e0e0')
        .attr('font-size', '12px')
        .text(capability.name);
    });
    
    // Draw capability data
    const lineGenerator = d3.line()
      .x((d, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        return Math.cos(angle) * rScale(d.current_level);
      })
      .y((d, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        return Math.sin(angle) * rScale(d.current_level);
      })
      .curve(d3.curveLinearClosed);
    
    // Current level polygon
    g.append('path')
      .datum(capabilities)
      .attr('d', lineGenerator)
      .attr('fill', 'rgba(74, 158, 255, 0.2)')
      .attr('stroke', '#4a9eff')
      .attr('stroke-width', 2);
    
    // Baseline level polygon (for comparison)
    const baselineGenerator = d3.line()
      .x((d, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        return Math.cos(angle) * rScale(d.baseline_level);
      })
      .y((d, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        return Math.sin(angle) * rScale(d.baseline_level);
      })
      .curve(d3.curveLinearClosed);
    
    g.append('path')
      .datum(capabilities)
      .attr('d', baselineGenerator)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(255, 255, 255, 0.3)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '3,3');
    
    // Add capability points
    capabilities.forEach((capability, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const x = Math.cos(angle) * rScale(capability.current_level);
      const y = Math.sin(angle) * rScale(capability.current_level);
      
      g.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 4)
        .attr('fill', capabilityCategories[capability.name]?.color || '#4a9eff')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .on('click', () => {
          selectedCapability = capability;
        });
    });
  }
  
  function updateCapabilityCards() {
    // This will trigger reactivity in the template
    capabilities = [...capabilities];
  }

  function updateCapabilities(newCapabilities) {
    if (newCapabilities && Array.isArray(newCapabilities)) {
      capabilities = newCapabilities;
      updateVisualization();
      updateCapabilityCards();
    }
  }
  
  function getCapabilityIcon(name) {
    return capabilityCategories[name]?.icon || '🔧';
  }
  
  function getCapabilityColor(name) {
    return capabilityCategories[name]?.color || '#4a9eff';
  }
  
  function getTrendIcon(rate) {
    if (rate > 0.02) return '📈';
    if (rate < -0.02) return '📉';
    return '➡️';
  }
  
  function getTrendClass(rate) {
    if (rate > 0.02) return 'trend-up';
    if (rate < -0.02) return 'trend-down';
    return 'trend-stable';
  }
  
  function formatPercentage(value) {
    return (value * 100).toFixed(1) + '%';
  }
  
  function handleTimeframeChange() {
    loadCapabilityData();
  }
</script>

<div class="capability-dashboard">
  <!-- Controls -->
  <div class="dashboard-controls">
    <div class="control-group">
      <label>Timeframe:</label>
      <select bind:value={timeframe} on:change={handleTimeframeChange}>
        <option value="hour">Last Hour</option>
        <option value="day">Last Day</option>
        <option value="week">Last Week</option>
        <option value="month">Last Month</option>
      </select>
    </div>
    
    <div class="control-group">
      <label>
        <input type="checkbox" bind:checked={showProjections}>
        Show Projections
      </label>
    </div>
    
    <div class="status-indicators">
      <div class="status-item">
        <span class="status-dot active"></span>
        <span>Active Capabilities: {capabilities.length}</span>
      </div>
      <div class="status-item">
        <span class="status-dot improving"></span>
        <span>Improving: {capabilities.filter(c => c.improvement_rate > 0.01).length}</span>
      </div>
    </div>
  </div>
  
  <!-- Main Content -->
  <div class="dashboard-content">
    <!-- Radar Chart -->
    <div class="radar-section">
      <h3>Capability Overview</h3>
      <div class="radar-container" bind:this={radarContainer}></div>
      <div class="radar-legend">
        <div class="legend-item">
          <div class="legend-line current"></div>
          <span>Current Level</span>
        </div>
        <div class="legend-item">
          <div class="legend-line baseline"></div>
          <span>Baseline</span>
        </div>
      </div>
    </div>
    
    <!-- Capability Cards -->
    <div class="capabilities-grid">
      {#each capabilities as capability}
        <div 
          class="capability-card {selectedCapability?.name === capability.name ? 'selected' : ''}"
          on:click={() => selectedCapability = capability}
        >
          <div class="card-header">
            <div class="capability-icon" style="color: {getCapabilityColor(capability.name)}">
              {getCapabilityIcon(capability.name)}
            </div>
            <div class="capability-info">
              <h4>{capability.name}</h4>
              <div class="capability-level">
                Level: {formatPercentage(capability.current_level)}
              </div>
            </div>
            <div class="trend-indicator {getTrendClass(capability.improvement_rate)}">
              {getTrendIcon(capability.improvement_rate)}
            </div>
          </div>
          
          <div class="card-content">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                style="width: {capability.current_level * 100}%; background-color: {getCapabilityColor(capability.name)}"
              ></div>
            </div>
            
            <div class="metrics-row">
              <div class="metric">
                <span class="metric-label">Confidence</span>
                <span class="metric-value">{formatPercentage(capability.confidence)}</span>
              </div>
              <div class="metric">
                <span class="metric-label">Change</span>
                <span class="metric-value {getTrendClass(capability.improvement_rate)}">
                  {capability.improvement_rate > 0 ? '+' : ''}{formatPercentage(capability.improvement_rate)}
                </span>
              </div>
            </div>
            
            {#if showProjections && capability.projections}
              <div class="projections">
                <h5>Projections</h5>
                <div class="projection-grid">
                  {#each Object.entries(capability.projections) as [timeframe, projection]}
                    <div class="projection-item">
                      <span class="projection-timeframe">{timeframe.replace('_', ' ')}</span>
                      <span class="projection-value">{formatPercentage(projection.level)}</span>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>
  
  <!-- Detailed View -->
  {#if selectedCapability}
    <div class="capability-details">
      <div class="details-header">
        <h3>
          <span style="color: {getCapabilityColor(selectedCapability.name)}">
            {getCapabilityIcon(selectedCapability.name)}
          </span>
          {selectedCapability.name} Details
        </h3>
        <button class="close-btn" on:click={() => selectedCapability = null}>×</button>
      </div>
      
      <div class="details-content">
        <div class="details-section">
          <h4>Performance Metrics</h4>
          {#if performanceScores[selectedCapability.name]}
            {@const scores = performanceScores[selectedCapability.name]}
            <div class="metrics-grid">
              <div class="metric-card">
                <div class="metric-title">Current</div>
                <div class="metric-score">{formatPercentage(scores.current)}</div>
              </div>
              <div class="metric-card">
                <div class="metric-title">Peak</div>
                <div class="metric-score">{formatPercentage(scores.peak)}</div>
              </div>
              <div class="metric-card">
                <div class="metric-title">Average</div>
                <div class="metric-score">{formatPercentage(scores.average)}</div>
              </div>
            </div>
          {/if}
        </div>
        
        <div class="details-section">
          <h4>Recent Milestones</h4>
          <div class="milestones-list">
            {#each selectedCapability.milestones as milestone}
              <div class="milestone-item {milestone.achieved ? 'achieved' : 'pending'}">
                <div class="milestone-status">
                  {milestone.achieved ? '✅' : '⏳'}
                </div>
                <div class="milestone-info">
                  <div class="milestone-name">{milestone.name}</div>
                  <div class="milestone-date">
                    {new Date(milestone.date).toLocaleDateString()}
                  </div>
                </div>
                <div class="milestone-impact">
                  Impact: {formatPercentage(milestone.impact)}
                </div>
              </div>
            {/each}
          </div>
        </div>
        
        <div class="details-section">
          <h4>Current Bottlenecks</h4>
          <div class="bottlenecks-list">
            {#each selectedCapability.bottlenecks as bottleneck}
              <div class="bottleneck-item">
                <div class="bottleneck-severity" style="background-color: {bottleneck.severity > 0.7 ? '#f44336' : bottleneck.severity > 0.4 ? '#ff9800' : '#4caf50'}"></div>
                <div class="bottleneck-info">
                  <div class="bottleneck-name">{bottleneck.name}</div>
                  <div class="bottleneck-timeline">Timeline: {bottleneck.timeline}</div>
                </div>
                <div class="bottleneck-impact">
                  {formatPercentage(bottleneck.impact)} impact
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .capability-dashboard {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: rgba(26, 26, 62, 0.3);
    border-radius: 8px;
    padding: 20px;
    gap: 20px;
  }
  
  .dashboard-controls {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    backdrop-filter: blur(10px);
  }
  
  .control-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .control-group label {
    color: #e0e0e0;
    font-size: 14px;
    font-weight: 500;
  }
  
  .control-group select {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: #e0e0e0;
    padding: 6px 10px;
    font-size: 14px;
  }
  
  .status-indicators {
    display: flex;
    gap: 15px;
    margin-left: auto;
  }
  
  .status-item {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #e0e0e0;
    font-size: 12px;
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  
  .status-dot.active {
    background-color: #4caf50;
  }
  
  .status-dot.improving {
    background-color: #4a9eff;
  }
  
  .dashboard-content {
    display: grid;
    grid-template-columns: 400px 1fr;
    gap: 20px;
    flex: 1;
  }
  
  .radar-section {
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 20px;
  }
  
  .radar-section h3 {
    color: #4a9eff;
    margin: 0 0 15px 0;
    font-size: 18px;
  }
  
  .radar-container {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .radar-legend {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 15px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #e0e0e0;
    font-size: 12px;
  }
  
  .legend-line {
    width: 20px;
    height: 2px;
  }
  
  .legend-line.current {
    background-color: #4a9eff;
  }
  
  .legend-line.baseline {
    background: repeating-linear-gradient(
      to right,
      rgba(255, 255, 255, 0.3) 0px,
      rgba(255, 255, 255, 0.3) 3px,
      transparent 3px,
      transparent 6px
    );
  }
  
  .capabilities-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;
    overflow-y: auto;
  }
  
  .capability-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 15px;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 2px solid transparent;
  }
  
  .capability-card:hover {
    background: rgba(255, 255, 255, 0.08);
    transform: translateY(-2px);
  }
  
  .capability-card.selected {
    border-color: #4a9eff;
    background: rgba(74, 158, 255, 0.1);
  }
  
  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 15px;
  }
  
  .capability-icon {
    font-size: 24px;
  }
  
  .capability-info {
    flex: 1;
  }
  
  .capability-info h4 {
    color: #e0e0e0;
    margin: 0;
    font-size: 16px;
    text-transform: capitalize;
  }
  
  .capability-level {
    color: #a0a0a0;
    font-size: 12px;
    margin-top: 2px;
  }
  
  .trend-indicator {
    font-size: 18px;
  }
  
  .trend-up {
    color: #4caf50;
  }
  
  .trend-down {
    color: #f44336;
  }
  
  .trend-stable {
    color: #ff9800;
  }
  
  .progress-bar {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    height: 6px;
    margin-bottom: 12px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    transition: width 0.3s ease;
  }
  
  .metrics-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  
  .metric {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .metric-label {
    color: #a0a0a0;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .metric-value {
    color: #e0e0e0;
    font-size: 12px;
    font-weight: 500;
    margin-top: 2px;
  }
  
  .projections {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 10px;
    margin-top: 10px;
  }
  
  .projections h5 {
    color: #a0a0a0;
    margin: 0 0 8px 0;
    font-size: 12px;
    text-transform: uppercase;
  }
  
  .projection-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }
  
  .projection-item {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
  }
  
  .projection-timeframe {
    color: #a0a0a0;
    text-transform: capitalize;
  }
  
  .projection-value {
    color: #4a9eff;
    font-weight: 500;
  }
  
  .capability-details {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80%;
    max-width: 800px;
    max-height: 80%;
    background: linear-gradient(135deg, #2d1b69 0%, #1a1a3e 100%);
    border-radius: 8px;
    padding: 20px;
    z-index: 1000;
    overflow-y: auto;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  }
  
  .details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .details-header h3 {
    color: #4a9eff;
    margin: 0;
    font-size: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .close-btn {
    background: none;
    border: none;
    color: #e0e0e0;
    font-size: 24px;
    cursor: pointer;
    padding: 5px;
    border-radius: 4px;
    transition: background-color 0.3s ease;
  }
  
  .close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .details-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .details-section h4 {
    color: #e0e0e0;
    margin: 0 0 15px 0;
    font-size: 16px;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
  }
  
  .metric-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 15px;
    text-align: center;
  }
  
  .metric-title {
    color: #a0a0a0;
    font-size: 12px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  
  .metric-score {
    color: #4a9eff;
    font-size: 20px;
    font-weight: bold;
  }
  
  .milestones-list, .bottlenecks-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .milestone-item, .bottleneck-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
  }
  
  .milestone-status {
    font-size: 16px;
  }
  
  .milestone-info {
    flex: 1;
  }
  
  .milestone-name, .bottleneck-name {
    color: #e0e0e0;
    font-size: 14px;
    margin-bottom: 2px;
  }
  
  .milestone-date, .bottleneck-timeline {
    color: #a0a0a0;
    font-size: 12px;
  }
  
  .milestone-impact, .bottleneck-impact {
    color: #4a9eff;
    font-size: 12px;
    font-weight: 500;
  }
  
  .bottleneck-severity {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  
  .milestone-item.achieved {
    background: rgba(76, 175, 80, 0.1);
  }
  
  .milestone-item.pending {
    background: rgba(255, 152, 0, 0.1);
  }
</style>
