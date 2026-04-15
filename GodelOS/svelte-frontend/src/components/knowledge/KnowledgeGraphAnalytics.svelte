<!--
Knowledge Graph Analytics Overlay Component
Provides advanced analytics, performance monitoring, and collaborative features
-->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable, derived } from 'svelte/store';
  
  // Props
  export let graphData = { nodes: [], edges: [] };
  export let selectedNode = null;
  export let isVisible = true;
  
  // Analytics state
  let analyticsData = writable({
    centralityMetrics: {},
    clusteringCoefficient: 0,
    pathLengths: {},
    communityStructure: [],
    knowledgeGaps: [],
    semanticClusters: [],
    influenceScores: {},
    lastAnalysis: null
  });
  
  // Performance monitoring
  let performanceMetrics = writable({
    fps: 0,
    nodeCount: 0,
    edgeCount: 0,
    renderTime: 0,
    memoryUsage: 0,
    lastUpdate: Date.now()
  });
  
  // Collaborative session state
  let collaborativeSession = writable({
    isActive: false,
    sessionId: null,
    participants: [],
    lastSync: null
  });
  
  // Real-time analytics computation
  function computeAdvancedAnalytics() {
    if (!graphData.nodes || graphData.nodes.length === 0) return;
    
    console.log('🧮 Computing advanced knowledge graph analytics...');
    
    const nodes = graphData.nodes;
    const edges = graphData.edges || [];
    
    // 1. Centrality Analysis
    const centralityMetrics = computeCentralityMetrics(nodes, edges);
    
    // 2. Community Detection
    const communityStructure = detectCommunities(nodes, edges);
    
    // 3. Knowledge Gap Analysis
    const knowledgeGaps = identifyKnowledgeGaps(nodes, edges);
    
    // 4. Semantic Clustering
    const semanticClusters = performSemanticClustering(nodes);
    
    // 5. Clustering Coefficient
    const clusteringCoefficient = calculateClusteringCoefficient(nodes, edges);
    
    // 6. Path Length Analysis
    const pathLengths = analyzePathLengths(nodes, edges);
    
    // 7. Influence Scores
    const influenceScores = calculateInfluenceScores(nodes, edges);
    
    analyticsData.update(current => ({
      ...current,
      centralityMetrics,
      clusteringCoefficient,
      pathLengths,
      communityStructure,
      knowledgeGaps,
      semanticClusters,
      influenceScores,
      lastAnalysis: new Date().toISOString()
    }));
  }
  
  function computeCentralityMetrics(nodes, edges) {
    const adjacencyList = new Map();
    const metrics = {};
    
    // Build adjacency list
    nodes.forEach(node => adjacencyList.set(node.id, new Set()));
    edges.forEach(edge => {
      const sourceId = edge.source?.id || edge.source;
      const targetId = edge.target?.id || edge.target;
      adjacencyList.get(sourceId)?.add(targetId);
      adjacencyList.get(targetId)?.add(sourceId);
    });
    
    nodes.forEach(node => {
      const degree = adjacencyList.get(node.id)?.size || 0;
      const degreeCentrality = degree / Math.max(1, nodes.length - 1);
      
      // Simplified betweenness centrality
      const betweenness = calculateBetweennessCentrality(node.id, adjacencyList, nodes);
      
      // Closeness centrality
      const closeness = calculateClosenessCentrality(node.id, adjacencyList, nodes);
      
      metrics[node.id] = {
        degree: degreeCentrality,
        betweenness: betweenness,
        closeness: closeness,
        combined: (degreeCentrality + betweenness + closeness) / 3
      };
    });
    
    return metrics;
  }
  
  function calculateBetweennessCentrality(nodeId, adjacencyList, nodes) {
    // Simplified betweenness calculation
    let betweenness = 0;
    const totalNodes = nodes.length;
    
    for (let i = 0; i < Math.min(50, totalNodes); i++) { // Sample for performance
      const source = nodes[i];
      if (source.id === nodeId) continue;
      
      for (let j = i + 1; j < Math.min(50, totalNodes); j++) {
        const target = nodes[j];
        if (target.id === nodeId || target.id === source.id) continue;
        
        const pathCount = countShortestPathsThrough(source.id, target.id, nodeId, adjacencyList);
        const totalPaths = countShortestPaths(source.id, target.id, adjacencyList);
        
        if (totalPaths > 0) {
          betweenness += pathCount / totalPaths;
        }
      }
    }
    
    return betweenness / (totalNodes * (totalNodes - 1) / 2);
  }
  
  function calculateClosenessCentrality(nodeId, adjacencyList, nodes) {
    const distances = bfsDistances(nodeId, adjacencyList);
    const validDistances = Object.values(distances).filter(d => d > 0 && d < Infinity);
    
    if (validDistances.length === 0) return 0;
    
    const avgDistance = validDistances.reduce((sum, d) => sum + d, 0) / validDistances.length;
    return avgDistance > 0 ? 1 / avgDistance : 0;
  }
  
  function detectCommunities(nodes, edges) {
    // Simple community detection using modularity
    const communities = [];
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const adjacencyList = new Map();
    
    // Build weighted adjacency list
    nodes.forEach(node => adjacencyList.set(node.id, new Map()));
    edges.forEach(edge => {
      const sourceId = edge.source?.id || edge.source;
      const targetId = edge.target?.id || edge.target;
      const weight = edge.strength || edge.weight || 1;
      adjacencyList.get(sourceId)?.set(targetId, weight);
      adjacencyList.get(targetId)?.set(sourceId, weight);
    });
    
    // Initialize communities (each node starts in its own community)
    let nodeCommunity = new Map(nodes.map(n => [n.id, n.id]));
    let improved = true;
    let iterations = 0;
    const maxIterations = 10;
    
    while (improved && iterations < maxIterations) {
      improved = false;
      iterations++;
      
      for (let node of nodes) {
        const currentCommunity = nodeCommunity.get(node.id);
        let bestCommunity = currentCommunity;
        let bestGain = 0;
        
        // Check neighboring communities
        const neighbors = adjacencyList.get(node.id) || new Map();
        const neighborCommunities = new Set();
        
        for (let [neighbor] of neighbors) {
          neighborCommunities.add(nodeCommunity.get(neighbor));
        }
        
        for (let community of neighborCommunities) {
          if (community === currentCommunity) continue;
          
          const gain = calculateModularityGain(node.id, community, nodeCommunity, adjacencyList);
          if (gain > bestGain) {
            bestGain = gain;
            bestCommunity = community;
          }
        }
        
        if (bestCommunity !== currentCommunity) {
          nodeCommunity.set(node.id, bestCommunity);
          improved = true;
        }
      }
    }
    
    // Group nodes by community
    const communityGroups = new Map();
    for (let [nodeId, communityId] of nodeCommunity) {
      if (!communityGroups.has(communityId)) {
        communityGroups.set(communityId, []);
      }
      communityGroups.get(communityId).push(nodeId);
    }
    
    // Convert to result format
    let communityIndex = 0;
    for (let [communityId, memberIds] of communityGroups) {
      if (memberIds.length > 1) { // Only include communities with multiple members
        communities.push({
          id: communityIndex++,
          name: `Community ${communityIndex}`,
          members: memberIds,
          size: memberIds.length,
          density: calculateCommunityDensity(memberIds, adjacencyList),
          topics: extractCommunityTopics(memberIds, nodeMap)
        });
      }
    }
    
    return communities.sort((a, b) => b.size - a.size);
  }
  
  function identifyKnowledgeGaps(nodes, edges) {
    const gaps = [];
    const adjacencyList = new Map();
    
    // Build adjacency list
    nodes.forEach(node => adjacencyList.set(node.id, new Set()));
    edges.forEach(edge => {
      const sourceId = edge.source?.id || edge.source;
      const targetId = edge.target?.id || edge.target;
      adjacencyList.get(sourceId)?.add(targetId);
      adjacencyList.get(targetId)?.add(sourceId);
    });
    
    // Find isolated nodes
    nodes.forEach(node => {
      const connections = adjacencyList.get(node.id)?.size || 0;
      if (connections < 2) {
        gaps.push({
          type: 'isolated_concept',
          nodeId: node.id,
          label: node.label || node.id,
          severity: connections === 0 ? 'high' : 'medium',
          suggestion: 'Consider adding relationships to related concepts',
          connections: connections
        });
      }
    });
    
    // Find dense clusters that might benefit from subdivision
    const communities = detectCommunities(nodes, edges);
    communities.forEach(community => {
      if (community.size > 10 && community.density > 0.8) {
        gaps.push({
          type: 'dense_cluster',
          communityId: community.id,
          label: community.name,
          severity: 'low',
          suggestion: 'Consider subdividing this dense cluster for better organization',
          size: community.size,
          density: community.density
        });
      }
    });
    
    // Find missing bridges between communities
    for (let i = 0; i < communities.length; i++) {
      for (let j = i + 1; j < communities.length; j++) {
        const bridgeCount = countBridgesBetweenCommunities(communities[i], communities[j], edges);
        if (bridgeCount === 0 && communities[i].size > 2 && communities[j].size > 2) {
          gaps.push({
            type: 'missing_bridge',
            community1: communities[i].name,
            community2: communities[j].name,
            severity: 'medium',
            suggestion: `Consider adding relationships between ${communities[i].name} and ${communities[j].name}`,
            bridgeCount: bridgeCount
          });
        }
      }
    }
    
    return gaps.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }
  
  function performSemanticClustering(nodes) {
    const clusters = [];
    const processed = new Set();
    
    for (let node of nodes) {
      if (processed.has(node.id)) continue;
      
      const cluster = {
        id: clusters.length,
        centroid: node.id,
        members: [node.id],
        avgSimilarity: 0,
        topics: extractSemanticTopics(node),
        coherence: 1
      };
      
      processed.add(node.id);
      
      // Find semantically similar nodes
      for (let otherNode of nodes) {
        if (processed.has(otherNode.id)) continue;
        
        const similarity = calculateSemanticSimilarity(node, otherNode);
        if (similarity > 0.4) {
          cluster.members.push(otherNode.id);
          processed.add(otherNode.id);
        }
      }
      
      if (cluster.members.length > 1) {
        cluster.avgSimilarity = calculateClusterCoherence(cluster.members, nodes);
        cluster.coherence = cluster.avgSimilarity;
        clusters.push(cluster);
      }
    }
    
    return clusters.sort((a, b) => b.coherence - a.coherence);
  }
  
  function calculateClusteringCoefficient(nodes, edges) {
    if (nodes.length < 3) return 0;
    
    const adjacencyList = new Map();
    nodes.forEach(node => adjacencyList.set(node.id, new Set()));
    edges.forEach(edge => {
      const sourceId = edge.source?.id || edge.source;
      const targetId = edge.target?.id || edge.target;
      adjacencyList.get(sourceId)?.add(targetId);
      adjacencyList.get(targetId)?.add(sourceId);
    });
    
    let totalCoefficient = 0;
    let nodeCount = 0;
    
    for (let node of nodes) {
      const neighbors = Array.from(adjacencyList.get(node.id) || []);
      if (neighbors.length < 2) continue;
      
      let triangles = 0;
      const possibleTriangles = neighbors.length * (neighbors.length - 1) / 2;
      
      for (let i = 0; i < neighbors.length; i++) {
        for (let j = i + 1; j < neighbors.length; j++) {
          if (adjacencyList.get(neighbors[i])?.has(neighbors[j])) {
            triangles++;
          }
        }
      }
      
      if (possibleTriangles > 0) {
        totalCoefficient += triangles / possibleTriangles;
        nodeCount++;
      }
    }
    
    return nodeCount > 0 ? totalCoefficient / nodeCount : 0;
  }
  
  function analyzePathLengths(nodes, edges) {
    const adjacencyList = new Map();
    nodes.forEach(node => adjacencyList.set(node.id, new Set()));
    edges.forEach(edge => {
      const sourceId = edge.source?.id || edge.source;
      const targetId = edge.target?.id || edge.target;
      adjacencyList.get(sourceId)?.add(targetId);
      adjacencyList.get(targetId)?.add(sourceId);
    });
    
    const pathLengths = [];
    const sampleSize = Math.min(100, nodes.length); // Sample for performance
    
    for (let i = 0; i < sampleSize; i++) {
      const distances = bfsDistances(nodes[i].id, adjacencyList);
      Object.values(distances).forEach(distance => {
        if (distance > 0 && distance < Infinity) {
          pathLengths.push(distance);
        }
      });
    }
    
    if (pathLengths.length === 0) return { avg: 0, min: 0, max: 0 };
    
    pathLengths.sort((a, b) => a - b);
    return {
      avg: pathLengths.reduce((sum, d) => sum + d, 0) / pathLengths.length,
      min: pathLengths[0],
      max: pathLengths[pathLengths.length - 1],
      median: pathLengths[Math.floor(pathLengths.length / 2)]
    };
  }
  
  function calculateInfluenceScores(nodes, edges) {
    const scores = {};
    const centralityMetrics = computeCentralityMetrics(nodes, edges);
    
    nodes.forEach(node => {
      const centrality = centralityMetrics[node.id] || { combined: 0 };
      const importance = node.importance || 0.5;
      const confidence = node.confidence || 0.5;
      const recency = node.recency || 0.5;
      
      // Combined influence score
      scores[node.id] = (
        centrality.combined * 0.4 +
        importance * 0.3 +
        confidence * 0.2 +
        recency * 0.1
      );
    });
    
    return scores;
  }
  
  // Utility functions
  function bfsDistances(startNodeId, adjacencyList) {
    const distances = {};
    const queue = [{ nodeId: startNodeId, distance: 0 }];
    const visited = new Set([startNodeId]);
    
    while (queue.length > 0) {
      const { nodeId, distance } = queue.shift();
      distances[nodeId] = distance;
      
      const neighbors = adjacencyList.get(nodeId) || new Set();
      for (let neighbor of neighbors) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push({ nodeId: neighbor, distance: distance + 1 });
        }
      }
    }
    
    return distances;
  }
  
  function calculateSemanticSimilarity(node1, node2) {
    const text1 = (node1.label + ' ' + (node1.content || '')).toLowerCase();
    const text2 = (node2.label + ' ' + (node2.content || '')).toLowerCase();
    
    const words1 = new Set(text1.split(/\W+/).filter(w => w.length > 2));
    const words2 = new Set(text2.split(/\W+/).filter(w => w.length > 2));
    
    const intersection = new Set([...words1].filter(w => words2.has(w)));
    const union = new Set([...words1, ...words2]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  }
  
  function extractSemanticTopics(node) {
    const text = (node.label + ' ' + (node.content || '')).toLowerCase();
    const words = text.split(/\W+/).filter(w => w.length > 3);
    return words.slice(0, 5); // Return top 5 words as topics
  }
  
  function calculateClusterCoherence(memberIds, nodes) {
    if (memberIds.length < 2) return 1;
    
    const members = nodes.filter(n => memberIds.includes(n.id));
    let totalSimilarity = 0;
    let comparisons = 0;
    
    for (let i = 0; i < members.length; i++) {
      for (let j = i + 1; j < members.length; j++) {
        totalSimilarity += calculateSemanticSimilarity(members[i], members[j]);
        comparisons++;
      }
    }
    
    return comparisons > 0 ? totalSimilarity / comparisons : 0;
  }
  
  function calculateModularityGain(nodeId, targetCommunity, nodeCommunity, adjacencyList) {
    // Simplified modularity gain calculation
    const neighbors = adjacencyList.get(nodeId) || new Map();
    let internalConnections = 0;
    let externalConnections = 0;
    
    for (let [neighbor, weight] of neighbors) {
      const neighborCommunity = nodeCommunity.get(neighbor);
      if (neighborCommunity === targetCommunity) {
        internalConnections += weight;
      } else {
        externalConnections += weight;
      }
    }
    
    return internalConnections - externalConnections;
  }
  
  function calculateCommunityDensity(memberIds, adjacencyList) {
    if (memberIds.length < 2) return 0;
    
    let internalEdges = 0;
    const possibleEdges = memberIds.length * (memberIds.length - 1) / 2;
    
    for (let i = 0; i < memberIds.length; i++) {
      for (let j = i + 1; j < memberIds.length; j++) {
        if (adjacencyList.get(memberIds[i])?.has(memberIds[j])) {
          internalEdges++;
        }
      }
    }
    
    return possibleEdges > 0 ? internalEdges / possibleEdges : 0;
  }
  
  function extractCommunityTopics(memberIds, nodeMap) {
    const allText = memberIds
      .map(id => {
        const node = nodeMap.get(id);
        return node ? (node.label + ' ' + (node.content || '')) : '';
      })
      .join(' ')
      .toLowerCase();
    
    const words = allText.split(/\W+/)
      .filter(w => w.length > 3)
      .filter(w => !['this', 'that', 'with', 'from', 'they', 'were', 'been', 'have'].includes(w));
    
    // Count word frequency
    const wordCount = {};
    words.forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });
    
    // Return top 5 most frequent words
    return Object.entries(wordCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);
  }
  
  function countBridgesBetweenCommunities(community1, community2, edges) {
    let bridgeCount = 0;
    
    edges.forEach(edge => {
      const sourceId = edge.source?.id || edge.source;
      const targetId = edge.target?.id || edge.target;
      
      const sourceInCommunity1 = community1.members.includes(sourceId);
      const targetInCommunity1 = community1.members.includes(targetId);
      const sourceInCommunity2 = community2.members.includes(sourceId);
      const targetInCommunity2 = community2.members.includes(targetId);
      
      if ((sourceInCommunity1 && targetInCommunity2) || (sourceInCommunity2 && targetInCommunity1)) {
        bridgeCount++;
      }
    });
    
    return bridgeCount;
  }
  
  function countShortestPathsThrough(sourceId, targetId, throughId, adjacencyList) {
    // Simplified path counting (BFS-based)
    const pathsFromSource = bfsDistances(sourceId, adjacencyList);
    const pathsFromThrough = bfsDistances(throughId, adjacencyList);
    const pathsFromTarget = bfsDistances(targetId, adjacencyList);
    
    const distSourceThrough = pathsFromSource[throughId] || Infinity;
    const distThroughTarget = pathsFromThrough[targetId] || Infinity;
    const directDist = pathsFromSource[targetId] || Infinity;
    
    // If path through 'throughId' is a shortest path
    if (distSourceThrough + distThroughTarget === directDist && directDist < Infinity) {
      return 1;
    }
    
    return 0;
  }
  
  function countShortestPaths(sourceId, targetId, adjacencyList) {
    const distances = bfsDistances(sourceId, adjacencyList);
    return distances[targetId] < Infinity ? 1 : 0;
  }
  
  // Start performance monitoring
  function startPerformanceMonitoring() {
    let frameCount = 0;
    let lastTime = performance.now();
    
    function monitor() {
      const currentTime = performance.now();
      const deltaTime = currentTime - lastTime;
      
      frameCount++;
      
      if (deltaTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / deltaTime);
        frameCount = 0;
        lastTime = currentTime;
        
        performanceMetrics.update(current => ({
          ...current,
          fps: fps,
          nodeCount: graphData.nodes?.length || 0,
          edgeCount: graphData.edges?.length || 0,
          memoryUsage: performance.memory ? Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)) : 0,
          lastUpdate: currentTime
        }));
      }
      
      requestAnimationFrame(monitor);
    }
    
    monitor();
  }
  
  // React to graph data changes
  $: if (graphData && graphData.nodes && graphData.nodes.length > 0) {
    setTimeout(computeAdvancedAnalytics, 500); // Debounce analytics computation
  }
  
  onMount(() => {
    startPerformanceMonitoring();
  });
  
  // Export stores for parent access
  export { analyticsData, performanceMetrics, collaborativeSession };
