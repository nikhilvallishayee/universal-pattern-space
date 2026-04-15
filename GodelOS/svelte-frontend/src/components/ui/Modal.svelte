<script>
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  
  export let show = false;
  export let title = '';
  export let size = 'large'; // 'small', 'medium', 'large', 'fullscreen'
  export let allowBackdropClose = true;
  export let showCloseButton = true;
  
  const dispatch = createEventDispatcher();
  
  function closeModal() {
    dispatch('close');
  }
  
  function handleBackdropClick(event) {
    if (allowBackdropClose && event.target === event.currentTarget) {
      closeModal();
    }
  }
  
  function handleKeydown(event) {
    if (event.key === 'Escape' && show) {
      closeModal();
    }
  }
  
  // Focus management
  let modalContent;
  $: if (show && modalContent) {
    modalContent.focus();
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
  <div 
    class="modal-backdrop" 
    on:click={handleBackdropClick}
    transition:fade={{ duration: 200 }}
    role="dialog"
    aria-modal="true"
    aria-labelledby={title ? "modal-title" : undefined}
  >
    <div 
      class="modal-content {size}"
      bind:this={modalContent}
      tabindex="-1"
      transition:scale={{ duration: 200, start: 0.95 }}
    >
      <!-- Modal Header -->
      <header class="modal-header">
        {#if title}
          <h2 id="modal-title" class="modal-title">{title}</h2>
        {/if}
        
        {#if showCloseButton}
          <button 
            class="modal-close-button" 
            on:click={closeModal}
            aria-label="Close modal"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        {/if}
      </header>
      
      <!-- Modal Body -->
      <main class="modal-body">
        <slot />
      </main>
      
      <!-- Modal Footer (if needed) -->
      {#if $$slots.footer}
        <footer class="modal-footer">
          <slot name="footer" />
        </footer>
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }
  
  .modal-content {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 12px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .modal-content.small {
    width: 400px;
    max-width: 90vw;
  }
  
  .modal-content.medium {
    width: 600px;
    max-width: 90vw;
  }
  
  .modal-content.large {
    width: 1000px;
    max-width: 95vw;
    height: 80vh;
  }
  
  .modal-content.fullscreen {
    width: 98vw;
    height: 95vh;
  }
  
  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 2rem 1rem;
    border-bottom: 1px solid #333;
    flex-shrink: 0;
  }
  
  .modal-title {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
    color: #e0e0e0;
  }
  
  .modal-close-button {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: all 0.2s ease;
  }
  
  .modal-close-button:hover {
    background: #333;
    color: #fff;
  }
  
  .modal-body {
    flex: 1;
    overflow: auto;
    padding: 1.5rem 2rem;
  }
  
  .modal-footer {
    padding: 1rem 2rem 1.5rem;
    border-top: 1px solid #333;
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    flex-shrink: 0;
  }
  
  /* Scrollbar styling */
  .modal-body::-webkit-scrollbar {
    width: 8px;
  }
  
  .modal-body::-webkit-scrollbar-track {
    background: #2a2a2a;
  }
  
  .modal-body::-webkit-scrollbar-thumb {
    background: #555;
    border-radius: 4px;
  }
  
  .modal-body::-webkit-scrollbar-thumb:hover {
    background: #666;
  }
  
  /* Focus management */
  .modal-content:focus {
    outline: none;
  }
</style>
