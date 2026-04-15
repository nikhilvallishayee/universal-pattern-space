<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { fade, slide, scale } from 'svelte/transition';
  import { GödelOSAPI } from '../../utils/api.js';
  import { API_BASE_URL } from '../../config.js';

  // Reactive stores
  let jobs = writable([]);
  let selectedJob = writable(null);
  let preflightEstimates = writable(null);
  let selectedAnalysisLevel = writable('balanced');
  let showPreflightModal = writable(false);
  let uploadFile = null;

  // UI state
  let dragActive = false;
  let loading = false;
  let error = null;
  let refreshInterval;
  let fileInput;

  // Analysis level configurations
  const analysisLevels = {
    fast: {
      name: 'Fast',
      description: 'Quick processing with basic chunking',
      icon: '⚡',
      color: '#10b981',
      features: ['Basic metadata', 'Quick embedding', 'Simhash dedup ≥0.92']
    },
    balanced: {
      name: 'Balanced',
      description: 'Optimal balance of speed and quality',
      icon: '⚖️',
      color: '#3b82f6',
      features: ['Heading tags', 'Layout awareness', 'Simhash dedup ≥0.88']
    },
    deep: {
      name: 'Deep',
      description: 'Comprehensive analysis with full features',
      icon: '🔬',
      color: '#8b5cf6',
      features: ['Rich tagging', 'Semantic chunking', 'Simhash dedup ≥0.85']
    }
  };

  // Status colors and icons
  const statusConfig = {
    queued: { color: '#6b7280', icon: '⏳', label: 'Queued' },
    processing: { color: '#3b82f6', icon: '⚙️', label: 'Processing' },
    completed: { color: '#10b981', icon: '✅', label: 'Completed' },
    failed: { color: '#ef4444', icon: '❌', label: 'Failed' },
    cancelled: { color: '#f59e0b', icon: '⏹️', label: 'Cancelled' }
  };

  onMount(async () => {
    await loadJobs();
    // Removed aggressive 2-second polling - use manual refresh or WebSocket events for job updates
  });

  onDestroy(() => {
    // No polling interval to clear - manual refresh only
  });

  async function loadJobs() {
    try {
      const response = await GödelOSAPI.get('/api/import/jobs');
      jobs.set(response.jobs || []);
    } catch (err) {
      console.error('Failed to load jobs:', err);
      error = 'Failed to load jobs';
    }
  }

  async function handleFileSelect(event) {
    const files = event.target.files;
    if (files && files.length > 0) {
      uploadFile = files[0];
      await showPreflight();
    }
  }

  async function handleFileDrop(event) {
    event.preventDefault();
    dragActive = false;
    
    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      uploadFile = files[0];
      await showPreflight();
    }
  }

  async function showPreflight() {
    if (!uploadFile) return;
    
    loading = true;
    error = null;
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      
      const response = await fetch(`${API_BASE_URL}/api/import/preflight`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      preflightEstimates.set(data.estimates);
      showPreflightModal.set(true);
    } catch (err) {
      console.error('Preflight failed:', err);
      error = `Preflight estimation failed: ${err.message}`;
    } finally {
      loading = false;
    }
  }

  async function startJob() {
    if (!uploadFile) return;
    
    loading = true;
    error = null;
    
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('analysis_level', $selectedAnalysisLevel);
      
      const response = await fetch(`${API_BASE_URL}/api/import/jobs`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Job started:', data);
      
      // Reset form
      uploadFile = null;
      if (fileInput) fileInput.value = '';
      showPreflightModal.set(false);
      
      // Refresh jobs list
      await loadJobs();
    } catch (err) {
      console.error('Failed to start job:', err);
      error = `Failed to start job: ${err.message}`;
    } finally {
      loading = false;
    }
  }

  async function cancelJob(jobId) {
    try {
      await GödelOSAPI.post(`/api/import/jobs/${jobId}/cancel`);
      await loadJobs();
    } catch (err) {
      console.error('Failed to cancel job:', err);
      error = `Failed to cancel job: ${err.message}`;
    }
  }

  function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '--';
    
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const secs = Math.round(seconds % 60);
      return `${minutes}m ${secs}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }

  function formatFileSize(bytes) {
    if (!bytes) return '--';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  }

  function getProgressColor(percent) {
    if (percent < 30) return '#ef4444';
    if (percent < 70) return '#f59e0b';
    return '#10b981';
  }
</script>

<div class="jobs-container">
  <!-- Header -->
  <div class="header">
    <h1>
      <span class="icon">📥</span>
      Knowledge Ingestion Jobs
    </h1>
    <p class="subtitle">
      Adaptive pipeline with CPU optimization and predictive ETAs
    </p>
  </div>

  <!-- Error display -->
  {#if error}
    <div class="error-banner" transition:slide>
      <span class="error-icon">⚠️</span>
      {error}
      <button on:click={() => error = null} class="error-close">×</button>
    </div>
  {/if}

  <!-- File upload area -->
  <div 
    class="upload-area"
    class:drag-active={dragActive}
    on:dragover|preventDefault={() => dragActive = true}
    on:dragleave={() => dragActive = false}
    on:drop={handleFileDrop}
  >
    <input 
      bind:this={fileInput}
      type="file" 
      accept=".pdf,.docx,.txt"
      on:change={handleFileSelect}
      hidden
    />
    
    <div class="upload-content">
      <div class="upload-icon">📄</div>
      <h3>Drop files here or click to upload</h3>
      <p>Supports PDF, DOCX, and TXT files up to 100MB</p>
      <button 
        class="upload-button"
        on:click={() => fileInput?.click()}
        disabled={loading}
      >
        {loading ? 'Processing...' : 'Select Files'}
      </button>
    </div>
  </div>

  <!-- Jobs list -->
  <div class="jobs-section">
    <div class="section-header">
      <h2>Active Jobs</h2>
      <div class="job-stats">
        {$jobs.filter(j => j.status === 'processing').length} processing,
        {$jobs.filter(j => j.status === 'queued').length} queued,
        {$jobs.filter(j => j.status === 'completed').length} completed
      </div>
    </div>

    {#if $jobs.length === 0}
      <div class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>No active jobs</h3>
        <p>Upload a file to start your first ingestion job</p>
      </div>
    {:else}
      <div class="jobs-grid">
        {#each $jobs as job (job.job_id)}
          <div 
            class="job-card"
            class:selected={$selectedJob?.job_id === job.job_id}
            on:click={() => selectedJob.set(job)}
            transition:fade={{ duration: 200 }}
          >
            <!-- Job header -->
            <div class="job-header">
              <div class="job-title">
                <span 
                  class="status-indicator"
                  style="background-color: {statusConfig[job.status].color}"
                ></span>
                <span class="job-id">Job {job.job_id.slice(-8)}</span>
                <span class="analysis-level-badge" style="background-color: {analysisLevels[job.analysis_level].color}20; color: {analysisLevels[job.analysis_level].color}">
                  {analysisLevels[job.analysis_level].icon} {analysisLevels[job.analysis_level].name}
                </span>
              </div>
              <div class="job-actions">
                {#if job.status === 'processing' || job.status === 'queued'}
                  <button 
                    class="action-button cancel"
                    on:click|stopPropagation={() => cancelJob(job.job_id)}
                    title="Cancel job"
                  >
                    ⏹️
                  </button>
                {/if}
              </div>
            </div>

            <!-- Progress bar -->
            <div class="progress-section">
              <div class="progress-bar">
                <div 
                  class="progress-fill"
                  style="width: {job.progress_percent}%; background-color: {getProgressColor(job.progress_percent)}"
                ></div>
              </div>
              <div class="progress-text">
                {job.progress_percent.toFixed(1)}% ({job.processed_chunks}/{job.total_chunks} chunks)
              </div>
            </div>

            <!-- Job details -->
            <div class="job-details">
              <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="detail-value status-{job.status}">
                  {statusConfig[job.status].icon} {statusConfig[job.status].label}
                </span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Elapsed:</span>
                <span class="detail-value">{formatDuration(job.elapsed_time_seconds)}</span>
              </div>
              
              {#if job.eta_seconds}
                <div class="detail-row">
                  <span class="detail-label">ETA:</span>
                  <span class="detail-value">{formatDuration(job.eta_seconds)}</span>
                </div>
              {/if}
              
              {#if job.error_message}
                <div class="detail-row error">
                  <span class="detail-label">Error:</span>
                  <span class="detail-value">{job.error_message}</span>
                </div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Preflight Modal -->
{#if $showPreflightModal && $preflightEstimates}
  <div class="modal-overlay" transition:fade>
    <div class="modal" transition:scale>
      <div class="modal-header">
        <h2>📊 Preflight Analysis</h2>
        <button 
          class="modal-close"
          on:click={() => showPreflightModal.set(false)}
        >
          ×
        </button>
      </div>
      
      <div class="modal-content">
        <p class="modal-subtitle">
          Choose your analysis level. Each provides different speed vs. quality tradeoffs.
        </p>
        
        <div class="analysis-levels">
          {#each Object.entries(analysisLevels) as [level, config]}
            <div 
              class="analysis-level-card"
              class:selected={$selectedAnalysisLevel === level}
              on:click={() => selectedAnalysisLevel.set(level)}
            >
              <div class="level-header">
                <span class="level-icon">{config.icon}</span>
                <span class="level-name">{config.name}</span>
              </div>
              
              <p class="level-description">{config.description}</p>
              
              <div class="level-features">
                {#each config.features as feature}
                  <span class="feature-tag">{feature}</span>
                {/each}
              </div>
              
              {#if $preflightEstimates[level]}
                <div class="level-estimates">
                  <div class="estimate-row">
                    <span>Chunks:</span>
                    <span>{$preflightEstimates[level].estimated_chunks.toLocaleString()}</span>
                  </div>
                  <div class="estimate-row">
                    <span>ETA (50%):</span>
                    <span>{$preflightEstimates[level].eta_p50_human}</span>
                  </div>
                  <div class="estimate-row">
                    <span>ETA (90%):</span>
                    <span>{$preflightEstimates[level].eta_p90_human}</span>
                  </div>
                  <div class="estimate-row">
                    <span>Memory:</span>
                    <span>{Math.round($preflightEstimates[level].memory_usage_mb)} MB</span>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
      
      <div class="modal-footer">
        <button 
          class="button secondary"
          on:click={() => showPreflightModal.set(false)}
        >
          Cancel
        </button>
        <button 
          class="button primary"
          on:click={startJob}
          disabled={loading}
        >
          {loading ? 'Starting...' : 'Start Job'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .jobs-container {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  }

  .header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 0.5rem 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
  }

  .header .icon {
    font-size: 2rem;
  }

  .subtitle {
    color: #6b7280;
    font-size: 1.1rem;
    margin: 0;
  }

  .error-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .error-icon {
    font-size: 1.25rem;
  }

  .error-close {
    background: none;
    border: none;
    color: #dc2626;
    font-size: 1.5rem;
    cursor: pointer;
    margin-left: auto;
    padding: 0;
    width: 1.5rem;
    height: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .upload-area {
    border: 2px dashed #d1d5db;
    border-radius: 1rem;
    padding: 3rem;
    text-align: center;
    margin-bottom: 3rem;
    transition: all 0.2s ease;
    background: #fafafa;
  }

  .upload-area:hover,
  .upload-area.drag-active {
    border-color: #3b82f6;
    background: #eff6ff;
  }

  .upload-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .upload-icon {
    font-size: 3rem;
    opacity: 0.7;
  }

  .upload-content h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #374151;
    margin: 0;
  }

  .upload-content p {
    color: #6b7280;
    margin: 0;
  }

  .upload-button {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .upload-button:hover:not(:disabled) {
    background: #2563eb;
  }

  .upload-button:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .jobs-section {
    margin-top: 3rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .section-header h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .job-stats {
    color: #6b7280;
    font-size: 0.875rem;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #6b7280;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    margin: 0 0 0.5rem 0;
  }

  .empty-state p {
    margin: 0;
  }

  .jobs-grid {
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  }

  .job-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .job-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .job-card.selected {
    border-color: #3b82f6;
    background: #eff6ff;
  }

  .job-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .job-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .status-indicator {
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    display: inline-block;
  }

  .job-id {
    font-weight: 600;
    color: #1f2937;
  }

  .analysis-level-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    font-weight: 500;
  }

  .job-actions {
    display: flex;
    gap: 0.5rem;
  }

  .action-button {
    background: none;
    border: 1px solid #d1d5db;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.2s;
  }

  .action-button.cancel:hover {
    background: #fef2f2;
    border-color: #fecaca;
  }

  .progress-section {
    margin-bottom: 1rem;
  }

  .progress-bar {
    width: 100%;
    height: 0.5rem;
    background: #f3f4f6;
    border-radius: 0.25rem;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }

  .progress-fill {
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 0.25rem;
  }

  .progress-text {
    font-size: 0.875rem;
    color: #6b7280;
    text-align: center;
  }

  .job-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.875rem;
  }

  .detail-row.error {
    color: #dc2626;
  }

  .detail-label {
    color: #6b7280;
    font-weight: 500;
  }

  .detail-value {
    color: #1f2937;
    font-weight: 600;
  }

  .detail-value.status-completed {
    color: #10b981;
  }

  .detail-value.status-failed {
    color: #ef4444;
  }

  .detail-value.status-processing {
    color: #3b82f6;
  }

  /* Modal styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 1rem;
    max-width: 900px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .modal-header h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6b7280;
    padding: 0;
    width: 2rem;
    height: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-content {
    padding: 1.5rem;
  }

  .modal-subtitle {
    color: #6b7280;
    margin: 0 0 1.5rem 0;
    text-align: center;
  }

  .analysis-levels {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }

  .analysis-level-card {
    border: 2px solid #e5e7eb;
    border-radius: 0.75rem;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .analysis-level-card:hover {
    border-color: #3b82f6;
  }

  .analysis-level-card.selected {
    border-color: #3b82f6;
    background: #eff6ff;
  }

  .level-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }

  .level-icon {
    font-size: 1.5rem;
  }

  .level-name {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1f2937;
  }

  .level-description {
    color: #6b7280;
    margin: 0 0 1rem 0;
    font-size: 0.875rem;
  }

  .level-features {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .feature-tag {
    background: #f3f4f6;
    color: #374151;
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
  }

  .level-estimates {
    border-top: 1px solid #e5e7eb;
    padding-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .estimate-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.875rem;
  }

  .estimate-row span:first-child {
    color: #6b7280;
  }

  .estimate-row span:last-child {
    font-weight: 600;
    color: #1f2937;
  }

  .modal-footer {
    padding: 1.5rem;
    border-top: 1px solid #e5e7eb;
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
  }

  .button {
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }

  .button.primary {
    background: #3b82f6;
    color: white;
  }

  .button.primary:hover:not(:disabled) {
    background: #2563eb;
  }

  .button.primary:disabled {
    background: #9ca3af;
    cursor: not-allowed;
  }

  .button.secondary {
    background: #f9fafb;
    color: #374151;
    border: 1px solid #d1d5db;
  }

  .button.secondary:hover {
    background: #f3f4f6;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .jobs-container {
      padding: 1rem;
    }
    
    .header h1 {
      font-size: 2rem;
    }
    
    .jobs-grid {
      grid-template-columns: 1fr;
    }
    
    .analysis-levels {
      grid-template-columns: 1fr;
    }
    
    .modal {
      width: 95%;
      margin: 1rem;
    }
    
    .section-header {
      flex-direction: column;
      gap: 0.5rem;
      align-items: flex-start;
    }
  }

  @media (max-width: 480px) {
    .upload-area {
      padding: 2rem 1rem;
    }
    
    .job-card {
      padding: 1rem;
    }
    
    .modal-content {
      padding: 1rem;
    }
    
    .modal-footer {
      padding: 1rem;
      flex-direction: column;
    }
    
    .button {
      width: 100%;
    }
  }
</style>