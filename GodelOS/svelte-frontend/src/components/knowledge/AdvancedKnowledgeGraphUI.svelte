<!--
Advanced Knowledge Graph UI Enhancements
- Enhanced 3D visualization performance with LOD and culling
- Collaborative knowledge editing with real-time sync
- Comprehensive knowledge graph analytics dashboard
-->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable, derived } from 'svelte/store';
  import { knowledgeState } from '../../stores/cognitive.js';
  import { GödelOSAPI } from '../../utils/api.js';
  import * as d3 from 'd3';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
  
  // Enhanced performance tracking
  let performanceMetrics = writable({
    fps: 0,
    renderTime: 0,
    nodeCount: 0,
    edgeCount: 0,
    culledNodes: 0,
    memoryUsage: 0,
    lastUpdate: Date.now()
  });
  
  // Collaborative editing state
  let collaborativeSession = writable({
    isActive: false,
    sessionId: null,
    participants: [],
    pendingChanges: [],
    conflictResolution: 'merge',
    lastSync: null
  });
  
  // Advanced analytics state
  let analyticsData = writable({
    centralityMetrics: {},
    clusteringCoefficient: 0,
    pathLengths: {},
    communityStructure: [],
    temporalEvolution: [],
    semanticClusters: [],
    influenceScores: {},
    knowledgeGaps: [],
    conceptDensity: {},
    lastAnalysis: null
  });
  
  // Performance optimization settings
  let performanceSettings = {
    enableLOD: true,
    maxVisibleNodes: 500,
    cullDistance: 1000,
    adaptiveQuality: true,
    useInstancedMeshes: true,
    enableFrustumCulling: true,
    targetFPS: 60,
    enableTemporal: true
  };
  
  // Enhanced 3D performance optimizations
  let lodLevels = {
    high: { distance: 200, sphereSegments: 32, detail: 'full' },
    medium: { distance: 500, sphereSegments: 16, detail: 'reduced' },
    low: { distance: 1000, sphereSegments: 8, detail: 'minimal' }
  };
  
  // Instanced mesh pools for performance
  let instancedGeometries = {};
  let instancedMaterials = {};
  let nodeInstancedMeshes = {};
  
  // Collaborative editing WebSocket
  let collaborativeWS = null;
  let editingState = writable({
    selectedNodes: new Set(),
    selectedEdges: new Set(),
    editMode: 'select', // select, add_node, add_edge, delete, edit_properties
    clipboardNodes: [],
    clipboardEdges: [],
    undoStack: [],
    redoStack: [],
    isEditing: false
  });
  
  // Advanced analytics computation
  function computeAdvancedAnalytics(graphData) {
    console.log('🧮 Computing advanced knowledge graph analytics...');
    
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    
    // 1. Centrality Metrics (Betweenness, Closeness, PageRank)
    const centralityMetrics = computeCentralityMetrics(nodes, edges);
    
    // 2. Community Detection using modularity optimization
    const communityStructure = detectCommunities(nodes, edges);
    
    // 3. Knowledge Gap Analysis
    const knowledgeGaps = identifyKnowledgeGaps(nodes, edges);
    
    // 4. Semantic Clustering
    const semanticClusters = performSemanticClustering(nodes);
    
    // 5. Temporal Evolution Analysis
    const temporalEvolution = analyzeTemporalEvolution(nodes, edges);
    
    // 6. Concept Density Mapping
    const conceptDensity = mapConceptDensity(nodes, edges);
    
    // 7. Influence Score Calculation
    const influenceScores = calculateInfluenceScores(nodes, edges);
    
    // 8. Path Length Analysis
    const pathLengths = analyzePathLengths(nodes, edges);
    
    // 9. Clustering Coefficient
    const clusteringCoefficient = calculateClusteringCoefficient(nodes, edges);
    
    analyticsData.update(current => ({
      ...current,
      centralityMetrics,
      clusteringCoefficient,
      pathLengths,
      communityStructure,
      temporalEvolution,
      semanticClusters,
      influenceScores,
      knowledgeGaps,
      conceptDensity,
      lastAnalysis: new Date().toISOString()
    }));
    
    return {
      centralityMetrics,
      clusteringCoefficient,
      pathLengths,
      communityStructure,
      temporalEvolution,
      semanticClusters,
      influenceScores,
      knowledgeGaps,
      conceptDensity
    };
  }
  
  function computeCentralityMetrics(nodes, edges) {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const adjacencyList = new Map();
    
    // Build adjacency list
    nodes.forEach(node => adjacencyList.set(node.id, new Set()));
    edges.forEach(edge => {
      adjacencyList.get(edge.source)?.add(edge.target);
      adjacencyList.get(edge.target)?.add(edge.source);
    });
    
    const metrics = {};
    
    nodes.forEach(node => {
      // Degree centrality
      const degree = adjacencyList.get(node.id)?.size || 0;
      const degreeCentrality = degree / Math.max(1, nodes.length - 1);
      
      // Betweenness centrality (simplified)
      const betweenness = calculateBetweennessCentrality(node.id, adjacencyList);
      
      // Closeness centrality
      const closeness = calculateClosenessCentrality(node.id, adjacencyList);
      
      // PageRank (simplified)
      const pagerank = calculatePageRank(node.id, adjacencyList, edges);
      
      metrics[node.id] = {
        degree: degreeCentrality,
        betweenness: betweenness,
        closeness: closeness,
        pagerank: pagerank,
        combined: (degreeCentrality + betweenness + closeness + pagerank) / 4
      };
    });
    
    return metrics;
  }
  
  function calculateBetweennessCentrality(nodeId, adjacencyList) {
    // Simplified betweenness centrality using BFS
    let betweenness = 0;
    const nodes = Array.from(adjacencyList.keys());
    
    for (let s of nodes) {
      if (s === nodeId) continue;
      for (let t of nodes) {
        if (t === nodeId || t === s) continue;
        
        const pathsThrough = countPathsThrough(s, t, nodeId, adjacencyList);
        const totalPaths = countAllPaths(s, t, adjacencyList);
        
        if (totalPaths > 0) {
          betweenness += pathsThrough / totalPaths;
        }
      }
    }
    
    const n = nodes.length;
    return n > 2 ? betweenness / ((n - 1) * (n - 2) / 2) : 0;
  }
  
  function calculateClosenessCentrality(nodeId, adjacencyList) {
    const distances = bfsDistances(nodeId, adjacencyList);
    const validDistances = Object.values(distances).filter(d => d > 0 && d < Infinity);
    
    if (validDistances.length === 0) return 0;
    
    const avgDistance = validDistances.reduce((sum, d) => sum + d, 0) / validDistances.length;
    return avgDistance > 0 ? 1 / avgDistance : 0;
  }
  
  function calculatePageRank(nodeId, adjacencyList, edges, damping = 0.85, iterations = 100) {
    const nodes = Array.from(adjacencyList.keys());
    const n = nodes.length;
    let pagerank = new Map(nodes.map(id => [id, 1 / n]));
    
    for (let i = 0; i < iterations; i++) {
      const newPagerank = new Map();
      
      for (let node of nodes) {
        let rank = (1 - damping) / n;
        
        // Add contributions from incoming links
        for (let edge of edges) {
          if (edge.target === node) {
            const sourceOutDegree = adjacencyList.get(edge.source)?.size || 1;
            rank += damping * (pagerank.get(edge.source) || 0) / sourceOutDegree;
          }
        }
        
        newPagerank.set(node, rank);
      }
      
      pagerank = newPagerank;
    }
    
    return pagerank.get(nodeId) || 0;
  }
  
  function detectCommunities(nodes, edges) {
    // Simplified Louvain algorithm for community detection
    const communities = [];
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const adjacencyList = new Map();
    
    // Build adjacency list with weights
    nodes.forEach(node => adjacencyList.set(node.id, new Map()));
    edges.forEach(edge => {
      const weight = edge.weight || 1;
      adjacencyList.get(edge.source)?.set(edge.target, weight);
      adjacencyList.get(edge.target)?.set(edge.source, weight);
    });
    
    // Initialize each node as its own community
    let nodeCommunity = new Map(nodes.map(n => [n.id, n.id]));
    let improved = true;
    
    while (improved) {
      improved = false;
      
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
      communities.push({
        id: communityIndex++,
        name: `Community ${communityIndex}`,
        members: memberIds,
        size: memberIds.length,
        centrality: calculateCommunityCentrality(memberIds, adjacencyList),
        topics: extractCommunityTopics(memberIds, nodeMap)
      });
    }
    
    return communities;
  }
  
  function identifyKnowledgeGaps(nodes, edges) {
    const gaps = [];
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const adjacencyList = new Map();
    
    // Build adjacency list
    nodes.forEach(node => adjacencyList.set(node.id, new Set()));
    edges.forEach(edge => {
      adjacencyList.get(edge.source)?.add(edge.target);
      adjacencyList.get(edge.target)?.add(edge.source);
    });
    
    // Find isolated nodes (potential knowledge gaps)
    nodes.forEach(node => {
      const connections = adjacencyList.get(node.id)?.size || 0;
      if (connections < 2) {
        gaps.push({
          type: 'isolated_concept',
          nodeId: node.id,
          label: node.label || node.id,
          severity: connections === 0 ? 'high' : 'medium',
          suggestion: 'Consider adding relationships to related concepts'
        });
      }
    });
    
    // Find missing bridges between communities
    const communities = detectCommunities(nodes, edges);
    for (let i = 0; i < communities.length; i++) {
      for (let j = i + 1; j < communities.length; j++) {
        const community1 = communities[i];
        const community2 = communities[j];
        
        const bridgeCount = countBridges(community1.members, community2.members, edges);
        if (bridgeCount < 2) {
          gaps.push({
            type: 'missing_bridge',
            community1: community1.name,
            community2: community2.name,
            severity: bridgeCount === 0 ? 'high' : 'low',
            suggestion: `Consider adding relationships between ${community1.name} and ${community2.name}`
          });
        }
      }
    }
    
    // Find concepts with low semantic diversity
    nodes.forEach(node => {
      const neighbors = Array.from(adjacencyList.get(node.id) || []);
      if (neighbors.length > 2) {
        const semanticDiversity = calculateSemanticDiversity(node, neighbors, nodeMap);
        if (semanticDiversity < 0.3) {
          gaps.push({
            type: 'low_diversity',
            nodeId: node.id,
            label: node.label || node.id,
            severity: 'medium',
            suggestion: 'Consider connecting to concepts from different domains'
          });
        }
      }
    });
    
    return gaps.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      return severityOrder[b.severity] - severityOrder[a.severity];
    });
  }
  
  function performSemanticClustering(nodes) {
    // Group nodes by semantic similarity using content analysis
    const clusters = [];
    const processed = new Set();
    
    for (let node of nodes) {
      if (processed.has(node.id)) continue;
      
      const cluster = {
        id: clusters.length,
        centroid: node.id,
        members: [node.id],
        avgSimilarity: 0,
        topics: extractKeyPhrases(node.content || node.label || ''),
        density: 1
      };
      
      processed.add(node.id);
      
      // Find similar nodes
      for (let otherNode of nodes) {
        if (processed.has(otherNode.id)) continue;
        
        const similarity = calculateSemanticSimilarity(node, otherNode);
        if (similarity > 0.6) {
          cluster.members.push(otherNode.id);
          processed.add(otherNode.id);
        }
      }
      
      if (cluster.members.length > 1) {
        cluster.avgSimilarity = calculateClusterCoherence(cluster.members, nodes);
        cluster.density = cluster.members.length / nodes.length;
        clusters.push(cluster);
      }
    }
    
    return clusters.sort((a, b) => b.density - a.density);
  }
  
  // Enhanced 3D Performance Optimizations
  function initializePerformanceOptimizations() {
    console.log('🚀 Initializing performance optimizations...');
    
    // Create instanced geometries for different node types
    Object.keys(nodeCategories).forEach(category => {
      const size = nodeCategories[category].size || 8;
      
      // High LOD
      instancedGeometries[`${category}_high`] = new THREE.SphereGeometry(
        size, lodLevels.high.sphereSegments, lodLevels.high.sphereSegments
      );
      
      // Medium LOD
      instancedGeometries[`${category}_medium`] = new THREE.SphereGeometry(
        size, lodLevels.medium.sphereSegments, lodLevels.medium.sphereSegments
      );
      
      // Low LOD
      instancedGeometries[`${category}_low`] = new THREE.SphereGeometry(
        size, lodLevels.low.sphereSegments, lodLevels.low.sphereSegments
      );
      
      // Create materials
      const color = nodeCategories[category].color || '#4CAF50';
      instancedMaterials[category] = new THREE.MeshLambertMaterial({
        color: color,
        transparent: true,
        opacity: 0.8
      });
    });
    
    // Start performance monitoring
    startPerformanceMonitoring();
  }
  
  function createOptimized3DNodes() {
    console.log('🔮 Creating optimized 3D nodes with LOD...');
    
    // Clear existing nodes
    nodeObjects.forEach(obj => scene.remove(obj));
    nodeObjects = [];
    
    if (!graphData.nodes) return;
    
    // Group nodes by category for instanced rendering
    const nodesByCategory = new Map();
    graphData.nodes.forEach(node => {
      const category = node.category || 'concept';
      if (!nodesByCategory.has(category)) {
        nodesByCategory.set(category, []);
      }
      nodesByCategory.get(category).push(node);
    });
    
    // Create instanced meshes for each category
    nodesByCategory.forEach((nodes, category) => {
      if (performanceSettings.useInstancedMeshes && nodes.length > 10) {
        createInstancedMeshForCategory(category, nodes);
      } else {
        // Create individual meshes for small groups
        nodes.forEach(node => createIndividualNode(node));
      }
    });
    
    updatePerformanceMetrics();
  }
  
  function createInstancedMeshForCategory(category, nodes) {
    const count = Math.min(nodes.length, performanceSettings.maxVisibleNodes);
    const geometry = instancedGeometries[`${category}_medium`];
    const material = instancedMaterials[category];
    
    if (!geometry || !material) return;
    
    const instancedMesh = new THREE.InstancedMesh(geometry, material, count);
    const dummy = new THREE.Object3D();
    
    nodes.slice(0, count).forEach((node, index) => {
      // Position
      dummy.position.set(
        (Math.random() - 0.5) * 400,
        (Math.random() - 0.5) * 400,
        (Math.random() - 0.5) * 400
      );
      
      // Scale based on importance
      const importance = node.importance || 1;
      dummy.scale.setScalar(importance);
      
      dummy.updateMatrix();
      instancedMesh.setMatrixAt(index, dummy.matrix);
      
      // Store node reference
      if (!instancedMesh.userData.nodes) instancedMesh.userData.nodes = [];
      instancedMesh.userData.nodes[index] = node;
    });
    
    instancedMesh.instanceMatrix.needsUpdate = true;
    instancedMesh.frustumCulled = performanceSettings.enableFrustumCulling;
    
    scene.add(instancedMesh);
    nodeInstancedMeshes[category] = instancedMesh;
    nodeObjects.push(instancedMesh);
  }
  
  function createIndividualNode(node) {
    const category = node.category || 'concept';
    const distance = camera.position.distanceTo(new THREE.Vector3(0, 0, 0));
    
    // Select LOD level based on distance
    let lodLevel = 'high';
    if (distance > lodLevels.medium.distance) lodLevel = 'medium';
    if (distance > lodLevels.low.distance) lodLevel = 'low';
    
    const geometry = instancedGeometries[`${category}_${lodLevel}`];
    const material = instancedMaterials[category];
    
    if (!geometry || !material) return;
    
    const mesh = new THREE.Mesh(geometry, material);
    
    // Position
    mesh.position.set(
      (Math.random() - 0.5) * 400,
      (Math.random() - 0.5) * 400,
      (Math.random() - 0.5) * 400
    );
    
    // Scale based on importance
    const importance = node.importance || 1;
    mesh.scale.setScalar(importance);
    
    mesh.userData = node;
    mesh.frustumCulled = performanceSettings.enableFrustumCulling;
    
    scene.add(mesh);
    nodeObjects.push(mesh);
  }
  
  function startPerformanceMonitoring() {
    let frameCount = 0;
    let lastTime = performance.now();
    let renderTimes = [];
    
    function monitor() {
      const currentTime = performance.now();
      const deltaTime = currentTime - lastTime;
      
      frameCount++;
      
      // Calculate FPS every second
      if (deltaTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / deltaTime);
        frameCount = 0;
        lastTime = currentTime;
        
        // Update performance metrics
        performanceMetrics.update(current => ({
          ...current,
          fps: fps,
          renderTime: renderTimes.length > 0 ? renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length : 0,
          nodeCount: nodeObjects.length,
          edgeCount: edgeObjects.length,
          memoryUsage: performance.memory ? performance.memory.usedJSHeapSize / (1024 * 1024) : 0,
          lastUpdate: currentTime
        }));
        
        renderTimes = [];
        
        // Adaptive quality adjustment
        if (performanceSettings.adaptiveQuality) {
          adjustQualityBasedOnPerformance(fps);
        }
      }
      
      if (renderer && scene && camera) {
        const renderStart = performance.now();
        
        // Frustum culling for individual objects
        if (performanceSettings.enableFrustumCulling) {
          performFrustumCulling();
        }
        
        renderer.render(scene, camera);
        
        const renderEnd = performance.now();
        renderTimes.push(renderEnd - renderStart);
      }
      
      requestAnimationFrame(monitor);
    }
    
    monitor();
  }
  
  function adjustQualityBasedOnPerformance(fps) {
    if (fps < performanceSettings.targetFPS * 0.8) {
      // Reduce quality
      if (performanceSettings.maxVisibleNodes > 100) {
        performanceSettings.maxVisibleNodes *= 0.9;
        console.log(`🔧 Reducing max visible nodes to ${Math.floor(performanceSettings.maxVisibleNodes)}`);
      }
      
      // Switch to lower LOD
      lodLevels.high.distance *= 0.8;
      lodLevels.medium.distance *= 0.8;
      
    } else if (fps > performanceSettings.targetFPS * 1.2) {
      // Increase quality
      if (performanceSettings.maxVisibleNodes < 1000) {
        performanceSettings.maxVisibleNodes *= 1.1;
      }
      
      // Switch to higher LOD
      lodLevels.high.distance *= 1.1;
      lodLevels.medium.distance *= 1.1;
    }
  }
  
  function performFrustumCulling() {
    const frustum = new THREE.Frustum();
    const matrix = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(matrix);
    
    let culledCount = 0;
    
    nodeObjects.forEach(obj => {
      if (obj.userData && obj.userData.nodes) {
        // Handle instanced meshes
        obj.visible = frustum.intersectsBox(obj.boundingBox || obj.geometry.boundingBox);
      } else {
        // Handle individual meshes
        obj.visible = frustum.containsPoint(obj.position);
      }
      
      if (!obj.visible) culledCount++;
    });
    
    performanceMetrics.update(current => ({
      ...current,
      culledNodes: culledCount
    }));
  }
  
  // Collaborative Editing Functions
  function initializeCollaborativeEditing() {
    console.log('👥 Initializing collaborative editing...');
    
    // Connect to collaborative WebSocket
    connectCollaborativeWebSocket();
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Initialize editing tools
    setupEditingTools();
  }
  
  function connectCollaborativeWebSocket() {
    const wsUrl = `${WS_BASE}/api/knowledge-graph/collaborative`;
    
    try {
      collaborativeWS = new WebSocket(wsUrl);
      
      collaborativeWS.onopen = () => {
        console.log('✅ Connected to collaborative editing session');
        
        collaborativeSession.update(current => ({
          ...current,
          isActive: true,
          sessionId: generateSessionId(),
          lastSync: new Date().toISOString()
        }));
      };
      
      collaborativeWS.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleCollaborativeMessage(message);
        } catch (error) {
          console.error('❌ Error parsing collaborative message:', error);
        }
      };
      
      collaborativeWS.onclose = () => {
        console.log('📡 Collaborative session disconnected');
        collaborativeSession.update(current => ({
          ...current,
          isActive: false,
          sessionId: null
        }));
        
        // Attempt to reconnect after 5 seconds
        setTimeout(connectCollaborativeWebSocket, 5000);
      };
      
      collaborativeWS.onerror = (error) => {
        console.error('❌ Collaborative WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('❌ Failed to initialize collaborative WebSocket:', error);
    }
  }
  
  function handleCollaborativeMessage(message) {
    switch (message.type) {
      case 'participant_joined':
        collaborativeSession.update(current => ({
          ...current,
          participants: [...current.participants, message.participant]
        }));
        break;
        
      case 'participant_left':
        collaborativeSession.update(current => ({
          ...current,
          participants: current.participants.filter(p => p.id !== message.participantId)
        }));
        break;
        
      case 'node_added':
        applyRemoteNodeAdd(message.node);
        break;
        
      case 'node_updated':
        applyRemoteNodeUpdate(message.nodeId, message.changes);
        break;
        
      case 'node_deleted':
        applyRemoteNodeDelete(message.nodeId);
        break;
        
      case 'edge_added':
        applyRemoteEdgeAdd(message.edge);
        break;
        
      case 'edge_deleted':
        applyRemoteEdgeDelete(message.edgeId);
        break;
        
      case 'selection_changed':
        showRemoteSelection(message.participantId, message.selection);
        break;
        
      case 'conflict_detected':
        handleConflict(message.conflict);
        break;
    }
  }
  
  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
      if (!$editingState.isEditing) return;
      
      // Ctrl/Cmd + Z: Undo
      if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        performUndo();
      }
      
      // Ctrl/Cmd + Shift + Z: Redo
      if ((event.ctrlKey || event.metaKey) && event.key === 'z' && event.shiftKey) {
        event.preventDefault();
        performRedo();
      }
      
      // Ctrl/Cmd + C: Copy
      if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
        event.preventDefault();
        copySelectedElements();
      }
      
      // Ctrl/Cmd + V: Paste
      if ((event.ctrlKey || event.metaKey) && event.key === 'v') {
        event.preventDefault();
        pasteElements();
      }
      
      // Delete: Delete selected elements
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        deleteSelectedElements();
      }
      
      // Escape: Exit edit mode
      if (event.key === 'Escape') {
        event.preventDefault();
        exitEditMode();
      }
    });
  }
  
  function setupEditingTools() {
    // Mouse event handlers for selection and editing
    if (renderer && renderer.domElement) {
      renderer.domElement.addEventListener('mousedown', handleMouseDown);
      renderer.domElement.addEventListener('mousemove', handleMouseMove);
      renderer.domElement.addEventListener('mouseup', handleMouseUp);
      renderer.domElement.addEventListener('dblclick', handleDoubleClick);
    }
  }
  
  // Helper functions for collaborative operations
  function applyRemoteNodeAdd(node) {
    graphData.nodes = [...(graphData.nodes || []), node];
    updateGraph();
    
    // Show notification
    showCollaborativeNotification(`Node "${node.label}" added by another user`, 'info');
  }
  
  function applyRemoteNodeUpdate(nodeId, changes) {
    graphData.nodes = graphData.nodes.map(node => 
      node.id === nodeId ? { ...node, ...changes } : node
    );
    updateGraph();
    
    showCollaborativeNotification(`Node updated by another user`, 'info');
  }
  
  function applyRemoteNodeDelete(nodeId) {
    graphData.nodes = graphData.nodes.filter(node => node.id !== nodeId);
    graphData.edges = graphData.edges.filter(edge => 
      edge.source !== nodeId && edge.target !== nodeId
    );
    updateGraph();
    
    showCollaborativeNotification(`Node deleted by another user`, 'warning');
  }
  
  function showCollaborativeNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `collaborative-notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    Object.assign(notification.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      padding: '12px 20px',
      borderRadius: '8px',
      backgroundColor: type === 'warning' ? '#ff9800' : '#2196f3',
      color: 'white',
      zIndex: '10000',
      fontSize: '14px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
      transition: 'all 0.3s ease'
    });
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.opacity = '0';
      setTimeout(() => document.body.removeChild(notification), 300);
    }, 3000);
  }
  
  // Utility functions for analytics
  function extractKeyPhrases(text) {
    if (!text) return [];
    // Simplified key phrase extraction
    return text.split(/[.!?]+/)
      .map(s => s.trim())
      .filter(s => s.length > 10)
      .slice(0, 5);
  }
  
  function calculateSemanticSimilarity(node1, node2) {
    // Simplified semantic similarity based on shared terms
    const text1 = (node1.content || node1.label || '').toLowerCase();
    const text2 = (node2.content || node2.label || '').toLowerCase();
    
    const words1 = new Set(text1.split(/\W+/).filter(w => w.length > 2));
    const words2 = new Set(text2.split(/\W+/).filter(w => w.length > 2));
    
    const intersection = new Set([...words1].filter(w => words2.has(w)));
    const union = new Set([...words1, ...words2]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  }
  
  function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9);
  }
  
  function updatePerformanceMetrics() {
    performanceMetrics.update(current => ({
      ...current,
      nodeCount: nodeObjects.length,
      edgeCount: edgeObjects.length,
      lastUpdate: Date.now()
    }));
  }
  
  // Cleanup function
  function cleanup3DPerformance() {
    // Clean up instanced geometries
    Object.values(instancedGeometries).forEach(geometry => geometry.dispose());
    instancedGeometries = {};
    
    // Clean up materials
    Object.values(instancedMaterials).forEach(material => material.dispose());
    instancedMaterials = {};
    
    // Clean up instanced meshes
    Object.values(nodeInstancedMeshes).forEach(mesh => {
      scene.remove(mesh);
      mesh.dispose();
    });
    nodeInstancedMeshes = {};
    
    // Close collaborative WebSocket
    if (collaborativeWS) {
      collaborativeWS.close();
      collaborativeWS = null;
    }
  }
  
  // Expose reactive stores for external access
  export { performanceMetrics, collaborativeSession, analyticsData, editingState };
  
  // Initialize on mount
  onMount(() => {
    initializePerformanceOptimizations();
    initializeCollaborativeEditing();
  });
  
  // Cleanup on destroy
  onDestroy(() => {
    cleanup3DPerformance();
  });
</script>

<style>
  .collaborative-notification {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    animation: slideIn 0.3s ease-out;
  }
  
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  .performance-overlay {
    position: absolute;
    top: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px;
    border-radius: 6px;
    font-family: monospace;
    font-size: 12px;
    z-index: 1000;
    min-width: 200px;
  }
  
  .analytics-panel {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 15px;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 13px;
    z-index: 1000;
    max-width: 300px;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .collaborative-status {
    position: absolute;
    bottom: 10px;
    left: 10px;
    background: rgba(0, 150, 0, 0.9);
    color: white;
    padding: 8px 15px;
    border-radius: 20px;
    font-size: 12px;
    z-index: 1000;
  }
  
  .collaborative-status.inactive {
    background: rgba(150, 0, 0, 0.9);
  }
  
  .editing-toolbar {
    position: absolute;
    bottom: 10px;
    right: 10px;
    background: rgba(255, 255, 255, 0.95);
    padding: 10px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    display: flex;
    gap: 8px;
  }
  
  .edit-button {
    padding: 8px 12px;
    border: none;
    border-radius: 4px;
    background: #2196f3;
    color: white;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.2s ease;
  }
  
  .edit-button:hover {
    background: #1976d2;
  }
  
  .edit-button.active {
    background: #ff9800;
  }
  
  .metric-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    padding: 2px 0;
  }
  
  .metric-label {
    font-weight: bold;
  }
  
  .metric-value {
    font-family: monospace;
  }
  
  .analytics-section {
    margin-bottom: 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    padding-bottom: 10px;
  }
  
  .analytics-title {
    font-weight: bold;
    font-size: 14px;
    margin-bottom: 8px;
    color: #4CAF50;
  }
</style>
