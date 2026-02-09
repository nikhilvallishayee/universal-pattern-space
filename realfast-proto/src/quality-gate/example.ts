/**
 * Quality Gate System - Example Usage
 *
 * Demonstrates how to use the quality gate system in practice.
 */

import {
  createQualityGateSystem,
  createQualityChecker,
  createAuditLog,
  createHumanReviewSystem,
  type TaskOutput,
  type QualityCheck,
} from './index.js';

// Example 1: Basic quality checking
function example1_BasicChecking() {
  console.log('=== Example 1: Basic Quality Checking ===\n');

  const checker = createQualityChecker();

  // Simulate an agent output
  const output: TaskOutput = {
    taskId: 'task-001',
    agentId: 'agent-coder-1',
    content: `
      function authenticateUser(username, password) {
        const user = db.query('SELECT * FROM users WHERE username = ' + username);
        return user && user.password === password;
      }
    `,
    confidence: 0.9,
    metadata: {
      requirements: ['implement authentication', 'validate inputs', 'secure password check'],
      completedRequirements: ['implement authentication', 'secure password check'],
      tokensUsed: 150,
      executionTime: 1200,
    },
  };

  const qualityCheck = checker.runQualityChecks(output);

  console.log(`Task: ${qualityCheck.taskId}`);
  console.log(`Overall Score: ${(qualityCheck.overallScore * 100).toFixed(1)}%`);
  console.log(`Verdict: ${qualityCheck.verdict}\n`);

  console.log('Individual Checks:');
  for (const check of qualityCheck.checks) {
    const status = check.passed ? '✓' : '✗';
    console.log(`  ${status} ${check.name}: ${(check.score * 100).toFixed(1)}% - ${check.details}`);
  }

  console.log('\nAudit Log:');
  for (const entry of qualityCheck.auditLog) {
    console.log(`  [${entry.actor}] ${entry.action}: ${entry.details}`);
  }

  return qualityCheck;
}

// Example 2: Human review workflow
function example2_HumanReview() {
  console.log('\n=== Example 2: Human Review Workflow ===\n');

  const auditLog = createAuditLog();
  const reviewSystem = createHumanReviewSystem({ auditLog });

  // Register reviewers
  reviewSystem.registerReviewer('alice@example.com');
  reviewSystem.registerReviewer('bob@example.com');

  // Create a quality check that needs review
  const qualityCheck: QualityCheck = {
    id: 'qc-002',
    taskId: 'task-002',
    checks: [
      { name: 'confidence', passed: true, score: 0.8, weight: 0.25, details: 'Good confidence' },
      {
        name: 'completeness',
        passed: false,
        score: 0.5,
        weight: 0.25,
        details: 'Missing some requirements',
      },
      { name: 'consistency', passed: true, score: 0.7, weight: 0.2, details: 'Mostly consistent' },
      { name: 'safety', passed: true, score: 1.0, weight: 0.3, details: 'No safety issues' },
    ],
    overallScore: 0.73,
    verdict: 'needs-human-review',
    auditLog: [],
    timestamp: Date.now(),
  };

  // Request human review
  const reviewRequest = reviewSystem.requestHumanReview(qualityCheck, 'high');
  console.log(`Review requested: ${reviewRequest.id}`);
  console.log(`Priority: ${reviewRequest.priority}`);
  console.log(`Status: ${reviewRequest.status}\n`);

  // Get pending reviews
  const pending = reviewSystem.getPendingReviews({ sortBy: 'priority' });
  console.log(`Pending reviews: ${pending.length}\n`);

  // Assign to a reviewer
  reviewSystem.assignReview(reviewRequest.id, 'alice@example.com');
  console.log(`Assigned to: alice@example.com\n`);

  // Human submits review
  const updatedCheck = reviewSystem.submitReview(reviewRequest.id, {
    verdict: 'approved',
    comments: 'Good work overall. Made minor improvements to error handling.',
    reviewerId: 'alice@example.com',
    modifications: ['Added input validation', 'Improved error messages'],
  });

  console.log(`Review completed: ${updatedCheck.verdict}`);
  console.log(`Reviewed by: ${updatedCheck.reviewedBy}\n`);

  // Check stats
  const stats = reviewSystem.getStats();
  console.log('Review Statistics:');
  console.log(`  Total completed: ${stats.completed}`);
  console.log(`  Average review time: ${(stats.averageReviewTime / 1000).toFixed(1)}s`);
}

