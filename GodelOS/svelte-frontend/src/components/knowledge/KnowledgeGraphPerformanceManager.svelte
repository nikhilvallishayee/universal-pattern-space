<!--
Knowledge Graph Performance Manager
Handles Level of Detail (LOD), Instanced Rendering, and 3D Performance Optimizations
-->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  
  // Props
  export let scene = null;
  export let camera = null;
  export let renderer = null;
  export let graphData = { nodes: [], edges: [] };
  export let isPerformanceMode = true;
  
  // Performance state
  let performanceState = writable({
    lodEnabled: true,
    frustumCulling: true,
    instancedRendering: true,
    maxVisibleNodes: 1000,
    maxVisibleEdges: 2000,
    lodLevels: {
      high: { distance: 100, detail: 1.0 },
      medium: { distance: 300, detail: 0.5 },
      low: { distance: 1000, detail: 0.25 }
    }
  });
  
  // Instanced geometries for performance
  let instancedNodeGeometry = null;
  let instancedEdgeGeometry = null;
  let nodeInstancedMesh = null;
  let edgeInstancedMesh = null;
  
  // Performance monitoring
  let performanceMetrics = writable({
    fps: 0,
    drawCalls: 0,
    triangles: 0,
    visibleNodes: 0,
    visibleEdges: 0,
    memoryUsage: 0
  });
  
  // LOD management
  let lodManager = {
    nodeVisibilityMap: new Map(),
    edgeVisibilityMap: new Map(),
    lastCameraPosition: { x: 0, y: 0, z: 0 },
    lastUpdateTime: 0,
    updateInterval: 100 // ms
  };
  
  // Import Three.js modules
  let THREE;
  
  async function initThreeJS() {
    const threeModule = await import('three');
    THREE = threeModule;
    
    if (scene && camera && renderer && isPerformanceMode) {
      initPerformanceOptimizations();
    }
  }
  
  function initPerformanceOptimizations() {
    console.log('🚀 Initializing performance optimizations...');
    
    // Enable frustum culling
    scene.frustumCulled = true;
    
    // Set up renderer optimizations
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = false; // Disable shadows for performance
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    
    // Initialize instanced rendering
    initInstancedRendering();
    
    // Start LOD update loop
    startLODUpdates();
    
    console.log('✅ Performance optimizations initialized');
  }
  
  function initInstancedRendering() {
    if (!THREE || !scene) return;
    
    const maxNodes = Math.max(1000, graphData.nodes?.length || 0);
    const maxEdges = Math.max(2000, graphData.edges?.length || 0);
    
    // Node instanced geometry
    const nodeGeometry = new THREE.SphereGeometry(1, 8, 6); // Lower poly sphere
    const nodeMaterial = new THREE.MeshBasicMaterial({ 
      color: 0x4CAF50,
      transparent: true,
      opacity: 0.8
    });
    
    nodeInstancedMesh = new THREE.InstancedMesh(nodeGeometry, nodeMaterial, maxNodes);
    nodeInstancedMesh.userData.type = 'instancedNodes';
    scene.add(nodeInstancedMesh);
    
    // Edge instanced geometry  
    const edgeGeometry = new THREE.CylinderGeometry(0.1, 0.1, 1, 4); // Lower poly cylinder
    const edgeMaterial = new THREE.MeshBasicMaterial({
      color: 0x666666,
      transparent: true,
      opacity: 0.6
    });
    
    edgeInstancedMesh = new THREE.InstancedMesh(edgeGeometry, edgeMaterial, maxEdges);
    edgeInstancedMesh.userData.type = 'instancedEdges';
    scene.add(edgeInstancedMesh);
    
    // Initialize transform matrices
    const matrix = new THREE.Matrix4();
    for (let i = 0; i < maxNodes; i++) {
      matrix.identity();
      nodeInstancedMesh.setMatrixAt(i, matrix);
    }
    for (let i = 0; i < maxEdges; i++) {
      matrix.identity();
      edgeInstancedMesh.setMatrixAt(i, matrix);
    }
    
    console.log(`📦 Initialized instanced rendering: ${maxNodes} nodes, ${maxEdges} edges`);
  }
  
  function updateInstancedNodes(nodes, lodLevel = 'high') {
    if (!nodeInstancedMesh || !THREE) return;
    
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const scale = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    
    const detailLevel = $performanceState.lodLevels[lodLevel]?.detail || 1.0;
    const maxVisible = $performanceState.maxVisibleNodes;
    
    let visibleCount = 0;
    
    nodes.slice(0, maxVisible).forEach((node, index) => {
      if (!node.position) return;
      
      // Calculate distance to camera for LOD
      const distance = camera.position.distanceTo(new THREE.Vector3(
        node.position.x || 0,
        node.position.y || 0,
        node.position.z || 0
      ));
      
      // Apply LOD-based scaling and visibility
      const baseScale = (node.size || 5) * detailLevel;
      const lodScale = getLODScale(distance);
      const finalScale = baseScale * lodScale;
      
      if (finalScale > 0.1) { // Only render if visible enough
        position.set(
          node.position.x || 0,
          node.position.y || 0,
          node.position.z || 0
        );
        scale.set(finalScale, finalScale, finalScale);
        quaternion.identity();
        
        matrix.compose(position, quaternion, scale);
        nodeInstancedMesh.setMatrixAt(index, matrix);
        
        lodManager.nodeVisibilityMap.set(node.id, true);
        visibleCount++;
      } else {
        // Make invisible by scaling to zero
        matrix.makeScale(0, 0, 0);
        nodeInstancedMesh.setMatrixAt(index, matrix);
        lodManager.nodeVisibilityMap.set(node.id, false);
      }
    });
    
    // Hide remaining instances
    for (let i = visibleCount; i < nodeInstancedMesh.count; i++) {
      matrix.makeScale(0, 0, 0);
      nodeInstancedMesh.setMatrixAt(i, matrix);
    }
    
    nodeInstancedMesh.instanceMatrix.needsUpdate = true;
    
    performanceMetrics.update(current => ({
      ...current,
      visibleNodes: visibleCount
    }));
  }
  
  function updateInstancedEdges(edges, nodes, lodLevel = 'high') {
    if (!edgeInstancedMesh || !THREE || !nodes) return;
    
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const scale = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const direction = new THREE.Vector3();
    const up = new THREE.Vector3(0, 1, 0);
    
    const detailLevel = $performanceState.lodLevels[lodLevel]?.detail || 1.0;
    const maxVisible = $performanceState.maxVisibleEdges;
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    
    let visibleCount = 0;
    
    edges.slice(0, maxVisible).forEach((edge, index) => {
      const sourceNode = nodeMap.get(edge.source?.id || edge.source);
      const targetNode = nodeMap.get(edge.target?.id || edge.target);
      
      if (!sourceNode?.position || !targetNode?.position) return;
      
      // Check if both nodes are visible
      const sourceVisible = lodManager.nodeVisibilityMap.get(sourceNode.id);
      const targetVisible = lodManager.nodeVisibilityMap.get(targetNode.id);
      
      if (!sourceVisible && !targetVisible) return;
      
      const sourcePos = new THREE.Vector3(
        sourceNode.position.x || 0,
        sourceNode.position.y || 0,
        sourceNode.position.z || 0
      );
      const targetPos = new THREE.Vector3(
        targetNode.position.x || 0,
        targetNode.position.y || 0,
        targetNode.position.z || 0
      );
      
      // Calculate edge properties
      const distance = sourcePos.distanceTo(targetPos);
      const midpoint = sourcePos.clone().add(targetPos).multiplyScalar(0.5);
      
      // Calculate camera distance for LOD
      const cameraDistance = camera.position.distanceTo(midpoint);
      const lodScale = getLODScale(cameraDistance);
      
      if (lodScale > 0.1) {
        // Position at midpoint
        position.copy(midpoint);
        
        // Scale: length along Y, thickness based on LOD
        const thickness = (edge.strength || 0.5) * detailLevel * lodScale;
        scale.set(thickness, distance, thickness);
        
        // Rotation to align with edge direction
        direction.subVectors(targetPos, sourcePos).normalize();
        quaternion.setFromUnitVectors(up, direction);
        
        matrix.compose(position, quaternion, scale);
        edgeInstancedMesh.setMatrixAt(index, matrix);
        
        lodManager.edgeVisibilityMap.set(`${edge.source}-${edge.target}`, true);
        visibleCount++;
      } else {
        // Make invisible
        matrix.makeScale(0, 0, 0);
        edgeInstancedMesh.setMatrixAt(index, matrix);
        lodManager.edgeVisibilityMap.set(`${edge.source}-${edge.target}`, false);
      }
    });
    
    // Hide remaining instances
    for (let i = visibleCount; i < edgeInstancedMesh.count; i++) {
      matrix.makeScale(0, 0, 0);
      edgeInstancedMesh.setMatrixAt(i, matrix);
    }
    
    edgeInstancedMesh.instanceMatrix.needsUpdate = true;
    
    performanceMetrics.update(current => ({
      ...current,
      visibleEdges: visibleCount
    }));
  }
  
  function getLODScale(distance) {
    const lodLevels = $performanceState.lodLevels;
    
    if (distance < lodLevels.high.distance) {
      return lodLevels.high.detail;
    } else if (distance < lodLevels.medium.distance) {
      const ratio = (distance - lodLevels.high.distance) / 
                    (lodLevels.medium.distance - lodLevels.high.distance);
      return lodLevels.high.detail + ratio * (lodLevels.medium.detail - lodLevels.high.detail);
    } else if (distance < lodLevels.low.distance) {
      const ratio = (distance - lodLevels.medium.distance) / 
                    (lodLevels.low.distance - lodLevels.medium.distance);
      return lodLevels.medium.detail + ratio * (lodLevels.low.detail - lodLevels.medium.detail);
    } else {
      return 0; // Too far away, don't render
    }
  }
  
  function getCurrentLODLevel() {
    if (!camera) return 'high';
    
    const avgDistance = graphData.nodes?.reduce((sum, node) => {
      if (!node.position) return sum;
      const pos = new THREE.Vector3(node.position.x, node.position.y, node.position.z);
      return sum + camera.position.distanceTo(pos);
    }, 0) / Math.max(1, graphData.nodes?.length || 1);
    
    const lodLevels = $performanceState.lodLevels;
    
    if (avgDistance < lodLevels.high.distance) return 'high';
    if (avgDistance < lodLevels.medium.distance) return 'medium';
    return 'low';
  }
  
  function startLODUpdates() {
    if (!camera) return;
    
    function updateLOD() {
      const now = Date.now();
      if (now - lodManager.lastUpdateTime < lodManager.updateInterval) {
        requestAnimationFrame(updateLOD);
        return;
      }
      
      // Check if camera moved significantly
      const currentPos = camera.position;
      const lastPos = lodManager.lastCameraPosition;
      const deltaDistance = Math.sqrt(
        Math.pow(currentPos.x - lastPos.x, 2) +
        Math.pow(currentPos.y - lastPos.y, 2) +
        Math.pow(currentPos.z - lastPos.z, 2)
      );
      
      if (deltaDistance > 10 || now - lodManager.lastUpdateTime > 1000) {
        const lodLevel = getCurrentLODLevel();
        
        if (graphData.nodes) {
          updateInstancedNodes(graphData.nodes, lodLevel);
        }
        if (graphData.edges && graphData.nodes) {
          updateInstancedEdges(graphData.edges, graphData.nodes, lodLevel);
        }
        
        lodManager.lastCameraPosition = { ...currentPos };
        lodManager.lastUpdateTime = now;
      }
      
      requestAnimationFrame(updateLOD);
    }
    
    updateLOD();
  }
  
  function enableFrustumCulling() {
    if (!scene) return;
    
    scene.traverse((object) => {
      if (object.isMesh) {
        object.frustumCulled = true;
      }
    });
  }
  
  function optimizeRenderer() {
    if (!renderer) return;
    
    // Disable unnecessary features for performance
    renderer.shadowMap.enabled = false;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    // Enable performance-friendly settings
    renderer.sortObjects = false; // Disable depth sorting for performance
    renderer.info.autoReset = false;
  }
  
  function adaptiveQuality() {
    const fps = $performanceMetrics.fps;
    
    if (fps < 30 && $performanceState.maxVisibleNodes > 500) {
      // Reduce visible nodes if FPS is low
      performanceState.update(state => ({
        ...state,
        maxVisibleNodes: Math.max(500, state.maxVisibleNodes * 0.8),
        maxVisibleEdges: Math.max(1000, state.maxVisibleEdges * 0.8)
      }));
      console.log('🔧 Adaptive quality: Reduced visible objects due to low FPS');
    } else if (fps > 55 && $performanceState.maxVisibleNodes < 2000) {
      // Increase visible nodes if FPS is high
      performanceState.update(state => ({
        ...state,
        maxVisibleNodes: Math.min(2000, state.maxVisibleNodes * 1.1),
        maxVisibleEdges: Math.min(4000, state.maxVisibleEdges * 1.1)
      }));
    }
  }
  
  function startPerformanceMonitoring() {
    let frameCount = 0;
    let lastTime = performance.now();
    let fps = 0;
    
    function monitor() {
      const currentTime = performance.now();
      const deltaTime = currentTime - lastTime;
      
      frameCount++;
      
      if (deltaTime >= 1000) {
        fps = Math.round((frameCount * 1000) / deltaTime);
        frameCount = 0;
        lastTime = currentTime;
        
        performanceMetrics.update(current => ({
          ...current,
          fps: fps,
          drawCalls: renderer?.info?.render?.calls || 0,
          triangles: renderer?.info?.render?.triangles || 0,
          memoryUsage: performance.memory ? 
            Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)) : 0
        }));
        
        // Run adaptive quality adjustment
        adaptiveQuality();
        
        // Reset renderer info
        if (renderer?.info) {
          renderer.info.reset();
        }
      }
      
      requestAnimationFrame(monitor);
    }
    
    monitor();
  }
  
  // Update when graph data changes
  $: if (graphData && nodeInstancedMesh && edgeInstancedMesh) {
    const lodLevel = getCurrentLODLevel();
    updateInstancedNodes(graphData.nodes || [], lodLevel);
    updateInstancedEdges(graphData.edges || [], graphData.nodes || [], lodLevel);
  }
  
  onMount(() => {
    initThreeJS();
    startPerformanceMonitoring();
  });
  
  onDestroy(() => {
    // Clean up instanced meshes
    if (nodeInstancedMesh) {
      scene?.remove(nodeInstancedMesh);
      nodeInstancedMesh.geometry?.dispose();
      nodeInstancedMesh.material?.dispose();
    }
    if (edgeInstancedMesh) {
      scene?.remove(edgeInstancedMesh);
      edgeInstancedMesh.geometry?.dispose();
      edgeInstancedMesh.material?.dispose();
    }
  });
  
  // Export state for parent access
  export { performanceState, performanceMetrics };
