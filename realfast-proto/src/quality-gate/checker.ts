/**
 * Quality Checking Engine
 *
 * The beating heart of the system - validates every AI output.
 * Each check is independent, scored, and auditable.
 */

import {
  QualityCheck,
  CheckResult,
  TaskOutput,
  QualityPolicy,
  SafetyViolation,
  AuditEntry,
} from './types.js';

export class QualityChecker {
  private policy: QualityPolicy;

  constructor(policy?: Partial<QualityPolicy>) {
    this.policy = {
      autoApproveThreshold: 0.85,
      rejectThreshold: 0.3,
      requiredChecks: ['confidence', 'completeness', 'safety'],
      humanReviewAlways: false,
      checkWeights: {
        confidence: 0.25,
        completeness: 0.25,
        consistency: 0.2,
        safety: 0.3, // safety is weighted highest
      },
      criticalChecks: ['safety'],
      ...policy,
    };
  }

  /**
   * Run all quality checks on an agent output
   */
  runQualityChecks(output: TaskOutput): QualityCheck {
    const checkId = `qc-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const auditLog: AuditEntry[] = [];

    // Log the start
    auditLog.push({
      action: 'quality-check-started',
      actor: 'quality-gate',
      actorId: 'checker',
      details: `Starting quality checks for task ${output.taskId}`,
      timestamp: Date.now(),
    });

    // Run all checks
    const checks: CheckResult[] = [
      this.checkConfidence(output, auditLog),
      this.checkCompleteness(output, auditLog),
      this.checkConsistency(output, auditLog),
      this.checkSafety(output, auditLog),
    ];

    // Calculate overall score (weighted average)
    const overallScore = this.calculateOverallScore(checks);

    // Determine verdict
    const verdict = this.determineVerdict(checks, overallScore);

    // Log the result
    auditLog.push({
      action: 'quality-check-completed',
      actor: 'quality-gate',
      actorId: 'checker',
      details: `Verdict: ${verdict}, Score: ${overallScore.toFixed(2)}`,
      timestamp: Date.now(),
      metadata: {
        overallScore,
        checksRun: checks.length,
        checksPassed: checks.filter(c => c.passed).length,
      },
    });

    return {
      id: checkId,
      taskId: output.taskId,
      checks,
      overallScore,
      verdict,
      auditLog,
      timestamp: Date.now(),
      metadata: {
        agentId: output.agentId,
        policy: this.policy,
      },
    };
  }

  /**
   * Check if agent is confident enough in its output
   */
  private checkConfidence(output: TaskOutput, auditLog: AuditEntry[]): CheckResult {
    const threshold = 0.7; // require 70% confidence minimum
    const passed = output.confidence >= threshold;
    const score = output.confidence;

    auditLog.push({
      action: 'confidence-check',
      actor: 'quality-gate',
      details: `Agent confidence: ${(output.confidence * 100).toFixed(1)}%, threshold: ${(threshold * 100).toFixed(1)}%`,
      timestamp: Date.now(),
    });

    return {
      name: 'confidence',
      passed,
      score,
      weight: this.policy.checkWeights?.confidence || 0.25,
      details: passed
        ? `Agent is ${(output.confidence * 100).toFixed(1)}% confident (above ${(threshold * 100).toFixed(1)}% threshold)`
        : `Agent is only ${(output.confidence * 100).toFixed(1)}% confident (below ${(threshold * 100).toFixed(1)}% threshold)`,
    };
  }

  /**
   * Check if all required artifacts are present
   */
  private checkCompleteness(output: TaskOutput, auditLog: AuditEntry[]): CheckResult {
    const requirements = output.metadata.requirements || [];
    const completed = output.metadata.completedRequirements || [];

    if (requirements.length === 0) {
      // No explicit requirements - check for basic output
      const hasContent = output.content && output.content.length > 0;
      const score = hasContent ? 1.0 : 0.0;

      auditLog.push({
        action: 'completeness-check',
        actor: 'quality-gate',
        details: 'No explicit requirements, checking basic output presence',
        timestamp: Date.now(),
      });

      return {
        name: 'completeness',
        passed: hasContent,
        score,
        weight: this.policy.checkWeights?.completeness || 0.25,
        details: hasContent
          ? 'Output has content'
          : 'Output is empty or missing',
      };
    }

    // Check requirement completion
    const completionRate = completed.length / requirements.length;
    const passed = completionRate >= 0.8; // require 80% completion
    const missing = requirements.filter(req => !completed.includes(req));

    auditLog.push({
      action: 'completeness-check',
      actor: 'quality-gate',
      details: `${completed.length}/${requirements.length} requirements met`,
      timestamp: Date.now(),
      metadata: {
        completed,
        missing,
      },
    });

    return {
      name: 'completeness',
      passed,
      score: completionRate,
      weight: this.policy.checkWeights?.completeness || 0.25,
      details: passed
        ? `${completed.length}/${requirements.length} requirements met`
        : `Missing requirements: ${missing.join(', ')}`,
    };
  }

  /**
   * Check if output matches input requirements
   */
  private checkConsistency(output: TaskOutput, auditLog: AuditEntry[]): CheckResult {
    const requirements = output.metadata.requirements || [];

    if (requirements.length === 0) {
      // No requirements to check against
      return {
        name: 'consistency',
        passed: true,
        score: 1.0,
        weight: this.policy.checkWeights?.consistency || 0.2,
        details: 'No requirements to validate against',
      };
    }

    // Check if output mentions/addresses each requirement
    const content = output.content.toLowerCase();
    const addressed = requirements.filter(req => {
      const reqKeywords = req.toLowerCase().split(/\s+/);
      return reqKeywords.some(keyword => content.includes(keyword));
    });

    const consistencyRate = addressed.length / requirements.length;
    const passed = consistencyRate >= 0.6; // require 60% consistency

    auditLog.push({
      action: 'consistency-check',
      actor: 'quality-gate',
      details: `${addressed.length}/${requirements.length} requirements addressed in output`,
      timestamp: Date.now(),
    });

    return {
      name: 'consistency',
      passed,
      score: consistencyRate,
      weight: this.policy.checkWeights?.consistency || 0.2,
      details: passed
        ? `Output addresses ${addressed.length}/${requirements.length} requirements`
        : `Output only addresses ${addressed.length}/${requirements.length} requirements`,
    };
  }

  /**
   * Check for safety violations (critical check)
   */
  private checkSafety(output: TaskOutput, auditLog: AuditEntry[]): CheckResult {
    const violations: SafetyViolation[] = [];

    // Check for SQL injection patterns
    const sqlPatterns = [
      /\b(union\s+select|drop\s+table|exec\s*\(|execute\s*\()/gi,
      /--\s*$/gm, // SQL comment at end of line
      /;\s*drop/gi,
    ];

    for (const pattern of sqlPatterns) {
      if (pattern.test(output.content)) {
        violations.push({
          type: 'sql-injection',
          severity: 'high',
          description: 'Potential SQL injection pattern detected',
          location: 'output.content',
          recommendation: 'Review SQL queries for proper parameterization',
        });
      }
    }

    // Check for exposed secrets
    const secretPatterns = [
      /api[_-]?key\s*[:=]\s*['"][a-zA-Z0-9]{20,}['"]/gi,
      /password\s*[:=]\s*['"][^'"]{8,}['"]/gi,
      /secret\s*[:=]\s*['"][^'"]{16,}['"]/gi,
      /bearer\s+[a-zA-Z0-9\-._~+/]+=*/gi,
    ];

    for (const pattern of secretPatterns) {
      if (pattern.test(output.content)) {
        violations.push({
          type: 'secret-exposure',
          severity: 'critical',
          description: 'Potential secret or credential exposed',
          location: 'output.content',
          recommendation: 'Remove hardcoded secrets, use environment variables',
        });
      }
    }

    // Check for path traversal
    const pathTraversalPatterns = [
      /\.\.[/\\]/g,
      /\/etc\/passwd/gi,
      /\/etc\/shadow/gi,
    ];

    for (const pattern of pathTraversalPatterns) {
      if (pattern.test(output.content)) {
        violations.push({
          type: 'path-traversal',
          severity: 'high',
          description: 'Potential path traversal vulnerability',
          location: 'output.content',
          recommendation: 'Validate and sanitize file paths',
        });
      }
    }

    // Check for XSS patterns
    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gis,
      /javascript:/gi,
      /on\w+\s*=\s*['"][^'"]*['"]/gi, // onclick, onerror, etc.
    ];

    for (const pattern of xssPatterns) {
      if (pattern.test(output.content)) {
        violations.push({
          type: 'xss',
          severity: 'medium',
          description: 'Potential XSS vulnerability',
          location: 'output.content',
          recommendation: 'Sanitize user input and escape HTML entities',
        });
      }
    }

    const hasCriticalViolations = violations.some(v => v.severity === 'critical');
    const passed = violations.length === 0;
    const score = passed ? 1.0 : hasCriticalViolations ? 0.0 : 0.5;

    auditLog.push({
      action: 'safety-check',
      actor: 'quality-gate',
      details: `Found ${violations.length} safety violations`,
      timestamp: Date.now(),
      metadata: {
        violations,
      },
    });

    return {
      name: 'safety',
      passed,
      score,
      weight: this.policy.checkWeights?.safety || 0.3,
      details: passed
        ? 'No safety violations detected'
        : `Found ${violations.length} violations: ${violations.map(v => v.type).join(', ')}`,
      criticalFailure: hasCriticalViolations,
    };
  }

  /**
   * Calculate weighted overall score
   */
  private calculateOverallScore(checks: CheckResult[]): number {
    const totalWeight = checks.reduce((sum, check) => sum + check.weight, 0);
    const weightedScore = checks.reduce((sum, check) => sum + check.score * check.weight, 0);
    return weightedScore / totalWeight;
  }

  /**
   * Determine verdict based on checks and policy
   */
  private determineVerdict(
    checks: CheckResult[],
    overallScore: number
  ): 'auto-approved' | 'needs-human-review' | 'rejected' {
    // Critical failure = instant rejection
    if (checks.some(c => c.criticalFailure)) {
      return 'rejected';
    }

    // Required checks must pass
    for (const requiredCheck of this.policy.requiredChecks) {
      const check = checks.find(c => c.name === requiredCheck);
      if (check && !check.passed) {
        return 'rejected';
      }
    }

    // Policy override: always require human review
    if (this.policy.humanReviewAlways) {
      return 'needs-human-review';
    }

    // Score-based decision
    if (overallScore >= this.policy.autoApproveThreshold) {
      return 'auto-approved';
    } else if (overallScore <= this.policy.rejectThreshold) {
      return 'rejected';
    } else {
      return 'needs-human-review';
    }
  }

  /**
   * Update policy configuration
   */
  updatePolicy(updates: Partial<QualityPolicy>): void {
    this.policy = { ...this.policy, ...updates };
  }

  /**
   * Get current policy
   */
  getPolicy(): QualityPolicy {
    return { ...this.policy };
  }
}

/**
 * Factory function for easy instantiation
 */
export function createQualityChecker(policy?: Partial<QualityPolicy>): QualityChecker {
  return new QualityChecker(policy);
}
