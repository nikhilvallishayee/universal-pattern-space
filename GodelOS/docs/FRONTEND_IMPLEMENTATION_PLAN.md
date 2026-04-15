# GödelOS Frontend Implementation Plan
## Bridging Backend-Frontend Gaps

Based on the comprehensive E2E testing results, this document provides specific implementation steps to bridge the identified gaps between backend capabilities and frontend implementation.

## 🎯 Implementation Phases

### Phase 1: Backend API Fixes (Week 1)

#### 1.1 Fix Knowledge Import Validation Issues

**Problem**: All import endpoints return 422 validation errors
**Root Cause**: Request payload structure mismatch

**Files to Fix**:
- `backend/main.py` - Import endpoint handlers
- `backend/knowledge_models.py` - Pydantic models

**Specific Fixes Needed**:

```python
# Fix POST /api/knowledge endpoint
# Current test payload: {"concept": "test_concept", "definition": "test definition", "category": "test"}
# Backend expects: {"content": "...", "title": "...", ...}

# Fix POST /api/knowledge/import/url endpoint  
# Current test payload: {"url": "https://example.com", "category": "web"}
# Backend expects: URLImportRequest model structure

# Fix POST /api/knowledge/import/wikipedia endpoint
# Current test payload: {"topic": "artificial intelligence", "category": "encyclopedia"}
# Backend expects: WikipediaImportRequest model structure
```

#### 1.2 Fix Knowledge Search Endpoint

**Problem**: GET /api/knowledge/search returns 422 validation error
**Solution**: Add proper query parameter handling

```python
# In backend/main.py, fix the search endpoint:
@app.get("/api/knowledge/search")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, description="Number of results")
):
    # Implementation here
```

#### 1.3 Fix Transparency Session Management

**Problem**: Several transparency endpoints return 404/500 errors
**Files to Fix**:
- `backend/cognitive_transparency_integration.py`

### Phase 2: Essential Frontend Components (Week 2-3)

#### 2.1 Implement Transparency Dashboard

**New Component**: `src/components/transparency/TransparencyDashboard.svelte`

```svelte
<script>
  import { onMount } from 'svelte';
  import { GödelOSAPI } from '../../utils/api.js';
  
  let activeSessions = [];
  let transparencyStats = {};
  let isLoading = true;
  
  onMount(async () => {
    await loadDashboardData();
  });
  
  async function loadDashboardData() {
    try {
      const [sessions, stats] = await Promise.all([
        GödelOSAPI.get('/api/transparency/sessions/active'),
        GödelOSAPI.get('/api/transparency/statistics')
      ]);
      
      activeSessions = sessions.data || [];
      transparencyStats = stats.data || {};
      isLoading = false;
    } catch (error) {
      console.error('Failed to load transparency dashboard:', error);
      isLoading = false;
    }
  }
</script>

<div class="transparency-dashboard">
  {#if isLoading}
    <div class="loading">Loading transparency data...</div>
  {:else}
    <div class="stats-grid">
      <div class="stat-card">
        <h3>Active Sessions</h3>
        <span class="stat-value">{activeSessions.length}</span>
      </div>
      <!-- More stats cards -->
    </div>
    
    <div class="sessions-list">
      <h3>Active Reasoning Sessions</h3>
      {#each activeSessions as session}
        <div class="session-card">
          <h4>{session.query}</h4>
          <p>Started: {new Date(session.start_time).toLocaleString()}</p>
          <button on:click={() => viewSession(session.id)}>View Details</button>
        </div>
      {/each}
    </div>
  {/if}
</div>
```

#### 2.2 Implement Knowledge Search Interface

**Enhancement**: Add search functionality to existing `KnowledgeGraph.svelte`

