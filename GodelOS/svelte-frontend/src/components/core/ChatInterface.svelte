<script>
  import { onMount, onDestroy } from 'svelte';
  import { cognitiveState } from '../../stores/cognitive.js';
  import { enhancedCognitiveState } from '../../stores/enhanced-cognitive.js';
  import { API_BASE_URL } from '../../config.js';

  // Component props
  export let mode = 'normal'; // normal, enhanced, diagnostic
  export let showCognitiveAnalysis = true;
  export let autoScroll = true;

  // Chat state
  let messages = [];
  let currentMessage = '';
  let isProcessing = false;
  let chatContainer;
  let messageInput;
  
  // Interface state
  let showAnalysisPanel = false;
  let currentAnalysis = null;
  let currentConsciousnessReflection = null;
  let currentSystemGuidance = null;

  // Reactive expressions
  $: canSend = currentMessage.trim().length > 0 && !isProcessing;
  $: modeIcon = {
    'normal': '💬',
    'enhanced': '🧠', 
    'diagnostic': '🔬'
  }[mode];
  
  $: modeDescription = {
    'normal': 'Natural conversation',
    'enhanced': 'Conversation with cognitive insights',
    'diagnostic': 'Deep diagnostic conversation with system guidance'
  }[mode];

  onMount(() => {
    // Add welcome message
    messages = [{
      id: Date.now(),
      type: 'system',
      content: `Welcome to GödelOS Chat Interface (${mode} mode). ${modeDescription}.`,
      timestamp: new Date()
    }];
    
    // Focus on input
    if (messageInput) {
      messageInput.focus();
    }
  });

  async function sendMessage() {
    if (!canSend) return;
    
    const userMessage = currentMessage.trim();
    const messageId = Date.now();
    
    // Add user message to chat
    messages = [...messages, {
      id: messageId,
      type: 'user',
      content: userMessage,
      timestamp: new Date()
    }];
    
    // Clear input and set processing state
    currentMessage = '';
    isProcessing = true;
    
    // Scroll to bottom
    scrollToBottom();
    
    try {
      // Send to backend
      const response = await fetch(`${API_BASE_URL}/api/llm-chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          include_cognitive_context: true,
          mode: mode
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add AI response to chat
      const aiMessage = {
        id: messageId + 1,
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        cognitiveAnalysis: data.cognitive_analysis,
        consciousnessReflection: data.consciousness_reflection,
        systemGuidance: data.system_guidance
      };
      
      messages = [...messages, aiMessage];
      
      // Store analysis data for panel
      if (data.cognitive_analysis || data.consciousness_reflection || data.system_guidance) {
        currentAnalysis = data.cognitive_analysis;
        currentConsciousnessReflection = data.consciousness_reflection;
        currentSystemGuidance = data.system_guidance;
        
        if (mode !== 'normal') {
          showAnalysisPanel = true;
        }
      }
      
    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      messages = [...messages, {
        id: messageId + 2,
        type: 'error',
        content: `Error: ${error.message}. The system may be initializing or experiencing connectivity issues.`,
        timestamp: new Date()
      }];
    } finally {
      isProcessing = false;
      scrollToBottom();
      
      // Refocus input
      if (messageInput) {
        messageInput.focus();
      }
    }
  }
  
  function scrollToBottom() {
    if (autoScroll && chatContainer) {
      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 100);
    }
  }
  
  function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }
  
  function clearChat() {
    messages = [{
      id: Date.now(),
      type: 'system', 
      content: `Chat cleared. Continue conversation in ${mode} mode.`,
      timestamp: new Date()
    }];
    showAnalysisPanel = false;
    currentAnalysis = null;
    currentConsciousnessReflection = null;
    currentSystemGuidance = null;
  }
  
  function exportChat() {
    const chatData = {
      mode: mode,
      timestamp: new Date().toISOString(),
      messages: messages.map(msg => ({
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        cognitiveAnalysis: msg.cognitiveAnalysis,
        consciousnessReflection: msg.consciousnessReflection,
        systemGuidance: msg.systemGuidance
      }))
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `godelos-chat-${mode}-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
  }
</script>

<div class="chat-interface">
  <!-- Header -->
  <div class="chat-header">
    <div class="mode-indicator">
      <span class="mode-icon">{modeIcon}</span>
      <div class="mode-info">
        <h3>LLM Chat Interface</h3>
        <span class="mode-description">{modeDescription}</span>
      </div>
    </div>
    
    <div class="chat-controls">
      <button class="btn-icon" on:click={() => showAnalysisPanel = !showAnalysisPanel} 
              disabled={!currentAnalysis && !currentConsciousnessReflection}
              title="Toggle Analysis Panel">
        🧠
      </button>
      <button class="btn-icon" on:click={clearChat} title="Clear Chat">
        🗑️
      </button>
      <button class="btn-icon" on:click={exportChat} title="Export Chat">
        💾
      </button>
    </div>
  </div>

  <div class="chat-body">
    <!-- Messages Container -->
    <div class="chat-messages" bind:this={chatContainer}>
      {#each messages as message (message.id)}
        <div class="message message-{message.type}">
          <div class="message-header">
            <span class="message-sender">
              {#if message.type === 'user'}
                👤 You
              {:else if message.type === 'ai'}
                🤖 GödelOS
              {:else if message.type === 'system'}
                ⚙️ System
              {:else}
                ⚠️ Error
              {/if}
            </span>
            <span class="message-time">{formatTimestamp(message.timestamp)}</span>
          </div>
          
          <div class="message-content">
            {message.content}
          </div>
          
          {#if message.cognitiveAnalysis || message.consciousnessReflection || message.systemGuidance}
            <div class="message-insights">
              <button class="insights-toggle" 
                      on:click={() => {
                        currentAnalysis = message.cognitiveAnalysis;
                        currentConsciousnessReflection = message.consciousnessReflection;
                        currentSystemGuidance = message.systemGuidance;
                        showAnalysisPanel = true;
                      }}>
                🔍 View Cognitive Insights
              </button>
            </div>
          {/if}
        </div>
      {/each}
      
      {#if isProcessing}
        <div class="message message-ai processing">
          <div class="message-header">
            <span class="message-sender">🤖 GödelOS</span>
            <span class="message-time">Processing...</span>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Analysis Panel -->
    {#if showAnalysisPanel && (currentAnalysis || currentConsciousnessReflection || currentSystemGuidance)}
      <div class="analysis-panel">
        <div class="analysis-header">
          <h4>Cognitive Analysis</h4>
          <button class="btn-close" on:click={() => showAnalysisPanel = false}>×</button>
        </div>
        
        <div class="analysis-content">
          {#if currentAnalysis}
            <div class="analysis-section">
              <h5>🧠 Cognitive Processing</h5>
              {#each Object.entries(currentAnalysis) as [key, value]}
                <div class="analysis-item">
                  <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                  <span>{value}</span>
                </div>
              {/each}
            </div>
          {/if}
          
          {#if currentConsciousnessReflection}
            <div class="analysis-section">
              <h5>✨ Consciousness Reflection</h5>
              {#each Object.entries(currentConsciousnessReflection) as [key, value]}
                <div class="analysis-item">
                  <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                  <span>{value}</span>
                </div>
              {/each}
            </div>
          {/if}
          
          {#if currentSystemGuidance}
            <div class="analysis-section">
              <h5>🎯 System Guidance</h5>
              {#each Object.entries(currentSystemGuidance) as [key, value]}
                <div class="analysis-item">
                  <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                  {#if Array.isArray(value)}
                    <ul>
                      {#each value as item}
                        <li>{item}</li>
                      {/each}
                    </ul>
                  {:else}
                    <span>{value}</span>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>

  <!-- Input Area -->
  <div class="chat-input">
    <div class="input-container">
      <textarea
        bind:this={messageInput}
        bind:value={currentMessage}
        on:keypress={handleKeyPress}
        placeholder="Type your message to GödelOS..."
        rows="1"
        disabled={isProcessing}
      ></textarea>
      
      <button 
        class="send-button"
        on:click={sendMessage}
        disabled={!canSend}
        title="Send message (Enter)"
      >
        {#if isProcessing}
          ⏳
        {:else}
          📤
        {/if}
      </button>
    </div>
    
    <div class="input-info">
      <span class="mode-info">Mode: {mode}</span>
      <span class="char-count">{currentMessage.length} characters</span>
    </div>
  </div>
</div>

<style>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: 600px;
    max-height: 80vh;
    background: linear-gradient(135deg, rgba(25, 25, 40, 0.95), rgba(15, 15, 25, 0.98));
    border: 1px solid rgba(100, 200, 255, 0.3);
    border-radius: 12px;
    backdrop-filter: blur(10px);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    overflow: hidden;
  }

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: linear-gradient(90deg, rgba(50, 100, 200, 0.2), rgba(100, 50, 200, 0.2));
    border-bottom: 1px solid rgba(100, 200, 255, 0.3);
  }

  .mode-indicator {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .mode-icon {
    font-size: 24px;
  }

  .mode-info h3 {
    margin: 0;
    color: #e0e0f0;
    font-size: 16px;
  }

  .mode-description {
    color: #a0a0c0;
    font-size: 12px;
  }

  .chat-controls {
    display: flex;
    gap: 8px;
  }

  .btn-icon {
    background: rgba(100, 200, 255, 0.1);
    border: 1px solid rgba(100, 200, 255, 0.3);
    color: #e0e0f0;
    border-radius: 6px;
    width: 32px;
    height: 32px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s ease;
  }

  .btn-icon:hover:not(:disabled) {
    background: rgba(100, 200, 255, 0.2);
    transform: scale(1.05);
  }

  .btn-icon:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .chat-body {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .message {
    max-width: 85%;
    padding: 12px 16px;
    border-radius: 12px;
    animation: messageSlide 0.3s ease-out;
  }

  @keyframes messageSlide {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .message-user {
    align-self: flex-end;
    background: linear-gradient(135deg, rgba(50, 150, 250, 0.8), rgba(100, 100, 250, 0.6));
    color: white;
  }

  .message-ai {
    align-self: flex-start;
    background: linear-gradient(135deg, rgba(25, 25, 40, 0.8), rgba(40, 40, 60, 0.6));
    border: 1px solid rgba(100, 200, 255, 0.3);
    color: #e0e0f0;
  }

  .message-system {
    align-self: center;
    background: rgba(100, 100, 100, 0.2);
    color: #c0c0c0;
    font-style: italic;
    font-size: 14px;
    max-width: 70%;
  }

  .message-error {
    align-self: center;
    background: rgba(255, 100, 100, 0.2);
    border: 1px solid rgba(255, 100, 100, 0.4);
    color: #ffa0a0;
    max-width: 70%;
  }

  .message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 12px;
  }

  .message-sender {
    font-weight: bold;
  }

  .message-time {
    opacity: 0.7;
  }

  .message-content {
    line-height: 1.4;
    white-space: pre-wrap;
  }

  .message-insights {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .insights-toggle {
    background: rgba(100, 200, 255, 0.1);
    border: 1px solid rgba(100, 200, 255, 0.3);
    color: #64c8ff;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .insights-toggle:hover {
    background: rgba(100, 200, 255, 0.2);
  }

  .processing {
    opacity: 0.8;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
    align-items: center;
  }

  .typing-indicator span {
    width: 6px;
    height: 6px;
    background: #64c8ff;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
  }

  .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
  .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

  @keyframes typing {
    0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
  }

  .analysis-panel {
    width: 350px;
    background: rgba(15, 15, 25, 0.95);
    border-left: 1px solid rgba(100, 200, 255, 0.3);
    display: flex;
    flex-direction: column;
  }

  .analysis-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: rgba(50, 100, 200, 0.2);
    border-bottom: 1px solid rgba(100, 200, 255, 0.3);
  }

  .analysis-header h4 {
    margin: 0;
    color: #e0e0f0;
    font-size: 14px;
  }

  .btn-close {
    background: none;
    border: none;
    color: #e0e0f0;
    font-size: 18px;
    cursor: pointer;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
  }

  .btn-close:hover {
    background: rgba(255, 100, 100, 0.2);
  }

  .analysis-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }

  .analysis-section {
    margin-bottom: 20px;
  }

  .analysis-section h5 {
    margin: 0 0 12px 0;
    color: #64c8ff;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .analysis-item {
    margin-bottom: 12px;
    font-size: 12px;
    line-height: 1.4;
  }

  .analysis-item strong {
    display: block;
    color: #b0b0d0;
    margin-bottom: 4px;
  }

  .analysis-item span {
    color: #e0e0f0;
  }

  .analysis-item ul {
    margin: 4px 0 0 16px;
    padding: 0;
  }

  .analysis-item li {
    color: #e0e0f0;
    margin-bottom: 4px;
  }

  .chat-input {
    border-top: 1px solid rgba(100, 200, 255, 0.3);
    padding: 16px;
    background: rgba(25, 25, 40, 0.8);
  }

  .input-container {
    display: flex;
    gap: 12px;
    align-items: flex-end;
  }

  .input-container textarea {
    flex: 1;
    background: rgba(15, 15, 25, 0.8);
    border: 1px solid rgba(100, 200, 255, 0.3);
    border-radius: 8px;
    padding: 12px;
    color: #e0e0f0;
    font-family: inherit;
    font-size: 14px;
    resize: none;
    min-height: 44px;
    max-height: 120px;
    transition: border-color 0.2s ease;
  }

  .input-container textarea:focus {
    outline: none;
    border-color: rgba(100, 200, 255, 0.6);
  }

  .input-container textarea:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .send-button {
    background: linear-gradient(135deg, rgba(50, 150, 250, 0.8), rgba(100, 100, 250, 0.6));
    border: 1px solid rgba(100, 200, 255, 0.4);
    color: white;
    border-radius: 8px;
    width: 44px;
    height: 44px;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .send-button:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(100, 200, 255, 0.3);
  }

  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .input-info {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 11px;
    color: #a0a0c0;
  }

  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .chat-interface {
      height: 500px;
    }
    
    .analysis-panel {
      width: 280px;
    }
    
    .message {
      max-width: 95%;
    }
    
    .chat-header {
      padding: 12px 16px;
    }
    
    .mode-info h3 {
      font-size: 14px;
    }
  }

  @media (max-width: 480px) {
    .chat-body {
      flex-direction: column;
    }
    
    .analysis-panel {
      width: 100%;
      max-height: 200px;
      border-left: none;
      border-top: 1px solid rgba(100, 200, 255, 0.3);
    }
    
    .chat-controls {
      flex-wrap: wrap;
    }
  }
</style>