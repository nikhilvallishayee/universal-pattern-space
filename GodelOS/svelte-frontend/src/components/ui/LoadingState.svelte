<script>
  import { onMount, onDestroy } from 'svelte';
  
  // Props
  export let loading = false;
  export let error = null;
  export let progress = null; // 0-100 for progress bar
  export let message = 'Loading...';
  export let size = 'md'; // 'sm', 'md', 'lg'
  export let variant = 'spinner'; // 'spinner', 'skeleton', 'progress', 'dots'
  export let overlay = false;
  export let retryable = false;
  export let timeout = null; // Auto-hide after ms
  
  // Internal state
  let showRetry = false;
  let timeoutId = null;
  
  // Events
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  
  // Auto-hide functionality
  $: if (loading && timeout) {
    if (timeoutId) clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      if (loading) {
        showRetry = true;
        dispatch('timeout');
      }
    }, timeout);
  }
  
  // Cleanup
  onDestroy(() => {
    if (timeoutId) clearTimeout(timeoutId);
  });
  
  // Size classes
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6', 
    lg: 'w-8 h-8'
  };
  
  function handleRetry() {
    showRetry = false;
    error = null;
    dispatch('retry');
  }
</script>

{#if loading || error}
  <div class="loading-container" class:overlay>
    <div class="loading-content">
      
      {#if error}
        <!-- Error State -->
        <div class="error-state">
          <div class="error-icon">
            <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.268 19.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p class="error-message">{error}</p>
          {#if retryable || showRetry}
            <button class="retry-button" on:click={handleRetry}>
              Try Again
            </button>
          {/if}
        </div>
        
      {:else if variant === 'spinner'}
        <!-- Spinner -->
        <div class="spinner-container">
          <div class="spinner {sizeClasses[size]}">
            <svg class="animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" 
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p class="loading-message">{message}</p>
          {#if progress !== null}
            <div class="progress-bar">
              <div class="progress-fill" style="width: {progress}%"></div>
            </div>
            <span class="progress-text">{Math.round(progress)}%</span>
          {/if}
        </div>
        
      {:else if variant === 'skeleton'}
        <!-- Skeleton Loading -->
        <div class="skeleton-container">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-text"></div>
          <div class="skeleton-line skeleton-text short"></div>
        </div>
        
      {:else if variant === 'progress'}
        <!-- Progress Bar -->
        <div class="progress-container">
          <p class="loading-message">{message}</p>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {progress || 0}%"></div>
          </div>
          <span class="progress-text">{Math.round(progress || 0)}%</span>
        </div>
        
      {:else if variant === 'dots'}
        <!-- Animated Dots -->
        <div class="dots-container">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
          <p class="loading-message">{message}</p>
        </div>
      {/if}
      
      {#if showRetry}
        <button class="timeout-retry" on:click={handleRetry}>
          Connection timeout - retry?
        </button>
      {/if}
    </div>
  </div>
{/if}

<style>
  .loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  
  .loading-container.overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 9999;
  }
  
  .loading-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem;
    background: var(--bg-elevated, #1a1a1a);
    border-radius: 12px;
    border: 1px solid var(--border-subtle, #333);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  }
  
  /* Spinner Styles */
  .spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  
  .spinner {
    color: var(--primary, #6366f1);
  }
  
  .loading-message {
    font-size: 0.875rem;
    color: var(--text-secondary, #9ca3af);
    margin: 0;
  }
  
  /* Progress Bar Styles */
  .progress-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    min-width: 200px;
  }
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--bg-subtle, #2a2a2a);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary, #6366f1), var(--primary-light, #8b5cf6));
    border-radius: 4px;
    transition: width 0.3s ease;
  }
  
  .progress-text {
    font-size: 0.75rem;
    color: var(--text-tertiary, #6b7280);
  }
  
  /* Skeleton Styles */
  .skeleton-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
    max-width: 300px;
  }
  
  .skeleton-line {
    height: 1rem;
    background: linear-gradient(90deg, 
      var(--bg-subtle, #2a2a2a) 25%, 
      var(--bg-muted, #333) 50%, 
      var(--bg-subtle, #2a2a2a) 75%);
    background-size: 200% 100%;
    border-radius: 4px;
    animation: skeleton-loading 1.5s infinite;
  }
  
  .skeleton-title {
    height: 1.25rem;
  }
  
  .skeleton-text {
    height: 1rem;
  }
  
  .skeleton-text.short {
    width: 60%;
  }
  
  @keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
  
  /* Dots Styles */
  .dots-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }
  
  .dots-container > div:first-child {
    display: flex;
    gap: 0.5rem;
  }
  
  .dot {
    width: 8px;
    height: 8px;
    background: var(--primary, #6366f1);
    border-radius: 50%;
    animation: dot-bounce 1.4s infinite ease-in-out;
  }
  
  .dot:nth-child(1) { animation-delay: -0.32s; }
  .dot:nth-child(2) { animation-delay: -0.16s; }
  .dot:nth-child(3) { animation-delay: 0s; }
  
  @keyframes dot-bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
  
  /* Error Styles */
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    text-align: center;
  }
  
  .error-icon {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .error-message {
    font-size: 0.875rem;
    color: var(--text-secondary, #9ca3af);
    margin: 0;
    max-width: 300px;
  }
  
  .retry-button, .timeout-retry {
    padding: 0.5rem 1rem;
    background: var(--primary, #6366f1);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .retry-button:hover, .timeout-retry:hover {
    background: var(--primary-dark, #4f46e5);
  }
  
  .timeout-retry {
    background: var(--warning, #f59e0b);
    font-size: 0.75rem;
    margin-top: 0.5rem;
  }
  
  /* Responsive */
  @media (max-width: 640px) {
    .loading-content {
      padding: 1rem;
      margin: 1rem;
      max-width: calc(100vw - 2rem);
    }
    
    .progress-container {
      min-width: 150px;
    }
  }
  
  /* Animation utilities */
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>