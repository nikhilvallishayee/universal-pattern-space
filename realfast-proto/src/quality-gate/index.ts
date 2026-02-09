/**
 * Quality Gate System
 *
 * The critical trust layer for AI-augmented work.
 * Every AI output passes through validation before approval.
 *
 * Key principles:
 * - "Automation without oversight creates vulnerability, not capability"
 * - Humans are the final authority (Iron Man suit principle)
 * - Every decision is logged and auditable (SOC2 compliance)
 * - Quality checks are transparent and configurable
 *
 * Inspired by RealFast.ai's production-tested approach.
 */

// Types
export type {
  QualityCheck,
  CheckResult,
  AuditEntry,
  QualityPolicy,
  HumanReviewRequest,
  HumanReviewSubmission,
  TaskOutput,
  SafetyViolation,
  QualityMetrics,
} from './types.js';

// Quality Checker
export { QualityChecker, createQualityChecker } from './checker.js';

// Audit Log
export {
  AuditLog,
  createAuditLog,
  getGlobalAuditLog,
  setGlobalAuditLog,
  type AuditLogOptions,
} from './audit-log.js';

// Human Review
export {
  HumanReviewSystem,
  createHumanReviewSystem,
  type HumanReviewSystemOptions,
} from './human-review.js';

/**
 * Complete Quality Gate System
 *
 * Combines checker, audit log, and human review into one integrated system.
 */
export class QualityGateSystem {
  public checker: QualityChecker;
  public auditLog: AuditLog;
  public humanReview: HumanReviewSystem;

  constructor(options?: {
    policy?: Partial<QualityPolicy>;
    auditLogOptions?: AuditLogOptions;
    humanReviewOptions?: Omit<HumanReviewSystemOptions, 'auditLog'>;
  }) {
    this.auditLog = createAuditLog(options?.auditLogOptions);
    this.checker = createQualityChecker(options?.policy);
    this.humanReview = createHumanReviewSystem({
      ...options?.humanReviewOptions,
      auditLog: this.auditLog,
    });

    this.auditLog.logQualityGateAction('system-initialized', 'Quality gate system initialized', {
      policy: this.checker.getPolicy(),
    });
  }

  /**
   * Process an agent output through the quality gate
   */
  async processOutput(output: TaskOutput): Promise<QualityCheck> {
    // Run quality checks
    const qualityCheck = this.checker.runQualityChecks(output);

    // If needs human review, create request
    if (qualityCheck.verdict === 'needs-human-review') {
      const reviewRequest = this.humanReview.requestHumanReview(qualityCheck);
      this.auditLog.logQualityGateAction(
        'human-review-required',
        `Task ${output.taskId} requires human review`,
        {
          qualityCheckId: qualityCheck.id,
          reviewRequestId: reviewRequest.id,
          reason: `Score ${qualityCheck.overallScore.toFixed(2)} in human review range`,
        }
      );
    }

    return qualityCheck;
  }

  /**
   * Get system metrics
   */
  getMetrics(): QualityMetrics {
    const stats = this.humanReview.getStats();
    const auditStats = this.auditLog.getStats();

    // Calculate metrics from audit log
    const qualityChecks = this.auditLog.getLogByAction('quality-check-completed');
    const totalChecks = qualityChecks.length;

    const autoApproved = qualityChecks.filter(
      e => e.metadata && (e.metadata as any).verdict === 'auto-approved'
    ).length;

    const humanReviewed = stats.completed;
    const rejected = qualityChecks.filter(
      e => e.metadata && (e.metadata as any).verdict === 'rejected'
    ).length;

    const scores = qualityChecks
      .map(e => (e.metadata as any)?.overallScore)
      .filter(s => typeof s === 'number');
    const averageScore = scores.length > 0 ? scores.reduce((sum, s) => sum + s, 0) / scores.length : 0;

    return {
      totalChecks,
      autoApproved,
      humanReviewed,
      rejected,
      averageScore,
      averageReviewTime: stats.averageReviewTime,
      checkSuccessRates: {}, // Could be calculated from audit log if needed
    };
  }

  /**
   * Export complete audit trail
   */
  exportAudit(format: 'json' | 'csv' | 'text'): string {
    return this.auditLog.exportLog(format);
  }
}

/**
 * Factory function for complete system
 */
export function createQualityGateSystem(options?: {
  policy?: Partial<QualityPolicy>;
  auditLogOptions?: AuditLogOptions;
  humanReviewOptions?: Omit<HumanReviewSystemOptions, 'auditLog'>;
}): QualityGateSystem {
  return new QualityGateSystem(options);
}

// Re-export types for convenience
import type { QualityPolicy, AuditLogOptions, HumanReviewSystemOptions } from './types.js';