```svelte
<!-- Add to existing KnowledgeGraph.svelte -->
<script>
  // ...existing imports
  
  let searchQuery = '';
  let searchResults = [];
  let searchCategory = '';
  
  async function performSearch() {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await GödelOSAPI.get('/api/knowledge/search', {
        params: {
          query: searchQuery,
          category: searchCategory || undefined,
          limit: 20
        }
      });
      
      searchResults = response.data.results || [];
    } catch (error) {
      console.error('Search failed:', error);
    }
  }
</script>

<!-- Add search interface -->
<div class="search-panel">
  <div class="search-form">
    <input 
      bind:value={searchQuery} 
      placeholder="Search knowledge base..."
      on:keydown={(e) => e.key === 'Enter' && performSearch()}
    />
    <select bind:value={searchCategory}>
      <option value="">All Categories</option>
      <option value="concept">Concepts</option>
      <option value="document">Documents</option>
      <option value="web">Web Content</option>
    </select>
    <button on:click={performSearch}>Search</button>
  </div>
  
  {#if searchResults.length > 0}
    <div class="search-results">
      {#each searchResults as result}
        <div class="result-item" on:click={() => selectKnowledgeItem(result)}>
          <h4>{result.title}</h4>
          <p>{result.summary}</p>
          <span class="category">{result.category}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>
```

#### 2.3 Enhance Smart Import with Progress Tracking

**Enhancement**: Add progress tracking to existing `SmartImport.svelte`

```svelte
<!-- Add to existing SmartImport.svelte -->
<script>
  // ...existing imports
  
  let activeImports = new Map();
  let importProgress = {};
  
  async function startImport(importData) {
    try {
      const response = await GödelOSAPI.post('/api/knowledge/import/url', importData);
      const importId = response.data.import_id;
      
      // Store active import
      activeImports.set(importId, {
        id: importId,
        type: 'url',
        status: 'started',
        data: importData
      });
      
      // Start progress monitoring
      monitorImportProgress(importId);
      
    } catch (error) {
      console.error('Import failed:', error);
    }
  }
  
  async function monitorImportProgress(importId) {
    const checkProgress = async () => {
      try {
        const response = await GödelOSAPI.get(`/api/knowledge/import/progress/${importId}`);
        importProgress[importId] = response.data;
        
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          activeImports.delete(importId);
          return;
        }
        
        // Continue monitoring
        setTimeout(checkProgress, 2000);
      } catch (error) {
        console.error('Failed to get import progress:', error);
        activeImports.delete(importId);
      }
    };
    
    checkProgress();
  }
</script>

<!-- Add progress tracking UI -->
{#if activeImports.size > 0}
  <div class="import-progress">
    <h3>Active Imports</h3>
    {#each [...activeImports.values()] as importItem}
      <div class="progress-item">
        <div class="import-info">
          <h4>{importItem.data.url || importItem.data.topic || 'Import'}</h4>
          <p>Status: {importProgress[importItem.id]?.status || 'Starting...'}</p>
        </div>
        
        {#if importProgress[importItem.id]?.progress}
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              style="width: {importProgress[importItem.id].progress}%"
            ></div>
          </div>
        {/if}
        
        <button on:click={() => cancelImport(importItem.id)}>Cancel</button>
      </div>
    {/each}
  </div>
{/if}
```

### Phase 3: Advanced Transparency Features (Week 4-5)

#### 3.1 Implement Reasoning Session Viewer

**New Component**: `src/components/transparency/ReasoningSessionViewer.svelte`

