/**
 * RealFast Proto - AI Agent Orchestration Platform
 *
 * Main entry point for library usage.
 * For a live demo, run: npm run demo
 */

// Export all agent types and pool
export {
  AgentPool,
  type AIAgent,
  type AgentRole,
  type AgentStatus,
} from './agents.js';

// Export orchestrator and pipeline types
export {
  PipelineOrchestrator,
  type Pipeline,
  type PipelineStage,
  type PipelineStageResult,
} from './orchestrator.js';

// Export quality gate system
export {
  QualityGate,
  type QualityCheckInput,
  type QualityCheckResult,
  type QualityGateConfig,
  type AuditLogEntry,
} from './quality-gate.js';

/**
 * Example usage:
 *
 * ```typescript
 * import { AgentPool, PipelineOrchestrator, QualityGate } from 'realfast-proto';
 *
 * // Create agent pool
 * const pool = new AgentPool();
 * pool.addAgent('code-analyzer');
 * pool.addAgent('test-generator');
 *
 * // Create quality gate
 * const qualityGate = new QualityGate({
 *   autoApproveThreshold: 0.85,
 *   autoRejectThreshold: 0.50,
 * });
 *
 * // Create orchestrator
 * const orchestrator = new PipelineOrchestrator(pool, qualityGate);
 *
 * // Define pipeline stages
 * const stages = [
 *   {
 *     name: 'analyze',
 *     agentRole: 'code-analyzer',
 *     input: { type: 'code', content: sourceCode },
 *     outputType: 'analysis',
 *   },
 *   {
 *     name: 'generate-tests',
 *     agentRole: 'test-generator',
 *     dependencies: ['analyze'],
 *     outputType: 'tests',
 *   },
 * ];
 *
 * // Execute pipeline
 * for (const stage of stages) {
 *   const input = stage.input || { type: 'derived', dependencies: stage.dependencies };
 *   const result = await orchestrator.executeStage('my-pipeline', stage, input);
 *   console.log(`Stage ${stage.name} completed:`, result);
 * }
 *
 * // Get audit trail
 * const auditLog = qualityGate.getAuditLog();
 * console.log('Quality checks:', auditLog);
 * ```
 */
