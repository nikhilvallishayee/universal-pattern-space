/**
 * Tests for Quality Gate System
 *
 * Tests quality checking, human review triggers, audit logging,
 * and required check enforcement.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import { QualityGate, QualityCheckInput } from '../src/quality-gate.js';

describe('QualityGate', () => {
  test('should create gate with default config', () => {
    const gate = new QualityGate();
    assert.ok(gate);

    const auditLog = gate.getAuditLog();
    assert.strictEqual(auditLog.length, 0);
  });

  test('should create gate with custom config', () => {
    const gate = new QualityGate({
      autoApproveThreshold: 0.90,
      autoRejectThreshold: 0.40,
      requiredChecks: ['completeness', 'correctness', 'security'],
    });
    assert.ok(gate);
  });

  test('should auto-approve above threshold', async () => {
    const gate = new QualityGate({
      autoApproveThreshold: 0.85,
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'high quality output',
        completeness: 1.0,
        correctness: 0.95,
      },
      metadata: {},
    };

    const result = await gate.check(input);

    assert.strictEqual(result.approved, true);
    assert.strictEqual(result.requiresHumanReview, false);
    assert.ok(result.score >= 0.85);
    assert.strictEqual(result.decision, 'AUTO_APPROVED');
  });

  test('should auto-reject below threshold', async () => {
    const gate = new QualityGate({
      autoRejectThreshold: 0.50,
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'low quality output',
        completeness: 0.3,
        correctness: 0.2,
      },
      metadata: {},
    };

    const result = await gate.check(input);

    assert.strictEqual(result.approved, false);
    assert.strictEqual(result.requiresHumanReview, false);
    assert.ok(result.score < 0.50);
    assert.strictEqual(result.decision, 'AUTO_REJECTED');
    assert.ok(result.issues.length > 0);
  });

  test('should require human review in middle zone', async () => {
    const gate = new QualityGate({
      autoApproveThreshold: 0.85,
      autoRejectThreshold: 0.50,
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'medium quality output',
        completeness: 0.7,
        correctness: 0.65,
      },
      metadata: {},
    };

    const result = await gate.check(input);

    assert.strictEqual(result.approved, false);
    assert.strictEqual(result.requiresHumanReview, true);
    assert.ok(result.score >= 0.50 && result.score < 0.85);
    assert.strictEqual(result.decision, 'REQUIRES_HUMAN_REVIEW');
  });

  test('should enforce required checks', async () => {
    const gate = new QualityGate({
      requiredChecks: ['completeness', 'correctness'],
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'output',
        completeness: 0.9,
        // Missing 'correctness' check
      },
      metadata: {},
    };

    const result = await gate.check(input);

    assert.strictEqual(result.approved, false);
    const missingCheckIssue = result.issues.find(issue =>
      issue.includes('Required check missing')
    );
    assert.ok(missingCheckIssue);
  });

  test('should pass when all required checks present', async () => {
    const gate = new QualityGate({
      requiredChecks: ['completeness', 'correctness'],
      autoApproveThreshold: 0.85,
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'output',
        completeness: 0.95,
        correctness: 0.90,
      },
      metadata: {},
    };

    const result = await gate.check(input);
    assert.strictEqual(result.approved, true);
  });

  test('should log all checks to audit trail', async () => {
    const gate = new QualityGate();

    const input1: QualityCheckInput = {
      stageId: 'stage-1',
      pipelineId: 'test-pipeline',
      output: { data: 'test' },
      metadata: {},
    };

    const input2: QualityCheckInput = {
      stageId: 'stage-2',
      pipelineId: 'test-pipeline',
      output: { data: 'test' },
      metadata: {},
    };

    await gate.check(input1);
    await gate.check(input2);

    const auditLog = gate.getAuditLog();
    assert.strictEqual(auditLog.length, 2);
    assert.strictEqual(auditLog[0].stageId, 'stage-1');
    assert.strictEqual(auditLog[1].stageId, 'stage-2');
  });

  test('should include timestamp in audit entries', async () => {
    const gate = new QualityGate();

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: { data: 'test' },
      metadata: {},
    };

    await gate.check(input);

    const auditLog = gate.getAuditLog();
    assert.ok(auditLog[0].timestamp);
    assert.ok(auditLog[0].timestamp instanceof Date);
  });

  test('should record reviewer in audit trail', async () => {
    const gate = new QualityGate();

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: { data: 'test' },
      metadata: {},
    };

    await gate.check(input);

    const auditLog = gate.getAuditLog();
    assert.ok(auditLog[0].reviewedBy);
    assert.match(auditLog[0].reviewedBy, /^(system|human)$/);
  });

  test('should track issues in audit log', async () => {
    const gate = new QualityGate({
      autoRejectThreshold: 0.50,
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'low quality',
        completeness: 0.2,
      },
      metadata: {},
    };

    await gate.check(input);

    const auditLog = gate.getAuditLog();
    assert.ok(auditLog[0].issues);
    assert.ok(auditLog[0].issues.length > 0);
  });

  test('should calculate score from multiple metrics', async () => {
    const gate = new QualityGate();

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'test',
        completeness: 0.8,
        correctness: 0.9,
        quality: 0.85,
      },
      metadata: {},
    };

    const result = await gate.check(input);

    // Score should be average of all quality metrics
    const expectedScore = (0.8 + 0.9 + 0.85) / 3;
    assert.ok(Math.abs(result.score - expectedScore) < 0.01);
  });

  test('should handle missing quality metrics gracefully', async () => {
    const gate = new QualityGate();

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'test',
        // No quality metrics
      },
      metadata: {},
    };

    const result = await gate.check(input);

    // Should default to middle score
    assert.ok(result.score > 0 && result.score < 1);
    assert.strictEqual(result.requiresHumanReview, true);
  });

  test('should support custom quality metrics', async () => {
    const gate = new QualityGate({
      autoApproveThreshold: 0.90,
    });

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'test-pipeline',
      output: {
        data: 'test',
        security: 0.95,
        performance: 0.88,
        maintainability: 0.92,
      },
      metadata: {},
    };

    const result = await gate.check(input);

    // Should consider all quality metrics
    assert.ok(result.score > 0.85);
  });

  test('should maintain audit log order', async () => {
    const gate = new QualityGate();

    const stages = ['stage-1', 'stage-2', 'stage-3'];
    for (const stageId of stages) {
      await gate.check({
        stageId,
        pipelineId: 'test-pipeline',
        output: { data: 'test' },
        metadata: {},
      });
    }

    const auditLog = gate.getAuditLog();
    assert.strictEqual(auditLog.length, 3);
    assert.strictEqual(auditLog[0].stageId, 'stage-1');
    assert.strictEqual(auditLog[1].stageId, 'stage-2');
    assert.strictEqual(auditLog[2].stageId, 'stage-3');
  });

  test('should include pipeline ID in audit entries', async () => {
    const gate = new QualityGate();

    const input: QualityCheckInput = {
      stageId: 'test-stage',
      pipelineId: 'my-pipeline-123',
      output: { data: 'test' },
      metadata: {},
    };

    await gate.check(input);

    const auditLog = gate.getAuditLog();
    assert.strictEqual(auditLog[0].pipelineId, 'my-pipeline-123');
  });
});
