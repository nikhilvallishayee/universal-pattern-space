# Quality Gate System

**The Critical Trust Layer for AI-Augmented Work**

> "Automation without oversight creates vulnerability, not capability."
> — Sidu Ponnappa, RealFast.ai

## Overview

The Quality Gate System is inspired by RealFast.ai's production-tested approach to making AI-augmented work trustworthy. Every AI agent output passes through transparent, auditable validation before approval.

### Key Principles

1. **Human Authority**: Humans are always the final decision-maker (the "Iron Man suit" principle)
2. **Full Auditability**: Every AI decision is logged for SOC2 compliance
3. **Transparent Validation**: Quality checks are clear, configurable, and explainable
4. **Safety First**: Security and safety violations trigger automatic rejection

## Architecture

```
┌─────────────────┐
│   AI Agent      │
│    Output       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Quality Checker │ ──► Auto-approve (score ≥ 0.85)
│  4 Built-in     │
│    Checks       │
└────────┬────────┘
         │
         ▼
    Score < 0.85?
         │
         ▼
┌─────────────────┐
│ Human Review    │
│   Request       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Human Makes    │
│  Final Decision │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Audit Log      │ ──► SOC2 compliance
│  (immutable)    │     Full traceability
└─────────────────┘
```

## Components

### 1. Quality Checker

Validates agent outputs against 4 built-in checks:

| Check | Weight | Description |
|-------|--------|-------------|
| **Confidence** | 25% | Is the agent confident enough? (≥70% required) |
| **Completeness** | 25% | Are all required artifacts present? (≥80% required) |
| **Consistency** | 20% | Does output match input requirements? (≥60% required) |
| **Safety** | 30% | No dangerous patterns (SQL injection, secrets, etc.) |

**Safety checks** detect:
- SQL injection patterns
- Exposed API keys, passwords, secrets
- Path traversal vulnerabilities
- XSS vulnerabilities

### 2. Audit Log

Immutable record of every action:

- **What**: Action type and details
- **Who**: Agent, quality gate, or human
- **When**: Precise timestamp
- **Why**: Context and metadata

Export formats: JSON, CSV, Text

### 3. Human Review System

Manages the human-in-the-loop workflow:

- Request reviews with priority levels
- Auto-assign reviewers (round-robin, least-busy, manual)
- Track review status and completion
- Record human decisions and modifications

## Usage

### Basic Quality Checking

```typescript
import { createQualityChecker, TaskOutput } from './quality-gate';

const checker = createQualityChecker();

const output: TaskOutput = {
  taskId: 'task-001',
  agentId: 'agent-coder-1',
  content: 'const result = await processData(input);',
  confidence: 0.9,
  metadata: {
    requirements: ['implement feature', 'add error handling'],
    completedRequirements: ['implement feature', 'add error handling'],
  },
};

const qualityCheck = checker.runQualityChecks(output);

console.log(qualityCheck.verdict); // 'auto-approved', 'needs-human-review', or 'rejected'
console.log(qualityCheck.overallScore); // 0-1
console.log(qualityCheck.checks); // Individual check results
```

### Human Review Workflow

```typescript
import { createHumanReviewSystem } from './quality-gate';

const reviewSystem = createHumanReviewSystem();

// Register reviewers
reviewSystem.registerReviewer('alice@example.com');
reviewSystem.registerReviewer('bob@example.com');

// Request review
const reviewRequest = reviewSystem.requestHumanReview(qualityCheck, 'high');

// Get pending reviews
const pending = reviewSystem.getPendingReviews({
  sortBy: 'priority'
});

// Submit review
const updatedCheck = reviewSystem.submitReview(reviewRequest.id, {
  verdict: 'approved',
  comments: 'Looks good, made minor improvements',
  reviewerId: 'alice@example.com',
  modifications: ['Added input validation'],
});
```

### Complete System

```typescript
import { createQualityGateSystem } from './quality-gate';

const system = createQualityGateSystem({
  policy: {
    autoApproveThreshold: 0.85,
    rejectThreshold: 0.3,
    requiredChecks: ['safety', 'completeness'],
    humanReviewAlways: false, // Set true for RealFast-style always-review
  },
});

// Register reviewers
system.humanReview.registerReviewer('alice@example.com');

// Process output
const qualityCheck = await system.processOutput(output);

// Get metrics
const metrics = system.getMetrics();
console.log(`Auto-approved: ${metrics.autoApproved}`);
console.log(`Human reviewed: ${metrics.humanReviewed}`);
console.log(`Average score: ${metrics.averageScore}`);

// Export audit trail for compliance
const auditJSON = system.exportAudit('json');
const auditCSV = system.exportAudit('csv');
```

### Audit Log

