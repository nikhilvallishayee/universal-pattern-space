<script>
  import { onMount, onDestroy } from 'svelte';
  import { cognitiveState, uiState } from '../../stores/cognitive.js';
  import * as d3 from 'd3';
  
  let processContainer;
  let timelineContainer;
  let svg;
  let timelineSvg;
  let width = 600;
  let height = 400;
  let timelineHeight = 200;
  let unsubscribe;
  
  // Process insight data
  $: processData = $cognitiveState.agentic_processes || [];
  $: daemonData = $cognitiveState.daemon_threads || [];
  $: systemHealth = $cognitiveState.system_health || {};
  
  // Process categories and their visual representations
  const processTypes = {
    reasoning: { color: '#4CAF50', icon: '🧠' },
    knowledge: { color: '#2196F3', icon: '📚' },
    reflection: { color: '#9C27B0', icon: '🎭' },
    monitoring: { color: '#FF9800', icon: '👁️' },
    learning: { color: '#00BCD4', icon: '🎓' },
    daemon: { color: '#607D8B', icon: '⚙️' }
  };
  
  // Timeline data for process lifecycle
  let timelineData = [];
  let selectedProcess = null;
  
  onMount(() => {
    initializeVisualizations();
    unsubscribe = cognitiveState.subscribe(() => {
      updateVisualizations();
    });
    
    // simulateProcessUpdates() call REMOVED - no synthetic process updates
  });
  
  onDestroy(() => {
    if (unsubscribe) unsubscribe();
  });
  
  function initializeVisualizations() {
    if (!processContainer || !timelineContainer) return;
    
    // Initialize process insight chart
    const rect = processContainer.getBoundingClientRect();
    width = Math.max(600, rect.width - 40);
    height = Math.max(400, rect.height - 40);
    
    svg = d3.select(processContainer)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', 'rgba(0, 0, 0, 0.05)')
      .style('border-radius', '8px');
    
    // Initialize timeline chart
    timelineSvg = d3.select(timelineContainer)
      .append('svg')
      .attr('width', width)
      .attr('height', timelineHeight)
      .style('background', 'rgba(0, 0, 0, 0.05)')
      .style('border-radius', '8px');
    
    updateVisualizations();
  }
  
  function updateVisualizations() {
    updateProcessInsight();
    updateTimeline();
  }
  
  function updateProcessInsight() {
    if (!svg) return;
    
    svg.selectAll('*').remove();
    
    const margin = { top: 20, right: 20, bottom: 60, left: 20 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    const group = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Combine agentic processes and daemon threads
    const allProcesses = [
      ...processData.map(p => ({ ...p, type: p.type || 'reasoning', category: 'agentic' })),
      ...daemonData.map(d => ({ ...d, type: 'daemon', category: 'daemon' }))
    ];
    
    if (allProcesses.length === 0) {
      // Show empty state
      group.append('text')
        .attr('x', chartWidth / 2)
        .attr('y', chartHeight / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#666')
        .attr('font-size', '16px')
        .text('No active processes detected');
      return;
    }
    
    // Create force simulation for process bubbles
    const simulation = d3.forceSimulation(allProcesses)
      .force('x', d3.forceX(chartWidth / 2).strength(0.1))
      .force('y', d3.forceY(chartHeight / 2).strength(0.1))
      .force('collision', d3.forceCollide().radius(d => getProcessRadius(d) + 2))
      .force('charge', d3.forceManyBody().strength(-50));
    
    // Create process bubbles
    const processGroups = group.selectAll('.process-group')
      .data(allProcesses)
      .enter()
      .append('g')
      .attr('class', 'process-group')
      .style('cursor', 'pointer')
      .on('click', selectProcess);
    
    // Process circles
    processGroups.append('circle')
      .attr('r', 0)
      .attr('fill', d => processTypes[d.type]?.color || '#999')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', 0.8)
      .transition()
      .duration(1000)
      .ease(d3.easeElasticOut)
      .attr('r', getProcessRadius);
    
    // Process icons/labels
    processGroups.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', 'white')
      .attr('font-size', d => Math.max(10, getProcessRadius(d) / 3))
      .attr('font-weight', 'bold')
      .text(d => processTypes[d.type]?.icon || '•');
    
    // Process names (on hover)
    processGroups.append('title')
      .text(d => `${d.name || d.type}: ${d.status || 'active'}`);
    
    // Update positions from simulation
    simulation.on('tick', () => {
      processGroups
        .attr('transform', d => `translate(${d.x}, ${d.y})`);
    });
    
    // Add legend
    addProcessLegend(group, chartWidth, chartHeight);
  }
  
  function getProcessRadius(process) {
    const baseRadius = 20;
    const priority = process.priority || 1;
    const load = process.cpu_usage || process.load || 0.5;
    return baseRadius + (priority * 5) + (load * 10);
  }
  
  function addProcessLegend(group, chartWidth, chartHeight) {
    const legend = group.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(10, ${chartHeight - 50})`);
    
    const legendData = Object.entries(processTypes);
    
    const legendItems = legend.selectAll('.legend-item')
      .data(legendData)
      .enter()
      .append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(${i * 80}, 0)`);
    
    legendItems.append('circle')
      .attr('r', 8)
      .attr('fill', d => d[1].color);
    
    legendItems.append('text')
      .attr('x', 15)
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .text(d => d[0]);
  }
  
  function updateTimeline() {
    if (!timelineSvg) return;
    
    timelineSvg.selectAll('*').remove();
    
    if (timelineData.length === 0) {
      generateTimelineData();
    }
    
    const margin = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = timelineHeight - margin.top - margin.bottom;
    
    const group = timelineSvg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Time scale
    const now = new Date();
    const timeExtent = [new Date(now - 60000), now]; // Last minute
    const xScale = d3.scaleTime()
      .domain(timeExtent)
      .range([0, chartWidth]);
    
    // Process scale
    const processes = [...new Set(timelineData.map(d => d.process))];
    const yScale = d3.scaleBand()
      .domain(processes)
      .range([0, chartHeight])
      .padding(0.1);
    
    // Draw timeline bars
    const bars = group.selectAll('.timeline-bar')
      .data(timelineData)
      .enter()
      .append('rect')
      .attr('class', 'timeline-bar')
      .attr('x', d => xScale(d.start))
      .attr('y', d => yScale(d.process))
      .attr('width', d => Math.max(2, xScale(d.end) - xScale(d.start)))
      .attr('height', yScale.bandwidth())
      .attr('fill', d => processTypes[d.type]?.color || '#999')
      .attr('opacity', 0.7)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('opacity', 1);
        // Show tooltip
      })
      .on('mouseout', function(event, d) {
        d3.select(this).attr('opacity', 0.7);
      });
    
    // Add time axis
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d3.timeFormat('%M:%S'));
    
    group.append('g')
      .attr('transform', `translate(0, ${chartHeight})`)
      .call(xAxis);
    
    // Add process labels
    group.selectAll('.process-label')
      .data(processes)
      .enter()
      .append('text')
      .attr('class', 'process-label')
      .attr('x', -10)
      .attr('y', d => yScale(d) + yScale.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .text(d => d);
  }
  
  function generateTimelineData() {
    const now = new Date();
    const processes = ['reasoning-001', 'knowledge-002', 'reflection-003', 'monitor-daemon'];
    
    timelineData = [];
    
    processes.forEach((process, i) => {
      const startTime = new Date(now - Math.random() * 50000);
      const duration = Math.random() * 20000 + 5000;
      const endTime = new Date(startTime.getTime() + duration);
      
      timelineData.push({
        process,
        type: process.includes('daemon') ? 'daemon' : 'reasoning',
        start: startTime,
        end: endTime,
        status: Math.random() > 0.8 ? 'completed' : 'active'
      });
    });
  }
  
  function selectProcess(event, process) {
    selectedProcess = process;
    // Highlight selected process
    d3.selectAll('.process-group circle')
      .attr('stroke-width', d => d === process ? 4 : 2)
      .attr('stroke', d => d === process ? '#FFD700' : '#fff');
  }
  
  // simulateProcessUpdates function REMOVED - no synthetic process simulation
  
  // Health status indicator
  $: healthStatus = getHealthStatus(systemHealth);
  
  function getHealthStatus(health) {
    const cpu = health.cpu_usage || 0;
    const memory = health.memory_usage || 0;
    const avgUsage = (cpu + memory) / 2;
    
    if (avgUsage < 0.3) return { status: 'optimal', color: '#4CAF50', message: 'System running optimally' };
    if (avgUsage < 0.7) return { status: 'moderate', color: '#FF9800', message: 'Moderate resource usage' };
    return { status: 'high', color: '#F44336', message: 'High resource usage detected' };
  }
