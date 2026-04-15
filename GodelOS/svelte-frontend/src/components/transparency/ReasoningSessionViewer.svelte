<!-- ReasoningSessionViewer.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  import { GödelOSAPI } from '../../utils/api.js';

  export let sessionId = null; // Optional specific session to view
  
  let activeSessions = [];
  let selectedSession = null;
  let sessionDetails = null;
  let isLoading = false;
  let error = null;
  // Manual refresh only - no auto-polling

  // WebSocket for live reasoning stream
  let reasoningSocket = null;
  // API configuration
  import { API_BASE_URL as API_BASE, WS_BASE_URL as WS_BASE } from '../../config.js';

  onMount(() => {
    loadActiveSessions();
    // Removed aggressive 3-second polling - use manual refresh or WebSocket events instead
  });

  onDestroy(() => {
    // No polling interval to clear - manual refresh only
    if (reasoningSocket) reasoningSocket.close();
  });

  // Manual refresh function for on-demand updates

  async function loadActiveSessions() {
    isLoading = true;
    try {
      // Get active sessions from transparency API
      const response = await fetch(`${API_BASE}/api/transparency/sessions/active`);
      if (response.ok) {
        const data = await response.json();
        activeSessions = data.sessions || [];
        
        // Auto-select the first session if none selected and we have sessions
        if (!selectedSession && activeSessions.length > 0) {
          selectSession(activeSessions[0]);
        }
        error = null;
      } else {
        console.error('Failed to load active sessions:', response.status);
        activeSessions = [];
        error = 'No reasoning sessions available';
      }
    } catch (err) {
      console.error('Error loading active sessions:', err);
      activeSessions = [];
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  async function selectSession(session) {
    selectedSession = session;
    await loadSessionDetails(session.session_id);
    connectReasoningStream(session.session_id);
  }

    async function loadSessionDetails(sessionId) {
    if (!sessionId) return;

    isLoading = true;
    try {
      // Try to get session details from transparency API
      const response = await fetch(`${API_BASE}/api/transparency/session/${sessionId}/trace`);
      if (response.ok) {
        const data = await response.json();
        sessionDetails = data;
        error = null;
      } else {
        console.error(`Session ${sessionId} not found:`, response.status);
        sessionDetails = null;
        error = 'Session details not available';
      }
    } catch (err) {
      console.error('Failed to load session details:', err);
      sessionDetails = null;
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  async function startNewSession() {
    try {
      const query = prompt('Enter a query for the new reasoning session:');
      if (!query) return;
      
      const response = await fetch(`${API_BASE}/api/transparency/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query, 
          transparency_level: 'detailed' 
        })
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      
      // Refresh sessions list to include the new session
      setTimeout(loadActiveSessions, 1000);
    } catch (err) {
      console.error('Failed to start new session:', err);
      error = err.message;
    }
  }

  function formatDuration(durationMs) {
    if (!durationMs) return 'N/A';
    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  }

  function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    return new Date(timestamp * 1000).toLocaleString();
  }

  function connectReasoningStream(id) {
    if (!id) return;
    if (reasoningSocket) {
      reasoningSocket.close();
    }
    try {
      reasoningSocket = new WebSocket(`${WS_BASE}/api/transparency/reasoning/stream/${id}`);
      reasoningSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (sessionDetails) {
            sessionDetails.steps = [...(sessionDetails.steps || []), data];
          }
        } catch (err) {
          console.error('Invalid reasoning stream message:', err);
        }
      };
      reasoningSocket.onerror = (error) => {
        console.error('Reasoning stream connection error:', error);
      };
    } catch (err) {
      console.error('Failed to connect to reasoning stream:', err);
    }
  }
</script>

<div class="reasoning-session-viewer">
  <div class="header">
    <h3>🧠 Reasoning Session Viewer</h3>
    <div class="controls">
      <button class="start-session-btn" on:click={startNewSession}>
        ➕ Start New Session
      </button>
      <button class="refresh-btn" on:click={loadActiveSessions}>
        🔄 Refresh
      </button>
    </div>
  </div>

  {#if error}
    <div class="error-banner">
      ❌ Error: {error}
      <button on:click={() => error = null}>✕</button>
    </div>
  {/if}

  <div class="main-content">
    <div class="sessions-panel">
      <h4>🔄 Active Sessions ({activeSessions.length})</h4>
      
      {#if activeSessions.length === 0}
        <div class="no-sessions">
          <p>No active reasoning sessions found.</p>
          <button on:click={startNewSession}>Start First Session</button>
        </div>
      {:else}
        <div class="sessions-list">
          {#each activeSessions as session}
            <div 
              class="session-item {selectedSession?.session_id === session.session_id ? 'selected' : ''}"
              on:click={() => selectSession(session)}
            >
              <div class="session-header">
                <span class="session-id">{session.session_id.substring(0, 8)}...</span>
                <span class="session-status {session.status}">{session.status}</span>
              </div>
              <div class="session-details">
                <div class="session-query">{session.query || 'No query specified'}</div>
                <div class="session-meta">
                  <span>Duration: {formatDuration(session.duration_ms)}</span>
                  <span>Started: {formatTimestamp(session.start_time)}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="details-panel">
      {#if selectedSession}
        <h4>📋 Session Details</h4>
        
        <div class="session-overview">
          <div class="overview-item">
            <label>Session ID:</label>
            <span class="session-id-full">{selectedSession.session_id}</span>
          </div>
          <div class="overview-item">
            <label>Query:</label>
            <span>{selectedSession.query || 'No query specified'}</span>
          </div>
          <div class="overview-item">
            <label>Status:</label>
            <span class="status {selectedSession.status}">{selectedSession.status}</span>
          </div>
          <div class="overview-item">
            <label>Transparency Level:</label>
            <span>{selectedSession.transparency_level}</span>
          </div>
          <div class="overview-item">
            <label>Duration:</label>
            <span>{formatDuration(selectedSession.duration_ms)}</span>
          </div>
        </div>

        {#if isLoading}
          <div class="loading">🔄 Loading session trace...</div>
        {:else if sessionDetails}
          <div class="trace-details">
            <h5>🔍 Reasoning Trace</h5>
            
            {#if sessionDetails.steps && sessionDetails.steps.length > 0}
              <div class="steps-list">
                {#each sessionDetails.steps as step, index}
                  <div class="step-item">
                    <div class="step-header">
                      <span class="step-number">{index + 1}</span>
                      <span class="step-type">{step.type || 'reasoning'}</span>
                      <span class="step-timestamp">{formatTimestamp(step.timestamp)}</span>
                    </div>
                    <div class="step-content">
                      {step.description || step.content || 'No description available'}
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="no-steps">
                <p>No reasoning steps recorded yet.</p>
                <small>Steps will appear here as the reasoning session progresses.</small>
              </div>
            {/if}

            {#if sessionDetails.decision_points && sessionDetails.decision_points.length > 0}
              <div class="decision-points">
                <h6>⚡ Decision Points</h6>
                {#each sessionDetails.decision_points as decision}
                  <div class="decision-item">
                    <div class="decision-question">{decision.question}</div>
                    <div class="decision-outcome">Outcome: {decision.outcome}</div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {:else}
          <div class="no-trace">
            <p>No trace data available for this session.</p>
          </div>
        {/if}
      {:else}
        <div class="no-selection">
          <h4>📋 Session Details</h4>
          <p>Select a session from the left to view its details and reasoning trace.</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .reasoning-session-viewer {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    border-radius: 10px;
    padding: 25px;
    color: #ffffff;
    min-height: 600px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 15px;
  }

  .header h3 {
    margin: 0;
    color: #FFD700;
    font-size: 20px;
  }

  .controls {
    display: flex;
    gap: 15px;
    align-items: center;
  }

  .start-session-btn, .refresh-btn {
    background: linear-gradient(135deg, #4CAF50, #45a049);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.3s ease;
  }

  .refresh-btn {
    background: linear-gradient(135deg, #2196F3, #1976D2);
  }

  .start-session-btn:hover, .refresh-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
  }

  .refresh-btn:hover {
    box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
  }

  .error-banner {
    background: rgba(244, 67, 54, 0.2);
    border: 1px solid rgba(244, 67, 54, 0.5);
    border-radius: 6px;
    padding: 10px 15px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #ffcdd2;
  }

  .error-banner button {
    background: none;
    border: none;
    color: #ffcdd2;
    cursor: pointer;
    font-size: 16px;
  }

  .main-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 25px;
    height: 500px;
  }

  .sessions-panel, .details-panel {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 20px;
    overflow: auto;
  }

  .sessions-panel h4, .details-panel h4 {
    margin: 0 0 15px 0;
    color: #FFD700;
    font-size: 16px;
  }

  .no-sessions {
    text-align: center;
    padding: 40px 20px;
    color: rgba(255, 255, 255, 0.6);
  }

  .no-sessions button {
    background: linear-gradient(135deg, #2196F3, #1976D2);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    margin-top: 15px;
  }

  .sessions-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .session-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    border-left: 3px solid transparent;
  }

  .session-item:hover {
    background: rgba(255, 255, 255, 0.1);
    border-left-color: #2196F3;
  }

  .session-item.selected {
    background: rgba(33, 150, 243, 0.2);
    border-left-color: #2196F3;
  }

  .session-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .session-id {
    font-family: monospace;
    font-size: 11px;
    color: #BBB;
  }

  .session-status {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    font-weight: bold;
  }

  .session-status.in_progress {
    background: rgba(255, 193, 7, 0.3);
    color: #FFC107;
  }

  .session-status.completed {
    background: rgba(76, 175, 80, 0.3);
    color: #4CAF50;
  }

  .session-query {
    font-size: 12px;
    margin-bottom: 6px;
    font-weight: bold;
  }

  .session-meta {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: rgba(255, 255, 255, 0.6);
  }

  .session-overview {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 20px;
  }

  .overview-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .overview-item:last-child {
    border-bottom: none;
  }

  .overview-item label {
    font-weight: bold;
    color: rgba(255, 255, 255, 0.8);
    font-size: 12px;
  }

  .session-id-full {
    font-family: monospace;
    font-size: 10px;
    color: #BBB;
  }

  .status.in_progress {
    color: #FFC107;
  }

  .status.completed {
    color: #4CAF50;
  }

  .loading {
    text-align: center;
    padding: 40px;
    color: rgba(255, 255, 255, 0.6);
  }

  .no-steps, .no-trace, .no-selection {
    text-align: center;
    padding: 40px 20px;
    color: rgba(255, 255, 255, 0.6);
  }

  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .step-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    padding: 12px;
    border-left: 3px solid #2196F3;
  }

  .step-header {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 8px;
    font-size: 11px;
  }

  .step-number {
    background: #2196F3;
    color: white;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 10px;
  }

  .step-type {
    background: rgba(33, 150, 243, 0.3);
    color: #2196F3;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    font-weight: bold;
  }

  .step-timestamp {
    color: rgba(255, 255, 255, 0.5);
    margin-left: auto;
  }

  .step-content {
    font-size: 12px;
    line-height: 1.4;
  }

  .decision-points {
    margin-top: 20px;
  }

  .decision-points h6 {
    margin: 0 0 10px 0;
    color: #FF9800;
    font-size: 14px;
  }

  .decision-item {
    background: rgba(255, 152, 0, 0.1);
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 8px;
  }

  .decision-question {
    font-weight: bold;
    margin-bottom: 5px;
    font-size: 12px;
  }

  .decision-outcome {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.7);
  }
</style>