```typescript
import { createAuditLog } from './quality-gate';

const auditLog = createAuditLog({
  maxEntries: 10000,
  retention: 7 * 24 * 60 * 60 * 1000, // 7 days
});

// Log actions
auditLog.logAgentAction('agent-001', 'task-completed', 'Generated authentication code');
auditLog.logQualityGateAction('quality-check', 'Safety check passed');
auditLog.logHumanAction('alice@example.com', 'review-approved', 'Approved with changes');

// Search and filter
const results = auditLog.searchLog('authentication');
const humanActions = auditLog.getLogByActor('human');
const recent = auditLog.getLogByTimeRange(Date.now() - 3600000, Date.now());

// Export for compliance
const json = auditLog.exportJSON();
const csv = auditLog.exportCSV();
const text = auditLog.exportText();

// Statistics
const stats = auditLog.getStats();
console.log(stats.entriesByActor); // { agent: 150, human: 45, quality-gate: 200 }
console.log(stats.entriesByAction); // { 'task-completed': 50, ... }
```

## Configuration

### Quality Policy

```typescript
interface QualityPolicy {
  autoApproveThreshold: number;    // Default: 0.85
  rejectThreshold: number;          // Default: 0.3
  requiredChecks: string[];         // Default: ['confidence', 'completeness', 'safety']
  humanReviewAlways: boolean;       // Default: false (true for RealFast-style)
  checkWeights?: Record<string, number>; // Custom check weights
  criticalChecks?: string[];        // Checks that cause instant rejection on failure
}
```

### Check Weights

Default weights (totaling 1.0):
- Confidence: 0.25
- Completeness: 0.25
- Consistency: 0.20
- Safety: 0.30

Customize for your needs:

```typescript
const checker = createQualityChecker({
  checkWeights: {
    confidence: 0.2,
    completeness: 0.3,
    consistency: 0.1,
    safety: 0.4, // Emphasize safety
  },
});
```

## Decision Flow

```
Output arrives
    │
    ▼
Run 4 checks
    │
    ├─► Critical failure? ──► REJECT
    │
    ├─► Required check fails? ──► REJECT
    │
    ├─► humanReviewAlways = true? ──► HUMAN REVIEW
    │
    └─► Calculate overall score
            │
            ├─► Score ≥ 0.85? ──► AUTO-APPROVE
            │
            ├─► Score ≤ 0.3? ──► REJECT
            │
            └─► 0.3 < Score < 0.85? ──► HUMAN REVIEW
```

## Real-World Integration

### With Task Execution System

```typescript
import { createQualityGateSystem } from './quality-gate';
import { executeTask } from './task-executor';

const qualityGate = createQualityGateSystem();

async function executeTaskWithQualityGate(task) {
  // Agent executes task
  const output = await executeTask(task);

  // Quality gate validates
  const qualityCheck = await qualityGate.processOutput(output);

  if (qualityCheck.verdict === 'auto-approved') {
    return { status: 'approved', output };
  }

  if (qualityCheck.verdict === 'rejected') {
    return { status: 'rejected', reason: qualityCheck.checks };
  }

  if (qualityCheck.verdict === 'needs-human-review') {
    // Human reviews and decides
    const reviewRequest = await waitForHumanReview(qualityCheck);
    return { status: 'human-approved', output, review: reviewRequest };
  }
}
```

### Dashboard Integration

```typescript
// Get real-time metrics for dashboard
const metrics = qualityGate.getMetrics();

const dashboardData = {
  totalTasks: metrics.totalChecks,
  automationRate: (metrics.autoApproved / metrics.totalChecks) * 100,
  qualityScore: metrics.averageScore * 100,
  avgReviewTime: metrics.averageReviewTime / 1000, // seconds
  pendingReviews: qualityGate.humanReview.getPendingReviews().length,
};
```

## Benefits

1. **Trust**: Every AI decision is validated and auditable
2. **Safety**: Automatic detection of security vulnerabilities
3. **Compliance**: SOC2-ready audit trails
4. **Transparency**: Clear explanation of why outputs are approved/rejected
5. **Human Control**: Humans remain in charge, AI augments
6. **Metrics**: Track quality trends over time

## Philosophy

This system embodies Sidu Ponnappa's insight: AI isn't about replacing humans, it's about building better tools that keep humans in control. Like an Iron Man suit, AI amplifies human capability while the human shapes the outcome.

The quality gate is the enforcement mechanism for this philosophy. It ensures that automation enhances capability without creating vulnerability.

## Examples

See `example.ts` for complete working examples:

```bash
# Run examples (if you have a runner)
ts-node example.ts
```

## Next Steps

1. **Integration**: Connect to your task execution system
2. **Customization**: Adjust policies and weights for your domain
3. **Monitoring**: Set up dashboards to track quality metrics
4. **Review Process**: Train reviewers on the human review workflow
5. **Compliance**: Configure audit log retention per your requirements

## References

- [RealFast.ai](https://realfast.ai) - Production AI-augmented software development
- [SOC2 Compliance](https://www.aicpa.org/soc2) - Security and audit requirements
- "The Iron Man Suit" - AI augments, humans decide

---

**Remember**: Quality gates aren't about slowing down work—they're about making AI-augmented work trustworthy enough to move fast with confidence.
