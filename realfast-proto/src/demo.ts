#!/usr/bin/env node
/**
 * DHIO Cockpit x RealFast Proto - Live Demo
 *
 * Multi-agent AI pipeline with quality gates and human oversight.
 * Inspired by RealFast.ai's Vayu: "An Iron Man suit for IT services teams"
 *
 * Live demo for Sidu Ponnappa - showing swarm-built agent orchestration.
 */

import { createAgent } from './agents/index.js';
import { QualityChecker } from './quality-gate/checker.js';
import { AuditLog, createAuditLog } from './quality-gate/audit-log.js';
import type { AgentTask, TaskOutput, AgentRole } from './orchestrator/types.js';
import type { TaskOutput as QGTaskOutput } from './quality-gate/types.js';

// ANSI colors
const C = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  cyan: '\x1b[36m', green: '\x1b[32m', yellow: '\x1b[33m',
  red: '\x1b[31m', magenta: '\x1b[35m', blue: '\x1b[34m',
};

const p = (text: string, c = '') => console.log(`${c}${text}${C.reset}`);
const header = (text: string) => {
  console.log();
  p('═'.repeat(64), C.cyan);
  p(`  ${text}`, C.bold);
  p('═'.repeat(64), C.cyan);
  console.log();
};

// Sample code to analyze - a real function with branching logic
const SAMPLE_CODE = `
export function calculateDiscount(price: number, customerType: string, loyaltyYears: number): number {
  if (price <= 0) throw new Error('Price must be positive');
  let discount = 0;
  if (customerType === 'premium') {
    discount = 0.2;
  } else if (customerType === 'business') {
    discount = 0.15;
  } else {
    discount = 0.05;
  }
  if (loyaltyYears > 5) discount += 0.1;
  if (loyaltyYears > 10) discount += 0.05;
  return Math.round(price * (1 - discount) * 100) / 100;
}

export function validateEmail(email: string): boolean {
  if (!email || typeof email !== 'string') return false;
  const regex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  return regex.test(email);
}
`;