</script>

<!-- Performance debug panel -->
{#if isPerformanceMode}
  <div class="performance-debug">
    <h4>🎯 Performance Manager</h4>
    <div class="debug-metrics">
      <div class="metric">FPS: {$performanceMetrics.fps}</div>
      <div class="metric">Draw Calls: {$performanceMetrics.drawCalls}</div>
      <div class="metric">Triangles: {$performanceMetrics.triangles.toLocaleString()}</div>
      <div class="metric">Visible Nodes: {$performanceMetrics.visibleNodes}</div>
      <div class="metric">Visible Edges: {$performanceMetrics.visibleEdges}</div>
      <div class="metric">Memory: {$performanceMetrics.memoryUsage}MB</div>
    </div>
    
    <div class="performance-controls">
      <label>
        <input type="checkbox" bind:checked={$performanceState.lodEnabled} />
        Level of Detail
      </label>
      <label>
        <input type="checkbox" bind:checked={$performanceState.frustumCulling} />
        Frustum Culling
      </label>
      <label>
        <input type="checkbox" bind:checked={$performanceState.instancedRendering} />
        Instanced Rendering
      </label>
    </div>
    
    <div class="lod-controls">
      <div class="lod-section">
        <h5>LOD Settings</h5>
        <div class="lod-level">
          <span>Max Nodes:</span>
          <input type="range" min="100" max="5000" bind:value={$performanceState.maxVisibleNodes} />
          <span>{$performanceState.maxVisibleNodes}</span>
        </div>
        <div class="lod-level">
          <span>Max Edges:</span>
          <input type="range" min="200" max="10000" bind:value={$performanceState.maxVisibleEdges} />
          <span>{$performanceState.maxVisibleEdges}</span>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .performance-debug {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 15px;
    border-radius: 8px;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 11px;
    z-index: 1000;
    min-width: 250px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .performance-debug h4 {
    margin: 0 0 12px 0;
    color: #FF6B35;
    font-size: 12px;
    font-weight: bold;
  }
  
  .debug-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-bottom: 12px;
  }
  
  .metric {
    background: rgba(255, 255, 255, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 10px;
  }
  
  .performance-controls {
    margin-bottom: 12px;
  }
  
  .performance-controls label {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
    font-size: 10px;
    cursor: pointer;
  }
  
  .performance-controls input[type="checkbox"] {
    accent-color: #4CAF50;
  }
  
  .lod-controls {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 8px;
  }
  
  .lod-section h5 {
    margin: 0 0 8px 0;
    color: #FFC107;
    font-size: 11px;
  }
  
  .lod-level {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-size: 9px;
  }
  
  .lod-level span:first-child {
    width: 70px;
    color: rgba(255, 255, 255, 0.8);
  }
  
  .lod-level input[type="range"] {
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    outline: none;
    accent-color: #4CAF50;
  }
  
  .lod-level span:last-child {
    width: 40px;
    text-align: right;
    color: #4CAF50;
    font-weight: bold;
  }
</style>
