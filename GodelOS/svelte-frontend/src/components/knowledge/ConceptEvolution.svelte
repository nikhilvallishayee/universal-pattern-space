<script>
  import { onMount } from 'svelte';
  import { knowledgeState } from '../../stores/cognitive.js';
  import { GödelOSAPI } from '../../utils/api.js';

  let evolutionData = [];
  let loading = true;
  let selectedTimeframe = '24h';
  let error = null;

  const timeframes = [
    { value: '1h', label: '1 Hour' },
    { value: '24h', label: '24 Hours' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' }
  ];

  onMount(() => {
    loadEvolutionData();
  });

  async function loadEvolutionData() {
    loading = true;
    error = null;
    
    try {
      // Try to fetch real evolution data from backend
      const apiData = await GödelOSAPI.fetchEvolutionData(selectedTimeframe);
      
      if (apiData && apiData.length > 0) {
        // Use real data from backend
        evolutionData = apiData.map(item => ({
          ...item,
          id: item.id || item.concept_id,
          name: item.name || item.concept_name,
          category: item.category || item.type || 'Core',
          change: item.change || item.growth_rate || 0,
          connections: item.connections || item.connection_count || 0,
          strength: item.strength || item.confidence || 0.5,
          timestamp: item.timestamp ? new Date(item.timestamp) : new Date()
        }));
        
        console.log('✅ Loaded real evolution data:', evolutionData);
      } else {
        // No data available
        console.error('❌ No evolution data available from backend');
        evolutionData = [];
      }
      
    } catch (err) {
      console.error('❌ Failed to load evolution data:', err);
      error = err.message;
      evolutionData = [];
    } finally {
      loading = false;
    }
  }

  function getCategoryColor(category) {
    const colors = {
      'Core': '#4fc3f7',
      'Logic': '#81c784',
      'Meta': '#ffb74d',
      'System': '#e57373'
    };
    return colors[category] || '#90a4ae';
  }

  function formatTimestamp(timestamp) {
    return new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(
      Math.floor((timestamp - Date.now()) / (1000 * 60 * 60)),
      'hour'
    );
  }

  $: {
    if (selectedTimeframe) {
      loadEvolutionData();
    }
  }
</script>

<div class="concept-evolution">
  <div class="evolution-header">
    <h3>Concept Evolution</h3>
    <select bind:value={selectedTimeframe} class="timeframe-selector">
      {#each timeframes as timeframe}
        <option value={timeframe.value}>{timeframe.label}</option>
      {/each}
    </select>
  </div>

  {#if loading}
    <div class="loading-state">
      <div class="spinner"></div>
      <span>Loading evolution data...</span>
    </div>
  {:else}
    <div class="evolution-content">
      <div class="evolution-stats">
        <div class="stat-item">
          <span class="stat-label">Active Concepts</span>
          <span class="stat-value">{evolutionData.length}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Total Connections</span>
          <span class="stat-value">{evolutionData.reduce((sum, item) => sum + item.connections, 0)}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Growth Rate</span>
          <span class="stat-value positive">+{Math.round(evolutionData.reduce((sum, item) => sum + item.change, 0) / evolutionData.length)}%</span>
        </div>
      </div>

      <div class="evolution-list">
        {#each evolutionData as concept}
          <div class="concept-item">
            <div class="concept-header">
              <div class="concept-info">
                <span class="concept-name">{concept.name}</span>
                <span class="concept-category" style="color: {getCategoryColor(concept.category)}">
                  {concept.category}
                </span>
              </div>
              <div class="concept-change {concept.change > 0 ? 'positive' : 'negative'}">
                {concept.change > 0 ? '+' : ''}{concept.change}%
              </div>
            </div>
            
            <div class="concept-details">
              <div class="detail-row">
                <span class="detail-label">Connections:</span>
                <span class="detail-value">{concept.connections}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Strength:</span>
                <div class="strength-bar">
                  <div class="strength-fill" style="width: {concept.strength * 100}%"></div>
                </div>
              </div>
              <div class="detail-row">
                <span class="detail-label">Updated:</span>
                <span class="detail-value">{formatTimestamp(concept.timestamp)}</span>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .concept-evolution {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .evolution-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .evolution-header h3 {
    margin: 0;
    font-size: 1.2rem;
    color: #64b5f6;
  }

  .timeframe-selector {
    background: rgba(100, 181, 246, 0.1);
    border: 1px solid rgba(100, 181, 246, 0.3);
    color: #e1e5e9;
    padding: 0.5rem;
    border-radius: 6px;
    font-size: 0.9rem;
  }

  .timeframe-selector option {
    background: #1a1a2e;
    color: #e1e5e9;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    gap: 1rem;
    opacity: 0.7;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid rgba(100, 181, 246, 0.3);
    border-top: 3px solid #64b5f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .evolution-content {
    flex: 1;
    overflow-y: auto;
  }

  .evolution-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .stat-item {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.75rem;
    border-radius: 8px;
    text-align: center;
  }

  .stat-label {
    display: block;
    font-size: 0.8rem;
    opacity: 0.7;
    margin-bottom: 0.25rem;
  }

  .stat-value {
    display: block;
    font-size: 1.2rem;
    font-weight: 600;
    color: #64b5f6;
  }

  .stat-value.positive {
    color: #81c784;
  }

  .evolution-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .concept-item {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(100, 181, 246, 0.2);
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s ease;
  }

  .concept-item:hover {
    border-color: rgba(100, 181, 246, 0.4);
    background: rgba(0, 0, 0, 0.4);
  }

  .concept-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .concept-info {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .concept-name {
    font-weight: 600;
    color: #e1e5e9;
    font-size: 1rem;
  }

  .concept-category {
    font-size: 0.8rem;
    opacity: 0.8;
  }

  .concept-change {
    font-weight: 600;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .concept-change.positive {
    color: #81c784;
    background: rgba(129, 199, 132, 0.1);
  }

  .concept-change.negative {
    color: #e57373;
    background: rgba(229, 115, 115, 0.1);
  }

  .concept-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    font-size: 0.9rem;
    opacity: 0.7;
  }

  .detail-value {
    font-size: 0.9rem;
    color: #64b5f6;
  }

  .strength-bar {
    width: 60px;
    height: 4px;
    background: rgba(100, 181, 246, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .strength-fill {
    height: 100%;
    background: #64b5f6;
    transition: width 0.3s ease;
  }
</style>