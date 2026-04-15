<script>
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly, slide } from 'svelte/transition';
  import { transparencyMode } from '../../stores/transparency.js';
  import { WS_BASE_URL, API_BASE_URL } from '../../config.js';

  // --- Constants ---
  const WS_RECONNECT_DELAY_MS = 5000;
  const MAX_REASONING_STEPS = 200;
  const STEP_GROUPING_WINDOW_SECONDS = 2;

  // --- State ---
  let activeTab = 'reasoning'; // 'reasoning' | 'decisions' | 'cognitive-map'
  let idCounter = 0;

  // Reasoning trace (live via WebSocket)
  let reasoningSteps = [];
  let wsConnected = false;
  let ws = null;
  let reconnectTimer = null;

  // Decision log (paginated HTTP)
  let decisions = [];
  let decisionsLoading = false;
  let decisionsLoaded = false;
  let decisionPage = 1;
  let totalDecisions = 0;
  let successRate = 0;

  // Cognitive map (d3-force)
  let mapNodes = [];
  let mapEdges = [];
  let mapLoading = false;
  let mapLoaded = false;
  let svgEl = null;
  let simulation = null;
  let d3Cached = null;

  // Errors
  let error = null;

  // ========================
  // WebSocket — Reasoning Trace
  // ========================
  function connectWS() {
    if (ws && ws.readyState === WebSocket.OPEN) return;

    try {
      ws = new WebSocket(`${WS_BASE_URL}/ws/transparency`);

      ws.onopen = () => {
        wsConnected = true;
        error = null;
        console.log('🔍 Transparency WebSocket connected');
        // Request initial metrics
        ws.send(JSON.stringify({ type: 'get_activity' }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          handleWSMessage(msg);
        } catch (e) {
          console.warn('Transparency WS parse error:', e);
        }
      };

      ws.onclose = () => {
        wsConnected = false;
        scheduleReconnect();
      };

      ws.onerror = () => {
        wsConnected = false;
      };
    } catch (e) {
      console.warn('Transparency WS connection failed:', e);
      wsConnected = false;
      scheduleReconnect();
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connectWS();
    }, WS_RECONNECT_DELAY_MS);
  }

  function handleWSMessage(msg) {
    idCounter += 1;
    const step = {
      id: `ws-${Date.now()}-${idCounter}`,
      timestamp: msg.timestamp || Date.now() / 1000,
      type: msg.type || 'event',
      description: msg.data?.description || msg.data?.event_type || msg.type || 'Unknown',
      detail: msg.data?.reasoning || msg.data?.detail || msg.data?.content || '',
      confidence: msg.data?.confidence ?? null,
      children: []
    };

    // Group by type — nest under parent if same type within grouping window
    const parent = reasoningSteps.find(
      s => s.type === step.type && (step.timestamp - s.timestamp) < STEP_GROUPING_WINDOW_SECONDS
    );
    if (parent) {
      parent.children = [...parent.children, step];
      reasoningSteps = [...reasoningSteps]; // trigger reactivity
    } else {
      reasoningSteps = [step, ...reasoningSteps].slice(0, MAX_REASONING_STEPS);
    }
  }

  // Also load initial traces via HTTP fallback
  async function loadReasoningTrace() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/transparency/reasoning-trace`);
      if (!res.ok) return;
      const data = await res.json();

      if (data.traces) {
        for (const trace of data.traces) {
          const traceId = trace.trace_id || `trace-${Date.now()}`;
          const steps = (trace.steps || []).map((s, i) => ({
            id: `http-${traceId}-${i}`,
            timestamp: Date.now() / 1000,
            type: s.type || 'step',
            description: s.description || `Step ${s.step}`,
            detail: '',
            confidence: trace.confidence ?? null,
            children: []
          }));
          // Merge — avoid duplicates by checking existing IDs
          const existingIds = new Set(reasoningSteps.map(s => s.id));
          const newSteps = steps.filter(s => !existingIds.has(s.id));
          if (newSteps.length > 0) {
            reasoningSteps = [...newSteps, ...reasoningSteps].slice(0, MAX_REASONING_STEPS);
          }
        }
      }
    } catch (e) {
      console.warn('Failed to load reasoning trace via HTTP:', e);
    }
  }

  // ========================
  // Decision Log (HTTP)
  // ========================
  async function loadDecisions() {
    decisionsLoading = true;
    try {
      const res = await fetch(`${API_BASE_URL}/api/transparency/decision-history`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      decisions = data.decisions || [];
      totalDecisions = data.total_decisions || decisions.length;
      successRate = data.success_rate ?? 0;
    } catch (e) {
      console.warn('Failed to load decisions:', e);
      error = 'Could not load decision log';
    } finally {
      decisionsLoading = false;
      decisionsLoaded = true;
    }
  }

  // ========================
  // Cognitive Map (d3-force)
  // ========================
  async function loadCognitiveMap() {
    mapLoading = true;
    try {
      const res = await fetch(`${API_BASE_URL}/api/transparency/knowledge-graph/export`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      mapNodes = (data.nodes || []).map(n => ({
        id: n.id || n.name || n.label,
        label: n.label || n.name || n.id,
        type: n.type || n.category || 'concept',
        weight: n.weight || n.importance || 1
      }));
      mapEdges = (data.edges || data.relationships || []).map(e => ({
        source: e.source || e.from,
        target: e.target || e.to,
        type: e.type || e.relationship || 'related',
        weight: e.weight || e.strength || 1
      }));
    } catch (e) {
      console.warn('Failed to load cognitive map:', e);
    } finally {
      mapLoading = false;
      mapLoaded = true;
    }
  }

  async function renderForceGraph() {
    if (!svgEl || mapNodes.length === 0) return;

    // Cache d3 import to avoid repeated dynamic imports
    if (!d3Cached) {
      d3Cached = await import('d3');
    }
    const d3 = d3Cached;

    const width = svgEl.clientWidth || 700;
    const height = svgEl.clientHeight || 500;

    // Clear previous
    d3.select(svgEl).selectAll('*').remove();

    const svg = d3.select(svgEl)
      .attr('viewBox', [0, 0, width, height]);

    // Deep-copy nodes/edges so d3 can mutate
    const nodes = mapNodes.map(n => ({ ...n }));
    const links = mapEdges.map(e => ({ ...e }));

    // Validate links reference existing nodes
    const nodeIds = new Set(nodes.map(n => n.id));
    const validLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
    if (validLinks.length < links.length) {
      console.warn(`Cognitive map: filtered ${links.length - validLinks.length} invalid link(s) referencing missing nodes`);
    }

    if (simulation) simulation.stop();
    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(validLinks).id(d => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-150))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(20));

    // Edges
    const link = svg.append('g')
      .selectAll('line')
      .data(validLinks)
      .join('line')
      .attr('stroke', 'rgba(100,180,255,0.4)')
      .attr('stroke-width', d => Math.max(1, d.weight));

    // Nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', d => 5 + (d.weight || 1) * 2)
      .attr('fill', d => nodeColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .call(drag(simulation, d3));

    // Labels
    const label = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text(d => d.label)
      .attr('font-size', '10px')
      .attr('fill', '#c8d6e5')
      .attr('dx', 12)
      .attr('dy', 4);

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
      label
        .attr('x', d => d.x)
        .attr('y', d => d.y);
    });
  }

  function drag(sim, d3) {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x; d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) sim.alphaTarget(0);
        d.fx = null; d.fy = null;
      });
  }

  function nodeColor(type) {
    const colors = {
      concept: '#64b5f6',
      entity: '#81c784',
      relationship: '#ffb74d',
      process: '#ba68c8',
      event: '#4dd0e1'
    };
    return colors[type] || '#90a4ae';
  }

  // ========================
  // Lifecycle
  // ========================
  onMount(() => {
    connectWS();
    loadReasoningTrace();
  });

  onDestroy(() => {
    if (ws) { try { ws.close(); } catch (_) {} }
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (simulation) simulation.stop();
  });

  // Tab change side-effects
  $: if (activeTab === 'decisions' && !decisionsLoaded && !decisionsLoading) {
    loadDecisions();
  }
  $: if (activeTab === 'cognitive-map' && !mapLoaded && !mapLoading) {
    loadCognitiveMap();
  }
  // Render graph when data + DOM ready
  $: if (activeTab === 'cognitive-map' && svgEl && mapNodes.length > 0) {
    renderForceGraph();
  }

  // Format helpers
  function fmtTime(ts) {
    const d = new Date(typeof ts === 'number' && ts < 1e12 ? ts * 1000 : ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function toggleTransparencyMode() {
    transparencyMode.update(v => !v);
  }
</script>

<div class="transparency-panel">
  <!-- Header -->
  <div class="panel-header">
    <div class="header-left">
      <h2>🔍 Cognitive Transparency</h2>
      <span class="ws-indicator" class:connected={wsConnected}>
        {wsConnected ? '● Live' : '○ Offline'}
      </span>
    </div>
    <div class="header-right">
      <label class="transparency-toggle">
        <input type="checkbox" checked={$transparencyMode} on:change={toggleTransparencyMode} />
        <span class="toggle-label">Transparency Mode</span>
        <small class="toggle-hint">{$transparencyMode ? 'ON — reasoning inline' : 'OFF'}</small>
      </label>
    </div>
  </div>

  <!-- Tabs -->
  <div class="tab-bar">
    <button class="tab" class:active={activeTab === 'reasoning'} on:click={() => activeTab = 'reasoning'}>
      ⚡ Reasoning Trace
    </button>
    <button class="tab" class:active={activeTab === 'decisions'} on:click={() => activeTab = 'decisions'}>
      📋 Decision Log
    </button>
    <button class="tab" class:active={activeTab === 'cognitive-map'} on:click={() => activeTab = 'cognitive-map'}>
      🗺️ Cognitive Map
    </button>
  </div>

  <!-- Tab Content -->
  <div class="tab-content">
    {#if activeTab === 'reasoning'}
      <!-- ====== Reasoning Trace ====== -->
      <div class="reasoning-trace" in:fade={{ duration: 200 }}>
        {#if reasoningSteps.length === 0}
          <div class="empty-state">
            <span class="empty-icon">🔬</span>
            <p>No reasoning steps captured yet.</p>
            <p class="hint">Submit a query to see live reasoning here, or wait for system events.</p>
          </div>
        {:else}
          <div class="trace-tree">
            {#each reasoningSteps as step (step.id)}
              <div class="trace-node" in:fly={{ y: -10, duration: 200 }}>
                <div class="node-header">
                  <span class="node-type-badge" style="background: {nodeColor(step.type)}">{step.type}</span>
                  <span class="node-desc">{step.description}</span>
                  {#if step.confidence != null}
                    <span class="node-confidence">{Math.round(step.confidence * 100)}%</span>
                  {/if}
                  <span class="node-time">{fmtTime(step.timestamp)}</span>
                </div>
                {#if step.detail}
                  <div class="node-detail">{step.detail}</div>
                {/if}
                {#if step.children.length > 0}
                  <div class="node-children" transition:slide={{ duration: 150 }}>
                    {#each step.children as child (child.id)}
                      <div class="trace-node child">
                        <div class="node-header">
                          <span class="node-type-badge small" style="background: {nodeColor(child.type)}">{child.type}</span>
                          <span class="node-desc">{child.description}</span>
                          <span class="node-time">{fmtTime(child.timestamp)}</span>
                        </div>
                        {#if child.detail}
                          <div class="node-detail">{child.detail}</div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

    {:else if activeTab === 'decisions'}
      <!-- ====== Decision Log ====== -->
      <div class="decision-log" in:fade={{ duration: 200 }}>
        {#if decisionsLoading}
          <div class="loading-state"><div class="spinner"></div> Loading decisions…</div>
        {:else if decisions.length === 0}
          <div class="empty-state">
            <span class="empty-icon">📋</span>
            <p>No decisions recorded yet.</p>
          </div>
        {:else}
          <div class="decision-stats">
            <span>Total: <strong>{totalDecisions}</strong></span>
            <span>Success Rate: <strong>{Math.round(successRate * 100)}%</strong></span>
          </div>
          <div class="decision-table-wrapper">
            <table class="decision-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Confidence</th>
                  <th>Outcome</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {#each decisions as d (d.decision_id)}
                  <tr in:fade={{ duration: 100 }}>
                    <td class="mono">{d.decision_id}</td>
                    <td><span class="type-badge">{d.type}</span></td>
                    <td>{d.description}</td>
                    <td>
                      <div class="confidence-bar">
                        <div class="confidence-fill" style="width:{(d.confidence || 0) * 100}%"></div>
                        <span>{Math.round((d.confidence || 0) * 100)}%</span>
                      </div>
                    </td>
                    <td>
                      <span class="outcome-badge {d.outcome || 'unknown'}">{d.outcome || '—'}</span>
                    </td>
                    <td class="mono">{d.timestamp ? fmtTime(d.timestamp) : '—'}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>

    {:else if activeTab === 'cognitive-map'}
      <!-- ====== Cognitive Map ====== -->
      <div class="cognitive-map" in:fade={{ duration: 200 }}>
        {#if mapLoading}
          <div class="loading-state"><div class="spinner"></div> Loading cognitive map…</div>
        {:else if mapNodes.length === 0}
          <div class="empty-state">
            <span class="empty-icon">🗺️</span>
            <p>No cognitive map data available.</p>
            <p class="hint">The map populates as the system processes queries and builds knowledge.</p>
          </div>
        {:else}
          <div class="map-info">
            <span>{mapNodes.length} nodes</span>
            <span>{mapEdges.length} connections</span>
            <button class="refresh-btn" on:click={() => { mapLoaded = false; mapNodes = []; mapEdges = []; loadCognitiveMap(); }}>🔄 Refresh</button>
          </div>
        {/if}
        <svg bind:this={svgEl} class="force-graph"></svg>
      </div>
    {/if}
  </div>

  {#if error}
    <div class="error-bar" in:fly={{ y: 20 }}>
      ⚠️ {error}
      <button on:click={() => error = null}>✕</button>
    </div>
  {/if}
</div>

<style>
  .transparency-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 500px;
    background: rgba(15, 20, 35, 0.85);
    color: #e1e5e9;
    border-radius: 12px;
    overflow: hidden;
  }

  /* Header */
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    background: rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(100,120,150,0.15);
    flex-wrap: wrap;
    gap: 0.75rem;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .panel-header h2 {
    margin: 0;
    font-size: 1.25rem;
  }
  .ws-indicator {
    font-size: 0.8rem;
    color: #ef5350;
    transition: color 0.3s;
  }
  .ws-indicator.connected {
    color: #66bb6a;
  }

  .header-right {
    display: flex;
    align-items: center;
  }
  .transparency-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    user-select: none;
  }
  .transparency-toggle input[type="checkbox"] {
    width: 18px;
    height: 18px;
    accent-color: #64b5f6;
    cursor: pointer;
  }
  .toggle-label {
    font-weight: 600;
    font-size: 0.9rem;
  }
  .toggle-hint {
    font-size: 0.75rem;
    color: #a0a9b8;
  }

  /* Tabs */
  .tab-bar {
    display: flex;
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid rgba(100,120,150,0.12);
  }
  .tab {
    flex: 1;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    color: #a0a9b8;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }
  .tab:hover {
    color: #e1e5e9;
    background: rgba(255,255,255,0.03);
  }
  .tab.active {
    color: #64b5f6;
    border-bottom-color: #64b5f6;
  }

  /* Content area */
  .tab-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 1.25rem;
  }

  /* Shared states */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem;
    color: #64748b;
    text-align: center;
  }
  .empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
  .hint { font-size: 0.85rem; opacity: 0.7; }

  .loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 2rem;
    color: #a0a9b8;
  }
  .spinner {
    width: 24px; height: 24px;
    border: 3px solid rgba(100,180,255,0.2);
    border-left-color: #64b5f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ====== Reasoning Trace ====== */
  .trace-tree {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .trace-node {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(100,120,150,0.1);
    border-radius: 8px;
    padding: 0.75rem 1rem;
  }
  .trace-node.child {
    margin-left: 1.5rem;
    border-left: 2px solid rgba(100,180,255,0.3);
    background: rgba(255,255,255,0.02);
  }
  .node-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
  }
  .node-type-badge {
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #fff;
    text-transform: uppercase;
  }
  .node-type-badge.small { font-size: 0.65rem; padding: 0.1rem 0.4rem; }
  .node-desc {
    flex: 1;
    font-size: 0.9rem;
  }
  .node-confidence {
    font-size: 0.8rem;
    font-weight: 600;
    color: #66bb6a;
  }
  .node-time {
    font-size: 0.75rem;
    color: #64748b;
    font-family: monospace;
  }
  .node-detail {
    margin-top: 0.4rem;
    padding: 0.5rem 0.75rem;
    background: rgba(0,0,0,0.15);
    border-radius: 6px;
    font-size: 0.85rem;
    color: #b0bec5;
    line-height: 1.4;
  }
  .node-children {
    margin-top: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  /* ====== Decision Log ====== */
  .decision-stats {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #a0a9b8;
  }
  .decision-table-wrapper {
    overflow-x: auto;
  }
  .decision-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  .decision-table th {
    text-align: left;
    padding: 0.6rem 0.75rem;
    color: #64b5f6;
    font-weight: 600;
    border-bottom: 1px solid rgba(100,120,150,0.2);
    white-space: nowrap;
  }
  .decision-table td {
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid rgba(100,120,150,0.08);
  }
  .mono { font-family: monospace; font-size: 0.8rem; color: #90a4ae; }
  .type-badge {
    background: rgba(100,180,255,0.15);
    color: #64b5f6;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.78rem;
    white-space: nowrap;
  }
  .confidence-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 100px;
  }
  .confidence-fill {
    height: 6px;
    border-radius: 3px;
    background: #66bb6a;
    flex: 1;
  }
  .confidence-bar span { font-size: 0.78rem; color: #a0a9b8; }
  .outcome-badge {
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 500;
  }
  .outcome-badge.successful { background: rgba(102,187,106,0.15); color: #66bb6a; }
  .outcome-badge.failed { background: rgba(239,83,80,0.15); color: #ef5350; }
  .outcome-badge.unknown { background: rgba(160,169,184,0.1); color: #a0a9b8; }

  /* ====== Cognitive Map ====== */
  .cognitive-map {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 400px;
  }
  .map-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.75rem;
    font-size: 0.85rem;
    color: #a0a9b8;
  }
  .refresh-btn {
    margin-left: auto;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(100,120,150,0.15);
    color: #a0a9b8;
    padding: 0.35rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.2s;
  }
  .refresh-btn:hover {
    background: rgba(255,255,255,0.1);
    color: #e1e5e9;
  }
  .force-graph {
    flex: 1;
    width: 100%;
    min-height: 400px;
    background: rgba(0,0,0,0.2);
    border-radius: 8px;
  }

  /* Error bar */
  .error-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 1rem;
    background: rgba(239,83,80,0.12);
    color: #ef5350;
    font-size: 0.85rem;
    border-top: 1px solid rgba(239,83,80,0.2);
  }
  .error-bar button {
    background: none;
    border: none;
    color: #ef5350;
    cursor: pointer;
    font-size: 1rem;
  }

  /* Scrollbar */
  .tab-content::-webkit-scrollbar { width: 6px; }
  .tab-content::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
  .tab-content::-webkit-scrollbar-thumb { background: rgba(100,120,150,0.25); border-radius: 3px; }

  @media (max-width: 768px) {
    .panel-header { flex-direction: column; align-items: flex-start; }
    .tab { font-size: 0.8rem; padding: 0.6rem 0.5rem; }
    .decision-table { font-size: 0.78rem; }
  }
</style>
