<script>
  import { onMount, onDestroy } from 'svelte';
  import { cognitiveState } from '../../stores/cognitive.js';
  import { getConnectionStatus, setupWebSocket, closeConnection } from '../../utils/websocket.js';
  
  // Connection states
  let connectionState = 'disconnected';
  let lastConnected = null;
  let reconnectAttempt = 0;
  let showDetails = false;
  let reconnectTimer = null;
  
  // Reactive connection status from store
  $: websocketHealth = $cognitiveState.systemHealth?.websocketConnection || 0;
  $: isConnected = websocketHealth > 0.5;
  
  // Update connection state based on WebSocket status
  $: {
    if (isConnected) {
      connectionState = 'connected';
      lastConnected = new Date();
      reconnectAttempt = 0;
    } else {
      connectionState = 'disconnected';
    }
  }
  
  // Auto-reconnect logic
  onMount(() => {
    const checkConnection = () => {
      const status = getConnectionStatus();
      
      if (status === WebSocket.CLOSED || status === WebSocket.CLOSING) {
        if (connectionState !== 'reconnecting') {
          attemptReconnect();
        }
      }
    };
    
    const interval = setInterval(checkConnection, 5000);
    
    return () => {
      clearInterval(interval);
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  });
  
  onDestroy(() => {
    if (reconnectTimer) clearTimeout(reconnectTimer);
  });
  
  function attemptReconnect() {
    if (reconnectAttempt >= 5) return; // Max 5 attempts
    
    connectionState = 'reconnecting';
    reconnectAttempt++;
    
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempt - 1), 10000); // Exponential backoff, max 10s
    
    reconnectTimer = setTimeout(async () => {
      try {
        await setupWebSocket();
      } catch (error) {
        console.warn('Reconnection attempt failed:', error);
        // Will try again on next check
      }
    }, delay);
  }
  
  function manualReconnect() {
    reconnectAttempt = 0;
    connectionState = 'reconnecting';
    setupWebSocket();
  }
  
  function disconnect() {
    closeConnection();
    connectionState = 'disconnected';
  }
  
  // Format time since last connection
  function formatTimeSince(date) {
    if (!date) return 'Never';
    
    const diff = Date.now() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  }
</script>

