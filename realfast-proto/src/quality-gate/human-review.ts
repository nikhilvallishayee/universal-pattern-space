/**
 * Human Review Interface
 *
 * "The Iron Man suit" - human shapes the outcome.
 * AI augments, but humans remain the final authority.
 */

import { QualityCheck, HumanReviewRequest, HumanReviewSubmission } from './types.js';
import { AuditLog } from './audit-log.js';

export interface HumanReviewSystemOptions {
  auditLog?: AuditLog;
  autoAssignPolicy?: 'round-robin' | 'least-busy' | 'manual';
  defaultPriority?: 'low' | 'medium' | 'high' | 'critical';
}

export class HumanReviewSystem {
  private pendingReviews: Map<string, HumanReviewRequest> = new Map();
  private completedReviews: Map<string, HumanReviewRequest> = new Map();
  private auditLog: AuditLog | null = null;
  private options: Required<HumanReviewSystemOptions>;
  private reviewerQueue: string[] = []; // for round-robin assignment

  constructor(options?: HumanReviewSystemOptions) {
    this.options = {
      auditLog: options?.auditLog || null,
      autoAssignPolicy: options?.autoAssignPolicy || 'manual',
      defaultPriority: options?.defaultPriority || 'medium',
    };
    this.auditLog = this.options.auditLog;
  }

