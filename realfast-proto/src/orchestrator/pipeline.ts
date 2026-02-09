/**
 * Pipeline orchestrator - manages multi-agent workflows with quality gates
 * Stages run in parallel when no dependencies, sequential when dependent
 */

import { EventEmitter } from 'events';
import {
  Pipeline,
  PipelineStage,
  AgentTask,
  TaskInput,
  TaskStatus,
  PipelineExecutionResult,
  StageResult,
  AgentRole,
} from './types.js';

export class PipelineOrchestrator extends EventEmitter {
  private pipelines: Map<string, Pipeline> = new Map();
  private executions: Map<string, PipelineExecutionResult> = new Map();
  private stageResults: Map<string, Map<AgentRole, StageResult>> = new Map();

  /**
   * Create a new pipeline definition
   */
  createPipeline(name: string, stages: PipelineStage[]): Pipeline {
    const pipeline: Pipeline = {
      id: this.generateId(),
      name,
      stages,
      status: 'idle',
    };

    this.pipelines.set(pipeline.id, pipeline);
    return pipeline;
  }

  /**
   * Execute a pipeline with given input
   * Respects stage dependencies and runs stages in correct order
   */
  async executePipeline(
    pipeline: Pipeline,
    input: TaskInput
  ): Promise<PipelineExecutionResult> {
    const execution: PipelineExecutionResult = {
      pipelineId: pipeline.id,
      status: 'completed',
      stages: [],
      startTime: Date.now(),
      humanReviewsRequired: 0,
    };

    this.executions.set(pipeline.id, execution);
    this.stageResults.set(pipeline.id, new Map());

    // Update pipeline status
    pipeline.status = 'running';
    this.emit('pipeline:started', { pipelineId: pipeline.id });

    try {
      // Build dependency graph
      const graph = this.buildDependencyGraph(pipeline.stages);

      // Execute stages in topological order
      const executedStages = new Set<AgentRole>();
      const stagesByLevel = this.getStagesByLevel(graph);

      for (const level of stagesByLevel) {
        // Execute all stages at this level in parallel
        const stagePromises = level.map(stage =>
          this.executeStage(pipeline.id, stage, input, executedStages)
        );

        const results = await Promise.all(stagePromises);

        // Check for failures
        const failed = results.find(r => r.status === 'failed');
        if (failed) {
          execution.status = 'failed';
          pipeline.status = 'failed';
          break;
        }

        // Mark stages as executed
        level.forEach(stage => executedStages.add(stage.role));
      }

      // Check if any stage needs human review
      const needsReview = execution.stages.some(s =>
        s.tasks.some(t => t.humanReviewRequired)
      );

      if (needsReview) {
        execution.status = 'needs-review';
        execution.humanReviewsRequired = execution.stages.reduce(
          (count, s) => count + s.tasks.filter(t => t.humanReviewRequired).length,
          0
        );
      }

      execution.endTime = Date.now();
      pipeline.status = execution.status === 'failed' ? 'failed' : 'completed';

      this.emit('pipeline:completed', {
        pipelineId: pipeline.id,
        status: execution.status,
      });

      return execution;
    } catch (error) {
      execution.status = 'failed';
      execution.endTime = Date.now();
      pipeline.status = 'failed';

      this.emit('pipeline:failed', {
        pipelineId: pipeline.id,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      return execution;
    }
  }

  /**
   * Get pipeline status
   */
  getStatus(pipelineId: string): Pipeline | undefined {
    return this.pipelines.get(pipelineId);
  }

  /**
   * Get execution result
   */
  getExecution(pipelineId: string): PipelineExecutionResult | undefined {
    return this.executions.get(pipelineId);
  }

  /**
   * Execute a single stage
   */
  private async executeStage(
    pipelineId: string,
    stage: PipelineStage,
    input: TaskInput,
    executedStages: Set<AgentRole>
  ): Promise<StageResult> {
    const stageResult: StageResult = {
      stage,
      tasks: [],
      status: 'pending',
      startTime: Date.now(),
    };

    this.emit('stage:started', {
      pipelineId,
      role: stage.role,
    });

    try {
      // Create task for this stage
      const task = this.createTask(stage.role, input, stage.config);
      stageResult.tasks.push(task);

      // Simulate task execution
      // In real implementation, this would delegate to agent pool
      await this.simulateTaskExecution(task);

      // Quality gate check
      const qualityPassed = this.checkQualityGate(task, stage);

      if (!qualityPassed) {
        stageResult.status = 'failed';
        this.emit('stage:quality-failed', {
          pipelineId,
          role: stage.role,
          qualityScore: task.qualityScore,
        });
      } else {
        stageResult.status = 'completed';
        this.emit('stage:completed', {
          pipelineId,
          role: stage.role,
        });
      }

      stageResult.endTime = Date.now();

      // Store stage result
      const stageResults = this.stageResults.get(pipelineId)!;
      stageResults.set(stage.role, stageResult);

      // Add to execution
      const execution = this.executions.get(pipelineId)!;
      execution.stages.push(stageResult);

      return stageResult;
    } catch (error) {
      stageResult.status = 'failed';
      stageResult.endTime = Date.now();

      this.emit('stage:failed', {
        pipelineId,
        role: stage.role,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      return stageResult;
    }
  }

  /**
   * Check if task passes quality gate
   */
  private checkQualityGate(task: AgentTask, stage: PipelineStage): boolean {
    const threshold = stage.config.qualityThreshold ?? 0.8;
    const qualityScore = task.qualityScore ?? 0;

    // Always require human review if configured
    if (stage.config.requiresHumanReview) {
      task.humanReviewRequired = true;
      task.status = 'review';
      return true; // Don't fail, just flag for review
    }

    // Auto-approve if above threshold
    if (qualityScore >= threshold) {
      task.status = 'approved';
      task.humanReviewRequired = false;
      return true;
    }

    // Require human review if below threshold
    task.status = 'review';
    task.humanReviewRequired = true;
    return true; // Don't fail, just flag for review
  }

  /**
   * Build dependency graph from stages
   */
  private buildDependencyGraph(
    stages: PipelineStage[]
  ): Map<AgentRole, AgentRole[]> {
    const graph = new Map<AgentRole, AgentRole[]>();

    stages.forEach(stage => {
      graph.set(stage.role, stage.dependsOn || []);
    });

    return graph;
  }

  /**
   * Get stages grouped by execution level (parallel groups)
   */
  private getStagesByLevel(
    graph: Map<AgentRole, AgentRole[]>
  ): PipelineStage[][] {
    const levels: PipelineStage[][] = [];
    const processed = new Set<AgentRole>();
    const stages = Array.from(graph.keys());

    while (processed.size < stages.length) {
      const currentLevel: PipelineStage[] = [];

      // Find stages with all dependencies satisfied
      for (const role of stages) {
        if (processed.has(role)) continue;

        const deps = graph.get(role) || [];
        const allDepsSatisfied = deps.every(dep => processed.has(dep));

        if (allDepsSatisfied) {
          // Find the stage definition
          const pipeline = Array.from(this.pipelines.values()).find(p =>
            p.stages.some(s => s.role === role)
          );
          const stage = pipeline?.stages.find(s => s.role === role);

          if (stage) {
            currentLevel.push(stage);
            processed.add(role);
          }
        }
      }

      if (currentLevel.length === 0 && processed.size < stages.length) {
        throw new Error('Circular dependency detected in pipeline');
      }

      if (currentLevel.length > 0) {
        levels.push(currentLevel);
      }
    }

    return levels;
  }

  /**
   * Create a task for a stage
   */
  private createTask(
    role: AgentRole,
    input: TaskInput,
    config: Partial<any>
  ): AgentTask {
    return {
      id: this.generateId(),
      type: role,
      input,
      status: 'queued',
      humanReviewRequired: config.requiresHumanReview ?? false,
      createdAt: Date.now(),
    };
  }

  /**
   * Simulate task execution (for prototype)
   * In production, this would delegate to agent pool
   */
  private async simulateTaskExecution(task: AgentTask): Promise<void> {
    // Simulate async work
    await new Promise(resolve => setTimeout(resolve, 100));

    // Simulate task completion with random quality score
    task.status = 'in-progress';
    task.output = {
      result: `Output from ${task.type}`,
      artifacts: [],
      confidence: Math.random() * 0.3 + 0.7, // 0.7-1.0
      reasoning: `Completed ${task.type} task`,
    };

    task.qualityScore = task.output.confidence;
    task.completedAt = Date.now();
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

/**
 * Create a new pipeline orchestrator
 */
export function createPipeline(
  name: string,
  stages: PipelineStage[]
): PipelineOrchestrator {
  const orchestrator = new PipelineOrchestrator();
  orchestrator.createPipeline(name, stages);
  return orchestrator;
}
