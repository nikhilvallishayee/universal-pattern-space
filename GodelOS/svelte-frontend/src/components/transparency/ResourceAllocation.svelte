<script>
  import { onMount, onDestroy } from 'svelte';
  import { cognitiveState } from '../../stores/cognitive.js';
  import * as d3 from 'd3';
  
  let chartContainer;
  let svg;
  let width = 400;
  let height = 300;
  let unsubscribe;
  
  // Reactive data for resource allocation
  $: resourceData = $cognitiveState.manifest_consciousness || {
    reasoning_engine: 0,
    knowledge_retrieval: 0,
    pattern_matching: 0,
    creative_generation: 0,
    reflection_processes: 0
  };
  
  // Resource allocation strategy
  let allocationStrategy = 'depth-first';
  let alternativeStrategies = ['breadth-first', 'parallel', 'adaptive', 'energy-efficient'];
  
  // Resource metrics
  $: totalResourceUsage = Object.values(resourceData).reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0) / Object.keys(resourceData).length;
  
  // Performance metrics
  $: performanceMetrics = {
    efficiency: Math.min(100, (totalResourceUsage * 1.2)),
    bottlenecks: Object.entries(resourceData).filter(([key, value]) => value > 0.8).length,
    optimization_potential: Math.max(0, 100 - totalResourceUsage * 100)
  };
  
  onMount(() => {
    initializeChart();
    unsubscribe = cognitiveState.subscribe(() => {
      updateChart();
    });
  });
  
  onDestroy(() => {
    if (unsubscribe) unsubscribe();
  });
  
  function initializeChart() {
    if (!chartContainer) return;
    
    // Clear any existing content
    d3.select(chartContainer).selectAll("*").remove();
    
    // Update dimensions based on container
    const rect = chartContainer.getBoundingClientRect();
    width = Math.max(400, rect.width - 40);
    height = Math.max(300, Math.min(400, rect.height - 40));
    
    svg = d3.select(chartContainer)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', 'rgba(0, 0, 0, 0.05)')
      .style('border-radius', '8px');
    
    updateChart();
  }
  
  function updateChart() {
    if (!svg) return;
    
    const margin = { top: 20, right: 120, bottom: 60, left: 150 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    
    // Clear existing chart
    svg.selectAll('g').remove();
    
    const chartGroup = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Prepare data
    const resources = Object.entries(resourceData)
      .filter(([key, value]) => typeof value === 'number')
      .map(([key, value]) => ({
        name: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: Math.max(0, Math.min(1, value)),
        percentage: Math.round(Math.max(0, Math.min(100, value * 100)))
      }))
      .sort((a, b) => b.value - a.value);
    
    if (resources.length === 0) return;
    
    // Create scales
    const yScale = d3.scaleBand()
      .domain(resources.map(d => d.name))
      .range([0, chartHeight])
      .padding(0.1);
    
    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, chartWidth]);
    
    // Color scale
    const colorScale = d3.scaleSequential(d3.interpolateViridis)
      .domain([0, 1]);
    
    // Create bars
    const bars = chartGroup.selectAll('.resource-bar')
      .data(resources)
      .enter()
      .append('g')
      .attr('class', 'resource-bar');
    
    // Background bars
    bars.append('rect')
      .attr('x', 0)
      .attr('y', d => yScale(d.name))
      .attr('width', chartWidth)
      .attr('height', yScale.bandwidth())
      .attr('fill', 'rgba(255, 255, 255, 0.1)')
      .attr('stroke', 'rgba(255, 255, 255, 0.2)')
      .attr('stroke-width', 1)
      .attr('rx', 4);
    
    // Value bars with animation
    bars.append('rect')
      .attr('x', 0)
      .attr('y', d => yScale(d.name))
      .attr('width', 0)
      .attr('height', yScale.bandwidth())
      .attr('fill', d => colorScale(d.value))
      .attr('rx', 4)
      .transition()
      .duration(1000)
      .ease(d3.easeElasticOut)
      .attr('width', d => xScale(d.value));
    
    // Value labels
    bars.append('text')
      .attr('x', d => Math.max(30, xScale(d.value) - 5))
      .attr('y', d => yScale(d.name) + yScale.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('fill', 'white')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .text(d => `${d.percentage}%`);
    
    // Resource labels
    chartGroup.selectAll('.resource-label')
      .data(resources)
      .enter()
      .append('text')
      .attr('class', 'resource-label')
      .attr('x', -10)
      .attr('y', d => yScale(d.name) + yScale.bandwidth() / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('fill', '#333')
      .attr('font-size', '12px')
      .text(d => d.name);
    
    // Add percentage scale
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d => `${Math.round(d * 100)}%`)
      .ticks(5);
    
    chartGroup.append('g')
      .attr('transform', `translate(0, ${chartHeight})`)
      .call(xAxis)
      .selectAll('text')
      .attr('fill', '#666')
      .attr('font-size', '10px');
    
    // Add performance indicators
    addPerformanceIndicators(chartGroup, chartWidth, chartHeight);
  }
  
  function addPerformanceIndicators(group, chartWidth, chartHeight) {
    const indicatorGroup = group.append('g')
      .attr('class', 'performance-indicators')
      .attr('transform', `translate(${chartWidth + 20}, 0)`);
    
    const indicators = [
      { label: 'Efficiency', value: performanceMetrics.efficiency, color: '#4CAF50' },
      { label: 'Bottlenecks', value: performanceMetrics.bottlenecks, color: '#FF9800', isCount: true },
      { label: 'Optimization', value: performanceMetrics.optimization_potential, color: '#2196F3' }
    ];
    
    indicators.forEach((indicator, i) => {
      const y = i * 40;
      
      // Label
      indicatorGroup.append('text')
        .attr('x', 0)
        .attr('y', y)
        .attr('fill', '#333')
        .attr('font-size', '11px')
        .attr('font-weight', 'bold')
        .text(indicator.label);
      
      // Value
      indicatorGroup.append('text')
        .attr('x', 0)
        .attr('y', y + 15)
        .attr('fill', indicator.color)
        .attr('font-size', '14px')
        .attr('font-weight', 'bold')
        .text(indicator.isCount ? indicator.value : `${Math.round(indicator.value)}%`);
    });
  }
  
  function changeStrategy(newStrategy) {
    allocationStrategy = newStrategy;
    // In a real implementation, this would trigger a backend API call
    console.log(`Resource allocation strategy changed to: ${newStrategy}`);
  }
