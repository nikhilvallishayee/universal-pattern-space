/**
 * Core types for the AI agent orchestration platform
 * Inspired by RealFast.ai's Vayu - AI augmentation with human oversight
 */

export type AgentRole = 'analyzer' | 'generator' | 'reviewer' | 'tester' | 'documenter';
export type TaskStatus = 'queued' | 'assigned' | 'in-progress' | 'review' | 'approved' | 'rejected';
export type QualityVerdict = 'pass' | 'fail' | 'needs-review';

export interface AgentTask {
  id: string;
  type: AgentRole;
  input: TaskInput;
  status: TaskStatus;
  output?: TaskOutput;
  qualityScore?: number; // 0-1, must be >0.8 to auto-approve
  assignedAgent?: string;
  humanReviewRequired: boolean;
  createdAt: number;
  completedAt?: number;
}

export interface TaskInput {
  code?: string;
  filePath?: string;
  context?: string;
  requirements?: string[];
}

export interface TaskOutput {
  result: string;
  artifacts: Artifact[];
  confidence: number;
  reasoning: string;
}

export interface Artifact {
  type: 'test' | 'code' | 'review' | 'doc' | 'analysis';
  content: string;
  filePath?: string;
}

export interface AgentConfig {
  role: AgentRole;
  name: string;
  maxConcurrent: number;
  qualityThreshold: number; // auto-approve above this
  requiresHumanReview: boolean; // always require human sign-off
}

export interface Pipeline {
  id: string;
  name: string;
  stages: PipelineStage[];
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
}

export interface PipelineStage {
  role: AgentRole;
  dependsOn?: AgentRole[];
  config: Partial<AgentConfig>;
}

export interface AgentPoolStatus {
  role: AgentRole;
  available: number;
  busy: number;
  total: number;
}

export interface PipelineExecutionResult {
  pipelineId: string;
  status: 'completed' | 'failed' | 'needs-review';
  stages: StageResult[];
  startTime: number;
  endTime?: number;
  humanReviewsRequired: number;
}

export interface StageResult {
  stage: PipelineStage;
  tasks: AgentTask[];
  status: 'completed' | 'failed' | 'pending';
  startTime: number;
  endTime?: number;
}
