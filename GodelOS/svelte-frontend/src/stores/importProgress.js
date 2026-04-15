import { writable } from 'svelte/store';

// Store for import progress events
export const importProgressState = writable({});

// Enhanced progress step mapping for better user experience
export const PROGRESS_STEPS = {
  'initialization': { order: 1, label: 'Initializing', progress: 0 },
  'chunking': { order: 2, label: 'Analyzing text structure', progress: 10 },
  'nlp_extraction': { order: 3, label: 'Extracting entities and relationships', progress: 40 },
  'graph_building': { order: 4, label: 'Building knowledge graph', progress: 60 },
  'vector_indexing': { order: 5, label: 'Creating semantic embeddings', progress: 80 },
  'finalization': { order: 6, label: 'Finalizing processing', progress: 100 },
  'complete': { order: 7, label: 'Complete', progress: 100 },
  'error': { order: 0, label: 'Error', progress: 0 }
};

// Function to update progress based on step
export function updateProgressForStep(importId, step, customMessage = null, customProgress = null) {
  const stepInfo = PROGRESS_STEPS[step] || { order: 0, label: step, progress: 0 };
  
  importProgressState.update(state => ({
    ...state,
    [importId]: {
      ...(state[importId] || {}),
      current_step: customMessage || stepInfo.label,
      progress: customProgress !== null ? customProgress : stepInfo.progress,
      completed_steps: stepInfo.order,
      total_steps: Object.keys(PROGRESS_STEPS).length - 1, // Exclude 'error'
      step_name: step,
      last_updated: Date.now()
    }
  }));
}

// Function to handle detailed progress updates from backend
export function handleProgressUpdate(progressData) {
  const { type, step, progress, message, title, entities_extracted, relationships_extracted, categories, deduplication_stats } = progressData;
  
  // Extract import ID from title or generate one
  const importId = progressData.import_id || `${type}-${Date.now()}`;
  
  // Map progress type to status
  let status = 'processing';
  if (type.includes('completed')) {
    status = 'completed';
  } else if (type.includes('failed')) {
    status = 'failed';
  }
  
  const stepInfo = PROGRESS_STEPS[step] || { order: 0, label: step, progress: progress || 0 };
  
  importProgressState.update(state => ({
    ...state,
    [importId]: {
      ...(state[importId] || {}),
      status,
      current_step: message || stepInfo.label,
      progress: progress !== undefined ? progress : stepInfo.progress,
      completed_steps: stepInfo.order,
      total_steps: Object.keys(PROGRESS_STEPS).length - 1,
      step_name: step,
      last_updated: Date.now(),
      // Enhanced details
      title: title || state[importId]?.title,
      entities_extracted: entities_extracted || state[importId]?.entities_extracted,
      relationships_extracted: relationships_extracted || state[importId]?.relationships_extracted,
      categories: categories || state[importId]?.categories,
      deduplication_stats: deduplication_stats || state[importId]?.deduplication_stats
    }
  }));
}