</script>

<div class="process-insight-container">
  <div class="header">
    <h3>🔍 Process Insight & Monitoring</h3>
    <div class="health-indicator">
      <span class="health-dot" style="background-color: {healthStatus.color}"></span>
      <span class="health-text">{healthStatus.message}</span>
    </div>
  </div>
  
  <div class="main-content">
    <div class="process-overview">
      <h4>Active Processes Overview</h4>
      <div class="chart-container" bind:this={processContainer}>
        <!-- D3 process visualization will be rendered here -->
      </div>
    </div>
    
    <div class="process-details">
      {#if selectedProcess}
        <div class="selected-process">
          <h4>📋 Process Details</h4>
          <div class="process-card">
            <div class="process-header">
              <span class="process-icon">{processTypes[selectedProcess.type]?.icon || '•'}</span>
              <span class="process-name">{selectedProcess.name || selectedProcess.type}</span>
              <span class="process-status {selectedProcess.status || 'active'}">{selectedProcess.status || 'active'}</span>
            </div>
            <div class="process-metrics">
              <div class="metric">
                <span class="metric-label">Priority:</span>
                <span class="metric-value">{selectedProcess.priority || 'Normal'}</span>
              </div>
              <div class="metric">
                <span class="metric-label">CPU Usage:</span>
                <span class="metric-value">{Math.round((selectedProcess.cpu_usage || 0.3) * 100)}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Memory:</span>
                <span class="metric-value">{Math.round((selectedProcess.memory_usage || 0.2) * 100)}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Uptime:</span>
                <span class="metric-value">{selectedProcess.uptime || '2m 34s'}</span>
              </div>
            </div>
          </div>
        </div>
      {:else}
        <div class="no-selection">
          <span class="selection-hint">👆 Click on a process bubble to view details</span>
        </div>
      {/if}
      
      <div class="system-metrics">
        <h4>📊 System Metrics</h4>
        <div class="metrics-grid">
          <div class="metric-card">
            <span class="metric-label">Total Processes</span>
            <span class="metric-value">{processData.length + daemonData.length}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Active Threads</span>
            <span class="metric-value">{daemonData.length}</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">CPU Load</span>
            <span class="metric-value">{Math.round((systemHealth.cpu_usage || 0.25) * 100)}%</span>
          </div>
          <div class="metric-card">
            <span class="metric-label">Memory Usage</span>
            <span class="metric-value">{Math.round((systemHealth.memory_usage || 0.45) * 100)}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="timeline-section">
    <h4>⏱️ Process Timeline (Last 60 seconds)</h4>
    <div class="timeline-container" bind:this={timelineContainer}>
      <!-- D3 timeline will be rendered here -->
    </div>
  </div>
  
  <div class="process-controls">
    <h4>🎛️ Process Controls</h4>
    <div class="controls-grid">
      <button class="control-btn refresh" on:click={() => updateVisualizations()}>
        🔄 Refresh
      </button>
      <button class="control-btn pause">
        ⏸️ Pause Monitoring
      </button>
      <button class="control-btn analyze">
        📈 Analyze Performance
      </button>
      <button class="control-btn export">
        📄 Export Logs
      </button>
    </div>
  </div>
</div>

<style>
  .process-insight-container {
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;
    min-height: 700px;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .header h3 {
    margin: 0;
    font-size: 18px;
  }
  
  .health-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
  }
  
  .health-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
  
  .main-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }
  
  .process-overview h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .chart-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    min-height: 400px;
  }
  
  .process-details {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .selected-process h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .process-card {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .process-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .process-icon {
    font-size: 20px;
  }
  
  .process-name {
    font-weight: bold;
    flex: 1;
  }
  
  .process-status {
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: bold;
    text-transform: uppercase;
  }
  
  .process-status.active {
    background: rgba(76, 175, 80, 0.3);
    color: #4CAF50;
  }
  
  .process-status.completed {
    background: rgba(33, 150, 243, 0.3);
    color: #2196F3;
  }
  
  .process-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  
  .metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .metric-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .metric-value {
    font-size: 12px;
    font-weight: bold;
  }
  
  .no-selection {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border: 2px dashed rgba(255, 255, 255, 0.2);
  }
  
  .selection-hint {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    text-align: center;
  }
  
  .system-metrics h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  
  .metric-card {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 10px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .metric-card .metric-label {
    display: block;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 5px;
  }
  
  .metric-card .metric-value {
    display: block;
    font-size: 16px;
    font-weight: bold;
    color: white;
  }
  
  .timeline-section {
    margin-bottom: 20px;
  }
  
  .timeline-section h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .timeline-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    min-height: 200px;
  }
  
  .process-controls h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .controls-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
  }
  
  .control-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    padding: 10px 15px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .control-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
  
  .control-btn.refresh:hover {
    background: rgba(76, 175, 80, 0.3);
  }
</style>
