<script>
  import { createEventDispatcher } from 'svelte';
  import { cognitiveState } from '../../stores/cognitive.js';
  import { transparencyMode } from '../../stores/transparency.js';
  import { sendQuery } from '../../utils/websocket.js';
  import { GödelOSAPI } from '../../utils/api.js';
  
  const dispatch = createEventDispatcher();
  
  let queryText = '';
  let isProcessing = false;
  let queryHistory = [];
  let historyIndex = -1;
  let showAdvanced = false;
  let queryOptions = {
    enableReflection: true,
    trackProcessing: true,
    maxDepth: 3,
    confidenceThreshold: 0.6,
    useCommonSense: true,
    enableLearning: true
  };
  
  // Reactive query suggestions based on cognitive state
  $: suggestions = generateSuggestions($cognitiveState);
  
  function generateSuggestions(cognitive) {
    const suggestions = [];
    
    // Suggest queries based on current attention using canonical format
    if (cognitive.manifestConsciousness?.attention?.focus?.length > 0) {
      const focusItems = cognitive.manifestConsciousness.attention.focus;
      suggestions.push(`Tell me more about ${focusItems[0]}`);
      suggestions.push(`How does "${focusItems[0]}" relate to other concepts?`);
    }
    
    // Fallback to legacy format for backward compatibility
    if (suggestions.length === 0 && cognitive.attention_focus && cognitive.attention_focus.length > 0) {
      const focusItem = cognitive.attention_focus[0];
      suggestions.push(`Tell me more about ${focusItem.description || focusItem.item_type}`);
      suggestions.push(`How does ${focusItem.description || focusItem.item_type} relate to other concepts?`);
    }
    
    // Suggest exploration of active processes
    if (cognitive.agenticProcesses && cognitive.agenticProcesses.length > 0) {
      suggestions.push('What are the current agentic processes working on?');
      suggestions.push('Show me the reasoning behind the current agent goals');
    }
    
    // Suggest system introspection based on metacognitive state
    if (cognitive.manifestConsciousness?.metaReflection?.coherence < 0.8) {
      suggestions.push('Why is the reasoning coherence low?');
      suggestions.push('How can the system improve its meta-reflection capabilities?');
    }
    
    // Default exploratory suggestions
    if (suggestions.length === 0) {
      suggestions.push(
        'What is the current state of consciousness?',
        'Explain your reasoning process',
        'What are you learning right now?',
        'Show me recent insights',
        'How do you understand this conversation?'
      );
    }
    
    return suggestions.slice(0, 3);
  }
  
  async function handleSubmit() {
    if (!queryText.trim() || isProcessing) return;
    
    isProcessing = true;
    const currentQuery = queryText;
    
    // Add to history
    queryHistory = [queryText, ...queryHistory.slice(0, 49)]; // Keep last 50
    historyIndex = -1;
    
    try {
      // Update cognitive state to show current query using canonical format
      cognitiveState.update(state => ({
        ...state,
        manifestConsciousness: {
          ...state.manifestConsciousness,
          attention: {
            ...state.manifestConsciousness.attention,
            focus: [currentQuery],
            intensity: Math.min(1.0, (state.manifestConsciousness.attention?.intensity || 0) + 0.2),
            coverage: 0.8
          },
          processMonitoring: {
            ...state.manifestConsciousness.processMonitoring,
            latency: Date.now(), // Start time
            throughput: Math.min(1.0, (state.manifestConsciousness.processMonitoring?.throughput || 0) + 0.1)
          }
        },
        lastUpdate: Date.now()
      }));
      
      // Add to query history
      const queryEntry = {
        id: Date.now(),
        text: currentQuery,
        timestamp: Date.now(),
        source: 'human',
        options: queryOptions
      };
      
      // Store in a queryHistory array (we can add this to the store later if needed)
      queryHistory = [queryEntry, ...queryHistory.slice(0, 49)];
      
      // Try WebSocket first, then fallback to HTTP API
      let queryResult = null;
      try {
        // Send query through WebSocket (non-blocking)
        sendQuery(currentQuery, queryOptions);
        
        // Use enhanced cognitive query API with fallback
        console.log('🔄 Processing query with enhanced cognitive system:', currentQuery);
        queryResult = await GödelOSAPI.enhancedQuery(currentQuery, 'user_interface');
        
        console.log('✅ Enhanced query result:', queryResult);
        
        // Dispatch the response for other components to handle
        dispatch('query-response', {
          query: currentQuery,
          response: queryResult,
          timestamp: Date.now()
        });
        
        // Also dispatch a global window event for ResponseDisplay
        window.dispatchEvent(new CustomEvent('query-response', {
          detail: {
            query: currentQuery,
            response: queryResult,
            timestamp: Date.now()
          }
        }));
        
      } catch (apiError) {
        console.warn('Enhanced API failed:', apiError);
        // Error handling is already in place
      }
      
      // Dispatch event for other components
      dispatch('query-submitted', {
        query: currentQuery,
        options: queryOptions,
        result: queryResult,
        timestamp: Date.now()
      });
      
      queryText = '';
      
    } catch (error) {
      console.error('Failed to send query:', error);
      // Update cognitive state to show error using canonical format
      cognitiveState.update(state => ({
        ...state,
        manifestConsciousness: {
          ...state.manifestConsciousness,
          attention: {
            ...state.manifestConsciousness.attention,
            focus: [], // Clear focus on error
            intensity: Math.max(0, (state.manifestConsciousness.attention?.intensity || 0) - 0.2)
          },
          processMonitoring: {
            ...state.manifestConsciousness.processMonitoring,
            throughput: Math.max(0, (state.manifestConsciousness.processMonitoring?.throughput || 0) - 0.2)
          }
        },
        lastUpdate: Date.now()
      }));
    } finally {
      isProcessing = false;
    }
  }
  
  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    } else if (event.key === 'ArrowUp' && queryHistory.length > 0) {
      event.preventDefault();
      historyIndex = Math.min(historyIndex + 1, queryHistory.length - 1);
      queryText = queryHistory[historyIndex];
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (historyIndex > 0) {
        historyIndex--;
        queryText = queryHistory[historyIndex];
      } else {
        historyIndex = -1;
        queryText = '';
      }
    }
  }
  
  function useSuggestion(suggestion) {
    queryText = suggestion;
  }
  
  function clearQuery() {
    queryText = '';
    historyIndex = -1;
  }
  
  function toggleAdvanced() {
    showAdvanced = !showAdvanced;
  }
