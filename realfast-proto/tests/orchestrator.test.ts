/**
 * Tests for PipelineOrchestrator
 *
 * Tests pipeline creation, stage execution, dependency resolution,
 * and quality gate integration.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import { PipelineOrchestrator, Pipeline, PipelineStage } from '../src/orchestrator.js';
import { AgentPool } from '../src/agents.js';
import { QualityGate } from '../src/quality-gate.js';

describe('PipelineOrchestrator', () => {
  test('should create pipeline with stages', () => {
    const agentPool = new AgentPool();
    const qualityGate = new QualityGate();
    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stages: PipelineStage[] = [
      {
        name: 'analyze',
        agentRole: 'code-analyzer',
        input: { type: 'code', content: 'sample code' },
        outputType: 'analysis',
      },
    ];

    const pipeline: Pipeline = {
      id: 'test-pipeline',
      name: 'Test Pipeline',
      stages,
      createdAt: new Date(),
    };

    assert.ok(pipeline);
    assert.strictEqual(pipeline.stages.length, 1);
    assert.strictEqual(pipeline.stages[0].name, 'analyze');
  });

  test('should execute single stage pipeline', async () => {
    const agentPool = new AgentPool();
    agentPool.addAgent('code-analyzer');

    const qualityGate = new QualityGate({
      autoApproveThreshold: 0.5, // Lower threshold for test
    });

    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stage: PipelineStage = {
      name: 'analyze',
      agentRole: 'code-analyzer',
      input: { type: 'code', content: 'function test() {}' },
      outputType: 'analysis',
    };

    const result = await orchestrator.executeStage('test-pipeline', stage, stage.input!);

    assert.ok(result);
    assert.ok(result.output);
    assert.strictEqual(result.stage, 'analyze');
    assert.ok(result.completedAt);
  });

  test('should respect stage dependencies', async () => {
    const agentPool = new AgentPool();
    agentPool.addAgent('code-analyzer');
    agentPool.addAgent('test-generator');

    const qualityGate = new QualityGate({ autoApproveThreshold: 0.5 });
    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stages: PipelineStage[] = [
      {
        name: 'analyze',
        agentRole: 'code-analyzer',
        input: { type: 'code', content: 'test code' },
        outputType: 'analysis',
      },
      {
        name: 'generate-tests',
        agentRole: 'test-generator',
        dependencies: ['analyze'], // Depends on first stage
        outputType: 'tests',
      },
    ];

    // Execute first stage
    const result1 = await orchestrator.executeStage(
      'test-pipeline',
      stages[0],
      stages[0].input!
    );
    assert.ok(result1);

    // Second stage should reference first stage's output
    const result2 = await orchestrator.executeStage(
      'test-pipeline',
      stages[1],
      { type: 'derived', dependencies: stages[1].dependencies! }
    );

    assert.ok(result2);
    assert.ok(result2.metadata?.dependencies);
    assert.deepStrictEqual(result2.metadata.dependencies, ['analyze']);
  });

  test('should integrate with quality gate', async () => {
    const agentPool = new AgentPool();
    agentPool.addAgent('code-analyzer');

    const qualityGate = new QualityGate({
      autoApproveThreshold: 0.85,
      autoRejectThreshold: 0.50,
    });

    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stage: PipelineStage = {
      name: 'analyze',
      agentRole: 'code-analyzer',
      input: { type: 'code', content: 'function test() { return 42; }' },
      outputType: 'analysis',
    };

    const result = await orchestrator.executeStage('test-pipeline', stage, stage.input!);

    // Check that quality gate was invoked
    const auditLog = qualityGate.getAuditLog();
    assert.strictEqual(auditLog.length, 1);
    assert.strictEqual(auditLog[0].stageId, 'analyze');
  });

  test('should handle missing agent gracefully', async () => {
    const agentPool = new AgentPool(); // Empty pool
    const qualityGate = new QualityGate();
    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stage: PipelineStage = {
      name: 'analyze',
      agentRole: 'code-analyzer',
      input: { type: 'code', content: 'test' },
      outputType: 'analysis',
    };

    await assert.rejects(
      async () => {
        await orchestrator.executeStage('test-pipeline', stage, stage.input!);
      },
      {
        message: /no agent available/i,
      }
    );
  });

  test('should track pipeline execution metadata', async () => {
    const agentPool = new AgentPool();
    const analyzerId = agentPool.addAgent('code-analyzer');

    const qualityGate = new QualityGate({ autoApproveThreshold: 0.5 });
    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stage: PipelineStage = {
      name: 'analyze',
      agentRole: 'code-analyzer',
      input: { type: 'code', content: 'test code' },
      outputType: 'analysis',
    };

    const result = await orchestrator.executeStage('test-pipeline', stage, stage.input!);

    assert.ok(result.metadata);
    assert.ok(result.metadata.agentId);
    assert.ok(result.metadata.startedAt);
    assert.ok(result.metadata.duration);
    assert.strictEqual(result.metadata.agentId, analyzerId);
  });

  test('should support multiple stages in sequence', async () => {
    const agentPool = new AgentPool();
    agentPool.addAgent('code-analyzer');
    agentPool.addAgent('test-generator');
    agentPool.addAgent('code-reviewer');

    const qualityGate = new QualityGate({ autoApproveThreshold: 0.5 });
    const orchestrator = new PipelineOrchestrator(agentPool, qualityGate);

    const stages: PipelineStage[] = [
      {
        name: 'analyze',
        agentRole: 'code-analyzer',
        input: { type: 'code', content: 'test' },
        outputType: 'analysis',
      },
      {
        name: 'generate-tests',
        agentRole: 'test-generator',
        dependencies: ['analyze'],
        outputType: 'tests',
      },
      {
        name: 'review',
        agentRole: 'code-reviewer',
        dependencies: ['analyze', 'generate-tests'],
        outputType: 'review',
      },
    ];

    // Execute all stages
    const results = [];
    for (const stage of stages) {
      const input = stage.input || { type: 'derived', dependencies: stage.dependencies! };
      const result = await orchestrator.executeStage('test-pipeline', stage, input);
      results.push(result);
    }

    assert.strictEqual(results.length, 3);
    assert.strictEqual(results[0].stage, 'analyze');
    assert.strictEqual(results[1].stage, 'generate-tests');
    assert.strictEqual(results[2].stage, 'review');

    // Verify audit trail
    const auditLog = qualityGate.getAuditLog();
    assert.strictEqual(auditLog.length, 3);
  });
});
