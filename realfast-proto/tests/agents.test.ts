/**
 * Tests for AI Agent Pool and Agent Behaviors
 *
 * Tests each agent role's core capabilities and the agent pool management.
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import { AgentPool, AIAgent } from '../src/agents.js';

describe('AgentPool', () => {
  test('should create empty pool', () => {
    const pool = new AgentPool();
    const status = pool.getPoolStatus();

    assert.strictEqual(status.activeAgents, 0);
    assert.strictEqual(status.totalTasks, 0);
    assert.strictEqual(status.agentsByRole.length, 0);
  });

  test('should add agent to pool', () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-analyzer');

    assert.ok(agentId);
    assert.match(agentId, /^agent-\w+/);

    const status = pool.getPoolStatus();
    assert.strictEqual(status.activeAgents, 1);
  });

  test('should retrieve agent by ID', () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-analyzer');

    const agent = pool.getAgent(agentId);
    assert.ok(agent);
    assert.strictEqual(agent.id, agentId);
    assert.strictEqual(agent.role, 'code-analyzer');
    assert.strictEqual(agent.status, 'idle');
  });

  test('should retrieve agent by role', () => {
    const pool = new AgentPool();
    pool.addAgent('code-analyzer');
    pool.addAgent('test-generator');

    const analyzer = pool.getAgentByRole('code-analyzer');
    assert.ok(analyzer);
    assert.strictEqual(analyzer.role, 'code-analyzer');

    const tester = pool.getAgentByRole('test-generator');
    assert.ok(tester);
    assert.strictEqual(tester.role, 'test-generator');
  });

  test('should return null for unknown agent', () => {
    const pool = new AgentPool();
    const agent = pool.getAgent('unknown-id');
    assert.strictEqual(agent, null);
  });

  test('should return null for unavailable role', () => {
    const pool = new AgentPool();
    const agent = pool.getAgentByRole('code-analyzer');
    assert.strictEqual(agent, null);
  });

  test('should track multiple agents', () => {
    const pool = new AgentPool();
    pool.addAgent('code-analyzer');
    pool.addAgent('test-generator');
    pool.addAgent('code-reviewer');

    const status = pool.getPoolStatus();
    assert.strictEqual(status.activeAgents, 3);
    assert.strictEqual(status.agentsByRole.length, 3);
  });

  test('should group agents by role in status', () => {
    const pool = new AgentPool();
    pool.addAgent('code-analyzer');
    pool.addAgent('code-analyzer'); // Another analyzer
    pool.addAgent('test-generator');

    const status = pool.getPoolStatus();
    const analyzerGroup = status.agentsByRole.find(g => g.role === 'code-analyzer');
    const testerGroup = status.agentsByRole.find(g => g.role === 'test-generator');

    assert.ok(analyzerGroup);
    assert.strictEqual(analyzerGroup.count, 2);

    assert.ok(testerGroup);
    assert.strictEqual(testerGroup.count, 1);
  });
});

describe('CodeAnalyzer Agent', () => {
  test('should analyze code complexity', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-analyzer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function test() { if (x) { if (y) { return z; } } }',
    };

    const result = await agent.process(input);

    assert.ok(result);
    assert.ok(result.complexity);
    assert.ok(result.findings);
    assert.ok(Array.isArray(result.findings));

    // Should detect nested complexity
    const complexityFinding = result.findings.find((f: string) =>
      f.toLowerCase().includes('complexity')
    );
    assert.ok(complexityFinding);
  });

  test('should detect missing error handling', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-analyzer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function riskyOperation() { JSON.parse(data); }',
    };

    const result = await agent.process(input);

    // Should warn about potential errors
    const errorHandlingIssue = result.findings.find((f: string) =>
      f.toLowerCase().includes('error') || f.toLowerCase().includes('try')
    );
    assert.ok(errorHandlingIssue);
  });

  test('should count lines of code', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-analyzer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function a() {}\nfunction b() {}\nfunction c() {}',
    };

    const result = await agent.process(input);
    assert.ok(result.linesOfCode);
    assert.strictEqual(result.linesOfCode, 3);
  });
});

describe('TestGenerator Agent', () => {
  test('should generate test skeletons', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('test-generator');
    const agent = pool.getAgent(agentId)!;

    const input = {
      analysis: {
        functions: ['calculateDiscount', 'validateInput'],
      },
    };

    const result = await agent.process(input);

    assert.ok(result);
    assert.ok(result.testCases);
    assert.ok(Array.isArray(result.testCases));
    assert.ok(result.testCases.length > 0);

    // Should include test for each function
    const discountTest = result.testCases.find((t: string) =>
      t.includes('calculateDiscount')
    );
    const validateTest = result.testCases.find((t: string) =>
      t.includes('validateInput')
    );

    assert.ok(discountTest);
    assert.ok(validateTest);
  });

  test('should estimate coverage', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('test-generator');
    const agent = pool.getAgent(agentId)!;

    const input = {
      analysis: { functions: ['test1', 'test2'] },
    };

    const result = await agent.process(input);
    assert.ok(result.estimatedCoverage);
    assert.ok(typeof result.estimatedCoverage === 'number');
    assert.ok(result.estimatedCoverage >= 0 && result.estimatedCoverage <= 100);
  });
});

describe('CodeReviewer Agent', () => {
  test('should review code quality', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-reviewer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function test() { var x = 1; }',
      analysis: { complexity: 5 },
    };

    const result = await agent.process(input);

    assert.ok(result);
    assert.ok(result.issues);
    assert.ok(Array.isArray(result.issues));
    assert.ok(result.score !== undefined);
  });

  test('should catch missing error handling', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-reviewer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'async function fetchData() { return await api.get(); }',
    };

    const result = await agent.process(input);

    const errorHandlingIssue = result.issues.find((issue: string) =>
      issue.toLowerCase().includes('error')
    );
    assert.ok(errorHandlingIssue);
  });

  test('should provide recommendations', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-reviewer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function test() { console.log("debug"); }',
    };

    const result = await agent.process(input);
    assert.ok(result.recommendations);
    assert.ok(Array.isArray(result.recommendations));
  });

  test('should calculate quality score', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('code-reviewer');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function test() {}',
      analysis: { complexity: 1 },
    };

    const result = await agent.process(input);
    assert.ok(typeof result.score === 'number');
    assert.ok(result.score >= 0 && result.score <= 1);
  });
});

describe('DocGenerator Agent', () => {
  test('should extract function signatures', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('doc-generator');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function calculateDiscount(price: number, discount: number): number {}',
      analysis: {},
    };

    const result = await agent.process(input);

    assert.ok(result);
    assert.ok(result.documentation);
    assert.ok(result.documentation.includes('calculateDiscount'));
    assert.ok(result.documentation.includes('price'));
    assert.ok(result.documentation.includes('discount'));
  });

  test('should generate API documentation', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('doc-generator');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'export function publicApi() {}',
      analysis: {},
    };

    const result = await agent.process(input);
    assert.ok(result.apiDocs);
    assert.ok(Array.isArray(result.apiDocs));
  });

  test('should track documentation coverage', async () => {
    const pool = new AgentPool();
    const agentId = pool.addAgent('doc-generator');
    const agent = pool.getAgent(agentId)!;

    const input = {
      code: 'function test1() {}\n/** Documented */\nfunction test2() {}',
      analysis: {},
    };

    const result = await agent.process(input);
    assert.ok(result.coverage !== undefined);
    assert.ok(typeof result.coverage === 'number');
  });
});