<div class="connection-status" class:connected={isConnected} class:reconnecting={connectionState === 'reconnecting'}>
  <button 
    class="status-indicator"
    on:click={() => showDetails = !showDetails}
    title={isConnected ? 'Connected to GödelOS' : 'Disconnected from GödelOS'}
  >
    <div class="status-icon">
      {#if connectionState === 'connected'}
        <!-- Connected icon -->
        <svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
        </svg>
      {:else if connectionState === 'reconnecting'}
        <!-- Reconnecting icon -->
        <svg class="w-4 h-4 text-yellow-400 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      {:else}
        <!-- Disconnected icon -->
        <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                d="M18.364 5.636l-12.728 12.728m0-12.728l12.728 12.728" />
        </svg>
      {/if}
    </div>
    
    <span class="status-text">
      {#if connectionState === 'connected'}
        Connected
      {:else if connectionState === 'reconnecting'}
        Reconnecting...
      {:else}
        Disconnected
      {/if}
    </span>
    
    <div class="connection-indicator">
      <div class="pulse-ring"></div>
      <div class="pulse-dot"></div>
    </div>
  </button>
  
  {#if showDetails}
    <div class="status-details">
      <div class="status-info">
        <div class="info-row">
          <span class="label">Status:</span>
          <span class="value" class:text-green-400={isConnected} class:text-red-400={!isConnected}>
            {connectionState.charAt(0).toUpperCase() + connectionState.slice(1)}
          </span>
        </div>
        
        {#if lastConnected}
          <div class="info-row">
            <span class="label">Last connected:</span>
            <span class="value">{formatTimeSince(lastConnected)}</span>
          </div>
        {/if}
        
        {#if reconnectAttempt > 0}
          <div class="info-row">
            <span class="label">Reconnect attempts:</span>
            <span class="value">{reconnectAttempt}/5</span>
          </div>
        {/if}
        
        <div class="info-row">
          <span class="label">Health:</span>
          <span class="value">{Math.round(websocketHealth * 100)}%</span>
        </div>
      </div>
      
      <div class="status-actions">
        {#if !isConnected}
          <button class="action-button primary" on:click={manualReconnect} disabled={connectionState === 'reconnecting'}>
            {connectionState === 'reconnecting' ? 'Reconnecting...' : 'Reconnect'}
          </button>
        {:else}
          <button class="action-button secondary" on:click={disconnect}>
            Disconnect
          </button>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .connection-status {
    position: relative;
    display: inline-block;
  }
  
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-elevated, #1a1a1a);
    border: 1px solid var(--border-subtle, #333);
    border-radius: 8px;
    color: var(--text-secondary, #9ca3af);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .status-indicator:hover {
    background: var(--bg-muted, #2a2a2a);
    border-color: var(--border-muted, #444);
  }
  
  .connection-status.connected .status-indicator {
    border-color: var(--success, #10b981);
    color: var(--success, #10b981);
  }
  
  .connection-status.reconnecting .status-indicator {
    border-color: var(--warning, #f59e0b);
    color: var(--warning, #f59e0b);
  }
  
  .status-icon {
    display: flex;
    align-items: center;
  }
  
  .status-text {
    font-weight: 500;
  }
  
  .connection-indicator {
    position: relative;
    width: 8px;
    height: 8px;
  }
  
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--red-400, #ef4444);
    position: absolute;
    top: 0;
    left: 0;
  }
  
  .connection-status.connected .pulse-dot {
    background: var(--green-400, #4ade80);
  }
  
  .connection-status.reconnecting .pulse-dot {
    background: var(--yellow-400, #facc15);
  }
  
  .pulse-ring {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    border: 2px solid var(--red-400, #ef4444);
    position: absolute;
    top: 0;
    left: 0;
    animation: pulse-ring 1.5s infinite;
    opacity: 0;
  }
  
  .connection-status.connected .pulse-ring {
    border-color: var(--green-400, #4ade80);
    animation: pulse-ring 2s infinite;
  }
  
  .connection-status.reconnecting .pulse-ring {
    border-color: var(--yellow-400, #facc15);
    animation: pulse-ring 1s infinite;
  }
  
  @keyframes pulse-ring {
    0% {
      transform: scale(0.5);
      opacity: 1;
    }
    100% {
      transform: scale(2);
      opacity: 0;
    }
  }
  
  .status-details {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    min-width: 250px;
    background: var(--bg-elevated, #1a1a1a);
    border: 1px solid var(--border-subtle, #333);
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    z-index: 1000;
  }
  
  .status-info {
    margin-bottom: 1rem;
  }
  
  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .info-row:last-child {
    margin-bottom: 0;
  }
  
  .label {
    font-size: 0.75rem;
    color: var(--text-tertiary, #6b7280);
  }
  
  .value {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary, #9ca3af);
  }
  
  .text-green-400 {
    color: var(--green-400, #4ade80);
  }
  
  .text-red-400 {
    color: var(--red-400, #ef4444);
  }
  
  .status-actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .action-button {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border: none;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .action-button.primary {
    background: var(--primary, #6366f1);
    color: white;
  }
  
  .action-button.primary:hover:not(:disabled) {
    background: var(--primary-dark, #4f46e5);
  }
  
  .action-button.primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .action-button.secondary {
    background: var(--bg-muted, #2a2a2a);
    color: var(--text-secondary, #9ca3af);
    border: 1px solid var(--border-subtle, #333);
  }
  
  .action-button.secondary:hover {
    background: var(--bg-subtle, #333);
  }
  
  /* Animation utilities */
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  /* Responsive */
  @media (max-width: 640px) {
    .status-details {
      right: -1rem;
      left: -1rem;
      min-width: auto;
    }
  }
</style>