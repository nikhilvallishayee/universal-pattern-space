<!--
Knowledge Graph Collaborative Manager
Handles real-time collaborative editing, conflict resolution, and synchronization
-->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable, derived } from 'svelte/store';
  import { createEventDispatcher } from 'svelte';
  
  import { WS_BASE_URL } from '../../config.js';
  
  const dispatch = createEventDispatcher();
  
  // Props
  export let graphData = { nodes: [], edges: [] };
  export let userId = null;
  export let sessionId = null;
  export let websocketUrl = `${WS_BASE_URL}/ws/knowledge-graph`;
  export let isEnabled = false;
  
  // Collaborative state
  let collaborativeSession = writable({
    isActive: false,
    sessionId: null,
    participants: [],
    lastSync: null,
    connectionStatus: 'disconnected', // disconnected, connecting, connected, error
    permissions: {
      canEdit: true,
      canDelete: false,
      canInvite: false
    }
  });
  
  // Operation queue for offline resilience
  let operationQueue = writable([]);
  
  // Conflict resolution state
  let conflictResolution = writable({
    activeConflicts: [],
    resolutionStrategy: 'last-write-wins', // last-write-wins, manual, collaborative
    pendingResolutions: []
  });
  
  // Undo/Redo system
  let historyManager = writable({
    undoStack: [],
    redoStack: [],
    maxHistorySize: 100,
    currentVersion: 0
  });
  
  // Real-time cursors and selections
  let collaboratorCursors = writable(new Map());
  
  // WebSocket connection
  let websocket = null;
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 5;
  let reconnectInterval = null;
  
  // Operation types
  const OperationType = {
    NODE_CREATE: 'node_create',
    NODE_UPDATE: 'node_update',
    NODE_DELETE: 'node_delete',
    EDGE_CREATE: 'edge_create',
    EDGE_UPDATE: 'edge_update',
    EDGE_DELETE: 'edge_delete',
    GRAPH_LAYOUT: 'graph_layout',
    SELECTION_CHANGE: 'selection_change',
    CURSOR_MOVE: 'cursor_move'
  };
  
  function connectWebSocket() {
    if (!isEnabled || !userId) return;
    
    collaborativeSession.update(session => ({
      ...session,
      connectionStatus: 'connecting'
    }));
    
    try {
      const wsUrl = `${websocketUrl}?userId=${userId}&sessionId=${sessionId || 'default'}`;
      websocket = new WebSocket(wsUrl);
      
      websocket.onopen = handleWebSocketOpen;
      websocket.onmessage = handleWebSocketMessage;
      websocket.onclose = handleWebSocketClose;
      websocket.onerror = handleWebSocketError;
      
      console.log('🔗 Connecting to collaborative session...');
      
    } catch (error) {
      console.error('❌ Failed to connect to WebSocket:', error);
      collaborativeSession.update(session => ({
        ...session,
        connectionStatus: 'error'
      }));
    }
  }
  
  function handleWebSocketOpen(event) {
    console.log('✅ Connected to collaborative session');
    reconnectAttempts = 0;
    
    collaborativeSession.update(session => ({
      ...session,
      isActive: true,
      connectionStatus: 'connected',
      lastSync: new Date().toISOString()
    }));
    
    // Send initial sync request
    sendOperation({
      type: 'sync_request',
      userId: userId,
      timestamp: Date.now()
    });
    
    // Send any queued operations
    flushOperationQueue();
  }
  
  function handleWebSocketMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'sync_response':
          handleSyncResponse(message);
          break;
        case 'participant_joined':
          handleParticipantJoined(message);
          break;
        case 'participant_left':
          handleParticipantLeft(message);
          break;
        case 'operation':
          handleRemoteOperation(message);
          break;
        case 'conflict':
          handleConflict(message);
          break;
        case 'cursor_update':
          handleCursorUpdate(message);
          break;
        case 'selection_update':
          handleSelectionUpdate(message);
          break;
        default:
          console.warn('Unknown message type:', message.type);
      }
      
    } catch (error) {
      console.error('❌ Error parsing WebSocket message:', error);
    }
  }
  
  function handleWebSocketClose(event) {
    console.log('🔌 WebSocket connection closed');
    
    collaborativeSession.update(session => ({
      ...session,
      isActive: false,
      connectionStatus: 'disconnected'
    }));
    
    // Attempt to reconnect
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      const delay = Math.pow(2, reconnectAttempts) * 1000; // Exponential backoff
      
      console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
      
      reconnectInterval = setTimeout(() => {
        connectWebSocket();
      }, delay);
    } else {
      console.error('❌ Max reconnection attempts reached');
    }
  }
  
  function handleWebSocketError(error) {
    console.error('❌ WebSocket error:', error);
    
    collaborativeSession.update(session => ({
      ...session,
      connectionStatus: 'error'
    }));
  }
  
  function sendOperation(operation) {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify(operation));
    } else {
      // Queue operation for when connection is restored
      operationQueue.update(queue => [...queue, operation]);
    }
  }
  
  function flushOperationQueue() {
    operationQueue.update(queue => {
      queue.forEach(operation => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify(operation));
        }
      });
      return [];
    });
  }
  
  function handleSyncResponse(message) {
    if (message.graphData) {
      // Apply remote graph state
      dispatch('graphDataSync', {
        graphData: message.graphData,
        version: message.version
      });
      
      historyManager.update(history => ({
        ...history,
        currentVersion: message.version
      }));
    }
    
    if (message.participants) {
      collaborativeSession.update(session => ({
        ...session,
        participants: message.participants
      }));
    }
    
    console.log('📥 Synchronized with server state');
  }
  
  function handleParticipantJoined(message) {
    collaborativeSession.update(session => ({
      ...session,
      participants: [...session.participants, message.participant]
    }));
    
    dispatch('participantJoined', message.participant);
    console.log('👋 Participant joined:', message.participant.name);
  }
  
  function handleParticipantLeft(message) {
    collaborativeSession.update(session => ({
      ...session,
      participants: session.participants.filter(p => p.id !== message.participantId)
    }));
    
    // Remove their cursor
    collaboratorCursors.update(cursors => {
      cursors.delete(message.participantId);
      return new Map(cursors);
    });
    
    dispatch('participantLeft', message.participantId);
    console.log('👋 Participant left:', message.participantId);
  }
  
  function handleRemoteOperation(message) {
    const operation = message.operation;
    
    // Check for conflicts
    const hasConflict = detectConflict(operation);
    
    if (hasConflict) {
      conflictResolution.update(conflicts => ({
        ...conflicts,
        activeConflicts: [...conflicts.activeConflicts, {
          id: generateConflictId(),
          operation: operation,
          localVersion: $historyManager.currentVersion,
          remoteVersion: message.version,
          timestamp: Date.now(),
          author: message.userId
        }]
      }));
      
      console.warn('⚠️ Conflict detected for operation:', operation.type);
      return;
    }
    
    // Apply operation to local state
    applyOperation(operation, false); // false = don't broadcast
    
    // Add to history
    addToHistory(operation);
    
    dispatch('remoteOperation', { operation, userId: message.userId });
  }
  
  function detectConflict(operation) {
    // Simple conflict detection based on object modification times
    // In a real implementation, this would be more sophisticated
    
    if (operation.type === OperationType.NODE_UPDATE || operation.type === OperationType.NODE_DELETE) {
      const localNode = graphData.nodes?.find(n => n.id === operation.nodeId);
      if (localNode && localNode.lastModified && operation.timestamp) {
        return Math.abs(localNode.lastModified - operation.timestamp) < 1000; // 1 second threshold
      }
    }
    
    if (operation.type === OperationType.EDGE_UPDATE || operation.type === OperationType.EDGE_DELETE) {
      const localEdge = graphData.edges?.find(e => e.id === operation.edgeId);
      if (localEdge && localEdge.lastModified && operation.timestamp) {
        return Math.abs(localEdge.lastModified - operation.timestamp) < 1000;
      }
    }
    
    return false;
  }
  
  function applyOperation(operation, broadcast = true) {
    const timestamp = Date.now();
    
    switch (operation.type) {
      case OperationType.NODE_CREATE:
        createNode(operation.node, broadcast);
        break;
        
      case OperationType.NODE_UPDATE:
        updateNode(operation.nodeId, operation.updates, broadcast);
        break;
        
      case OperationType.NODE_DELETE:
        deleteNode(operation.nodeId, broadcast);
        break;
        
      case OperationType.EDGE_CREATE:
        createEdge(operation.edge, broadcast);
        break;
        
      case OperationType.EDGE_UPDATE:
        updateEdge(operation.edgeId, operation.updates, broadcast);
        break;
        
      case OperationType.EDGE_DELETE:
        deleteEdge(operation.edgeId, broadcast);
        break;
        
      case OperationType.GRAPH_LAYOUT:
        updateLayout(operation.layoutData, broadcast);
        break;
    }
    
    if (broadcast) {
      addToHistory(operation);
    }
  }
  
  function createNode(node, broadcast = true) {
    const newNode = {
      ...node,
      id: node.id || generateNodeId(),
      lastModified: Date.now(),
      createdBy: userId
    };
    
    dispatch('nodeCreate', newNode);
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.NODE_CREATE,
          node: newNode,
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function updateNode(nodeId, updates, broadcast = true) {
    dispatch('nodeUpdate', { nodeId, updates });
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.NODE_UPDATE,
          nodeId: nodeId,
          updates: {
            ...updates,
            lastModified: Date.now(),
            modifiedBy: userId
          },
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function deleteNode(nodeId, broadcast = true) {
    dispatch('nodeDelete', nodeId);
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.NODE_DELETE,
          nodeId: nodeId,
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function createEdge(edge, broadcast = true) {
    const newEdge = {
      ...edge,
      id: edge.id || generateEdgeId(),
      lastModified: Date.now(),
      createdBy: userId
    };
    
    dispatch('edgeCreate', newEdge);
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.EDGE_CREATE,
          edge: newEdge,
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function updateEdge(edgeId, updates, broadcast = true) {
    dispatch('edgeUpdate', { edgeId, updates });
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.EDGE_UPDATE,
          edgeId: edgeId,
          updates: {
            ...updates,
            lastModified: Date.now(),
            modifiedBy: userId
          },
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function deleteEdge(edgeId, broadcast = true) {
    dispatch('edgeDelete', edgeId);
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.EDGE_DELETE,
          edgeId: edgeId,
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function updateLayout(layoutData, broadcast = true) {
    dispatch('layoutUpdate', layoutData);
    
    if (broadcast) {
      sendOperation({
        type: 'operation',
        operation: {
          type: OperationType.GRAPH_LAYOUT,
          layoutData: layoutData,
          timestamp: Date.now()
        },
        userId: userId,
        version: $historyManager.currentVersion + 1
      });
    }
  }
  
  function handleCursorUpdate(message) {
    collaboratorCursors.update(cursors => {
      cursors.set(message.userId, {
        userId: message.userId,
        userName: message.userName,
        position: message.position,
        color: message.color,
        timestamp: Date.now()
      });
      return new Map(cursors);
    });
  }
  
  function handleSelectionUpdate(message) {
    dispatch('remoteSelection', {
      userId: message.userId,
      selectedNodes: message.selectedNodes,
      selectedEdges: message.selectedEdges
    });
  }
  
  function addToHistory(operation) {
    historyManager.update(history => {
      const newUndoStack = [...history.undoStack, operation];
      
      // Limit history size
      if (newUndoStack.length > history.maxHistorySize) {
        newUndoStack.shift();
      }
      
      return {
        ...history,
        undoStack: newUndoStack,
        redoStack: [], // Clear redo stack when new operation is added
        currentVersion: history.currentVersion + 1
      };
    });
  }
  
  function undo() {
    historyManager.update(history => {
      if (history.undoStack.length === 0) return history;
      
      const lastOperation = history.undoStack[history.undoStack.length - 1];
      const inverseOperation = createInverseOperation(lastOperation);
      
      if (inverseOperation) {
        applyOperation(inverseOperation, true);
        
        return {
          ...history,
          undoStack: history.undoStack.slice(0, -1),
          redoStack: [...history.redoStack, lastOperation]
        };
      }
      
      return history;
    });
  }
  
  function redo() {
    historyManager.update(history => {
      if (history.redoStack.length === 0) return history;
      
      const operationToRedo = history.redoStack[history.redoStack.length - 1];
      applyOperation(operationToRedo, true);
      
      return {
        ...history,
        undoStack: [...history.undoStack, operationToRedo],
        redoStack: history.redoStack.slice(0, -1)
      };
    });
  }
  
  function createInverseOperation(operation) {
    // Create inverse operations for undo functionality
    switch (operation.type) {
      case OperationType.NODE_CREATE:
        return {
          type: OperationType.NODE_DELETE,
          nodeId: operation.node.id,
          timestamp: Date.now()
        };
        
      case OperationType.NODE_DELETE:
        // Note: Would need to store deleted node data for proper undo
        return null;
        
      case OperationType.EDGE_CREATE:
        return {
          type: OperationType.EDGE_DELETE,
          edgeId: operation.edge.id,
          timestamp: Date.now()
        };
        
      case OperationType.EDGE_DELETE:
        // Note: Would need to store deleted edge data for proper undo
        return null;
        
      default:
        return null;
    }
  }
  
  function broadcastCursorPosition(position) {
    if (!$collaborativeSession.isActive) return;
    
    sendOperation({
      type: 'cursor_update',
      userId: userId,
      position: position,
      timestamp: Date.now()
    });
  }
  
  function broadcastSelection(selectedNodes, selectedEdges) {
    if (!$collaborativeSession.isActive) return;
    
    sendOperation({
      type: 'selection_update',
      userId: userId,
      selectedNodes: selectedNodes,
      selectedEdges: selectedEdges,
      timestamp: Date.now()
    });
  }
  
  function resolveConflict(conflictId, resolution) {
    conflictResolution.update(conflicts => ({
      ...conflicts,
      activeConflicts: conflicts.activeConflicts.filter(c => c.id !== conflictId),
      pendingResolutions: [...conflicts.pendingResolutions, {
        conflictId: conflictId,
        resolution: resolution,
        timestamp: Date.now()
      }]
    }));
    
    // Apply resolved operation
    if (resolution.action === 'accept_remote') {
      applyOperation(resolution.operation, false);
    } else if (resolution.action === 'accept_local') {
      // Keep local state, broadcast to override remote
      sendOperation({
        type: 'operation',
        operation: resolution.localOperation,
        userId: userId,
        version: $historyManager.currentVersion + 1,
        forceOverride: true
      });
    }
  }
  
  // Utility functions
  function generateNodeId() {
    return `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  function generateEdgeId() {
    return `edge_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  function generateConflictId() {
    return `conflict_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  // Connect when enabled changes
  $: if (isEnabled && userId) {
    connectWebSocket();
  } else if (!isEnabled && websocket) {
    websocket.close();
    websocket = null;
  }
  
  onMount(() => {
    // Clean up old connection intervals
    if (reconnectInterval) {
      clearTimeout(reconnectInterval);
    }
  });
  
  onDestroy(() => {
    if (websocket) {
      websocket.close();
    }
    if (reconnectInterval) {
      clearTimeout(reconnectInterval);
    }
  });
  
  // Export functions and stores for parent access
  export {
    collaborativeSession,
    operationQueue,
    conflictResolution,
    historyManager,
    collaboratorCursors,
    createNode,
    updateNode,
    deleteNode,
    createEdge,
    updateEdge,
    deleteEdge,
    undo,
    redo,
    broadcastCursorPosition,
    broadcastSelection,
    resolveConflict
  };
</script>

<!-- Collaborative UI Components -->
{#if isEnabled}
  <!-- Connection Status -->
  <div class="collaborative-status" class:connected={$collaborativeSession.isActive}>
    <div class="status-indicator" class:connected={$collaborativeSession.connectionStatus === 'connected'}></div>
    <span class="status-text">
      {#if $collaborativeSession.connectionStatus === 'connected'}
        Collaborative ({$collaborativeSession.participants.length} users)
      {:else if $collaborativeSession.connectionStatus === 'connecting'}
        Connecting...
      {:else if $collaborativeSession.connectionStatus === 'error'}
        Connection Error
      {:else}
        Offline
      {/if}
    </span>
  </div>
  
  <!-- Participants List -->
  {#if $collaborativeSession.isActive && $collaborativeSession.participants.length > 0}
    <div class="participants-panel">
      <h4 class="panel-title">👥 Collaborators</h4>
      <div class="participants-list">
        {#each $collaborativeSession.participants as participant}
          <div class="participant-item" style="--user-color: {participant.color}">
            <div class="participant-avatar" style="background-color: {participant.color}">
              {participant.name.charAt(0).toUpperCase()}
            </div>
            <div class="participant-info">
              <div class="participant-name">{participant.name}</div>
              <div class="participant-status">{participant.status || 'online'}</div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Conflict Resolution Panel -->
  {#if $conflictResolution.activeConflicts.length > 0}
    <div class="conflict-panel">
      <h4 class="panel-title">⚠️ Conflicts ({$conflictResolution.activeConflicts.length})</h4>
      <div class="conflicts-list">
        {#each $conflictResolution.activeConflicts as conflict}
          <div class="conflict-item">
            <div class="conflict-header">
              <span class="conflict-type">{conflict.operation.type}</span>
              <span class="conflict-author">by {conflict.author}</span>
            </div>
            <div class="conflict-description">
              {#if conflict.operation.type.includes('node')}
                Node operation conflict
              {:else if conflict.operation.type.includes('edge')}
                Edge operation conflict
              {:else}
                Layout operation conflict
              {/if}
            </div>
            <div class="conflict-actions">
              <button class="conflict-btn accept" on:click={() => resolveConflict(conflict.id, { action: 'accept_remote', operation: conflict.operation })}>
                Accept Remote
              </button>
              <button class="conflict-btn reject" on:click={() => resolveConflict(conflict.id, { action: 'accept_local' })}>
                Keep Local
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Operation Queue Status -->
  {#if $operationQueue.length > 0}
    <div class="operation-queue-status">
      <div class="queue-icon">⏳</div>
      <div class="queue-text">{$operationQueue.length} operations queued</div>
    </div>
  {/if}
  
  <!-- History Controls -->
  <div class="history-controls">
    <button class="history-btn" disabled={$historyManager.undoStack.length === 0} on:click={undo}>
      ↶ Undo
    </button>
    <button class="history-btn" disabled={$historyManager.redoStack.length === 0} on:click={redo}>
      ↷ Redo
    </button>
  </div>
{/if}

<style>
  .collaborative-status {
    position: fixed;
    top: 60px;
    left: 20px;
    background: rgba(150, 0, 0, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 16px;
    font-size: 11px;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 8px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }
  
  .collaborative-status.connected {
    background: rgba(0, 150, 0, 0.9);
  }
  
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #f44336;
    animation: pulse 2s infinite;
  }
  
  .status-indicator.connected {
    background: #4CAF50;
    animation: none;
  }
  
  .status-text {
    font-weight: 600;
  }
  
  .participants-panel {
    position: fixed;
    top: 100px;
    left: 20px;
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 12px;
    border-radius: 8px;
    font-size: 11px;
    z-index: 1000;
    max-width: 200px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .panel-title {
    margin: 0 0 8px 0;
    font-size: 12px;
    font-weight: bold;
    color: #4CAF50;
  }
  
  .participants-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  
  .participant-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .participant-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: bold;
    color: white;
  }
  
  .participant-info {
    flex: 1;
  }
  
  .participant-name {
    font-weight: 600;
    font-size: 11px;
  }
  
  .participant-status {
    font-size: 9px;
    opacity: 0.8;
  }
  
  .conflict-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(244, 67, 54, 0.95);
    color: white;
    padding: 16px;
    border-radius: 12px;
    font-size: 12px;
    z-index: 2000;
    min-width: 300px;
    backdrop-filter: blur(15px);
    border: 2px solid rgba(255, 255, 255, 0.2);
  }
  
  .conflicts-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .conflict-item {
    background: rgba(0, 0, 0, 0.3);
    padding: 12px;
    border-radius: 8px;
  }
  
  .conflict-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }
  
  .conflict-type {
    font-weight: bold;
    text-transform: capitalize;
  }
  
  .conflict-author {
    font-size: 10px;
    opacity: 0.8;
  }
  
  .conflict-description {
    margin-bottom: 12px;
    font-size: 11px;
    line-height: 1.4;
  }
  
  .conflict-actions {
    display: flex;
    gap: 8px;
  }
  
  .conflict-btn {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .conflict-btn.accept {
    background: #4CAF50;
    color: white;
  }
  
  .conflict-btn.reject {
    background: #FF9800;
    color: white;
  }
  
  .conflict-btn:hover {
    opacity: 0.8;
    transform: translateY(-1px);
  }
  
  .operation-queue-status {
    position: fixed;
    bottom: 60px;
    left: 20px;
    background: rgba(255, 152, 0, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 16px;
    font-size: 11px;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 8px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .queue-icon {
    font-size: 12px;
    animation: spin 2s linear infinite;
  }
  
  .queue-text {
    font-weight: 600;
  }
  
  .history-controls {
    position: fixed;
    bottom: 20px;
    right: 350px;
    display: flex;
    gap: 8px;
    z-index: 1000;
  }
  
  .history-btn {
    background: rgba(0, 0, 0, 0.8);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: bold;
    cursor: pointer;
    backdrop-filter: blur(10px);
    transition: all 0.2s ease;
  }
  
  .history-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .history-btn:not(:disabled):hover {
    background: rgba(76, 175, 80, 0.8);
    transform: translateY(-1px);
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
</style>
