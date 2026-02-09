/**
 * Quality Gate Types
 *
 * Every AI decision flows through quality validation.
 * "Automation without oversight creates vulnerability, not capability."
 * - Sidu Ponnappa, RealFast.ai
 */

export interface QualityCheck {
  id: string;
  taskId: string;
  checks: CheckResult[];
  overallScore: number; // 0-1
  verdict: 'auto-approved' | 'needs-human-review' | 'rejected';
  reviewedBy?: string; // human reviewer ID if reviewed
  auditLog: AuditEntry[];
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface CheckResult {
  name: string;
  passed: boolean;
  score: number; // 0-1
  weight: number; // how much this check matters
  details: string;
  criticalFailure?: boolean; // if true, instant rejection
}

export interface AuditEntry {
  action: string;
  actor: 'agent' | 'quality-gate' | 'human';
  actorId?: string; // specific agent or human ID
  details: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface QualityPolicy {
  autoApproveThreshold: number; // score above this = auto-approve (default 0.85)
  rejectThreshold: number; // score below this = auto-reject (default 0.3)
  requiredChecks: string[]; // check names that MUST pass
  humanReviewAlways: boolean; // override: always require human (like RealFast)
  checkWeights?: Record<string, number>; // custom weights for checks
  criticalChecks?: string[]; // any failure = instant rejection
}

export interface HumanReviewRequest {
  id: string;
  qualityCheck: QualityCheck;
  priority: 'low' | 'medium' | 'high' | 'critical';
  requestedAt: number;
  resolvedAt?: number;
  assignedTo?: string;
  status: 'pending' | 'in-progress' | 'completed';
}

export interface HumanReviewSubmission {
  verdict: 'approved' | 'rejected' | 'needs-revision';
  comments: string;
  reviewerId: string;
  modifications?: string[]; // what the human changed
  timestamp: number;
}

export interface TaskOutput {
  taskId: string;
  agentId: string;
  content: string;
  artifacts?: Record<string, unknown>; // files, data, etc.
  confidence: number; // 0-1, how confident is the agent?
  metadata: {
    requirements?: string[];
    completedRequirements?: string[];
    tokensUsed?: number;
    executionTime?: number;
    [key: string]: unknown;
  };
}

export interface SafetyViolation {
  type: 'sql-injection' | 'secret-exposure' | 'path-traversal' | 'xss' | 'other';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  location?: string;
  recommendation: string;
}

export interface QualityMetrics {
  totalChecks: number;
  autoApproved: number;
  humanReviewed: number;
  rejected: number;
  averageScore: number;
  averageReviewTime: number; // milliseconds
  checkSuccessRates: Record<string, number>; // per check type
}
