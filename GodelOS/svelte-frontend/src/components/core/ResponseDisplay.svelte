<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { cognitiveState } from '../../stores/cognitive.js';
  import { transparencyMode } from '../../stores/transparency.js';
  import { fade, fly } from 'svelte/transition';
  
  const dispatch = createEventDispatcher();
  
  let responses = [];
  let currentResponse = null;
  let isStreaming = false;
  let expandedResponse = null;
  
  // Real response handling instead of mock data
  let responseHistory = [];
  
  // Listen for query response events from parent
  onMount(() => {
    // Listen for custom events dispatched by QueryInterface
    const handleQueryResponse = (event) => {
      if (event.detail && event.detail.response) {
        addNewResponse(event.detail);
      }
    };
    
    // Listen on the window for global query response events
    window.addEventListener('query-response', handleQueryResponse);
    
    return () => {
      window.removeEventListener('query-response', handleQueryResponse);
    };
  });
  
  // Add new response to history
  function addNewResponse(eventDetail) {
    const newResponse = {
      id: Date.now(),
      query: eventDetail.query,
      response: eventDetail.response?.response || eventDetail.response?.natural_response || "No response received",
      confidence: eventDetail.response?.confidence || 0.5,
      timestamp: eventDetail.timestamp || Date.now(),
      reasoning: eventDetail.response?.reasoning_steps || [],
      concepts: eventDetail.response?.knowledge_used || [],
      processingTime: eventDetail.response?.inference_time_ms || 0
    };
    
    responseHistory = [newResponse, ...responseHistory];
    currentResponse = newResponse;
    console.log('New response added:', newResponse);
  }
  
  // Listen for new responses from the cognitive system
  $: if ($cognitiveState.lastUpdate) {
    // In real implementation, this would be driven by WebSocket events
    checkForNewResponses();
  }
  
  function checkForNewResponses() {
    // This would be replaced by actual WebSocket message handling
    // For now, we'll simulate responses when queries are processed
  }
  
  function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  function getConfidenceColor(confidence) {
    if (confidence >= 0.8) return '#66bb6a';
    if (confidence >= 0.6) return '#ffa726';
    return '#ef5350';
  }
  
  function getConfidenceLabel(confidence) {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.7) return 'Good';
    if (confidence >= 0.6) return 'Moderate';
    return 'Low';
  }
  
  function toggleExpanded(responseId) {
    expandedResponse = expandedResponse === responseId ? null : responseId;
  }
  
  function copyResponse(response) {
    navigator.clipboard.writeText(response);
    // Could add a toast notification here
  }
  
  function exportResponse(responseObj) {
    const exportData = {
      ...responseObj,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `godelos-response-${responseObj.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }
  
  // simulateStreamingResponse function REMOVED - no synthetic response simulation
  
</script>

<div class="response-display">
  <div class="response-header">
    <h3>
      <span class="header-icon">💬</span>
      Response Stream
    </h3>
    <div class="response-stats">
      {responseHistory.length} responses
    </div>
  </div>
  
  <!-- Current streaming response -->
  {#if isStreaming && currentResponse}
    <div class="current-response" in:fade>
      <div class="response-indicator">
        <div class="streaming-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <span class="streaming-text">Generating response...</span>
      </div>
      
      <div class="response-content streaming">
        {currentResponse}<span class="cursor">|</span>
      </div>
    </div>
  {/if}
  
  <!-- Response history -->
  <div class="response-list">
    {#each responseHistory as response (response.id)}
      <div class="response-item" in:fly={{ y: 20, duration: 300 }}>
        <!-- Response header -->
        <div class="response-item-header">
          <div class="query-preview">
            <span class="query-icon">❓</span>
            <span class="query-text">{response.query}</span>
          </div>
          
          <div class="response-meta">
            <div class="timestamp">{formatTimestamp(response.timestamp)}</div>
            <div class="confidence-badge" style="background: {getConfidenceColor(response.confidence)}20; color: {getConfidenceColor(response.confidence)}">
              {getConfidenceLabel(response.confidence)}
            </div>
          </div>
        </div>
        
        <!-- Response content -->
        <div class="response-content">
          {response.response}
        </div>
        
        <!-- Response actions -->
        <div class="response-actions">
          <button
            class="action-btn expand-btn"
            on:click={() => toggleExpanded(response.id)}
          >
            <span class="action-icon">{expandedResponse === response.id || $transparencyMode ? '▼' : '▶'}</span>
            {expandedResponse === response.id || $transparencyMode ? 'Collapse' : 'Details'}
          </button>
          
          <button
            class="action-btn copy-btn"
            on:click={() => copyResponse(response.response)}
            title="Copy response"
          >
            <span class="action-icon">📋</span>
            Copy
          </button>
          
          <button
            class="action-btn export-btn"
            on:click={() => exportResponse(response)}
            title="Export response data"
          >
            <span class="action-icon">📤</span>
            Export
          </button>

          {#if $transparencyMode}
            <span class="transparency-badge">🔍 Transparency Mode</span>
          {/if}
        </div>
        
        <!-- Expanded details (auto-expand when Transparency Mode is on) -->
        {#if expandedResponse === response.id || $transparencyMode}
          <div class="response-details" in:fade>
            <!-- Reasoning process -->
            <div class="detail-section">
              <h4>Reasoning Process</h4>
              <div class="reasoning-steps">
                {#each response.reasoning as step, index}
                  <div class="reasoning-step">
                    <span class="step-number">{index + 1}</span>
                    <span class="step-text">{step}</span>
                  </div>
                {/each}
              </div>
            </div>
            
            <!-- Key concepts -->
            <div class="detail-section">
              <h4>Key Concepts</h4>
              <div class="concepts-list">
                {#each response.concepts as concept}
                  <span class="concept-tag">{concept}</span>
                {/each}
              </div>
            </div>
            
            <!-- Performance metrics -->
            <div class="detail-section">
              <h4>Performance Metrics</h4>
              <div class="metrics-grid">
                <div class="metric-item">
                  <span class="metric-label">Processing Time:</span>
                  <span class="metric-value">{response.processingTime}s</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Confidence:</span>
                  <span class="metric-value" style="color: {getConfidenceColor(response.confidence)}">
                    {Math.round(response.confidence * 100)}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Word Count:</span>
                  <span class="metric-value">{response.response.split(' ').length}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Concepts Used:</span>
                  <span class="metric-value">{response.concepts.length}</span>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/each}
  </div>
  
  <!-- Empty state -->
  {#if responseHistory.length === 0 && !isStreaming}
    <div class="response-empty">
      <span class="empty-icon">💭</span>
      <span class="empty-text">No responses yet</span>
      <span class="empty-subtext">Ask GödelOS a question to see responses here</span>
    </div>
  {/if}
</div>

<style>
  .response-display {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: rgba(20, 25, 40, 0.6);
  }
  
  .response-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid rgba(100, 120, 150, 0.15);
    background: rgba(255, 255, 255, 0.02);
  }
  
  .response-header h3 {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 0;
    color: #e1e5e9;
    font-size: 1.1rem;
  }
  
  .header-icon {
    font-size: 1.3rem;
  }
  
  .response-stats {
    font-size: 0.85rem;
    color: #a0a9b8;
    background: rgba(255, 255, 255, 0.05);
    padding: 0.5rem 0.75rem;
    border-radius: 12px;
  }
  
  /* Current streaming response */
  .current-response {
    padding: 1.5rem;
    background: rgba(100, 181, 246, 0.05);
    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
  }
  
  .response-indicator {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }
  
  .streaming-dots {
    display: flex;
    gap: 0.25rem;
  }
  
  .streaming-dots span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #64b5f6;
    animation: pulse 1.5s infinite;
  }
  
  .streaming-dots span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .streaming-dots span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  .streaming-text {
    color: #64b5f6;
    font-size: 0.9rem;
  }
  
  /* Response list */
  .response-list {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .response-item {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(100, 120, 150, 0.1);
    border-radius: 12px;
    margin-bottom: 1rem;
    overflow: hidden;
    transition: border-color 0.2s ease;
  }
  
  .response-item:hover {
    border-color: rgba(100, 120, 150, 0.2);
  }
  
  .response-item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1rem 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    border-bottom: 1px solid rgba(100, 120, 150, 0.1);
  }
  
  .query-preview {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex: 1;
    margin-right: 1rem;
  }
  
  .query-icon {
    font-size: 0.9rem;
    margin-top: 0.1rem;
    opacity: 0.7;
  }
  
  .query-text {
    color: #a0a9b8;
    font-size: 0.9rem;
    line-height: 1.4;
    font-style: italic;
  }
  
  .response-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
  }
  
  .timestamp {
    color: #64748b;
    font-size: 0.8rem;
  }
  
  .confidence-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .response-content {
    padding: 1.5rem;
    color: #e1e5e9;
    line-height: 1.6;
    font-size: 0.95rem;
  }
  
  .response-content.streaming {
    position: relative;
  }
  
  .cursor {
    animation: blink 1s infinite;
    color: #64b5f6;
  }
  
  .response-actions {
    display: flex;
    gap: 0.5rem;
    padding: 1rem 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    border-top: 1px solid rgba(100, 120, 150, 0.1);
  }
  
  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(100, 120, 150, 0.1);
    color: #a0a9b8;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.8rem;
  }
  
  .action-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(100, 120, 150, 0.2);
    color: #e1e5e9;
  }

  .transparency-badge {
    margin-left: auto;
    font-size: 0.75rem;
    color: #64b5f6;
    background: rgba(100, 181, 246, 0.1);
    padding: 0.35rem 0.6rem;
    border-radius: 6px;
    font-weight: 500;
  }
  
  .action-icon {
    font-size: 0.9rem;
  }
  
  /* Response details */
  .response-details {
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    border-top: 1px solid rgba(100, 120, 150, 0.1);
  }
  
  .detail-section {
    margin-bottom: 1.5rem;
  }
  
  .detail-section:last-child {
    margin-bottom: 0;
  }
  
  .detail-section h4 {
    margin: 0 0 0.75rem 0;
    color: #64b5f6;
    font-size: 0.9rem;
    font-weight: 600;
  }
  
  .reasoning-steps {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .reasoning-step {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
  }
  
  .step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: rgba(100, 181, 246, 0.2);
    color: #64b5f6;
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 600;
    flex-shrink: 0;
  }
  
  .step-text {
    color: #e1e5e9;
    font-size: 0.9rem;
  }
  
  .concepts-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .concept-tag {
    background: rgba(129, 199, 132, 0.2);
    color: #81c784;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.75rem;
  }
  
  .metric-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
  }
  
  .metric-label {
    color: #a0a9b8;
    font-size: 0.8rem;
  }
  
  .metric-value {
    color: #e1e5e9;
    font-weight: 600;
    font-size: 0.9rem;
  }
  
  /* Empty state */
  .response-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: #64748b;
    text-align: center;
    gap: 0.5rem;
  }
  
  .empty-icon {
    font-size: 2rem;
    opacity: 0.6;
  }
  
  .empty-text {
    font-weight: 500;
    font-size: 1rem;
  }
  
  .empty-subtext {
    font-size: 0.85rem;
    opacity: 0.7;
  }
  
  /* Animations */
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  /* Scrollbar styling */
  .response-list::-webkit-scrollbar {
    width: 6px;
  }
  
  .response-list::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .response-list::-webkit-scrollbar-thumb {
    background: rgba(100, 120, 150, 0.3);
    border-radius: 3px;
  }
  
  .response-list::-webkit-scrollbar-thumb:hover {
    background: rgba(100, 120, 150, 0.5);
  }
</style>