```svelte
<script>
  import { onMount, onDestroy } from 'svelte';
  import { GödelOSAPI } from '../../utils/api.js';
  
  export let sessionId;
  
  let sessionTrace = null;
  let sessionStats = null;
  let isLoading = true;
  let pollInterval;
  
  onMount(async () => {
    await loadSessionData();
    
    // Poll for updates if session is active
    pollInterval = setInterval(loadSessionData, 3000);
  });
  
  onDestroy(() => {
    if (pollInterval) clearInterval(pollInterval);
  });
  
  async function loadSessionData() {
    try {
      const [trace, stats] = await Promise.all([
        GödelOSAPI.get(`/api/transparency/session/${sessionId}/trace`),
        GödelOSAPI.get(`/api/transparency/session/${sessionId}/statistics`)
      ]);
      
      sessionTrace = trace.data;
      sessionStats = stats.data;
      isLoading = false;
    } catch (error) {
      console.error('Failed to load session data:', error);
      isLoading = false;
    }
  }
</script>

<div class="reasoning-session-viewer">
  {#if isLoading}
    <div class="loading">Loading reasoning trace...</div>
  {:else if sessionTrace}
    <div class="session-header">
      <h2>Reasoning Session: {sessionTrace.query}</h2>
      <div class="session-meta">
        <span>Started: {new Date(sessionTrace.start_time).toLocaleString()}</span>
        <span>Status: {sessionTrace.status}</span>
      </div>
    </div>
    
    <div class="reasoning-steps">
      {#each sessionTrace.steps as step, index}
        <div class="step" class:active={step.status === 'active'}>
          <div class="step-header">
            <span class="step-number">{index + 1}</span>
            <h3>{step.type}</h3>
            <span class="step-status">{step.status}</span>
          </div>
          
          <div class="step-content">
            <p>{step.description}</p>
            
            {#if step.reasoning}
              <div class="reasoning-detail">
                <h4>Reasoning Process:</h4>
                <p>{step.reasoning}</p>
              </div>
            {/if}
            
            {#if step.confidence}
              <div class="confidence-meter">
                <span>Confidence: {(step.confidence * 100).toFixed(1)}%</span>
                <div class="confidence-bar">
                  <div class="confidence-fill" style="width: {step.confidence * 100}%"></div>
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
    
    {#if sessionStats}
      <div class="session-statistics">
        <h3>Session Statistics</h3>
        <div class="stats-grid">
          <div class="stat">
            <label>Total Steps:</label>
            <span>{sessionStats.total_steps}</span>
          </div>
          <div class="stat">
            <label>Average Confidence:</label>
            <span>{(sessionStats.average_confidence * 100).toFixed(1)}%</span>
          </div>
          <div class="stat">
            <label>Processing Time:</label>
            <span>{sessionStats.processing_time}ms</span>
          </div>
        </div>
      </div>
    {/if}
  {:else}
    <div class="error">Failed to load reasoning session data</div>
  {/if}
</div>
```

#### 3.2 Implement Provenance Tracking Interface

**New Component**: `src/components/transparency/ProvenanceTracker.svelte`

```svelte
<script>
  import { onMount } from 'svelte';
  import { GödelOSAPI } from '../../utils/api.js';
  
  let provenanceData = null;
  let selectedTarget = '';
  let provenanceHistory = [];
  let confidenceHistory = [];
  
  async function queryProvenance() {
    if (!selectedTarget) return;
    
    try {
      const [attribution, confidence] = await Promise.all([
        GödelOSAPI.get(`/api/transparency/provenance/attribution/${selectedTarget}`),
        GödelOSAPI.get(`/api/transparency/provenance/confidence-history/${selectedTarget}`)
      ]);
      
      provenanceHistory = attribution.data.history || [];
      confidenceHistory = confidence.data.history || [];
    } catch (error) {
      console.error('Failed to query provenance:', error);
    }
  }
</script>

<div class="provenance-tracker">
  <div class="query-form">
    <h2>Provenance Tracking</h2>
    <div class="form-group">
      <label for="target-id">Target ID:</label>
      <input 
        id="target-id"
        bind:value={selectedTarget} 
        placeholder="Enter knowledge item ID"
      />
      <button on:click={queryProvenance}>Track Provenance</button>
    </div>
  </div>
  
  {#if provenanceHistory.length > 0}
    <div class="provenance-results">
      <h3>Provenance Chain</h3>
      <div class="provenance-chain">
        {#each provenanceHistory as item}
          <div class="provenance-item">
            <h4>{item.source_type}</h4>
            <p>{item.description}</p>
            <div class="metadata">
              <span>Created: {new Date(item.created_at).toLocaleString()}</span>
              <span>Confidence: {(item.confidence * 100).toFixed(1)}%</span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
  
  {#if confidenceHistory.length > 0}
    <div class="confidence-timeline">
      <h3>Confidence Evolution</h3>
      <!-- Add confidence chart visualization here -->
    </div>
  {/if}
</div>
```

### Phase 4: Integration and Enhancement (Week 6)

#### 4.1 Update Main App Component

**Enhancement**: Integrate new components into `App.svelte`

