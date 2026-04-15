<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';
  import { knowledgeState, uiState } from '../../stores/cognitive.js';
  import { importProgressState, handleProgressUpdate, PROGRESS_STEPS } from '../../stores/importProgress.js';
  import { GödelOSAPI } from '../../utils/api.js';
  import { get } from 'svelte/store';
  import { apiHelpers } from '../../stores/cognitive.js';
  import LoadingState from '../ui/LoadingState.svelte';
  import { WS_BASE_URL } from '../../config.js';

  // Modal props
  export let show = false;
  const dispatch = createEventDispatcher();

  let fileInput;
  let dragActive = false;
  let selectedTab = 'file';
  let urlInput = '';
  let textInput = '';
  let textTitle = 'Text Import';
  let apiKeyInput = '';

  // Options
  let enableAI = false;
  let confidenceLevel = 'medium';
  let tabs = [
    { id: 'file', name: 'File', icon: '📁' },
    { id: 'url', name: 'URL', icon: '🌐' },
    { id: 'text', name: 'Text', icon: '📝' },
    { id: 'api', name: 'API', icon: '🔗' }
  ];

  // Progress tracking
  let activeImports = new Map();
  let importProgress = {};
  $: importProgress = $importProgressState;
  $: activeImportsArray = [...activeImports.values()];

  // WebSocket for real-time import progress updates
  let importProgressSocket = null;

  // Utility function to format file sizes
  function formatFileSize(bytes) {
    if (!bytes) return '';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  // Utility function to format file type
  function formatFileType(type) {
    if (!type || type === 'file') return 'Unknown';
    if (type.startsWith('application/pdf')) return 'PDF Document';
    if (type.startsWith('application/vnd.openxmlformats-officedocument.wordprocessingml')) return 'Word Document';
    if (type.startsWith('text/plain')) return 'Text File';
    if (type.startsWith('text/')) return 'Text';
    if (type.startsWith('image/')) return 'Image';
    return type.split('/').pop().toUpperCase();
  }

  // Utility function to get status color
  function getStatusColor(status) {
    switch (status) {
      case 'completed': return '#4ade80';
      case 'failed': return '#f87171';
      case 'cancelled': return '#94a3b8';
      case 'processing': return '#3b82f6';
      default: return '#64748b';
    }
  }

  // Import progress WebSocket connection
  function connectImportProgressWebSocket() {
    if (importProgressSocket) {
      importProgressSocket.close();
    }

    try {
      // Connect to import progress WebSocket endpoint
      importProgressSocket = new WebSocket(`${WS_BASE_URL}/api/knowledge/import/progress/stream`);
      
      importProgressSocket.onopen = () => {
        console.log('Import progress WebSocket connected');
      };

      importProgressSocket.onmessage = (event) => {
        try {
          const progressUpdate = JSON.parse(event.data);
          const { importId, ...progress } = progressUpdate;
          
          if (importId && progress) {
            importProgressState.update(state => ({
              ...state,
              [importId]: progress
            }));

            // Remove completed/failed imports from active tracking after delay
            if (progress.status === 'completed' || progress.status === 'failed') {
              setTimeout(() => {
                activeImports.delete(importId);
                activeImports = activeImports;
              }, 3000);
            }
          }
        } catch (err) {
          console.error('Invalid import progress WebSocket message:', err);
        }
      };

      importProgressSocket.onerror = (error) => {
        console.error('Import progress WebSocket error:', error);
      };

      importProgressSocket.onclose = () => {
        console.log('Import progress WebSocket disconnected');
        // Attempt to reconnect after delay
        setTimeout(connectImportProgressWebSocket, 5000);
      };
    } catch (err) {
      console.error('Failed to connect to import progress WebSocket:', err);
    }
  }

  // Lifecycle management
  onMount(() => {
    connectImportProgressWebSocket();
  });

  onDestroy(() => {
    if (importProgressSocket) {
      importProgressSocket.close();
    }
  });

  // --- Import handlers (restored) ---
  async function handleFileSelect(event) {
    const files = event?.target?.files || event;
    if (!files || files.length === 0) return;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      // optimistic temporary id until backend returns a real import id
      const tempId = `temp-${Date.now()}-${i}`;
      activeImports.set(tempId, { id: tempId, filename: file.name, type: file.type || 'file', source: 'upload' });
      activeImports = activeImports;

      importProgressState.update(state => ({
        ...state,
        [tempId]: { status: 'queued', progress: 0, message: 'Queued for upload' }
      }));

      try {
        const result = await GödelOSAPI.importFromFile(file);
  console.debug('[Import] importFromFile result:', result);
        const importId = result?.import_id || result?.id || result?.importId || tempId;
  console.debug('[Import] resolved importId:', importId, 'tempId:', tempId);

        // normalize activeImports key if backend returned a different id
        if (importId !== tempId) {
          const item = activeImports.get(tempId);
          activeImports.delete(tempId);
          item.id = importId;
          activeImports.set(importId, item);
          activeImports = activeImports;
        }

        importProgressState.update(state => ({
          ...state,
          [importId]: { status: 'started', progress: 0, message: 'Upload started' }
        }));

        // Progress updates will come via WebSocket
        console.log(`Import ${importId} started - progress updates via WebSocket`);
      } catch (err) {
        importProgressState.update(state => ({
          ...state,
          [tempId]: { status: 'failed', progress: 0, message: err?.message || 'Upload failed' }
        }));
        // remove after short delay
        setTimeout(() => {
          activeImports.delete(tempId);
          activeImports = activeImports;
        }, 3000);
      }
    }

    // reset file input so same file can be chosen again
    if (fileInput) fileInput.value = '';
  }

  async function importFromUrl() {
    if (!urlInput || !urlInput.trim()) return;
    const tempId = `url-${Date.now()}`;
    activeImports.set(tempId, { id: tempId, source: urlInput, type: 'url' });
    activeImports = activeImports;
    importProgressState.update(s => ({ ...s, [tempId]: { status: 'queued', progress: 0, message: 'Starting URL import' } }));

    try {
      const result = await GödelOSAPI.importFromUrl(urlInput, 'web');
  console.debug('[Import] importFromUrl result:', result);
      const importId = result?.import_id || result?.id || tempId;
  console.debug('[Import] resolved importId:', importId, 'tempId:', tempId);
      if (importId !== tempId) {
        const item = activeImports.get(tempId);
        activeImports.delete(tempId);
        item.id = importId;
        activeImports.set(importId, item);
        activeImports = activeImports;
      }
      importProgressState.update(s => ({ ...s, [importId]: { status: 'started', progress: 0, message: 'URL import started' } }));
      console.log(`URL import ${importId} started - progress updates via WebSocket`);
      urlInput = '';
    } catch (err) {
      importProgressState.update(s => ({ ...s, [tempId]: { status: 'failed', progress: 0, message: err?.message || 'URL import failed' } }));
      setTimeout(() => { activeImports.delete(tempId); activeImports = activeImports; }, 3000);
    }
  }

  async function importFromText() {
    if (!textInput || !textInput.trim()) return;
    const tempId = `text-${Date.now()}`;
    activeImports.set(tempId, { id: tempId, filename: textTitle || 'Text Import', type: 'text' });
    activeImports = activeImports;
    importProgressState.update(s => ({ ...s, [tempId]: { status: 'queued', progress: 0, message: 'Submitting text' } }));

    try {
      const result = await GödelOSAPI.importFromText(textInput, textTitle, 'document');
  console.debug('[Import] importFromText result:', result);
      const importId = result?.import_id || result?.id || tempId;
  console.debug('[Import] resolved importId:', importId, 'tempId:', tempId);
      if (importId !== tempId) {
        const item = activeImports.get(tempId);
        activeImports.delete(tempId);
        item.id = importId;
        activeImports.set(importId, item);
        activeImports = activeImports;
      }
      importProgressState.update(s => ({ ...s, [importId]: { status: 'started', progress: 0, message: 'Processing text' } }));
      console.log(`Text import ${importId} started - progress updates via WebSocket`);
      // clear text input after sending
      textInput = '';
      textTitle = 'Text Import';
    } catch (err) {
      importProgressState.update(s => ({ ...s, [tempId]: { status: 'failed', progress: 0, message: err?.message || 'Text import failed' } }));
      setTimeout(() => { activeImports.delete(tempId); activeImports = activeImports; }, 3000);
    }
  }

  // Drag & drop support and cleanup
  onMount(() => {
    const handleDragOver = (e) => { e.preventDefault(); dragActive = true; };
    const handleDragLeave = (e) => { e.preventDefault(); dragActive = false; };
    const handleDrop = (e) => {
      e.preventDefault(); dragActive = false;
      if (e.dataTransfer && e.dataTransfer.files) {
        handleFileSelect(e.dataTransfer.files);
      }
    };

    window.addEventListener('dragover', handleDragOver);
    window.addEventListener('dragleave', handleDragLeave);
    window.addEventListener('drop', handleDrop);

    return () => {
      window.removeEventListener('dragover', handleDragOver);
      window.removeEventListener('dragleave', handleDragLeave);
      window.removeEventListener('drop', handleDrop);
      // No polling intervals to clear - using WebSocket only
    };
  });

  // Clean up completed imports
  $: {
    for (const [id, progress] of Object.entries(importProgress)) {
      if (progress.status === 'completed' || progress.status === 'failed' || progress.status === 'cancelled') {
        setTimeout(() => {
          activeImports.delete(id);
          activeImports = activeImports;
        }, 3000);
        if (progress.status === 'completed') {
          // refresh knowledge graph so imported data becomes visible
          try { apiHelpers.updateKnowledgeFromBackend(); } catch (e) { /* ignore */ }
        }
      }
    }
  }

  // allow cancelling an import (best-effort - backend may not implement)
  async function cancelImport(id) {
    try {
      if (GödelOSAPI.cancelImport) {
        await GödelOSAPI.cancelImport(id);
        importProgressState.update(s => ({ ...s, [id]: { ...(s[id] || {}), status: 'cancelled', message: 'Cancelled by user' } }));
      } else {
        // Best-effort local update if backend doesn't support cancel
        importProgressState.update(s => ({ ...s, [id]: { ...(s[id] || {}), status: 'cancelled', message: 'Cancelled (local)' } }));
      }
    } catch (err) {
      console.warn('cancelImport error', err);
      importProgressState.update(s => ({ ...s, [id]: { ...(s[id] || {}), status: 'failed', message: err?.message || 'Cancel failed' } }));
    }
    // remove from active list shortly after
    setTimeout(() => { activeImports.delete(id); activeImports = activeImports; }, 1000);
  }

  // Bulk import management functions
  async function cancelAllImports() {
    try {
      if (GödelOSAPI.cancelAllImports) {
        const result = await GödelOSAPI.cancelAllImports();
        console.log('Cancelled all imports:', result);
        
        // Update local state for all active imports
        for (const [id] of activeImports.entries()) {
          importProgressState.update(s => ({ ...s, [id]: { ...(s[id] || {}), status: 'cancelled', message: 'Cancelled by bulk action' } }));
        }
        
        // Clear active imports after a delay
        setTimeout(() => { 
          activeImports.clear(); 
          activeImports = activeImports; 
        }, 2000);
      }
    } catch (err) {
      console.warn('cancelAllImports error', err);
    }
  }

  async function resetStuckImports() {
    try {
      if (GödelOSAPI.resetStuckImports) {
        const result = await GödelOSAPI.resetStuckImports();
        console.log('Reset stuck imports:', result);
        
        // Refresh the active imports list to reflect changes
        setTimeout(() => {
          // Force refresh of active imports (could be enhanced to call an API)
          activeImports = activeImports;
        }, 1000);
      }
    } catch (err) {
      console.warn('resetStuckImports error', err);
    }
  }

  // Modal functions
  function closeModal() {
    dispatch('close');
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      closeModal();
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && show) {
      closeModal();
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if show}
  <div 
    class="modal-backdrop" 
    on:click={handleBackdropClick}
    on:keydown={handleKeydown}
    transition:fade={{ duration: 200 }}
    role="button"
    aria-label="Close modal"
    tabindex="0"
  >
    <div class="import-container" class:drag-active={dragActive} transition:scale={{ duration: 200, start: 0.95 }}>
      <!-- Close button -->
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
  <!-- Header -->
  <div class="header">
    <div class="title-section">
      <h2 id="import-title">🧠 Knowledge Import</h2>
      <p>Import and process knowledge from various sources</p>
    </div>
    <div class="stats">
      <div class="stat">
        <span class="stat-value">{$knowledgeState.totalConcepts || 0}</span>
        <span class="stat-label">Concepts</span>
      </div>
      <div class="stat">
        <span class="stat-value">{activeImports.size}</span>
        <span class="stat-label">Active</span>
      </div>
    </div>
  </div>

  <!-- Tab Navigation -->
  <div class="tabs">
    {#each tabs as tab}
      <button 
        class="tab" 
        class:active={selectedTab === tab.id}
        on:click={() => selectedTab = tab.id}
      >
        <span class="tab-icon">{tab.icon}</span>
        <span class="tab-name">{tab.name}</span>
      </button>
    {/each}
  </div>

  <!-- Main Content Area -->
  <div class="content">
    <!-- Import Interface -->
    <div class="import-section">
      {#if selectedTab === 'file'}
        <div class="upload-zone" class:drag-active={dragActive}>
          <div class="upload-content">
            <div class="upload-icon">📁</div>
            <h3>Drop files here or click to browse</h3>
            <p>Supports PDF, TXT, MD, JSON, CSV and more</p>
            <button class="upload-btn" on:click={() => fileInput.click()}>
              Choose Files
            </button>
          </div>
          <input 
            type="file" 
            bind:this={fileInput}
            on:change={handleFileSelect}
            multiple
            hidden
          />
        </div>
      {:else if selectedTab === 'url'}
        <div class="input-section">
          <h3>Import from Web URL</h3>
          <div class="input-group">
            <input 
              type="url" 
              bind:value={urlInput}
              placeholder="https://example.com/document.pdf"
              class="url-input"
            />
            <button 
              class="import-btn" 
              on:click={importFromUrl}
              disabled={!urlInput.trim()}
            >
              Import
            </button>
          </div>
          <p class="help-text">Supports web pages, PDFs, and documents</p>
        </div>
      {:else if selectedTab === 'text'}
        <div class="input-section">
          <h3>Import Text Content</h3>
          <input 
            type="text" 
            bind:value={textTitle}
            placeholder="Document title"
            class="title-input"
          />
          <textarea 
            bind:value={textInput}
            placeholder="Paste your text content here..."
            class="text-input"
            rows="8"
          ></textarea>
          <button 
            class="import-btn" 
            on:click={importFromText}
            disabled={!textInput.trim()}
          >
            Process Text
          </button>
        </div>
      {:else if selectedTab === 'api'}
        <div class="input-section">
          <h3>Connect API Source</h3>
          <div class="input-group">
            <input 
              type="password" 
              bind:value={apiKeyInput}
              placeholder="API key or connection string"
              class="api-input"
            />
            <button 
              class="import-btn" 
              disabled={!apiKeyInput.trim()}
            >
              Connect
            </button>
          </div>
          <p class="help-text">Connect to external knowledge sources</p>
        </div>
      {/if}

      <!-- Inline Progress Panel (moved into import-section for better visibility) -->
      {#if activeImports.size > 0}
        <div class="inline-progress">
          <div class="progress-header-section">
            <h4>Active Imports ({activeImports.size})</h4>
            <div class="bulk-actions">
              <button class="bulk-btn cancel-all" on:click={cancelAllImports}>
                🛑 Cancel All
              </button>
              <button class="bulk-btn reset-stuck" on:click={resetStuckImports}>
                🔄 Reset Stuck
              </button>
            </div>
          </div>
          <div class="progress-list">
            {#each activeImportsArray as item}
              <div class="progress-item">
                <div class="progress-header">
                  <div style="display:flex;flex-direction:column;">
                    <span class="progress-name">{item.source || item.filename}</span>
                    <small class="progress-type">{item.type}</small>
                  </div>
                  <div style="display:flex;gap:8px;align-items:center;">
                    {#if importProgress[item.id]?.status === 'completed'}
                      <button class="view-btn" on:click={() => apiHelpers.updateKnowledgeFromBackend()}>View in KG</button>
                    {/if}
                    <button class="cancel-btn" on:click={() => cancelImport(item.id)}>Cancel</button>
                  </div>
                </div>
                {#if importProgress[item.id]}
                  <div class="progress-bar large">
                    <div 
                      class="progress-fill" 
                      style="width: {importProgress[item.id].progress || 0}%"
                    ></div>
                    <div class="progress-percent">{Math.round(importProgress[item.id].progress || 0)}%</div>
                  </div>
                  <div class="progress-status">
                    <span class="status-badge" style="background-color: {getStatusColor(importProgress[item.id].status)}20; color: {getStatusColor(importProgress[item.id].status)}; border: 1px solid {getStatusColor(importProgress[item.id].status)}40;">
                      {importProgress[item.id].status.toUpperCase()}
                    </span>
                    <span class="status-step">
                      {importProgress[item.id].current_step || importProgress[item.id].message || ''}
                    </span>
                  </div>
                  
                  <!-- Enhanced Progress Details -->
                  {#if importProgress[item.id].step_name && PROGRESS_STEPS[importProgress[item.id].step_name]}
                    <div class="step-indicator">
                      <div class="step-progress">
                        {#each Object.entries(PROGRESS_STEPS) as [stepKey, stepInfo], index}
                          {#if stepKey !== 'error'}
                            <div 
                              class="step-dot"
                              class:completed={stepInfo.order <= (importProgress[item.id].completed_steps || 0)}
                              class:current={stepKey === importProgress[item.id].step_name}
                            >
                              <span class="step-number">{stepInfo.order}</span>
                              <span class="step-label">{stepInfo.label}</span>
                            </div>
                          {/if}
                        {/each}
                      </div>
                    </div>
                  {/if}
                  
                  <!-- File Details -->
                  <div class="file-details">
                    <div class="detail-row">
                      <span class="detail-label">File:</span>
                      <span class="detail-value">{item.filename || item.source}</span>
                    </div>
                    {#if item.type && item.type !== 'file'}
                      <div class="detail-row">
                        <span class="detail-label">Type:</span>
                        <span class="detail-value">{formatFileType(item.type)}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].completed_steps !== undefined && importProgress[item.id].total_steps}
                      <div class="detail-row">
                        <span class="detail-label">Steps:</span>
                        <span class="detail-value">{importProgress[item.id].completed_steps}/{importProgress[item.id].total_steps}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].entities_extracted !== undefined}
                      <div class="detail-row">
                        <span class="detail-label">Entities:</span>
                        <span class="detail-value">{importProgress[item.id].entities_extracted}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].relationships_extracted !== undefined}
                      <div class="detail-row">
                        <span class="detail-label">Relations:</span>
                        <span class="detail-value">{importProgress[item.id].relationships_extracted}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].categories && importProgress[item.id].categories.length > 0}
                      <div class="detail-row">
                        <span class="detail-label">Categories:</span>
                        <span class="detail-value">{importProgress[item.id].categories.map(c => c.category).join(', ')}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].deduplication_stats}
                      <div class="detail-row">
                        <span class="detail-label">Deduplicates:</span>
                        <span class="detail-value">{importProgress[item.id].deduplication_stats.duplicates_removed || 0} removed</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].started_at}
                      <div class="detail-row">
                        <span class="detail-label">Started:</span>
                        <span class="detail-value">{new Date(importProgress[item.id].started_at * 1000).toLocaleTimeString()}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].estimated_completion}
                      <div class="detail-row">
                        <span class="detail-label">ETA:</span>
                        <span class="detail-value">{new Date(importProgress[item.id].estimated_completion * 1000).toLocaleTimeString()}</span>
                      </div>
                    {/if}
                    {#if importProgress[item.id].warnings && importProgress[item.id].warnings.length > 0}
                      <div class="detail-row">
                        <span class="detail-label">Warnings:</span>
                        <span class="detail-value warning">{importProgress[item.id].warnings.length}</span>
                      </div>
                    {/if}
                  </div>
                {:else}
                  <div class="progress-bar large">
                    <div class="progress-fill" style="width: 10%"></div>
                    <div class="progress-percent">0%</div>
                  </div>
                  <div class="progress-status">Starting...</div>
                  
                  <!-- File Details -->
                  <div class="file-details">
                    <div class="detail-row">
                      <span class="detail-label">File:</span>
                      <span class="detail-value">{item.filename || item.source}</span>
                    </div>
                    {#if item.type && item.type !== 'file'}
                      <div class="detail-row">
                        <span class="detail-label">Type:</span>
                        <span class="detail-value">{formatFileType(item.type)}</span>
                      </div>
                    {/if}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  <!-- Options Panel + Progress pinned below -->
  <div class="options-panel">
      <h4>Processing Options</h4>
      <div class="option-group">
        <label class="toggle-option">
          <input type="checkbox" bind:checked={enableAI} />
          <span class="toggle"></span>
          <span>AI Processing</span>
        </label>
        <div class="confidence-option">
          <label for="confidence-select">Confidence Level:</label>
          <select id="confidence-select" bind:value={confidenceLevel}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>
    </div>
  </div>

  
    </div>
  </div>
{/if}

<style>
  /* Modal styles */
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
    padding: 20px;
  }

  .modal-close-button {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #fff;
    transition: all 0.2s ease;
    z-index: 10;
  }

  .modal-close-button:hover {
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(255, 255, 255, 0.4);
    transform: scale(1.05);
  }

  .modal-close-button svg {
    width: 18px;
    height: 18px;
  }

  .import-container {
    width: 90vw;
    max-width: 1200px;
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
    backdrop-filter: blur(20px);
    color: #fff;
    border-radius: 20px;
    min-height: 80vh;
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    border: 1px solid rgba(74, 158, 255, 0.2);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 
                0 0 0 1px rgba(74, 158, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
    position: relative;
  }

  .import-container.drag-active {
    background: linear-gradient(135deg, #1a1a3e 0%, rgba(74, 158, 255, 0.2) 100%);
    border: 2px solid rgba(74, 158, 255, 0.8);
    box-shadow: 0 25px 50px -12px rgba(74, 158, 255, 0.5), 
                0 0 100px rgba(74, 158, 255, 0.3);
  }

  /* Header */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem 2.5rem 1.5rem 2.5rem;
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.1) 0%, rgba(74, 158, 255, 0.05) 100%);
    border-bottom: 1px solid rgba(74, 158, 255, 0.2);
    backdrop-filter: blur(10px);
  }

  .title-section h2 {
    margin: 0;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.025em;
  }

  .title-section p {
    margin: 0.5rem 0 0 0;
    color: rgba(255, 255, 255, 0.8);
    font-size: 1rem;
    font-weight: 400;
  }

  .stats {
    display: flex;
    gap: 2rem;
  }

  .stat {
    text-align: center;
    background: rgba(74, 158, 255, 0.1);
    padding: 1rem 1.25rem;
    border-radius: 12px;
    border: 1px solid rgba(74, 158, 255, 0.2);
    backdrop-filter: blur(10px);
    min-width: 70px;
  }

  .stat-value {
    display: block;
    font-size: 1.75rem;
    font-weight: 800;
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
  }

  .stat-label {
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 600;
    margin-top: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 0.5rem;
    background: rgba(74, 158, 255, 0.08);
    padding: 0.75rem;
    margin: 0 2.5rem;
    border-radius: 16px;
    border: 1px solid rgba(74, 158, 255, 0.15);
    backdrop-filter: blur(10px);
  }

  .tab {
    flex: 1;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    padding: 1rem 1.25rem;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    font-size: 0.95rem;
    font-weight: 600;
    position: relative;
    overflow: hidden;
  }

  .tab::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.15) 0%, rgba(126, 214, 255, 0.1) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .tab:hover::before {
    opacity: 1;
  }

  .tab:hover {
    color: rgba(255, 255, 255, 0.95);
    transform: translateY(-1px);
  }

  .tab.active {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    color: #fff;
    box-shadow: 0 8px 20px -5px rgba(74, 158, 255, 0.5),
                0 0 0 1px rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
  }

  .tab.active::before {
    opacity: 0;
  }

  .tab-icon {
    font-size: 1.2rem;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
  }

  /* Content */
  .content {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 2rem;
    flex: 1;
    padding: 1.5rem 2.5rem 2.5rem 2.5rem;
    min-height: 0;
  }

  /* Import Section */
  .import-section {
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.08) 0%, rgba(74, 158, 255, 0.04) 100%);
    border-radius: 16px;
    border: 1px solid rgba(74, 158, 255, 0.15);
    padding: 2rem;
    display: flex;
    align-items: stretch;
    justify-content: flex-start;
    overflow: auto;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 20px -5px rgba(0, 0, 0, 0.3);
  }

  .upload-zone {
    width: 100%;
    min-height: 280px;
    border: 2px dashed rgba(74, 158, 255, 0.3);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.04) 0%, rgba(74, 158, 255, 0.02) 100%);
    position: relative;
    overflow: hidden;
  }

  .upload-zone::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.15) 0%, rgba(126, 214, 255, 0.08) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .upload-zone:hover::before,
  .upload-zone.drag-active::before {
    opacity: 1;
  }

  .upload-zone:hover,
  .upload-zone.drag-active {
    border-color: rgba(74, 158, 255, 0.7);
    transform: translateY(-2px);
    box-shadow: 0 15px 30px -8px rgba(74, 158, 255, 0.3);
  }

  .upload-content {
    text-align: center;
    z-index: 1;
    position: relative;
  }

  .upload-icon {
    font-size: 3.5rem;
    margin-bottom: 1.25rem;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
    opacity: 0.9;
  }

  .upload-content h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.025em;
  }

  .upload-content p {
    margin: 0 0 1.75rem 0;
    color: rgba(255, 255, 255, 0.8);
    font-size: 1rem;
    line-height: 1.5;
  }

  .upload-btn {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    color: #fff;
    border: none;
    padding: 0.875rem 2rem;
    border-radius: 10px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 8px 20px -5px rgba(74, 158, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .upload-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 25px -5px rgba(74, 158, 255, 0.7);
  }

  /* Input Section */
  .input-section {
    width: 100%;
    display: flex;
    flex-direction: column;
  }

  .input-section h3 {
    margin: 0 0 2rem 0;
    font-size: 1.5rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.025em;
  }

  .input-group {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .url-input,
  .api-input,
  .title-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #fff;
    padding: 1rem 1.25rem;
    border-radius: 12px;
    font-size: 1rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
  }

  .url-input:focus,
  .api-input:focus,
  .title-input:focus,
  .text-input:focus {
    outline: none;
    border-color: rgba(74, 158, 255, 0.6);
    background: rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.1);
    transform: translateY(-1px);
  }

  .text-input {
    width: 100%;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #fff;
    padding: 1.25rem;
    border-radius: 12px;
    font-size: 1rem;
    resize: vertical;
    margin-bottom: 1.5rem;
    min-height: 150px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
    font-family: inherit;
    line-height: 1.6;
  }

  .import-btn {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    color: #fff;
    border: none;
    padding: 1rem 2rem;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    white-space: nowrap;
    box-shadow: 0 10px 25px -5px rgba(74, 158, 255, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.2);
    align-self: flex-start;
  }

  .import-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 15px 35px -5px rgba(74, 158, 255, 0.6);
  }

  .import-btn:disabled {
    background: rgba(255, 255, 255, 0.1);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
    opacity: 0.6;
  }

  .help-text {
    margin: 1rem 0 0 0;
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.95rem;
    line-height: 1.5;
  }

  /* Options Panel */
  .options-panel {
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.08) 0%, rgba(74, 158, 255, 0.04) 100%);
    border-radius: 16px;
    border: 1px solid rgba(74, 158, 255, 0.15);
    padding: 1.75rem;
    height: fit-content;
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 20px -5px rgba(0, 0, 0, 0.3);
  }

  .options-panel h4 {
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.025em;
  }

  .option-group {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .toggle-option {
    display: flex;
    align-items: center;
    gap: 1rem;
    cursor: pointer;
    padding: 1rem;
    border-radius: 12px;
    transition: all 0.3s ease;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .toggle-option:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-1px);
  }

  .toggle-option input[type="checkbox"] {
    display: none;
  }

  .toggle {
    width: 48px;
    height: 24px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .toggle::after {
    content: '';
    position: absolute;
    left: 2px;
    top: 2px;
    width: 18px;
    height: 18px;
    background: #fff;
    border-radius: 50%;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .toggle-option input[type="checkbox"]:checked + .toggle {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    border-color: rgba(74, 158, 255, 0.6);
  }

  .toggle-option input[type="checkbox"]:checked + .toggle::after {
    left: 26px;
    background: #fff;
  }

  .toggle-option label {
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
    cursor: pointer;
    flex: 1;
  }

  .confidence-option {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .confidence-option select {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #fff;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-size: 0.95rem;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
    flex: 1;
  }

  .confidence-option select:focus {
    outline: none;
    border-color: rgba(74, 158, 255, 0.6);
    background: rgba(255, 255, 255, 0.08);
  }

  .confidence-option label {
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
    min-width: 100px;
  }

  /* Progress Section */
  .progress-section {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 2rem;
    width: 100%;
    max-height: 300px;
    overflow: hidden;
    position: sticky;
    bottom: 0;
    backdrop-filter: blur(10px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
  }

  .progress-section h4 {
    margin: 0 0 1.5rem 0;
    font-size: 1.25rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.025em;
  }

  .progress-list {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    max-height: 240px;
    overflow: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(74, 158, 255, 0.3) transparent;
  }

  .progress-list::-webkit-scrollbar {
    width: 4px;
  }

  .progress-list::-webkit-scrollbar-track {
    background: transparent;
  }

  .progress-list::-webkit-scrollbar-thumb {
    background: rgba(74, 158, 255, 0.3);
    border-radius: 2px;
  }

  .progress-list::-webkit-scrollbar-thumb:hover {
    background: rgba(74, 158, 255, 0.5);
  }

  .cancel-btn {
    background: transparent;
    color: #ff6b6b;
    border: 1px solid rgba(255, 107, 107, 0.3);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
  }

  .cancel-btn:hover {
    background: rgba(255, 107, 107, 0.1);
    border-color: rgba(255, 107, 107, 0.5);
    transform: translateY(-1px);
  }

  .progress-item {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 1.5rem;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
  }

  .progress-item:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .progress-name {
    font-weight: 700;
    color: #fff;
    font-size: 1rem;
  }

  .progress-type {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    color: #fff;
    padding: 0.375rem 0.75rem;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 4px 12px rgba(74, 158, 255, 0.3);
  }

  .progress-bar {
    width: 100%;
    height: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 1rem;
    position: relative;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4a9eff 0%, #7ed6ff 100%);
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 6px;
    box-shadow: 0 0 10px rgba(74, 158, 255, 0.3);
  }

  .progress-status {
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .status-badge {
    padding: 0.375rem 0.75rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    backdrop-filter: blur(10px);
  }

  .status-step {
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.9rem;
    font-weight: 500;
  }

  /* Inline progress panel inside import-section */
  .inline-progress {
    margin-top: 2rem;
    background: rgba(255, 255, 255, 0.03);
    padding: 1.5rem;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
  }

  .progress-header-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .progress-header-section h4 {
    margin: 0;
    color: #fff;
    font-size: 1.125rem;
  }

  .bulk-actions {
    display: flex;
    gap: 0.75rem;
  }

  .bulk-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    border: 1px solid;
    background: rgba(255, 255, 255, 0.05);
    color: #fff;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .bulk-btn.cancel-all {
    border-color: rgba(255, 107, 107, 0.4);
    color: #ff6b6b;
  }

  .bulk-btn.cancel-all:hover {
    background: rgba(255, 107, 107, 0.1);
    border-color: rgba(255, 107, 107, 0.6);
    transform: translateY(-1px);
  }

  .bulk-btn.reset-stuck {
    border-color: rgba(255, 193, 7, 0.4);
    color: #ffc107;
  }

  .bulk-btn.reset-stuck:hover {
    background: rgba(255, 193, 7, 0.1);
    border-color: rgba(255, 193, 7, 0.6);
    transform: translateY(-1px);
  }

  .progress-bar.large {
    height: 16px;
    position: relative;
  }

  .progress-percent {
    position: absolute;
    right: 12px;
    top: -22px;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 600;
  }

  .view-btn {
    background: rgba(74, 158, 255, 0.2);
    color: #4a9eff;
    border: 1px solid rgba(74, 158, 255, 0.4);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
  }

  .view-btn:hover {
    background: rgba(74, 158, 255, 0.3);
    transform: translateY(-1px);
  }

  .file-details {
    margin-top: 1rem;
    background: rgba(255, 255, 255, 0.03);
    padding: 1.25rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    padding: 0.5rem 0;
  }

  .detail-row:last-child {
    margin-bottom: 0;
  }

  .detail-label {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.6);
    font-weight: 600;
    min-width: 80px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .detail-value {
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.9);
    text-align: right;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
    word-break: break-word;
    max-width: 200px;
    font-weight: 500;
  }

  .detail-value.warning {
    color: #fbbf24;
    font-weight: 700;
  }

  /* Step Indicator */
  .step-indicator {
    margin: 1.5rem 0;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
  }

  .step-progress {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
  }

  .step-dot {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    min-width: 90px;
    padding: 1rem 0.75rem;
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .step-dot.completed {
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.15) 0%, rgba(126, 214, 255, 0.1) 100%);
    border: 1px solid rgba(74, 158, 255, 0.4);
    transform: translateY(-2px);
  }

  .step-dot.current {
    background: linear-gradient(135deg, rgba(74, 158, 255, 0.25) 0%, rgba(126, 214, 255, 0.15) 100%);
    border: 1px solid rgba(74, 158, 255, 0.6);
    animation: pulse 2s infinite;
    transform: translateY(-3px);
    box-shadow: 0 10px 25px -5px rgba(74, 158, 255, 0.4);
  }

  .step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: rgba(255, 255, 255, 0.2);
    color: #fff;
    border-radius: 50%;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .step-dot.completed .step-number {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    border-color: rgba(74, 158, 255, 0.4);
    box-shadow: 0 4px 12px rgba(74, 158, 255, 0.3);
  }

  .step-dot.current .step-number {
    background: linear-gradient(135deg, #4a9eff 0%, #7ed6ff 100%);
    border-color: rgba(74, 158, 255, 0.6);
    box-shadow: 0 6px 20px rgba(74, 158, 255, 0.5);
  }

  .step-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
    line-height: 1.3;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .step-dot.completed .step-label {
    color: rgba(74, 158, 255, 0.9);
    font-weight: 600;
  }

  .step-dot.current .step-label {
    color: rgba(74, 158, 255, 1);
    font-weight: 700;
  }

  @keyframes pulse {
    0%, 100% { 
      opacity: 1; 
      transform: translateY(-3px) scale(1);
    }
    50% { 
      opacity: 0.8; 
      transform: translateY(-3px) scale(1.02);
    }
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-10px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  /* Add entrance animations */
  .import-container {
    animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .progress-item {
    animation: slideIn 0.4s ease-out;
  }

  .step-dot {
    animation: fadeInUp 0.4s ease-out;
  }

  /* Responsive Design */
  @media (max-width: 1200px) {
    .content {
      grid-template-columns: 1fr 280px;
      gap: 1.5rem;
    }
    
    .import-container {
      width: 95vw;
      margin: 0;
    }
  }

  @media (max-width: 968px) {
    .content {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }
    
    .header {
      padding: 1.75rem 2rem 1.25rem 2rem;
      flex-direction: column;
      align-items: flex-start;
      gap: 1.25rem;
    }
    
    .stats {
      gap: 1.5rem;
      align-self: stretch;
      justify-content: space-around;
    }
    
    .tabs {
      margin: 0 2rem;
      flex-wrap: wrap;
    }
    
    .tab {
      flex: 1 1 45%;
      min-width: 110px;
    }
    
    .content {
      padding: 0 2rem 2rem 2rem;
    }
  }

  @media (max-width: 640px) {
    .import-container {
      width: 100vw;
      border-radius: 12px;
      min-height: 85vh;
    }
    
    .header {
      padding: 1.5rem;
    }
    
    .title-section h2 {
      font-size: 1.6rem;
    }
    
    .stats {
      flex-direction: column;
      gap: 1rem;
    }
    
    .stat {
      padding: 0.875rem 1rem;
    }
    
    .tabs {
      margin: 0 1.5rem;
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .tab {
      flex: none;
      padding: 0.875rem;
    }
    
    .content {
      padding: 0 1.5rem 1.5rem 1.5rem;
    }
    
    .import-section,
    .options-panel {
      padding: 1.5rem;
    }
    
    .upload-zone {
      min-height: 220px;
    }
    
    .upload-icon {
      font-size: 2.75rem;
    }
  }

  /* Enhanced focus states for accessibility */
  .tab:focus,
  .upload-btn:focus,
  .import-btn:focus,
  .cancel-btn:focus,
  .view-btn:focus {
    outline: 2px solid rgba(74, 158, 255, 0.6);
    outline-offset: 2px;
  }

  /* Smooth transitions for all interactive elements */
  * {
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Custom scrollbar styling */
  .import-section::-webkit-scrollbar,
  .progress-section::-webkit-scrollbar {
    width: 6px;
  }

  .import-section::-webkit-scrollbar-track,
  .progress-section::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }

  .import-section::-webkit-scrollbar-thumb,
  .progress-section::-webkit-scrollbar-thumb {
    background: rgba(74, 158, 255, 0.4);
    border-radius: 3px;
  }

  .import-section::-webkit-scrollbar-thumb:hover,
  .progress-section::-webkit-scrollbar-thumb:hover {
    background: rgba(74, 158, 255, 0.6);
  }
</style>
