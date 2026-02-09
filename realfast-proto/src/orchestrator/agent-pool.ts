/**
 * Agent pool manager - handles agent assignment and lifecycle
 * Simple round-robin assignment within role
 */

import { AgentConfig, AgentTask, AgentRole, AgentPoolStatus } from './types.js';

interface PoolAgent {
  id: string;
  config: AgentConfig;
  busy: boolean;
  currentTask?: string;
  tasksCompleted: number;
}

export class AgentPool {
  private agents: Map<string, PoolAgent> = new Map();
  private roleIndex: Map<AgentRole, number> = new Map();

  constructor(configs: AgentConfig[]) {
    configs.forEach((config, index) => {
      const agentId = `${config.role}-${config.name}-${index}`;
      this.agents.set(agentId, {
        id: agentId,
        config,
        busy: false,
        tasksCompleted: 0,
      });
    });

    // Initialize round-robin index for each role
    const roles = new Set(configs.map(c => c.role));
    roles.forEach(role => this.roleIndex.set(role, 0));
  }

  /**
   * Assign task to available agent of matching role
   * Uses round-robin within role
   */
  assignTask(task: AgentTask): string | null {
    const availableAgents = Array.from(this.agents.values())
      .filter(agent =>
        agent.config.role === task.type &&
        !agent.busy &&
        this.canAcceptTask(agent)
      );

    if (availableAgents.length === 0) {
      return null;
    }

    // Round-robin selection
    const currentIndex = this.roleIndex.get(task.type) || 0;
    const selectedAgent = availableAgents[currentIndex % availableAgents.length];

    // Update index for next assignment
    this.roleIndex.set(task.type, currentIndex + 1);

    // Mark agent as busy
    selectedAgent.busy = true;
    selectedAgent.currentTask = task.id;

    return selectedAgent.id;
  }

  /**
   * Release agent back to pool
   */
  releaseAgent(agentId: string): void {
    const agent = this.agents.get(agentId);
    if (!agent) {
      throw new Error(`Agent not found: ${agentId}`);
    }

    agent.busy = false;
    agent.currentTask = undefined;
    agent.tasksCompleted++;
  }

  /**
   * Get pool status per role
   */
  getPoolStatus(): AgentPoolStatus[] {
    const statusMap = new Map<AgentRole, AgentPoolStatus>();

    // Initialize status for all roles
    this.agents.forEach(agent => {
      if (!statusMap.has(agent.config.role)) {
        statusMap.set(agent.config.role, {
          role: agent.config.role,
          available: 0,
          busy: 0,
          total: 0,
        });
      }
    });

    // Count agents
    this.agents.forEach(agent => {
      const status = statusMap.get(agent.config.role)!;
      status.total++;
      if (agent.busy) {
        status.busy++;
      } else {
        status.available++;
      }
    });

    return Array.from(statusMap.values());
  }

  /**
   * Get agent by ID
   */
  getAgent(agentId: string): PoolAgent | undefined {
    return this.agents.get(agentId);
  }

  /**
   * Check if agent can accept more concurrent tasks
   */
  private canAcceptTask(agent: PoolAgent): boolean {
    // Currently simple - just check if not busy
    // Could be extended to support maxConcurrent > 1
    return !agent.busy;
  }

  /**
   * Get all agents for a specific role
   */
  getAgentsByRole(role: AgentRole): PoolAgent[] {
    return Array.from(this.agents.values())
      .filter(agent => agent.config.role === role);
  }

  /**
   * Reset pool - release all agents
   */
  reset(): void {
    this.agents.forEach(agent => {
      agent.busy = false;
      agent.currentTask = undefined;
    });
  }
}

/**
 * Create an agent pool from configs
 */
export function createPool(configs: AgentConfig[]): AgentPool {
  return new AgentPool(configs);
}
