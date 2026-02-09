/**
 * AI Agent Platform Orchestrator
 * Inspired by RealFast.ai's Vayu - AI augmentation with human oversight
 *
 * Core philosophy:
 * - Every AI output gets quality gates
 * - Human review when confidence is below threshold
 * - Composable pipelines with dependency management
 * - Round-robin agent assignment within roles
 */

export * from './types.js';
export * from './agent-pool.js';
export * from './pipeline.js';

// Re-export main functions for convenience
export { createPool } from './agent-pool.js';
export { createPipeline, PipelineOrchestrator } from './pipeline.js';
