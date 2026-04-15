<script>
  import { onMount, onDestroy } from 'svelte';
  import { GödelOSAPI } from '../../utils/api.js';
  import * as d3 from 'd3';

  export let selectedTarget = null;

  // Component state
  let container;
  let provenanceData = {
    chains: new Map(),
    records: new Map(),
    attributions: new Map(),
    snapshots: new Map()
  };
  let loading = false;
  let error = null;
  let selectedChain = null;
  let viewMode = 'timeline'; // timeline, dependency, attribution, audit
  let timeRange = { hours: 24 }; // Last 24 hours by default
  let searchTerm = '';
  let refreshInterval = null;

  // Visualization elements
  let svg;
  let width = 800;
  let height = 600;
  let margin = { top: 20, right: 20, bottom: 40, left: 60 };

  onMount(async () => {
    setupVisualization();
    await loadProvenanceData();
    startAutoRefresh();
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  function setupVisualization() {
    if (!container) return;

    const rect = container.getBoundingClientRect();
    width = Math.max(800, rect.width - 40);
    height = Math.max(400, rect.height - 100);

    svg = d3.select(container)
      .select('.provenance-viz')
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('background', '#fafafa')
      .style('border', '1px solid #ddd')
      .style('border-radius', '8px');

    svg.append('g').attr('class', 'main-group');
  }

  async function loadProvenanceData() {
    loading = true;
    error = null;

    try {
      // Load provenance chains and statistics
      const [chains, stats, attribution] = await Promise.all([
        queryProvenance('backward_trace'),
        GödelOSAPI.fetchTransparencyStatistics(),
        selectedTarget ? getAttributionChain(selectedTarget) : Promise.resolve(null)
      ]);

      if (chains?.results) {
        updateProvenanceData(chains.results);
      }

      if (attribution) {
        provenanceData.attributions.set(selectedTarget, attribution);
      }

      updateVisualization();
    } catch (err) {
      console.error('Failed to load provenance data:', err);
      error = `Failed to load provenance data: ${err.message}`;
    } finally {
      loading = false;
    }
  }

  async function queryProvenance(queryType = 'backward_trace', targetId = null) {
    try {
      const response = await fetch('http://localhost:8000/api/transparency/provenance/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_id: targetId || selectedTarget || 'default',
          query_type: queryType,
          max_depth: 5,
          time_window_start: timeRange.start || null,
          time_window_end: timeRange.end || null
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Provenance query failed:', error);
      return null;
    }
  }

  async function getAttributionChain(targetId) {
    try {
      const response = await fetch(`http://localhost:8000/api/transparency/provenance/attribution/${targetId}`);
      if (!response.ok) return null;
      return await response.json();
    } catch (error) {
      console.error('Attribution query failed:', error);
      return null;
    }
  }

  async function getProvenanceStatistics() {
    try {
      const response = await fetch('http://localhost:8000/api/transparency/provenance/statistics');
      if (!response.ok) return null;
      return await response.json();
    } catch (error) {
      console.error('Statistics query failed:', error);
      return null;
    }
  }

  function updateProvenanceData(results) {
    if (!results) return;

    // Process nodes and edges from the provenance query
    if (results.nodes) {
      results.nodes.forEach(node => {
        provenanceData.records.set(node.id, {
          id: node.id,
          type: node.type,
          depth: node.depth,
          timestamp: new Date(),
          metadata: node
        });
      });
    }

    if (results.edges) {
      results.edges.forEach(edge => {
        if (!provenanceData.chains.has(edge.record_id)) {
          provenanceData.chains.set(edge.record_id, {
            id: edge.record_id,
            source: edge.source,
            target: edge.target,
            operation: edge.operation,
            type: 'reasoning_chain'
          });
        }
      });
    }
  }

  function updateVisualization() {
    if (!svg) return;

    const mainGroup = svg.select('.main-group');
    mainGroup.selectAll('*').remove();

    switch (viewMode) {
      case 'timeline':
        drawTimelineView(mainGroup);
        break;
      case 'dependency':
        drawDependencyView(mainGroup);
        break;
      case 'attribution':
        drawAttributionView(mainGroup);
        break;
      case 'audit':
        drawAuditView(mainGroup);
        break;
    }
  }

  function drawTimelineView(group) {
    const records = Array.from(provenanceData.records.values())
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    if (records.length === 0) {
      group.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')
        .style('fill', '#666')
        .text('No provenance data available');
      return;
    }

    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Create scales
    const timeExtent = d3.extent(records, d => new Date(d.timestamp));
    const xScale = d3.scaleTime()
      .domain(timeExtent)
      .range([margin.left, margin.left + chartWidth]);

    const yScale = d3.scaleBand()
      .domain(records.map(d => d.id))
      .range([margin.top, margin.top + chartHeight])
      .padding(0.1);

    // Draw axis
    group.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0, ${margin.top + chartHeight})`)
      .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%H:%M')));

    // Draw timeline items
    const items = group.selectAll('.timeline-item')
      .data(records)
      .enter()
      .append('g')
      .attr('class', 'timeline-item')
      .style('cursor', 'pointer')
      .on('click', (event, d) => selectRecord(d));

    items.append('circle')
      .attr('cx', d => xScale(new Date(d.timestamp)))
      .attr('cy', d => yScale(d.id) + yScale.bandwidth() / 2)
      .attr('r', 6)
      .style('fill', d => getOperationColor(d.operation))
      .style('stroke', '#fff')
      .style('stroke-width', 2);

    items.append('text')
      .attr('x', d => xScale(new Date(d.timestamp)) + 10)
      .attr('y', d => yScale(d.id) + yScale.bandwidth() / 2)
      .attr('dy', '0.35em')
      .style('font-size', '12px')
      .style('fill', '#333')
      .text(d => `${d.operation}: ${d.target}`);
  }

  function drawDependencyView(group) {
    // Create a simple network visualization
    const chains = Array.from(provenanceData.chains.values());
    
    if (chains.length === 0) {
      group.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')
        .style('fill', '#666')
        .text('No dependency data available');
      return;
    }

    // Simple force-directed layout
    const simulation = d3.forceSimulation(chains)
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    const nodes = group.selectAll('.dep-node')
      .data(chains)
      .enter()
      .append('g')
      .attr('class', 'dep-node');

    nodes.append('circle')
      .attr('r', 20)
      .style('fill', '#4CAF50')
      .style('stroke', '#fff')
      .style('stroke-width', 2);

    nodes.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('font-size', '10px')
      .style('fill', '#fff')
      .text(d => d.type);

    simulation.on('tick', () => {
      nodes.attr('transform', d => `translate(${d.x}, ${d.y})`);
    });
  }

  function drawAttributionView(group) {
    const attributions = Array.from(provenanceData.attributions.values());

    if (attributions.length === 0) {
      group.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .style('font-size', '16px')
        .style('fill', '#666')
        .text('No attribution data available');
      return;
    }

    // Draw attribution bars
    const yScale = d3.scaleBand()
      .domain(attributions.map((d, i) => i))
      .range([margin.top, height - margin.bottom])
      .padding(0.1);

    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([margin.left, width - margin.right]);

    attributions.forEach((attr, i) => {
      const confidence = attr.confidence || Math.random();
      
      group.append('rect')
        .attr('x', margin.left)
        .attr('y', yScale(i))
        .attr('width', xScale(confidence) - margin.left)
        .attr('height', yScale.bandwidth())
        .style('fill', '#2196F3')
        .style('opacity', 0.7);

      group.append('text')
        .attr('x', margin.left + 5)
        .attr('y', yScale(i) + yScale.bandwidth() / 2)
        .attr('dy', '0.35em')
        .style('font-size', '12px')
        .style('fill', '#333')
        .text(`${attr.source || 'Unknown'} (${(confidence * 100).toFixed(1)}%)`);
    });
  }

  function drawAuditView(group) {
    group.append('text')
      .attr('x', width / 2)
      .attr('y', height / 2)
      .attr('text-anchor', 'middle')
      .style('font-size', '16px')
      .style('fill', '#666')
      .text('Audit trail visualization will be implemented here');
  }

  function getOperationColor(operation) {
    const colors = {
      'create': '#4CAF50',
      'update': '#2196F3', 
      'infer': '#FF9800',
      'query': '#9C27B0',
      'resolve': '#607D8B',
      'delete': '#F44336'
    };
    return colors[operation] || '#757575';
  }

  function selectRecord(record) {
    console.log('Selected record:', record);
    selectedChain = record.id;
  }

  function setViewMode(mode) {
    viewMode = mode;
    updateVisualization();
  }

  function setTimeRange(hours) {
    const now = new Date();
    timeRange = hours ? {
      start: new Date(now.getTime() - hours * 60 * 60 * 1000),
      end: now,
      hours
    } : { hours: null };
    loadProvenanceData();
  }

  function startAutoRefresh() {
    // Refresh every 30 seconds
    refreshInterval = setInterval(() => {
      if (!loading) {
        loadProvenanceData();
      }
    }, 30000);
  }

  async function exportProvenanceData() {
    try {
      const exportData = {
        chains: Array.from(provenanceData.chains.entries()),
        records: Array.from(provenanceData.records.entries()),
        attributions: Array.from(provenanceData.attributions.entries()),
        timestamp: new Date().toISOString(),
        metadata: {
          viewMode,
          timeRange,
          selectedTarget
        }
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `provenance-export-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  }

  // Filter chains based on search term
  $: filteredChains = Array.from(provenanceData.chains.values()).filter(chain =>
    !searchTerm || 
    chain.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chain.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    chain.source?.toLowerCase().includes(searchTerm.toLowerCase())
  );
</script>

<div class="provenance-tracker" bind:this={container}>
  <div class="tracker-header">
    <h3>🔗 Provenance & Attribution Tracker</h3>
    <div class="header-actions">
      {#if loading}
        <span class="loading-indicator">⟳ Loading...</span>
      {:else}
        <button class="refresh-btn" on:click={loadProvenanceData}>
          🔄 Refresh
        </button>
      {/if}
      
      <button class="export-btn" on:click={exportProvenanceData}>
        📥 Export
      </button>
    </div>
  </div>

  {#if error}
    <div class="error-message">
      ⚠️ {error}
      <button on:click={() => { error = null; loadProvenanceData(); }}>Retry</button>
    </div>
  {/if}

  <div class="tracker-controls">
    <div class="control-group">
      <label>View Mode:</label>
      <div class="view-mode-tabs">
        <button 
          class="tab-btn" 
          class:active={viewMode === 'timeline'}
          on:click={() => setViewMode('timeline')}
        >
          📅 Timeline
        </button>
        <button 
          class="tab-btn" 
          class:active={viewMode === 'dependency'}
          on:click={() => setViewMode('dependency')}
        >
          🕸️ Dependencies
        </button>
        <button 
          class="tab-btn" 
          class:active={viewMode === 'attribution'}
          on:click={() => setViewMode('attribution')}
        >
          📊 Attribution
        </button>
        <button 
          class="tab-btn" 
          class:active={viewMode === 'audit'}
          on:click={() => setViewMode('audit')}
        >
          📋 Audit
        </button>
      </div>
    </div>

    <div class="control-group">
      <label>Time Range:</label>
      <div class="time-controls">
        <button class="time-btn" class:active={timeRange.hours === 1} on:click={() => setTimeRange(1)}>
          1H
        </button>
        <button class="time-btn" class:active={timeRange.hours === 24} on:click={() => setTimeRange(24)}>
          24H
        </button>
        <button class="time-btn" class:active={timeRange.hours === 168} on:click={() => setTimeRange(168)}>
          7D
        </button>
        <button class="time-btn" class:active={timeRange.hours === null} on:click={() => setTimeRange(null)}>
          All
        </button>
      </div>
    </div>

    <div class="control-group">
      <input 
        type="text" 
        placeholder="Search chains..." 
        bind:value={searchTerm}
        class="search-input"
      />
    </div>
  </div>

  <div class="tracker-content">
    <div class="sidebar">
      <h4>Provenance Chains ({filteredChains.length})</h4>
      <div class="chain-list">
        {#each filteredChains as chain (chain.id)}
          <div 
            class="chain-item" 
            class:selected={selectedChain === chain.id}
            on:click={() => selectRecord(chain)}
            role="button"
            tabindex="0"
            on:keydown={(e) => e.key === 'Enter' && selectRecord(chain)}
          >
            <div class="chain-name">{chain.name || chain.id}</div>
            <div class="chain-meta">
              <span class="chain-type">{chain.type}</span>
              <span class="chain-source">{chain.source}</span>
              {#if chain.created}
                <span class="chain-time">{new Date(chain.created).toLocaleTimeString()}</span>
              {/if}
            </div>
          </div>
        {/each}

        {#if filteredChains.length === 0}
          <div class="no-chains">
            {searchTerm ? 'No chains match your search' : 'No provenance chains available'}
          </div>
        {/if}
      </div>
    </div>

    <div class="visualization-area">
      <div class="provenance-viz"></div>
      
      {#if selectedChain}
        <div class="details-panel">
          <h4>Chain Details</h4>
          <div class="details-content">
            <p><strong>ID:</strong> {selectedChain}</p>
            {#if provenanceData.chains.get(selectedChain)}
              {@const chain = provenanceData.chains.get(selectedChain)}
              <p><strong>Type:</strong> {chain.type}</p>
              <p><strong>Source:</strong> {chain.source}</p>
              {#if chain.created}
                <p><strong>Created:</strong> {new Date(chain.created).toLocaleString()}</p>
              {/if}
            {/if}
          </div>
        </div>
      {/if}
    </div>
  </div>

  <div class="tracker-status">
    <div class="status-info">
      <span>Chains: {provenanceData.chains.size}</span>
      <span>Records: {provenanceData.records.size}</span>
      <span>Attributions: {provenanceData.attributions.size}</span>
    </div>
    {#if selectedTarget}
      <div class="target-info">
        Target: <code>{selectedTarget}</code>
      </div>
    {/if}
  </div>
</div>

<style>
  .provenance-tracker {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #e1e5e9;
    overflow: hidden;
  }

  .tracker-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom: 1px solid #e1e5e9;
  }

  .tracker-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .header-actions {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .loading-indicator {
    font-size: 14px;
    opacity: 0.9;
  }

  .refresh-btn, .export-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .refresh-btn:hover, .export-btn:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  .error-message {
    background: #fee;
    color: #c33;
    padding: 12px 20px;
    border-bottom: 1px solid #fcc;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .error-message button {
    background: #c33;
    color: white;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
  }

  .tracker-controls {
    display: flex;
    gap: 20px;
    padding: 16px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #e1e5e9;
    flex-wrap: wrap;
  }

  .control-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .control-group label {
    font-size: 14px;
    font-weight: 500;
    color: #495057;
    min-width: fit-content;
  }

  .view-mode-tabs {
    display: flex;
    gap: 4px;
  }

  .tab-btn {
    background: white;
    border: 1px solid #dee2e6;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .tab-btn:hover {
    background: #e9ecef;
  }

  .tab-btn.active {
    background: #007bff;
    color: white;
    border-color: #007bff;
  }

  .time-controls {
    display: flex;
    gap: 4px;
  }

  .time-btn {
    background: white;
    border: 1px solid #dee2e6;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .time-btn:hover {
    background: #e9ecef;
  }

  .time-btn.active {
    background: #28a745;
    color: white;
    border-color: #28a745;
  }

  .search-input {
    border: 1px solid #dee2e6;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 14px;
    min-width: 200px;
  }

  .search-input:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  }

  .tracker-content {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .sidebar {
    width: 300px;
    background: #f8f9fa;
    border-right: 1px solid #e1e5e9;
    display: flex;
    flex-direction: column;
  }

  .sidebar h4 {
    margin: 0;
    padding: 16px 20px;
    font-size: 14px;
    font-weight: 600;
    color: #495057;
    border-bottom: 1px solid #e1e5e9;
  }

  .chain-list {
    flex: 1;
    overflow-y: auto;
  }

  .chain-item {
    padding: 12px 20px;
    border-bottom: 1px solid #e1e5e9;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .chain-item:hover {
    background: #e9ecef;
  }

  .chain-item.selected {
    background: #007bff;
    color: white;
  }

  .chain-name {
    font-weight: 500;
    font-size: 14px;
    margin-bottom: 4px;
  }

  .chain-meta {
    display: flex;
    gap: 8px;
    font-size: 11px;
    opacity: 0.8;
  }

  .chain-type {
    background: rgba(0, 0, 0, 0.1);
    padding: 2px 6px;
    border-radius: 3px;
  }

  .no-chains {
    padding: 20px;
    text-align: center;
    color: #6c757d;
    font-style: italic;
  }

  .visualization-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  .provenance-viz {
    flex: 1;
    min-height: 400px;
  }

  .details-panel {
    background: #f8f9fa;
    border-top: 1px solid #e1e5e9;
    padding: 16px 20px;
    max-height: 200px;
    overflow-y: auto;
  }

  .details-panel h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #495057;
  }

  .details-content {
    font-size: 13px;
    line-height: 1.5;
  }

  .details-content p {
    margin: 0 0 8px 0;
  }

  .tracker-status {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #f8f9fa;
    border-top: 1px solid #e1e5e9;
    font-size: 12px;
    color: #6c757d;
  }

  .status-info {
    display: flex;
    gap: 16px;
  }

  .target-info code {
    background: #e9ecef;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Monaco', 'Consolas', monospace;
  }
</style>