  /**
   * Request human review for a quality check
   */
  requestHumanReview(
    qualityCheck: QualityCheck,
    priority?: 'low' | 'medium' | 'high' | 'critical'
  ): HumanReviewRequest {
    const requestId = `hr-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    const finalPriority = priority || this.determinePriority(qualityCheck);

    const request: HumanReviewRequest = {
      id: requestId,
      qualityCheck,
      priority: finalPriority,
      requestedAt: Date.now(),
      status: 'pending',
    };

    // Auto-assign if policy is set
    if (this.options.autoAssignPolicy !== 'manual') {
      const assignee = this.autoAssignReviewer();
      if (assignee) {
        request.assignedTo = assignee;
        request.status = 'in-progress';
      }
    }

    this.pendingReviews.set(requestId, request);

    // Log the request
    this.auditLog?.logQualityGateAction('human-review-requested', `Review requested for task ${qualityCheck.taskId}`, {
      requestId,
      priority: finalPriority,
      qualityCheckId: qualityCheck.id,
      overallScore: qualityCheck.overallScore,
      assignedTo: request.assignedTo,
    });

    return request;
  }

  /**
   * Submit a human review
   */
  submitReview(
    requestId: string,
    submission: Omit<HumanReviewSubmission, 'timestamp'>
  ): QualityCheck {
    const request = this.pendingReviews.get(requestId);

    if (!request) {
      throw new Error(`Review request ${requestId} not found`);
    }

    if (request.status === 'completed') {
      throw new Error(`Review request ${requestId} already completed`);
    }

    // Create full submission with timestamp
    const fullSubmission: HumanReviewSubmission = {
      ...submission,
      timestamp: Date.now(),
    };

    // Update quality check with human decision
    const updatedCheck: QualityCheck = {
      ...request.qualityCheck,
      verdict:
        fullSubmission.verdict === 'approved'
          ? 'auto-approved'
          : fullSubmission.verdict === 'rejected'
          ? 'rejected'
          : 'needs-human-review',
      reviewedBy: fullSubmission.reviewerId,
      auditLog: [
        ...request.qualityCheck.auditLog,
        {
          action: 'human-review-submitted',
          actor: 'human',
          actorId: fullSubmission.reviewerId,
          details: `Verdict: ${fullSubmission.verdict}. ${fullSubmission.comments}`,
          timestamp: fullSubmission.timestamp,
          metadata: {
            modifications: fullSubmission.modifications,
          },
        },
      ],
    };

    // Update request
    request.qualityCheck = updatedCheck;
    request.status = 'completed';
    request.resolvedAt = Date.now();

    // Move to completed
    this.pendingReviews.delete(requestId);
    this.completedReviews.set(requestId, request);

    // Log the submission
    this.auditLog?.logHumanAction(
      fullSubmission.reviewerId,
      'review-submitted',
      `Reviewed task ${request.qualityCheck.taskId}: ${fullSubmission.verdict}`,
      {
        requestId,
        verdict: fullSubmission.verdict,
        comments: fullSubmission.comments,
        modifications: fullSubmission.modifications,
        reviewTime: request.resolvedAt - request.requestedAt,
      }
    );

    return updatedCheck;
  }

  /**
   * Get all pending reviews
   */
  getPendingReviews(options?: {
    assignedTo?: string;
    priority?: 'low' | 'medium' | 'high' | 'critical';
    sortBy?: 'priority' | 'age' | 'score';
  }): HumanReviewRequest[] {
    let reviews = Array.from(this.pendingReviews.values());

    // Filter by assignee
    if (options?.assignedTo) {
      reviews = reviews.filter(r => r.assignedTo === options.assignedTo);
    }

    // Filter by priority
    if (options?.priority) {
      reviews = reviews.filter(r => r.priority === options.priority);
    }

    // Sort
    if (options?.sortBy === 'priority') {
      const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      reviews.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
    } else if (options?.sortBy === 'age') {
      reviews.sort((a, b) => a.requestedAt - b.requestedAt); // oldest first
    } else if (options?.sortBy === 'score') {
      reviews.sort((a, b) => a.qualityCheck.overallScore - b.qualityCheck.overallScore); // lowest first
    }

    return reviews;
  }

  /**
   * Get a specific review request
   */
  getReviewRequest(requestId: string): HumanReviewRequest | undefined {
    return this.pendingReviews.get(requestId) || this.completedReviews.get(requestId);
  }

  /**
   * Assign a review to a human reviewer
   */
  assignReview(requestId: string, reviewerId: string): HumanReviewRequest {
    const request = this.pendingReviews.get(requestId);

    if (!request) {
      throw new Error(`Review request ${requestId} not found`);
    }

    request.assignedTo = reviewerId;
    request.status = 'in-progress';

    this.auditLog?.logQualityGateAction('review-assigned', `Assigned review ${requestId} to ${reviewerId}`, {
      requestId,
      reviewerId,
      taskId: request.qualityCheck.taskId,
    });

    return request;
  }

  /**
   * Reassign a review to a different reviewer
   */
  reassignReview(requestId: string, newReviewerId: string): HumanReviewRequest {
    const request = this.pendingReviews.get(requestId);

    if (!request) {
      throw new Error(`Review request ${requestId} not found`);
    }

    const previousReviewer = request.assignedTo;
    request.assignedTo = newReviewerId;

    this.auditLog?.logQualityGateAction(
      'review-reassigned',
      `Reassigned review ${requestId} from ${previousReviewer} to ${newReviewerId}`,
      {
        requestId,
        previousReviewer,
        newReviewerId,
        taskId: request.qualityCheck.taskId,
      }
    );

    return request;
  }

  /**
   * Cancel a pending review
   */
  cancelReview(requestId: string, reason: string): void {
    const request = this.pendingReviews.get(requestId);

    if (!request) {
      throw new Error(`Review request ${requestId} not found`);
    }

    this.pendingReviews.delete(requestId);

    this.auditLog?.logQualityGateAction('review-cancelled', `Cancelled review ${requestId}: ${reason}`, {
      requestId,
      reason,
      taskId: request.qualityCheck.taskId,
    });
  }

  /**
   * Get completed reviews
   */
  getCompletedReviews(options?: {
    reviewedBy?: string;
    limit?: number;
  }): HumanReviewRequest[] {
    let reviews = Array.from(this.completedReviews.values());

    if (options?.reviewedBy) {
      reviews = reviews.filter(r => r.qualityCheck.reviewedBy === options.reviewedBy);
    }

    // Sort by completion time (newest first)
    reviews.sort((a, b) => (b.resolvedAt || 0) - (a.resolvedAt || 0));

    if (options?.limit) {
      reviews = reviews.slice(0, options.limit);
    }

    return reviews;
  }

  /**
   * Get review statistics
   */
  getStats(): {
    pending: number;
    inProgress: number;
    completed: number;
    averageReviewTime: number;
    reviewsByPriority: Record<string, number>;
    reviewsByReviewer: Record<string, number>;
  } {
    const pending = Array.from(this.pendingReviews.values()).filter(r => r.status === 'pending').length;
    const inProgress = Array.from(this.pendingReviews.values()).filter(r => r.status === 'in-progress')
      .length;
    const completed = this.completedReviews.size;

    const reviewsByPriority: Record<string, number> = {};
    for (const request of this.pendingReviews.values()) {
      reviewsByPriority[request.priority] = (reviewsByPriority[request.priority] || 0) + 1;
    }

    const reviewsByReviewer: Record<string, number> = {};
    const reviewTimes: number[] = [];
    for (const request of this.completedReviews.values()) {
      const reviewer = request.qualityCheck.reviewedBy || 'unknown';
      reviewsByReviewer[reviewer] = (reviewsByReviewer[reviewer] || 0) + 1;

      if (request.resolvedAt) {
        reviewTimes.push(request.resolvedAt - request.requestedAt);
      }
    }

    const averageReviewTime =
      reviewTimes.length > 0 ? reviewTimes.reduce((sum, time) => sum + time, 0) / reviewTimes.length : 0;

    return {
      pending,
      inProgress,
      completed,
      averageReviewTime,
      reviewsByPriority,
      reviewsByReviewer,
    };
  }

  /**
   * Register a reviewer for auto-assignment
   */
  registerReviewer(reviewerId: string): void {
    if (!this.reviewerQueue.includes(reviewerId)) {
      this.reviewerQueue.push(reviewerId);
      this.auditLog?.logQualityGateAction('reviewer-registered', `Registered reviewer ${reviewerId}`, {
        reviewerId,
      });
    }
  }

  /**
   * Unregister a reviewer
   */
  unregisterReviewer(reviewerId: string): void {
    this.reviewerQueue = this.reviewerQueue.filter(id => id !== reviewerId);
    this.auditLog?.logQualityGateAction('reviewer-unregistered', `Unregistered reviewer ${reviewerId}`, {
      reviewerId,
    });
  }

  /**
   * Auto-assign a reviewer based on policy
   */
  private autoAssignReviewer(): string | null {
    if (this.reviewerQueue.length === 0) {
      return null;
    }

    if (this.options.autoAssignPolicy === 'round-robin') {
      const reviewer = this.reviewerQueue.shift()!;
      this.reviewerQueue.push(reviewer); // rotate
      return reviewer;
    } else if (this.options.autoAssignPolicy === 'least-busy') {
      const stats = this.getStats();
      const reviewerCounts = stats.reviewsByReviewer;

      // Find reviewer with fewest active reviews
      const leastBusy = this.reviewerQueue.reduce((min, reviewer) => {
        const count = reviewerCounts[reviewer] || 0;
        const minCount = reviewerCounts[min] || 0;
        return count < minCount ? reviewer : min;
      });

      return leastBusy;
    }

    return null;
  }

  /**
   * Determine priority based on quality check results
   */
  private determinePriority(
    qualityCheck: QualityCheck
  ): 'low' | 'medium' | 'high' | 'critical' {
    // Critical failures = critical priority
    if (qualityCheck.checks.some(c => c.criticalFailure)) {
      return 'critical';
    }

    // Very low score = high priority
    if (qualityCheck.overallScore < 0.4) {
      return 'high';
    }

    // Low score = medium priority
    if (qualityCheck.overallScore < 0.6) {
      return 'medium';
    }

    // Otherwise low priority
    return 'low';
  }
}

/**
 * Factory function for easy instantiation
 */
export function createHumanReviewSystem(options?: HumanReviewSystemOptions): HumanReviewSystem {
  return new HumanReviewSystem(options);
}