</script>

<div class="query-interface">
  <!-- Main query input -->
  <div class="query-input-container">
    <div class="input-wrapper">
      <textarea
        bind:value={queryText}
        on:keydown={handleKeydown}
        placeholder="Ask GödelOS anything... (Enter to send, Shift+Enter for new line)"
        rows="1"
        class="query-input"
        disabled={isProcessing}
      ></textarea>
      
      <div class="input-actions">
        <button
          on:click={toggleAdvanced}
          class="action-btn advanced-btn {showAdvanced ? 'active' : ''}"
          title="Advanced options"
        >
          ⚙️
        </button>
        
        {#if queryText}
          <button
            on:click={clearQuery}
            class="action-btn clear-btn"
            title="Clear query"
          >
            ✕
          </button>
        {/if}
        
        <button
          on:click={handleSubmit}
          class="submit-btn"
          disabled={!queryText.trim() || isProcessing}
          title="Send query (Enter)"
        >
          {#if isProcessing}
            <div class="spinner"></div>
          {:else}
            <span class="submit-icon">→</span>
          {/if}
        </button>
      </div>
    </div>
    
    <!-- Processing indicator -->
    {#if $cognitiveState.manifestConsciousness.currentQuery}
      <div class="processing-indicator">
        <div class="processing-bar">
          <div 
            class="processing-fill"
            style="width: {$cognitiveState.manifestConsciousness.processingLoad * 100}%"
          ></div>
        </div>
        <span class="processing-text">
          Processing: "{$cognitiveState.manifestConsciousness.currentQuery}"
        </span>
      </div>
    {/if}
  </div>
  
  <!-- Suggestions -->
  {#if suggestions.length > 0 && !queryText}
    <div class="suggestions">
      <div class="suggestions-label">Try asking:</div>
      <div class="suggestion-list">
        {#each suggestions as suggestion}
          <button
            class="suggestion-chip"
            on:click={() => useSuggestion(suggestion)}
          >
            {suggestion}
          </button>
        {/each}
      </div>
    </div>
  {/if}
  
  <!-- Advanced options panel -->
  {#if showAdvanced}
    <div class="advanced-options">
      <div class="options-header">
        <h4>Query Options</h4>
        <button
          on:click={() => showAdvanced = false}
          class="close-advanced"
        >
          ✕
        </button>
      </div>
      
      <div class="options-grid">
        <label class="option-item">
          <input
            type="checkbox"
            bind:checked={queryOptions.enableReflection}
          />
          <span>Enable Reflection</span>
          <small>Generate metacognitive insights</small>
        </label>
        
        <label class="option-item">
          <input
            type="checkbox"
            bind:checked={queryOptions.trackProcessing}
          />
          <span>Track Processing</span>
          <small>Monitor reasoning steps</small>
        </label>
        
        <label class="option-item">
          <input
            type="checkbox"
            bind:checked={queryOptions.useCommonSense}
          />
          <span>Use Common Sense</span>
          <small>Apply commonsense reasoning</small>
        </label>
        
        <label class="option-item">
          <input
            type="checkbox"
            bind:checked={queryOptions.enableLearning}
          />
          <span>Enable Learning</span>
          <small>Update knowledge from interaction</small>
        </label>
        
        <label class="option-item">
          <input
            type="checkbox"
            checked={$transparencyMode}
            on:change={() => transparencyMode.update(v => !v)}
          />
          <span>Transparency Mode</span>
          <small>Show reasoning trace inline with responses</small>
        </label>
        
        <label class="option-item range-item">
          <span>Max Reasoning Depth</span>
          <input
            type="range"
            min="1"
            max="10"
            bind:value={queryOptions.maxDepth}
          />
          <span class="range-value">{queryOptions.maxDepth}</span>
        </label>
        
        <label class="option-item range-item">
          <span>Confidence Threshold</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            bind:value={queryOptions.confidenceThreshold}
          />
          <span class="range-value">{queryOptions.confidenceThreshold}</span>
        </label>
      </div>
    </div>
  {/if}
</div>

<style>
  .query-interface {
    padding: 1.5rem;
    background: rgba(20, 25, 40, 0.8);
    border-bottom: 1px solid rgba(100, 120, 150, 0.15);
  }
  
  .query-input-container {
    margin-bottom: 1rem;
  }
  
  .input-wrapper {
    display: flex;
    align-items: flex-end;
    gap: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(100, 120, 150, 0.2);
    border-radius: 12px;
    padding: 1rem;
    transition: border-color 0.2s ease;
  }
  
  .input-wrapper:focus-within {
    border-color: rgba(100, 181, 246, 0.5);
    box-shadow: 0 0 0 2px rgba(100, 181, 246, 0.1);
  }
  
  .query-input {
    flex: 1;
    background: none;
    border: none;
    color: #e1e5e9;
    font-size: 1rem;
    line-height: 1.5;
    resize: none;
    min-height: 24px;
    max-height: 120px;
    font-family: inherit;
  }
  
  .query-input::placeholder {
    color: #64748b;
  }
  
  .query-input:focus {
    outline: none;
  }
  
  .input-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .action-btn {
    background: none;
    border: none;
    color: #a0a9b8;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: all 0.2s ease;
    font-size: 0.9rem;
  }
  
  .action-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #e1e5e9;
  }
  
  .action-btn.active {
    background: rgba(100, 181, 246, 0.2);
    color: #64b5f6;
  }
  
  .submit-btn {
    background: linear-gradient(135deg, #64b5f6, #42a5f5);
    border: none;
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 44px;
  }
  
  .submit-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #42a5f5, #1e88e5);
    transform: translateY(-1px);
  }
  
  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
  
  .submit-icon {
    font-size: 1.2rem;
    font-weight: bold;
  }
  
  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  .processing-indicator {
    margin-top: 0.75rem;
    padding: 0.75rem;
    background: rgba(100, 181, 246, 0.1);
    border-radius: 8px;
    border-left: 3px solid #64b5f6;
  }
  
  .processing-bar {
    height: 3px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }
  
  .processing-fill {
    height: 100%;
    background: linear-gradient(90deg, #64b5f6, #42a5f5);
    transition: width 0.3s ease;
    animation: pulse 2s infinite;
  }
  
  .processing-text {
    font-size: 0.9rem;
    color: #a0a9b8;
    font-style: italic;
  }
  
  .suggestions {
    margin-top: 1rem;
  }
  
  .suggestions-label {
    font-size: 0.85rem;
    color: #a0a9b8;
    margin-bottom: 0.5rem;
  }
  
  .suggestion-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .suggestion-chip {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(100, 120, 150, 0.2);
    color: #a0a9b8;
    padding: 0.5rem 0.75rem;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.85rem;
  }
  
  .suggestion-chip:hover {
    background: rgba(100, 181, 246, 0.1);
    border-color: rgba(100, 181, 246, 0.3);
    color: #64b5f6;
  }
  
  .advanced-options {
    margin-top: 1rem;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(100, 120, 150, 0.15);
    border-radius: 8px;
    overflow: hidden;
  }
  
  .options-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(100, 120, 150, 0.1);
  }
  
  .options-header h4 {
    margin: 0;
    font-size: 0.9rem;
    color: #e1e5e9;
  }
  
  .close-advanced {
    background: none;
    border: none;
    color: #a0a9b8;
    cursor: pointer;
    padding: 0.25rem;
  }
  
  .options-grid {
    padding: 1rem;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
  }
  
  .option-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    cursor: pointer;
  }
  
  .option-item input[type="checkbox"] {
    margin-right: 0.5rem;
  }
  
  .option-item span:first-of-type {
    font-size: 0.9rem;
    color: #e1e5e9;
  }
  
  .option-item small {
    color: #a0a9b8;
    font-size: 0.8rem;
  }
  
  .range-item {
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
  }
  
  .range-item input[type="range"] {
    flex: 1;
  }
  
  .range-value {
    min-width: 30px;
    text-align: center;
    font-size: 0.85rem;
    color: #64b5f6;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
</style>