```svelte
<!-- Add to existing App.svelte -->
<script>
  // ...existing imports
  import TransparencyDashboard from './components/transparency/TransparencyDashboard.svelte';
  import ReasoningSessionViewer from './components/transparency/ReasoningSessionViewer.svelte';
  import ProvenanceTracker from './components/transparency/ProvenanceTracker.svelte';
  
  // ...existing code
  
  let showTransparencyDashboard = false;
  let showProvenanceTracker = false;
  let selectedSessionId = null;
</script>

<!-- Add new navigation items -->
<nav class="sidebar">
  <!-- ...existing nav items -->
  
  <button 
    class:active={activeView === 'transparency'}
    on:click={() => activeView = 'transparency'}
  >
    <Icon name="brain" />
    Transparency
  </button>
  
  <button 
    class:active={activeView === 'provenance'}
    on:click={() => activeView = 'provenance'}
  >
    <Icon name="git-branch" />
    Provenance
  </button>
</nav>

<!-- Add new view panels -->
<main class="main-content">
  {#if activeView === 'transparency'}
    <TransparencyDashboard />
  {:else if activeView === 'provenance'}
    <ProvenanceTracker />
  {:else if activeView === 'session' && selectedSessionId}
    <ReasoningSessionViewer sessionId={selectedSessionId} />
  {/if}
  
  <!-- ...existing views -->
</main>
```

#### 4.2 API Utility Enhancements

**Enhancement**: Update `src/utils/api.js` with new endpoints

```javascript
// Add to existing api.js
export const GödelOSAPI = {
  // ...existing methods
  
  // Transparency API methods
  async startReasoningSession(query, transparencyLevel = 'detailed') {
    return this.post('/api/transparency/session/start', {
      query,
      transparency_level: transparencyLevel
    });
  },
  
  async getActiveTransparencySessions() {
    return this.get('/api/transparency/sessions/active');
  },
  
  async getTransparencyStatistics() {
    return this.get('/api/transparency/statistics');
  },
  
  async getReasoningTrace(sessionId) {
    return this.get(`/api/transparency/session/${sessionId}/trace`);
  },
  
  // Knowledge API enhancements
  async searchKnowledge(query, category = null, limit = 10) {
    const params = { query, limit };
    if (category) params.category = category;
    
    return this.get('/api/knowledge/search', { params });
  },
  
  async getKnowledgeItem(itemId) {
    return this.get(`/api/knowledge/${itemId}`);
  },
  
  // Import API methods
  async importFromUrl(url, category = 'web') {
    return this.post('/api/knowledge/import/url', { url, category });
  },
  
  async getImportProgress(importId) {
    return this.get(`/api/knowledge/import/progress/${importId}`);
  },
  
  async cancelImport(importId) {
    return this.delete(`/api/knowledge/import/${importId}`);
  }
};
```

## 🚀 Implementation Timeline

### Week 1: Backend Fixes
- [ ] Fix knowledge import validation issues
- [ ] Fix knowledge search endpoint
- [ ] Fix transparency session management
- [ ] Test all endpoints to achieve 75%+ success rate

### Week 2: Core Frontend Features
- [ ] Implement TransparencyDashboard component
- [ ] Add search functionality to KnowledgeGraph
- [ ] Enhance SmartImport with progress tracking
- [ ] Test integration with fixed backend APIs

### Week 3: Advanced Transparency
- [ ] Implement ReasoningSessionViewer
- [ ] Connect existing transparency components to APIs
- [ ] Add real-time updates for active sessions
- [ ] Test transparency workflow end-to-end

### Week 4: Provenance and Advanced Features
- [ ] Implement ProvenanceTracker component
- [ ] Add knowledge graph export functionality
- [ ] Implement batch import operations
- [ ] Add advanced statistics visualizations

### Week 5: Integration and Polish
- [ ] Integrate all new components into main app
- [ ] Add comprehensive error handling
- [ ] Implement loading states and user feedback
- [ ] Add responsive design improvements

### Week 6: Testing and Documentation
- [ ] Run comprehensive E2E tests
- [ ] Achieve target metrics (85% backend success, 80% frontend coverage)
- [ ] Update user documentation
- [ ] Prepare deployment

## 📊 Success Criteria

**Backend Success Rate**: 85%+ (33/39 endpoints working correctly)
**Frontend Coverage**: 80%+ (31/39 endpoints with UI implementation)
**User Workflows**: 100% completion rate for all major user journeys

---

*This implementation plan addresses all critical gaps identified in the comprehensive E2E testing analysis.*