function makeTask(role: AgentRole, code: string): AgentTask {
  return {
    id: `task-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    type: role,
    input: { code, context: 'Demo analysis pipeline' },
    status: 'queued',
    humanReviewRequired: false,
    createdAt: Date.now(),
  };
}

async function run() {
  header('DHIO Cockpit x RealFast Proto');
  p('Multi-Agent Pipeline with Quality Gates', C.dim);
  p('Inspired by RealFast.ai Vayu - "Iron Man suit for IT teams"', C.dim);
  p(`Built by swarm: 4 agents in parallel, wired live\n`, C.dim);

  // --- Step 1: Create agents ---
  p('1. Creating Agent Pool', C.bold);
  const agents = {
    analyzer: createAgent('analyzer', 'CodeScope'),
    tester: createAgent('tester', 'TestForge'),
    reviewer: createAgent('reviewer', 'GuardRail'),
    documenter: createAgent('documenter', 'DocWeave'),
  };
  for (const [role, agent] of Object.entries(agents)) {
    p(`   ${C.green}✓${C.reset} ${role}: ${agent.name} (${agent.id.slice(0, 8)}...)`);
  }

  // --- Step 2: Quality gate ---
  p('\n2. Initializing Quality Gate', C.bold);
  const checker = new QualityChecker({
    autoApproveThreshold: 0.85,
    rejectThreshold: 0.3,
    humanReviewAlways: false,
  });
  const auditLog = createAuditLog();
  p(`   ${C.green}✓${C.reset} Thresholds: auto-approve > 0.85, reject < 0.3`);
  p(`   ${C.green}✓${C.reset} Checks: confidence, completeness, consistency, safety`);

  // --- Step 3: Pipeline stages ---
  const stages: { name: string; role: AgentRole; icon: string }[] = [
    { name: 'Analyze', role: 'analyzer', icon: '🔍' },
    { name: 'Generate Tests', role: 'tester', icon: '🧪' },
    { name: 'Code Review', role: 'reviewer', icon: '👁️' },
    { name: 'Document', role: 'documenter', icon: '📝' },
  ];

  p('\n3. Pipeline: ' + stages.map(s => s.name).join(' → '), C.bold);

  header('Pipeline Execution');

  const results: { stage: string; output: TaskOutput; qualityScore: number; verdict: string; duration: number }[] = [];

  for (const stage of stages) {
    p(`\n${stage.icon} Stage: ${stage.name}`, C.magenta + C.bold);
    p('─'.repeat(56), C.dim);

    const agent = agents[stage.role as keyof typeof agents];
    const task = makeTask(stage.role, SAMPLE_CODE);

    p(`   Agent: ${agent.name} (${stage.role})`, C.cyan);

    const start = Date.now();
    const output = await agent.execute(task);
    const duration = Date.now() - start;

    p(`   ${C.green}✓${C.reset} Completed in ${duration}ms`);
    p(`   Confidence: ${(output.confidence * 100).toFixed(0)}%`, C.dim);
    p(`   Artifacts: ${output.artifacts.length}`, C.dim);

    // Show preview of first artifact
    if (output.artifacts.length > 0) {
      const preview = output.artifacts[0].content.split('\n').slice(0, 3).join('\n');
      p(`   Preview:`, C.dim);
      preview.split('\n').forEach(line => p(`     ${line}`, C.dim));
      if (output.artifacts[0].content.split('\n').length > 3) p('     ...', C.dim);
    }

    // Quality gate - bridge agent output to quality-gate format
    p(`   ${C.cyan}🛡️  Quality check...${C.reset}`);
    const qgOutput: QGTaskOutput = {
      taskId: task.id,
      agentId: agent.id,
      content: output.artifacts.length > 0 ? output.artifacts[0].content : output.result,
      confidence: output.confidence,
      metadata: {
        requirements: [],
        completedRequirements: [],
        executionTime: duration,
      },
    };
    const qc = checker.runQualityChecks(qgOutput);

    const verdictIcon = qc.verdict === 'auto-approved' ? `${C.green}✓` : qc.verdict === 'needs-human-review' ? `${C.yellow}⚠` : `${C.red}✗`;
    p(`   ${verdictIcon} ${qc.verdict}${C.reset} (score: ${qc.overallScore.toFixed(2)})`);

    qc.checks.forEach(check => {
      const ci = check.passed ? `${C.green}✓` : `${C.red}✗`;
      p(`     ${ci}${C.reset} ${check.name}: ${check.score.toFixed(2)} - ${check.details.slice(0, 60)}`);
    });

    // Log to audit
    auditLog.log({
      action: `stage:${stage.name.toLowerCase().replace(/\s/g, '-')}`,
      actor: 'quality-gate',
      details: `${stage.name}: verdict=${qc.verdict}, score=${qc.overallScore.toFixed(2)}`,
      timestamp: Date.now(),
    });

    results.push({ stage: stage.name, output, qualityScore: qc.overallScore, verdict: qc.verdict, duration });
  }

  // --- Summary ---
  header('Audit Trail');
  const log = auditLog.getLog();
  log.forEach((entry, i) => {
    p(`${i + 1}. [${new Date(entry.timestamp).toISOString().slice(11, 23)}] ${entry.details}`, C.dim);
  });

  header('Execution Summary');
  const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);
  const avgScore = results.reduce((sum, r) => sum + r.qualityScore, 0) / results.length;
  const approved = results.filter(r => r.verdict === 'auto-approved').length;

  p(`Stages:     ${results.length}`, C.cyan);
  p(`Approved:   ${approved}/${results.length}`, approved === results.length ? C.green : C.yellow);
  p(`Avg Score:  ${avgScore.toFixed(2)}`, C.cyan);
  p(`Duration:   ${totalDuration}ms`, C.cyan);
  p(`Artifacts:  ${results.reduce((sum, r) => sum + r.output.artifacts.length, 0)} total`, C.cyan);

  console.log();
  results.forEach(r => {
    const icon = r.verdict === 'auto-approved' ? `${C.green}✓` : `${C.yellow}⚠`;
    p(`  ${icon}${C.reset} ${r.stage.padEnd(16)} score=${r.qualityScore.toFixed(2)}  ${r.duration}ms  ${r.output.artifacts.length} artifacts`);
  });

  header('Demo Complete');
  p('Built by 4 swarm agents in parallel, wired live in dhio-cockpit.', C.green);
  p('Architecture: Composable agents + Quality gates + Audit trail', C.dim);
  p('Philosophy: "Iron Man suit" - AI augments, human decides.', C.dim);
  p('', C.reset);
}

run().catch(err => {
  p(`\n✗ ${err.message}`, C.red);
  console.error(err);
  process.exit(1);
});
