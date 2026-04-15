<script>
    import { onMount, onDestroy } from 'svelte';
    import { enhancedCognitive, cognitiveConfig } from '../../stores/enhanced-cognitive.js';
    import { writable, get } from 'svelte/store';

    // Component props
    export let maxEvents = 100;
    export let showFilters = true;
    export let autoScroll = true;
    export let compactMode = false;
    export let formatJson = true; // New prop to control JSON formatting

    // Local reactive state
    let streamEvents = [];
    let filteredEvents = [];
    let selectedEventTypes = new Set(['reasoning', 'knowledge_gap', 'acquisition', 'reflection']);
    let selectedGranularities = new Set(['detailed', 'summary', 'minimal']);
    let searchTerm = '';
    let isExpanded = true;
    let eventContainer;
    let isConnected = false;
    let eventRate = 0;

    // Subscriptions
    let unsubscribe;
    let streamUnsubscribe;

    onMount(() => {
        // Subscribe to cognitive state
        unsubscribe = enhancedCognitive.subscribe(state => {
            if (state.cognitiveStreaming && state.cognitiveStreaming.connected) {
                isConnected = true;
                // Process event history with same structure validation
                const rawEvents = state.cognitiveStreaming.eventHistory?.slice(-maxEvents) || [];
                streamEvents = rawEvents.map(event => ({
                    id: event.id || `${Date.now()}-${Math.random()}`,
                    event_type: event.event_type || event.type || 'unknown',
                    content: event.content || event.message || (typeof event.data === 'string' ? event.data : ''),
                    timestamp: event.timestamp || Date.now(),
                    granularity: event.granularity || 'detailed',
                    metadata: event.metadata || {}
                })).filter(event => event.content && event.content.trim() !== '');
                eventRate = state.cognitiveStreaming.eventRate || 0;
                filterEvents();
            } else {
                isConnected = false;
            }
        });

        // Subscribe to real-time stream events
        streamUnsubscribe = enhancedCognitive.subscribeToStream((event) => {
            // Ensure event has proper structure for rendering
            const processedEvent = {
                id: event.id || `${Date.now()}-${Math.random()}`,
                event_type: event.event_type || event.type || 'unknown',
                content: event.content || event.message || (typeof event.data === 'string' ? event.data : ''),
                timestamp: event.timestamp || Date.now(),
                granularity: event.granularity || 'detailed',
                metadata: event.metadata || {}
            };
            
            // Skip events that don't have meaningful content
            if (!processedEvent.content || processedEvent.content.trim() === '') {
                console.log('Skipping event with no content:', event);
                return;
            }
            
            streamEvents = [...streamEvents.slice(-(maxEvents-1)), processedEvent];
            filterEvents();
            
            if (autoScroll && eventContainer) {
                setTimeout(() => {
                    eventContainer.scrollTop = eventContainer.scrollHeight;
                }, 50);
            }
        });

        // Start streaming only if enabled in config
        const config = get(cognitiveConfig);
        if (config.cognitiveStreaming.enabled) {
            enhancedCognitive.startCognitiveStreaming();
        } else {
            console.log('🚫 Cognitive streaming disabled in configuration');
        }
    });

    onDestroy(() => {
        if (unsubscribe) unsubscribe();
        if (streamUnsubscribe) streamUnsubscribe();
    });

    function filterEvents() {
        filteredEvents = streamEvents.filter(event => {
            const typeMatch = selectedEventTypes.has(event.event_type);
            const granularityMatch = selectedGranularities.has(event.granularity);
            const searchMatch = !searchTerm || 
                event.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                event.event_type.toLowerCase().includes(searchTerm.toLowerCase());
            
            return typeMatch && granularityMatch && searchMatch;
        });
    }

    function toggleEventType(type) {
        if (selectedEventTypes.has(type)) {
            selectedEventTypes.delete(type);
        } else {
            selectedEventTypes.add(type);
        }
        selectedEventTypes = selectedEventTypes;
        filterEvents();
    }

    function toggleGranularity(granularity) {
        if (selectedGranularities.has(granularity)) {
            selectedGranularities.delete(granularity);
        } else {
            selectedGranularities.add(granularity);
        }
        selectedGranularities = selectedGranularities;
        filterEvents();
    }

    function clearEvents() {
        enhancedCognitive.clearEventHistory();
        streamEvents = [];
        filteredEvents = [];
    }

    function exportEvents() {
        const data = JSON.stringify(streamEvents, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cognitive-stream-${new Date().toISOString()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    function getEventIcon(eventType) {
        switch (eventType) {
            case 'reasoning': return '🧠';
            case 'knowledge_gap': return '❓';
            case 'acquisition': return '📚';
            case 'reflection': return '🤔';
            case 'learning': return '💡';
            case 'synthesis': return '🔄';
            default: return '💭';
        }
    }

    function getEventColor(eventType) {
        switch (eventType) {
            case 'reasoning': return '#3b82f6';
            case 'knowledge_gap': return '#f59e0b';
            case 'acquisition': return '#10b981';
            case 'reflection': return '#8b5cf6';
            case 'learning': return '#6366f1';
            case 'synthesis': return '#06b6d4';
            default: return '#6b7280';
        }
    }

    function formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleTimeString();
    }

    function getGranularityColor(granularity) {
        switch (granularity) {
            case 'detailed': return '#3b82f6';
            case 'summary': return '#10b981';
            case 'minimal': return '#6b7280';
            default: return '#6b7280';
        }
    }

    function getIntensityFromContent(content) {
        // Simple heuristic based on content length and keywords
        const length = content.length;
        const keywords = ['critical', 'important', 'urgent', 'significant'];
        const hasKeywords = keywords.some(kw => content.toLowerCase().includes(kw));
        
        if (hasKeywords || length > 200) return 'high';
        if (length > 100) return 'medium';
        return 'low';
    }
</script>

<div class="stream-monitor" class:compact={compactMode}>
    <!-- Modern Header -->
    <header class="monitor-header">
        <div class="header-left">
            <button 
                on:click={() => isExpanded = !isExpanded}
                class="expand-btn"
                aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
                <div class="expand-icon" class:rotated={!isExpanded}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                </div>
            </button>
            
            <div class="header-info">
                <h3 class="monitor-title">
                    <span class="title-icon">🧠</span>
                    Stream of Consciousness
                </h3>
                <div class="monitor-stats">
                    <div class="stat-item">
                        <div class="connection-indicator" class:connected={isConnected}>
                            <div class="indicator-pulse"></div>
                        </div>
                        <span class="stat-text">{isConnected ? 'Live' : 'Offline'}</span>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-item">
                        <span class="stat-number">{filteredEvents.length}</span>
                        <span class="stat-text">events</span>
                    </div>
                    {#if eventRate > 0}
                        <div class="stat-divider"></div>
                        <div class="stat-item">
                            <span class="stat-number">{eventRate.toFixed(1)}</span>
                            <span class="stat-text">events/min</span>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
        
        <div class="header-actions">
            <button
                on:click={clearEvents}
                class="action-btn secondary"
                title="Clear all events"
            >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 3.5a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5V4h4v-.5ZM4.5 5.029l.5 8.5a1.5 1.5 0 0 0 1.5 1.5h3a1.5 1.5 0 0 0 1.5-1.5l.5-8.5H4.5Z"/>
                </svg>
                Clear
            </button>
            
            <button
                on:click={exportEvents}
                class="action-btn secondary"
                title="Export events as JSON"
            >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                    <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                </svg>
                Export
            </button>
            
            <div class="auto-scroll-toggle">
                <label class="toggle-switch">
                    <input 
                        type="checkbox" 
                        bind:checked={autoScroll}
                        class="toggle-input"
                    />
                    <span class="toggle-slider"></span>
                </label>
                <span class="toggle-label">Auto-scroll</span>
            </div>
        </div>
    </header>

    {#if isExpanded}
        <!-- Filters Section -->
        {#if showFilters}
            <section class="filters-section">
                <!-- Search -->
                <div class="search-container">
                    <div class="search-input-wrapper">
                        <svg class="search-icon" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
                        </svg>
                        <input
                            type="text"
                            bind:value={searchTerm}
                            on:input={filterEvents}
                            placeholder="Search events..."
                            class="search-input"
                        />
                        {#if searchTerm}
                            <button
                                on:click={() => { searchTerm = ''; filterEvents(); }}
                                class="search-clear"
                            >
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                    <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                                </svg>
                            </button>
                        {/if}
                    </div>
                </div>

                <!-- Filter Chips -->
                <div class="filter-groups">
                    <div class="filter-group">
                        <label class="filter-label">Event Types:</label>
                        <div class="filter-chips">
                            {#each ['reasoning', 'knowledge_gap', 'acquisition', 'reflection', 'learning', 'synthesis'] as type}
                                <button
                                    on:click={() => toggleEventType(type)}
                                    class="filter-chip"
                                    class:active={selectedEventTypes.has(type)}
                                    style="--chip-color: {getEventColor(type)}"
                                >
                                    <span class="chip-icon">{getEventIcon(type)}</span>
                                    <span class="chip-text">{type.replace('_', ' ')}</span>
                                </button>
                            {/each}
                        </div>
                    </div>

                    <div class="filter-group">
                        <label class="filter-label">Granularity:</label>
                        <div class="filter-chips">
                            {#each ['detailed', 'summary', 'minimal'] as granularity}
                                <button
                                    on:click={() => toggleGranularity(granularity)}
                                    class="filter-chip"
                                    class:active={selectedGranularities.has(granularity)}
                                    style="--chip-color: {getGranularityColor(granularity)}"
                                >
                                    <span class="chip-text">{granularity}</span>
                                </button>
                            {/each}
                        </div>
                    </div>
                </div>
            </section>
        {/if}

        <!-- Events Stream -->
        <section class="events-section">
            <div 
                bind:this={eventContainer}
                class="events-container"
                class:compact={compactMode}
            >
                {#if filteredEvents.length === 0}
                    <div class="empty-state">
                        <div class="empty-icon">🧠</div>
                        <h4 class="empty-title">No cognitive events</h4>
                        <p class="empty-description">
                            {#if streamEvents.length === 0}
                                Waiting for cognitive stream to begin...
                            {:else if !isConnected}
                                Connection lost. Attempting to reconnect...
                            {:else}
                                Try adjusting your filters to see more events
                            {/if}
                        </p>
                        {#if !isConnected}
                            <button
                                on:click={() => enhancedCognitive.startCognitiveStreaming()}
                                class="action-btn primary"
                            >
                                Reconnect Stream
                            </button>
                        {/if}
                    </div>
                {:else}
                    <div class="events-list">
                        {#each filteredEvents as event, index (event.id || index)}
                            <article class="event-item" class:compact={compactMode}>
                                <div class="event-header">
                                    <div class="event-type" style="--event-color: {getEventColor(event.event_type)}">
                                        <span class="event-icon">{getEventIcon(event.event_type)}</span>
                                        <span class="event-label">{event.event_type.replace('_', ' ')}</span>
                                    </div>
                                    
                                    <div class="event-meta">
                                        <span class="event-granularity" style="--granularity-color: {getGranularityColor(event.granularity)}">
                                            {event.granularity}
                                        </span>
                                        <span class="event-time">
                                            {formatTimestamp(event.timestamp)}
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="event-content">
                                    <p class="event-text">{event.content}</p>
                                    
                                    {#if event.metadata && Object.keys(event.metadata).length > 0}
                                        <details class="event-metadata">
                                            <summary class="metadata-toggle">
                                                <span>Metadata</span>
                                                <svg class="toggle-arrow" width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                                                    <path d="M4.5 3L7.5 6L4.5 9" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                                                </svg>
                                            </summary>
                                            <div class="metadata-content">
                                                {#each Object.entries(event.metadata) as [key, value]}
                                                    <div class="metadata-item">
                                                        <span class="metadata-key">{key}:</span>
                                                        <span class="metadata-value">{JSON.stringify(value)}</span>
                                                    </div>
                                                {/each}
                                            </div>
                                        </details>
                                    {/if}
                                </div>
                                
                                <div class="event-intensity intensity-{getIntensityFromContent(event.content)}"></div>
                            </article>
                        {/each}
                    </div>
                {/if}
            </div>
        </section>
    {/if}
</div>

<style>
    .stream-monitor {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }

    .stream-monitor.compact {
        border-radius: 12px;
    }

    /* Header Styles */
    .monitor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        gap: 1rem;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex: 1;
    }

    .expand-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.8);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .expand-btn:hover {
        background: rgba(255, 255, 255, 0.2);
        color: white;
    }

    .expand-icon {
        transition: transform 0.2s ease;
    }

    .expand-icon.rotated {
        transform: rotate(-90deg);
    }

    .header-info {
        flex: 1;
    }

    .monitor-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0 0 0.5rem 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: white;
    }

    .title-icon {
        font-size: 1.5rem;
    }

    .monitor-stats {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .stat-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }

    .connection-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #ef4444;
        position: relative;
    }

    .connection-indicator.connected {
        background: #10b981;
    }

    .connection-indicator.connected .indicator-pulse {
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        border-radius: 50%;
        background: #10b981;
        opacity: 0.3;
        animation: pulse 2s infinite;
    }

    .stat-number {
        font-weight: 600;
        color: white;
        font-size: 0.875rem;
    }

    .stat-text {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
    }

    .stat-divider {
        width: 1px;
        height: 12px;
        background: rgba(255, 255, 255, 0.2);
    }

    .header-actions {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .action-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .action-btn.primary {
        background: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }

    .action-btn.primary:hover {
        background: #2563eb;
        border-color: #2563eb;
    }

    .action-btn.secondary {
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.8);
    }

    .action-btn.secondary:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .auto-scroll-toggle {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .toggle-switch {
        position: relative;
        width: 36px;
        height: 20px;
    }

    .toggle-input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        transition: 0.2s;
    }

    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        left: 2px;
        bottom: 2px;
        background: white;
        border-radius: 50%;
        transition: 0.2s;
    }

    .toggle-input:checked + .toggle-slider {
        background: #3b82f6;
    }

    .toggle-input:checked + .toggle-slider:before {
        transform: translateX(16px);
    }

    .toggle-label {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.7);
        font-weight: 500;
    }

    /* Filters Section */
    .filters-section {
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.02);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .search-container {
        margin-bottom: 1.5rem;
    }

    .search-input-wrapper {
        position: relative;
        max-width: 400px;
    }

    .search-icon {
        position: absolute;
        left: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: rgba(255, 255, 255, 0.5);
    }

    .search-input {
        width: 100%;
        padding: 0.75rem 1rem 0.75rem 2.5rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }

    .search-input::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }

    .search-input:focus {
        outline: none;
        border-color: #3b82f6;
        background: rgba(255, 255, 255, 0.1);
    }

    .search-clear {
        position: absolute;
        right: 8px;
        top: 50%;
        transform: translateY(-50%);
        padding: 4px;
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.5);
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .search-clear:hover {
        color: white;
        background: rgba(255, 255, 255, 0.1);
    }

    .filter-groups {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .filter-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .filter-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
    }

    .filter-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .filter-chip {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.5rem 0.75rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .filter-chip:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .filter-chip.active {
        background: var(--chip-color, #3b82f6);
        border-color: var(--chip-color, #3b82f6);
        color: white;
    }

    .chip-icon {
        font-size: 0.875rem;
    }

    .chip-text {
        text-transform: capitalize;
    }

    /* Events Section */
    .events-section {
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    .events-container {
        height: 500px;
        overflow-y: auto;
        padding: 1rem;
    }

    .events-container.compact {
        height: 300px;
    }

    .events-container::-webkit-scrollbar {
        width: 6px;
    }

    .events-container::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
    }

    .events-container::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
    }

    .events-container::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        text-align: center;
        gap: 1rem;
    }

    .empty-icon {
        font-size: 4rem;
        opacity: 0.5;
    }

    .empty-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: white;
        margin: 0;
    }

    .empty-description {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.7);
        margin: 0;
        max-width: 300px;
        line-height: 1.5;
    }

    .events-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .event-item {
        position: relative;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.2s ease;
    }

    .event-item:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .event-item.compact {
        padding: 0.75rem;
        border-radius: 8px;
    }

    .event-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        gap: 1rem;
    }

    .event-type {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--event-color, #6b7280);
        font-weight: 500;
    }

    .event-icon {
        font-size: 1.25rem;
    }

    .event-label {
        font-size: 0.875rem;
        text-transform: capitalize;
    }

    .event-meta {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .event-granularity {
        padding: 0.25rem 0.5rem;
        background: var(--granularity-color, #6b7280);
        color: white;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: capitalize;
    }

    .event-time {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
    }

    .event-content {
        margin-bottom: 0.75rem;
    }

    .event-text {
        color: rgba(255, 255, 255, 0.9);
        line-height: 1.6;
        margin: 0;
        font-size: 0.875rem;
    }

    .event-metadata {
        margin-top: 0.75rem;
    }

    .metadata-toggle {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0;
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        border: none;
        background: none;
        width: 100%;
        text-align: left;
    }

    .metadata-toggle:hover {
        color: white;
    }

    .toggle-arrow {
        transition: transform 0.2s ease;
    }

    .event-metadata[open] .toggle-arrow {
        transform: rotate(90deg);
    }

    .metadata-content {
        padding: 0.5rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }

    .metadata-item {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.25rem;
        font-size: 0.75rem;
    }

    .metadata-key {
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
        min-width: 80px;
    }

    .metadata-value {
        color: rgba(255, 255, 255, 0.8);
        font-family: 'Monaco', 'Menlo', monospace;
    }

    .event-intensity {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        border-radius: 0 2px 2px 0;
    }

    .event-intensity.intensity-low {
        background: #10b981;
    }

    .event-intensity.intensity-medium {
        background: #f59e0b;
    }

    .event-intensity.intensity-high {
        background: #ef4444;
    }

    /* Animations */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .monitor-header {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
        }

        .header-left {
            flex-direction: column;
            align-items: stretch;
            gap: 1rem;
        }

        .monitor-stats {
            justify-content: space-between;
        }

        .header-actions {
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .filter-groups {
            gap: 1.5rem;
        }

        .filter-chips {
            gap: 0.25rem;
        }

        .filter-chip {
            font-size: 0.7rem;
            padding: 0.375rem 0.5rem;
        }

        .event-header {
            flex-direction: column;
            align-items: stretch;
            gap: 0.5rem;
        }

        .event-meta {
            justify-content: space-between;
        }

        .events-container {
            height: 400px;
        }

        .events-container.compact {
            height: 250px;
        }
    }

    @media (max-width: 480px) {
        .monitor-header {
            padding: 1rem;
        }

        .filters-section {
            padding: 1rem;
        }

        .events-container {
            padding: 0.75rem;
            height: 350px;
        }

        .event-item {
            padding: 0.75rem;
        }

        .search-input-wrapper {
            max-width: none;
        }

        .filter-group {
            gap: 0.75rem;
        }

        .action-btn {
            padding: 0.5rem;
            font-size: 0.75rem;
        }

        .action-btn span {
            display: none;
        }
    }
</style>