// Example 3: Complete system with policy
function example3_CompleteSystem() {
  console.log('\n=== Example 3: Complete Quality Gate System ===\n');

  // Create system with custom policy
  const system = createQualityGateSystem({
    policy: {
      autoApproveThreshold: 0.9, // stricter threshold
      rejectThreshold: 0.4,
      requiredChecks: ['safety', 'completeness'],
      humanReviewAlways: false,
      checkWeights: {
        confidence: 0.2,
        completeness: 0.3,
        consistency: 0.2,
        safety: 0.3, // safety most important
      },
    },
  });

  // Register reviewers
  system.humanReview.registerReviewer('alice@example.com');

  // Process a high-quality output
  const goodOutput: TaskOutput = {
    taskId: 'task-003',
    agentId: 'agent-coder-2',
    content: 'const result = await authenticateUser(username, password);',
    confidence: 0.95,
    metadata: {
      requirements: ['implement feature', 'add tests'],
      completedRequirements: ['implement feature', 'add tests'],
    },
  };

  console.log('Processing high-quality output...');
  const goodCheck = system.checker.runQualityChecks(goodOutput);
  console.log(`Result: ${goodCheck.verdict} (score: ${(goodCheck.overallScore * 100).toFixed(1)}%)\n`);

  // Process a low-quality output
  const badOutput: TaskOutput = {
    taskId: 'task-004',
    agentId: 'agent-coder-3',
    content: 'const apiKey = "sk-abc123-secret-key-here";',
    confidence: 0.6,
    metadata: {
      requirements: ['implement feature'],
      completedRequirements: [],
    },
  };

  console.log('Processing low-quality output with safety violations...');
  const badCheck = system.checker.runQualityChecks(badOutput);
  console.log(`Result: ${badCheck.verdict} (score: ${(badCheck.overallScore * 100).toFixed(1)}%)`);
  console.log(
    `Critical failure: ${badCheck.checks.some(c => c.criticalFailure) ? 'YES' : 'NO'}\n`
  );

  // Get system metrics
  const metrics = system.getMetrics();
  console.log('System Metrics:');
  console.log(`  Total checks: ${metrics.totalChecks}`);
  console.log(`  Auto-approved: ${metrics.autoApproved}`);
  console.log(`  Human reviewed: ${metrics.humanReviewed}`);
  console.log(`  Rejected: ${metrics.rejected}`);
  console.log(`  Average score: ${(metrics.averageScore * 100).toFixed(1)}%\n`);

  // Export audit trail
  console.log('Audit Trail (JSON):');
  const auditJSON = system.exportAudit('json');
  console.log(auditJSON.substring(0, 500) + '...\n');
}

// Example 4: Audit log features
function example4_AuditLog() {
  console.log('\n=== Example 4: Audit Log Features ===\n');

  const auditLog = createAuditLog({
    maxEntries: 1000,
    retention: 7 * 24 * 60 * 60 * 1000, // 7 days
  });

  // Log various actions
  auditLog.logAgentAction('agent-001', 'task-started', 'Started working on authentication feature');
  auditLog.logAgentAction('agent-001', 'code-generated', 'Generated authentication function');
  auditLog.logQualityGateAction('quality-check', 'Running safety checks');
  auditLog.logHumanAction('alice@example.com', 'review-submitted', 'Approved with minor changes');

  // Get stats
  const stats = auditLog.getStats();
  console.log('Audit Stats:');
  console.log(`  Total entries: ${stats.totalEntries}`);
  console.log(`  Entries by actor:`, stats.entriesByActor);
  console.log(`  Entries by action:`, stats.entriesByAction);
  console.log(`  Oldest entry: ${stats.oldestEntry?.toISOString()}`);
  console.log(`  Newest entry: ${stats.newestEntry?.toISOString()}\n`);

  // Search log
  const searchResults = auditLog.searchLog('authentication');
  console.log(`Search results for "authentication": ${searchResults.length} entries\n`);

  // Export formats
  console.log('Export as CSV:');
  const csv = auditLog.exportCSV();
  console.log(csv.split('\n').slice(0, 3).join('\n') + '\n...\n');

  console.log('Export as Text:');
  const text = auditLog.exportText();
  console.log(text.substring(0, 300) + '...\n');
}

// Run all examples
if (import.meta.url === `file://${process.argv[1]}`) {
  example1_BasicChecking();
  example2_HumanReview();
  example3_CompleteSystem();
  example4_AuditLog();
}

export {
  example1_BasicChecking,
  example2_HumanReview,
  example3_CompleteSystem,
  example4_AuditLog,
};