</script>

{#if isVisible}
  <!-- Performance Overlay -->
  <div class="performance-overlay">
    <h4 class="overlay-title">⚡ Performance</h4>
    <div class="metric-row">
      <span class="metric-label">FPS:</span>
      <span class="metric-value" class:warning={$performanceMetrics.fps < 30} class:critical={$performanceMetrics.fps < 15}>
        {$performanceMetrics.fps}
      </span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Nodes:</span>
      <span class="metric-value">{$performanceMetrics.nodeCount}</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Edges:</span>
      <span class="metric-value">{$performanceMetrics.edgeCount}</span>
    </div>
    <div class="metric-row">
      <span class="metric-label">Memory:</span>
      <span class="metric-value">{$performanceMetrics.memoryUsage}MB</span>
    </div>
  </div>
  
  <!-- Analytics Panel -->
  <div class="analytics-panel">
    <h4 class="panel-title">📊 Knowledge Graph Analytics</h4>
    
    {#if $analyticsData.lastAnalysis}
      <div class="analytics-section">
        <h5 class="section-title">🎯 Centrality Analysis</h5>
        <div class="metric-grid">
          <div class="metric-item">
            <span class="metric-name">Clustering Coefficient:</span>
            <span class="metric-score">{($analyticsData.clusteringCoefficient * 100).toFixed(1)}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-name">Avg Path Length:</span>
            <span class="metric-score">{$analyticsData.pathLengths.avg?.toFixed(2) || 'N/A'}</span>
          </div>
        </div>
      </div>
      
      <div class="analytics-section">
        <h5 class="section-title">🏘️ Communities</h5>
        <div class="community-list">
          {#each $analyticsData.communityStructure.slice(0, 3) as community}
            <div class="community-item">
              <div class="community-header">
                <span class="community-name">{community.name}</span>
                <span class="community-size">{community.size} nodes</span>
              </div>
              <div class="community-topics">
                {#each community.topics.slice(0, 3) as topic}
                  <span class="topic-tag">{topic}</span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      </div>
      
      <div class="analytics-section">
        <h5 class="section-title">⚠️ Knowledge Gaps</h5>
        <div class="gaps-list">
          {#each $analyticsData.knowledgeGaps.slice(0, 3) as gap}
            <div class="gap-item severity-{gap.severity}">
              <div class="gap-type">{gap.type.replace('_', ' ')}</div>
              <div class="gap-suggestion">{gap.suggestion}</div>
            </div>
          {/each}
        </div>
      </div>
      
      <div class="analytics-section">
        <h5 class="section-title">🧩 Semantic Clusters</h5>
        <div class="cluster-list">
          {#each $analyticsData.semanticClusters.slice(0, 3) as cluster}
            <div class="cluster-item">
              <div class="cluster-header">
                <span class="cluster-size">{cluster.members.length} concepts</span>
                <span class="cluster-coherence">{(cluster.coherence * 100).toFixed(1)}% coherent</span>
              </div>
              <div class="cluster-topics">
                {#each cluster.topics.slice(0, 3) as topic}
                  <span class="topic-tag semantic">{topic}</span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      </div>
      
      {#if selectedNode && $analyticsData.centralityMetrics[selectedNode.id]}
        <div class="analytics-section">
          <h5 class="section-title">🔍 Node Analysis: {selectedNode.label}</h5>
          <div class="node-metrics">
            <div class="metric-bar-item">
              <span class="bar-label">Degree Centrality:</span>
              <div class="metric-bar">
                <div class="bar-fill degree" style="width: {$analyticsData.centralityMetrics[selectedNode.id].degree * 100}%"></div>
              </div>
              <span class="bar-value">{($analyticsData.centralityMetrics[selectedNode.id].degree * 100).toFixed(1)}%</span>
            </div>
            <div class="metric-bar-item">
              <span class="bar-label">Betweenness:</span>
              <div class="metric-bar">
                <div class="bar-fill betweenness" style="width: {$analyticsData.centralityMetrics[selectedNode.id].betweenness * 100}%"></div>
              </div>
              <span class="bar-value">{($analyticsData.centralityMetrics[selectedNode.id].betweenness * 100).toFixed(1)}%</span>
            </div>
            <div class="metric-bar-item">
              <span class="bar-label">Closeness:</span>
              <div class="metric-bar">
                <div class="bar-fill closeness" style="width: {$analyticsData.centralityMetrics[selectedNode.id].closeness * 100}%"></div>
              </div>
              <span class="bar-value">{($analyticsData.centralityMetrics[selectedNode.id].closeness * 100).toFixed(1)}%</span>
            </div>
            <div class="metric-bar-item">
              <span class="bar-label">Influence Score:</span>
              <div class="metric-bar">
                <div class="bar-fill influence" style="width: {($analyticsData.influenceScores[selectedNode.id] || 0) * 100}%"></div>
              </div>
              <span class="bar-value">{(($analyticsData.influenceScores[selectedNode.id] || 0) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      {/if}
      
      <div class="analytics-footer">
        <div class="last-update">
          Last analyzed: {new Date($analyticsData.lastAnalysis).toLocaleTimeString()}
        </div>
      </div>
    {:else}
      <div class="analytics-loading">
        <div class="loading-icon">🔄</div>
        <div class="loading-text">Computing analytics...</div>
      </div>
    {/if}
  </div>
  
  <!-- Collaborative Status -->
  <div class="collaborative-status" class:active={$collaborativeSession.isActive}>
    <div class="collab-icon">
      {$collaborativeSession.isActive ? '👥' : '📡'}
    </div>
    <div class="collab-text">
      {#if $collaborativeSession.isActive}
        <span class="status-text">Collaborative Session Active</span>
        <span class="participant-count">{$collaborativeSession.participants.length} participants</span>
      {:else}
        <span class="status-text">Offline Mode</span>
      {/if}
    </div>
  </div>
{/if}

<style>
  .performance-overlay {
    position: fixed;
    top: 20px;
    left: 20px;
    background: rgba(0, 0, 0, 0.85);
    color: white;
    padding: 12px;
    border-radius: 8px;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 11px;
    z-index: 1000;
    min-width: 150px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .overlay-title {
    margin: 0 0 8px 0;
    font-size: 12px;
    font-weight: bold;
    color: #4CAF50;
  }
  
  .metric-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 4px;
  }
  
  .metric-label {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .metric-value {
    color: #4CAF50;
    font-weight: bold;
  }
  
  .metric-value.warning {
    color: #FF9800;
  }
  
  .metric-value.critical {
    color: #F44336;
  }
  
  .analytics-panel {
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 16px;
    border-radius: 12px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 12px;
    z-index: 1000;
    max-width: 320px;
    max-height: 500px;
    overflow-y: auto;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  .panel-title {
    margin: 0 0 16px 0;
    font-size: 14px;
    font-weight: 600;
    color: #4CAF50;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 8px;
  }
  
  .analytics-section {
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  .section-title {
    margin: 0 0 8px 0;
    font-size: 13px;
    font-weight: 600;
    color: #E3F2FD;
  }
  
  .metric-grid {
    display: grid;
    gap: 6px;
  }
  
  .metric-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.05);
    padding: 6px 8px;
    border-radius: 4px;
  }
  
  .metric-name {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .metric-score {
    font-weight: 600;
    color: #4CAF50;
  }
  
  .community-list, .gaps-list, .cluster-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .community-item, .cluster-item {
    background: rgba(33, 150, 243, 0.1);
    border: 1px solid rgba(33, 150, 243, 0.2);
    border-radius: 6px;
    padding: 8px;
  }
  
  .community-header, .cluster-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }
  
  .community-name {
    font-weight: 600;
    color: #2196F3;
    font-size: 11px;
  }
  
  .community-size, .cluster-size, .cluster-coherence {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .community-topics, .cluster-topics {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .topic-tag {
    background: rgba(76, 175, 80, 0.2);
    color: #4CAF50;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 9px;
    font-weight: 500;
  }
  
  .topic-tag.semantic {
    background: rgba(156, 39, 176, 0.2);
    color: #9C27B0;
  }
  
  .gap-item {
    background: rgba(255, 152, 0, 0.1);
    border: 1px solid rgba(255, 152, 0, 0.2);
    border-radius: 6px;
    padding: 8px;
  }
  
  .gap-item.severity-high {
    background: rgba(244, 67, 54, 0.1);
    border-color: rgba(244, 67, 54, 0.3);
  }
  
  .gap-item.severity-medium {
    background: rgba(255, 152, 0, 0.1);
    border-color: rgba(255, 152, 0, 0.3);
  }
  
  .gap-item.severity-low {
    background: rgba(255, 235, 59, 0.1);
    border-color: rgba(255, 235, 59, 0.3);
  }
  
  .gap-type {
    font-weight: 600;
    font-size: 11px;
    color: #FF9800;
    text-transform: capitalize;
    margin-bottom: 4px;
  }
  
  .gap-suggestion {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.3;
  }
  
  .node-metrics {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .metric-bar-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
  }
  
  .bar-label {
    width: 80px;
    color: rgba(255, 255, 255, 0.8);
    font-size: 9px;
  }
  
  .metric-bar {
    flex: 1;
    height: 12px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    overflow: hidden;
  }
  
  .bar-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.3s ease;
  }
  
  .bar-fill.degree {
    background: linear-gradient(90deg, #4CAF50, #2E7D32);
  }
  
  .bar-fill.betweenness {
    background: linear-gradient(90deg, #2196F3, #1565C0);
  }
  
  .bar-fill.closeness {
    background: linear-gradient(90deg, #FF9800, #F57C00);
  }
  
  .bar-fill.influence {
    background: linear-gradient(90deg, #9C27B0, #6A1B9A);
  }
  
  .bar-value {
    width: 35px;
    text-align: right;
    font-weight: 600;
    color: #4CAF50;
    font-size: 9px;
  }
  
  .analytics-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 8px;
    margin-top: 8px;
  }
  
  .last-update {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.6);
    text-align: center;
  }
  
  .analytics-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
  }
  
  .loading-icon {
    font-size: 24px;
    animation: spin 2s linear infinite;
    margin-bottom: 8px;
  }
  
  .loading-text {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
  }
  
  .collaborative-status {
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: rgba(150, 0, 0, 0.9);
    color: white;
    padding: 10px 15px;
    border-radius: 20px;
    font-size: 11px;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 8px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }
  
  .collaborative-status.active {
    background: rgba(0, 150, 0, 0.9);
  }
  
  .collab-icon {
    font-size: 14px;
  }
  
  .collab-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .status-text {
    font-weight: 600;
    font-size: 11px;
  }
  
  .participant-count {
    font-size: 9px;
    opacity: 0.8;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Scrollbar styling for analytics panel */
  .analytics-panel::-webkit-scrollbar {
    width: 4px;
  }
  
  .analytics-panel::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }
  
  .analytics-panel::-webkit-scrollbar-thumb {
    background: rgba(76, 175, 80, 0.6);
    border-radius: 2px;
  }
  
  .analytics-panel::-webkit-scrollbar-thumb:hover {
    background: rgba(76, 175, 80, 0.8);
  }
</style>