</script>

<div class="resource-allocation-container">
  <div class="header">
    <h3>⚡ Cognitive Resource Allocation</h3>
    <div class="strategy-selector">
      <label for="strategy">Strategy:</label>
      <select id="strategy" bind:value={allocationStrategy} on:change={() => changeStrategy(allocationStrategy)}>
        <option value="depth-first">Depth-First</option>
        {#each alternativeStrategies as strategy}
          <option value={strategy}>{strategy.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</option>
        {/each}
      </select>
    </div>
  </div>
  
  <div class="current-query-section">
    <h4>Current Query Processing:</h4>
    <div class="chart-container" bind:this={chartContainer}>
      <!-- D3 chart will be rendered here -->
    </div>
  </div>
  
  <div class="metrics-section">
    <div class="metric-card">
      <span class="metric-label">Overall Efficiency</span>
      <span class="metric-value efficiency">{Math.round(performanceMetrics.efficiency)}%</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Active Bottlenecks</span>
      <span class="metric-value bottlenecks">{performanceMetrics.bottlenecks}</span>
    </div>
    <div class="metric-card">
      <span class="metric-label">Optimization Potential</span>
      <span class="metric-value optimization">{Math.round(performanceMetrics.optimization_potential)}%</span>
    </div>
  </div>
  
  <div class="alternative-strategies">
    <h4>Alternative Strategies Available:</h4>
    <div class="strategy-grid">
      {#each alternativeStrategies as strategy}
        <button 
          class="strategy-option {allocationStrategy === strategy ? 'active' : ''}"
          on:click={() => changeStrategy(strategy)}
        >
          {strategy.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
        </button>
      {/each}
    </div>
  </div>
  
  <div class="resource-insights">
    <h4>💡 Resource Insights:</h4>
    <div class="insights-list">
      {#if performanceMetrics.bottlenecks > 0}
        <div class="insight warning">
          <span class="insight-icon">⚠️</span>
          <span>Detected {performanceMetrics.bottlenecks} resource bottleneck{performanceMetrics.bottlenecks > 1 ? 's' : ''}</span>
        </div>
      {/if}
      
      {#if performanceMetrics.optimization_potential > 20}
        <div class="insight suggestion">
          <span class="insight-icon">💡</span>
          <span>Consider switching to parallel processing for {Math.round(performanceMetrics.optimization_potential)}% improvement</span>
        </div>
      {/if}
      
      {#if totalResourceUsage < 0.3}
        <div class="insight info">
          <span class="insight-icon">📊</span>
          <span>Low resource utilization - system ready for complex queries</span>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .resource-allocation-container {
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;
    min-height: 600px;
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
    color: #fff;
  }
  
  .strategy-selector {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .strategy-selector label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .strategy-selector select {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    padding: 5px 10px;
    font-size: 12px;
  }
  
  .current-query-section h4 {
    margin: 20px 0 10px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .chart-container {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    min-height: 300px;
    margin-bottom: 20px;
  }
  
  .metrics-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
  }
  
  .metric-card {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .metric-label {
    display: block;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 5px;
  }
  
  .metric-value {
    display: block;
    font-size: 18px;
    font-weight: bold;
  }
  
  .metric-value.efficiency { color: #4CAF50; }
  .metric-value.bottlenecks { color: #FF9800; }
  .metric-value.optimization { color: #2196F3; }
  
  .alternative-strategies h4 {
    margin: 20px 0 10px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .strategy-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .strategy-option {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 6px;
    color: white;
    padding: 8px 12px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .strategy-option:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }
  
  .strategy-option.active {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.6);
    font-weight: bold;
  }
  
  .resource-insights h4 {
    margin: 20px 0 10px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .insights-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .insight {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 10px;
    font-size: 12px;
    border-left: 3px solid;
  }
  
  .insight.warning {
    border-left-color: #FF9800;
    background: rgba(255, 152, 0, 0.1);
  }
  
  .insight.suggestion {
    border-left-color: #4CAF50;
    background: rgba(76, 175, 80, 0.1);
  }
  
  .insight.info {
    border-left-color: #2196F3;
    background: rgba(33, 150, 243, 0.1);
  }
  
  .insight-icon {
    font-size: 14px;
  }
</style>
