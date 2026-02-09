import { AgentRole } from '../orchestrator/types';
import { BaseAgent } from './base-agent';
import { CodeAnalyzer } from './code-analyzer';
import { TestGenerator } from './test-generator';
import { CodeReviewer } from './code-reviewer';
import { DocGenerator } from './doc-generator';

export { BaseAgent } from './base-agent';
export { CodeAnalyzer } from './code-analyzer';
export { TestGenerator } from './test-generator';
export { CodeReviewer } from './code-reviewer';
export { DocGenerator } from './doc-generator';

/**
 * Factory function to create specialized agents based on role
 * Inspired by RealFast.ai's agent architecture
 *
 * @param role - The agent's specialized role
 * @param name - Optional custom name for the agent
 * @returns Initialized agent instance
 */
export function createAgent(role: AgentRole, name?: string): BaseAgent {
  switch (role) {
    case 'analyzer':
      return new CodeAnalyzer(name);

    case 'tester':
      return new TestGenerator(name);

    case 'reviewer':
      return new CodeReviewer(name);

    case 'documenter':
      return new DocGenerator(name);

    case 'coordinator':
      throw new Error('Coordinator agents are created directly by the orchestrator');

    default:
      throw new Error(`Unknown agent role: ${role}`);
  }
}

/**
 * Get agent capabilities description for a given role
 * Useful for explaining what each agent type does
 *
 * @param role - The agent role to describe
 * @returns Human-readable description of agent capabilities
 */
export function getAgentCapabilities(role: AgentRole): string {
  const capabilities: Record<AgentRole, string> = {
    analyzer: 'Analyzes code for complexity, patterns, and potential issues. Provides detailed metrics on cyclomatic complexity, function length, and naming conventions.',
    tester: 'Generates comprehensive unit test skeletons with happy path, edge cases, and error scenarios. Mirrors RealFast.ai\'s Vayu capability for automated test generation.',
    reviewer: 'Reviews code against best practices including error handling, security, style consistency, and typing. Provides actionable feedback with pass/fail/warning statuses.',
    documenter: 'Auto-generates API documentation by extracting interfaces, types, classes, and functions. Creates markdown documentation with signatures and inferred descriptions.',
    coordinator: 'Orchestrates multi-agent workflows, manages task dependencies, and coordinates agent execution. Not directly instantiable via factory.'
  };

  return capabilities[role] || 'Unknown agent role';
}

/**
 * List all available agent roles
 *
 * @returns Array of available agent roles
 */
export function getAvailableRoles(): AgentRole[] {
  return ['analyzer', 'tester', 'reviewer', 'documenter', 'coordinator'];
}
