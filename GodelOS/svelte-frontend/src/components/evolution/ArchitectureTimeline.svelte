<script>
  import { onMount, onDestroy } from 'svelte';
  import { evolutionState } from '../../stores/cognitive.js';
  import * as d3 from 'd3';
  
  let container;
  let svg;
  let width = 1000;
  let height = 600;
  let timelineData = [];
  let selectedEvent = null;
  let zoomLevel = 1;
  let timeRange = 'month'; // week, month, quarter, year, all
  let eventFilter = 'all'; // all, critical, major, minor
  
  const margin = { top: 60, right: 40, bottom: 60, left: 60 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.bottom - margin.top;
  
  // Event type configurations
  const eventTypes = {
    architecture_change: {
      icon: '🏗️',
      color: '#4a9eff',
      label: 'Architecture Change'
    },
    capability_milestone: {
      icon: '🎯',
      color: '#4caf50',
      label: 'Capability Milestone'
    },
    performance_improvement: {
      icon: '📈',
      color: '#ff9800',
      label: 'Performance Improvement'
    },
    integration_update: {
      icon: '🔗',
      color: '#9c27b0',
      label: 'Integration Update'
    },
    learning_breakthrough: {
      icon: '💡',
      color: '#e91e63',
      label: 'Learning Breakthrough'
    },
    system_optimization: {
      icon: '⚡',
      color: '#00bcd4',
      label: 'System Optimization'
    },
    error_resolution: {
      icon: '🔧',
      color: '#f44336',
      label: 'Error Resolution'
    },
    feature_addition: {
      icon: '✨',
      color: '#ffc107',
      label: 'Feature Addition'
    }
  };
  
  // Impact levels
  const impactLevels = {
    critical: { size: 12, priority: 1 },
    major: { size: 8, priority: 2 },
    minor: { size: 5, priority: 3 }
  };
  
  onMount(() => {
    initializeVisualization();
    loadTimelineData();
    
    // Subscribe to evolution state updates
    const unsubscribe = evolutionState.subscribe(state => {
      if (state.timeline) {
        updateTimelineData(state.timeline);
      }
    });
    
    // Update every 60 seconds
    const interval = setInterval(loadTimelineData, 60000);
    
    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  });
  
  onDestroy(() => {
    if (svg) {
      svg.remove();
    }
  });
  
  function initializeVisualization() {
    // Clear any existing SVG
    d3.select(container).selectAll('*').remove();
    
    svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', 'linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)');
    
    // Add title
    svg.append('text')
      .attr('x', width / 2)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#e0e0e0')
      .attr('font-size', '18px')
      .attr('font-weight', 'bold')
      .text('GödelOS Architecture Evolution Timeline');
    
    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);
    
    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on('zoom', handleZoom);
    
    svg.call(zoom);
    
    // Add axis groups
    g.append('g').attr('class', 'x-axis');
    g.append('g').attr('class', 'timeline-line');
    g.append('g').attr('class', 'events');
    g.append('g').attr('class', 'connections');
  }
  
  async function loadTimelineData() {
    try {
      // Try to get real timeline data from API
      const response = await fetch(`${API_BASE}/api/evolution/timeline`);
      if (response.ok) {
        const data = await response.json();
        timelineData = data.events || [];
        console.log('✅ Loaded timeline data:', timelineData);
      } else {
        console.error('❌ No timeline data available from backend');
        timelineData = [];
      }
    } catch (error) {
      console.error('❌ Error loading timeline data:', error);
      timelineData = [];
    }
  }
  
  // ALL MOCK DATA GENERATION FUNCTIONS REMOVED
  // - generateMockTimelineData() REMOVED
  // - generateEventTitle() REMOVED  
  // - generateEventDescription() REMOVED
  // - generateAffectedComponents() REMOVED
  // - generateEventMetrics() REMOVED
  
  function updateVisualization() {
    if (!svg || timelineData.length === 0) return;
    
    const g = svg.select('g');
    
    // Filter events based on current filter
    const filteredEvents = filterEvents(timelineData);
    
    // Create time scale
    const timeExtent = d3.extent(filteredEvents, d => d.timestamp);
    const xScale = d3.scaleTime()
      .domain(timeExtent)
      .range([0, innerWidth]);
    
    // Create lanes for different event types
    const eventTypeLanes = {};
    Object.keys(eventTypes).forEach((type, i) => {
      eventTypeLanes[type] = i * 40;
    });
    
    // Update x-axis
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d3.timeFormat('%m/%d %H:%M'));
    
    g.select('.x-axis')
      .attr('transform', `translate(0, ${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .attr('fill', '#a0a0a0')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)');
    
    // Draw timeline line
    g.select('.timeline-line')
      .selectAll('.timeline-base')
      .data([null])
      .join('line')
      .attr('class', 'timeline-base')
      .attr('x1', 0)
      .attr('y1', innerHeight / 2)
      .attr('x2', innerWidth)
      .attr('y2', innerHeight / 2)
      .attr('stroke', 'rgba(255, 255, 255, 0.2)')
      .attr('stroke-width', 2);
    
    // Draw event lanes
    Object.entries(eventTypeLanes).forEach(([type, y]) => {
      g.select('.timeline-line')
        .append('line')
        .attr('x1', 0)
        .attr('y1', y + 20)
        .attr('x2', innerWidth)
        .attr('y2', y + 20)
        .attr('stroke', eventTypes[type].color)
        .attr('stroke-width', 1)
        .attr('opacity', 0.3);
      
      // Add lane labels
      g.select('.timeline-line')
        .append('text')
        .attr('x', -10)
        .attr('y', y + 25)
        .attr('text-anchor', 'end')
        .attr('fill', eventTypes[type].color)
        .attr('font-size', '10px')
        .text(eventTypes[type].label);
    });
    
    // Draw connections between related events
    const connections = g.select('.connections')
      .selectAll('.connection')
      .data(getEventConnections(filteredEvents));
    
    connections.exit().remove();
    
    connections.enter()
      .append('path')
      .attr('class', 'connection')
      .merge(connections)
      .attr('d', d => {
        const sourceX = xScale(d.source.timestamp);
        const targetX = xScale(d.target.timestamp);
        const sourceY = eventTypeLanes[d.source.type] + 20;
        const targetY = eventTypeLanes[d.target.type] + 20;
        
        return `M ${sourceX} ${sourceY} Q ${(sourceX + targetX) / 2} ${Math.min(sourceY, targetY) - 30} ${targetX} ${targetY}`;
      })
      .attr('stroke', '#4a9eff')
      .attr('stroke-width', 1)
      .attr('fill', 'none')
      .attr('opacity', 0.4)
      .attr('stroke-dasharray', '2,2');
    
    // Draw events
    const events = g.select('.events')
      .selectAll('.event')
      .data(filteredEvents, d => d.id);
    
    events.exit().remove();
    
    const eventsEnter = events.enter()
      .append('g')
      .attr('class', 'event')
      .style('cursor', 'pointer');
    
    // Add event circles
    eventsEnter.append('circle')
      .attr('class', 'event-circle')
      .attr('r', 0);
    
    // Add event icons
    eventsEnter.append('text')
      .attr('class', 'event-icon')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '12px')
      .attr('opacity', 0);
    
    // Merge and update
    const eventsUpdate = events.merge(eventsEnter);
    
    eventsUpdate
      .attr('transform', d => `translate(${xScale(d.timestamp)}, ${eventTypeLanes[d.type] + 20})`)
      .on('click', handleEventClick)
      .on('mouseenter', handleEventHover)
      .on('mouseleave', handleEventLeave);
    
    eventsUpdate.select('.event-circle')
      .transition()
      .duration(300)
      .attr('r', d => impactLevels[d.impact].size)
      .attr('fill', d => eventTypes[d.type].color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('opacity', d => selectedEvent?.id === d.id ? 1 : 0.8);
    
    eventsUpdate.select('.event-icon')
      .text(d => eventTypes[d.type].icon)
      .transition()
      .duration(300)
      .attr('opacity', 1);
  }
  
  function filterEvents(events) {
    if (eventFilter === 'all') {
      return events;
    }
    return events.filter(event => event.impact === eventFilter);
  }
  
  function getEventConnections(events) {
    const connections = [];
    events.forEach(event => {
      event.related_events.forEach(relatedId => {
        const relatedEvent = events.find(e => e.id === relatedId);
        if (relatedEvent) {
          connections.push({
            source: event,
            target: relatedEvent
          });
        }
      });
    });
    return connections;
  }
  
  function handleEventClick(event, d) {
    selectedEvent = selectedEvent?.id === d.id ? null : d;
    updateVisualization();
  }
  
  function handleEventHover(event, d) {
    // Show tooltip
    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'timeline-tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.9)')
      .style('color', '#fff')
      .style('padding', '10px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '1000')
      .html(`
        <strong>${d.title}</strong><br>
        <small>${new Date(d.timestamp).toLocaleString()}</small><br>
        Impact: ${d.impact}<br>
        Components: ${d.affected_components.join(', ')}
      `);
    
    tooltip
      .style('left', (event.pageX + 10) + 'px')
      .style('top', (event.pageY - 10) + 'px');
  }
  
  function handleEventLeave(event, d) {
    d3.selectAll('.timeline-tooltip').remove();
  }
  
  function handleZoom(event) {
    zoomLevel = event.transform.k;
    const g = svg.select('g');
    g.attr('transform', `translate(${margin.left + event.transform.x}, ${margin.top + event.transform.y}) scale(${event.transform.k})`);
  }
  
  function updateTimelineData(timeline) {
    timelineData = timeline || [];
    updateVisualization();
  }
  
  function getTimeSpanMs(range) {
    const spans = {
      week: 7 * 24 * 60 * 60 * 1000,
      month: 30 * 24 * 60 * 60 * 1000,
      quarter: 90 * 24 * 60 * 60 * 1000,
      year: 365 * 24 * 60 * 60 * 1000,
      all: 5 * 365 * 24 * 60 * 60 * 1000 // 5 years
    };
    return spans[range] || spans.month;
  }
  
  function handleTimeRangeChange() {
    loadTimelineData();
  }
  
  function handleFilterChange() {
    updateVisualization();
  }
  
  function resetZoom() {
    svg.transition()
      .duration(300)
      .call(d3.zoom().transform, d3.zoomIdentity);
    zoomLevel = 1;
  }
</script>

<div class="architecture-timeline">
  <!-- Controls -->
  <div class="timeline-controls">
    <div class="control-section">
      <div class="control-group">
        <label>Time Range:</label>
        <select bind:value={timeRange} on:change={handleTimeRangeChange}>
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="quarter">Last Quarter</option>
          <option value="year">Last Year</option>
          <option value="all">All Time</option>
        </select>
      </div>
      
      <div class="control-group">
        <label>Event Filter:</label>
        <select bind:value={eventFilter} on:change={handleFilterChange}>
          <option value="all">All Events</option>
          <option value="critical">Critical Only</option>
          <option value="major">Major Only</option>
          <option value="minor">Minor Only</option>
        </select>
      </div>
      
      <button class="reset-zoom-btn" on:click={resetZoom}>
        Reset Zoom
      </button>
    </div>
    
    <div class="timeline-stats">
      <div class="stat-item">
        <span class="stat-value">{timelineData.length}</span>
        <span class="stat-label">Total Events</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{timelineData.filter(e => e.impact === 'critical').length}</span>
        <span class="stat-label">Critical</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{Math.round(zoomLevel * 100)}%</span>
        <span class="stat-label">Zoom</span>
      </div>
    </div>
  </div>
  
  <!-- Timeline Visualization -->
  <div class="timeline-container" bind:this={container}></div>
  
  <!-- Legend -->
  <div class="timeline-legend">
    <h4>Event Types</h4>
    <div class="legend-grid">
      {#each Object.entries(eventTypes) as [type, config]}
        <div class="legend-item">
          <div class="legend-icon" style="color: {config.color}">
            {config.icon}
          </div>
          <span class="legend-label">{config.label}</span>
        </div>
      {/each}
    </div>
    
    <h4>Impact Levels</h4>
    <div class="impact-legend">
      {#each Object.entries(impactLevels) as [level, config]}
        <div class="impact-item">
          <div 
            class="impact-circle" 
            style="width: {config.size * 2}px; height: {config.size * 2}px; background-color: #4a9eff"
          ></div>
          <span class="impact-label">{level}</span>
        </div>
      {/each}
    </div>
  </div>
  
  <!-- Event Details Panel -->
  {#if selectedEvent}
    <div class="event-details">
      <div class="details-header">
        <div class="event-title">
          <span class="event-type-icon" style="color: {eventTypes[selectedEvent.type].color}">
            {eventTypes[selectedEvent.type].icon}
          </span>
          <div>
            <h3>{selectedEvent.title}</h3>
            <div class="event-meta">
              {new Date(selectedEvent.timestamp).toLocaleString()} • 
              {selectedEvent.impact} impact • 
              {selectedEvent.confidence ? Math.round(selectedEvent.confidence * 100) + '% confidence' : 'Unknown confidence'}
            </div>
          </div>
        </div>
        <button class="close-details" on:click={() => selectedEvent = null}>×</button>
      </div>
      
      <div class="details-content">
        <div class="detail-section">
          <h4>Description</h4>
          <p>{selectedEvent.description}</p>
        </div>
        
        <div class="detail-section">
          <h4>Affected Components</h4>
          <div class="component-tags">
            {#each selectedEvent.affected_components as component}
              <span class="component-tag">{component}</span>
            {/each}
          </div>
        </div>
        
        <div class="detail-section">
          <h4>Impact Metrics</h4>
          <div class="metrics-grid">
            {#each Object.entries(selectedEvent.metrics) as [metric, value]}
              <div class="metric-item">
                <span class="metric-name">{metric.replace('_', ' ')}</span>
                <span class="metric-value {value > 0 ? 'positive' : 'negative'}">
                  {value > 0 ? '+' : ''}{(value * 100).toFixed(1)}%
                </span>
              </div>
            {/each}
          </div>
        </div>
        
        {#if selectedEvent.related_events.length > 0}
          <div class="detail-section">
            <h4>Related Events</h4>
            <div class="related-events">
              {#each selectedEvent.related_events as relatedId}
                {@const relatedEvent = timelineData.find(e => e.id === relatedId)}
                {#if relatedEvent}
                  <div 
                    class="related-event"
                    on:click={() => selectedEvent = relatedEvent}
                  >
                    <span class="related-icon" style="color: {eventTypes[relatedEvent.type].color}">
                      {eventTypes[relatedEvent.type].icon}
                    </span>
                    <span class="related-title">{relatedEvent.title}</span>
                  </div>
                {/if}
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .architecture-timeline {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: linear-gradient(135deg, #1a1a3e 0%, #2d1b69 100%);
    border-radius: 8px;
    padding: 20px;
    gap: 20px;
  }
  
  .timeline-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    backdrop-filter: blur(10px);
  }
  
  .control-section {
    display: flex;
    gap: 20px;
    align-items: center;
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
  
  .reset-zoom-btn {
    background: rgba(74, 158, 255, 0.2);
    border: 1px solid #4a9eff;
    border-radius: 4px;
    color: #4a9eff;
    padding: 8px 12px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .reset-zoom-btn:hover {
    background: rgba(74, 158, 255, 0.3);
  }
  
  .timeline-stats {
    display: flex;
    gap: 20px;
  }
  
  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .stat-value {
    color: #4a9eff;
    font-size: 18px;
    font-weight: bold;
  }
  
  .stat-label {
    color: #a0a0a0;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .timeline-container {
    flex: 1;
    min-height: 400px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 6px;
    overflow: hidden;
  }
  
  .timeline-legend {
    display: grid;
    grid-template-columns: 1fr 200px;
    gap: 20px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
  }
  
  .timeline-legend h4 {
    color: #e0e0e0;
    margin: 0 0 10px 0;
    font-size: 14px;
  }
  
  .legend-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 8px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .legend-icon {
    font-size: 16px;
  }
  
  .legend-label {
    color: #e0e0e0;
    font-size: 12px;
  }
  
  .impact-legend {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .impact-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .impact-circle {
    border-radius: 50%;
    border: 2px solid #fff;
  }
  
  .impact-label {
    color: #e0e0e0;
    font-size: 12px;
    text-transform: capitalize;
  }
  
  .event-details {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70%;
    max-width: 700px;
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
    align-items: flex-start;
    margin-bottom: 20px;
  }
  
  .event-title {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }
  
  .event-type-icon {
    font-size: 24px;
    margin-top: 4px;
  }
  
  .event-title h3 {
    color: #4a9eff;
    margin: 0;
    font-size: 18px;
  }
  
  .event-meta {
    color: #a0a0a0;
    font-size: 12px;
    margin-top: 4px;
  }
  
  .close-details {
    background: none;
    border: none;
    color: #e0e0e0;
    font-size: 24px;
    cursor: pointer;
    padding: 5px;
    border-radius: 4px;
    transition: background-color 0.3s ease;
  }
  
  .close-details:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .details-content {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .detail-section h4 {
    color: #e0e0e0;
    margin: 0 0 10px 0;
    font-size: 14px;
  }
  
  .detail-section p {
    color: #a0a0a0;
    margin: 0;
    line-height: 1.5;
  }
  
  .component-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .component-tag {
    background: rgba(74, 158, 255, 0.2);
    color: #4a9eff;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    border: 1px solid rgba(74, 158, 255, 0.3);
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 10px;
  }
  
  .metric-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }
  
  .metric-name {
    color: #a0a0a0;
    font-size: 12px;
    text-transform: capitalize;
  }
  
  .metric-value {
    font-size: 12px;
    font-weight: 500;
  }
  
  .metric-value.positive {
    color: #4caf50;
  }
  
  .metric-value.negative {
    color: #f44336;
  }
  
  .related-events {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .related-event {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }
  
  .related-event:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .related-icon {
    font-size: 16px;
  }
  
  .related-title {
    color: #e0e0e0;
    font-size: 13px;
  }
  
  /* Global styles for timeline tooltips */
  :global(.timeline-tooltip) {
    pointer-events: none !important;
  }
</style>
