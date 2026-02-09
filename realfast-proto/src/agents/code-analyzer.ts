import { BaseAgent } from './base-agent';
import { AgentTask, TaskOutput, Artifact } from '../orchestrator/types';

interface AnalysisFindings {
  complexity: number;
  issues: string[];
  metrics: {
    functionCount: number;
    avgFunctionLength: number;
    maxFunctionLength: number;
    branchCount: number;
  };
}

export class CodeAnalyzer extends BaseAgent {
  constructor(name: string = 'CodeAnalyzer') {
    super('analyzer', name);
  }

  protected async process(task: AgentTask): Promise<TaskOutput> {
    const code = task.input.code as string || '';

    const findings = this.analyzeCode(code);
    const confidence = this.calculateConfidence(findings, code);

    const artifact: Artifact = {
      type: 'analysis',
      content: JSON.stringify(findings, null, 2),
      metadata: {
        complexity: findings.complexity,
        issueCount: findings.issues.length,
        metrics: findings.metrics
      }
    };

    return {
      artifacts: [artifact],
      reasoning: this.buildReasoning(findings),
      confidence,
      nextSteps: this.suggestNextSteps(findings)
    };
  }

  private analyzeCode(code: string): AnalysisFindings {
    const lines = code.split('\n').filter(l => l.trim());
    const functions = this.extractFunctions(code);

    // Calculate cyclomatic complexity (simplified)
    const wordKeywords = ['if', 'else', 'for', 'while', 'case', 'catch'];
    const symbolKeywords = ['&&', '||'];
    let branchCount = 0;
    for (const keyword of wordKeywords) {
      const regex = new RegExp(`\\b${keyword}\\b`, 'g');
      branchCount += (code.match(regex) || []).length;
    }
    for (const symbol of symbolKeywords) {
      const escaped = symbol.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      branchCount += (code.match(new RegExp(escaped, 'g')) || []).length;
    }
    // Count ternary operators
    branchCount += (code.match(/\?[^?]/g) || []).length;

    const complexity = branchCount + functions.length + 1;

    // Analyze function lengths
    const functionLengths = functions.map(f => f.body.split('\n').length);
    const avgLength = functionLengths.length > 0
      ? functionLengths.reduce((a, b) => a + b, 0) / functionLengths.length
      : 0;
    const maxLength = functionLengths.length > 0 ? Math.max(...functionLengths) : 0;

    // Identify issues
    const issues: string[] = [];

    // Check function length
    if (maxLength > 50) {
      issues.push(`Long function detected (${maxLength} lines). Consider breaking into smaller functions.`);
    }

    // Check complexity
    if (complexity > 20) {
      issues.push(`High cyclomatic complexity (${complexity}). Refactor to reduce branching.`);
    }

    // Check naming conventions
    const poorlyNamedFunctions = functions.filter(f =>
      f.name.length < 3 || !/^[a-z][a-zA-Z0-9]*$/.test(f.name)
    );
    if (poorlyNamedFunctions.length > 0) {
      issues.push(`${poorlyNamedFunctions.length} function(s) with unclear names: ${poorlyNamedFunctions.map(f => f.name).join(', ')}`);
    }

    // Check for common anti-patterns
    if (code.includes('any') && code.includes('typescript')) {
      issues.push('Excessive use of "any" type. Consider proper typing.');
    }

    if (code.includes('console.log')) {
      issues.push('Debug statements (console.log) found. Remove before production.');
    }

    // Check for nested callbacks (callback hell)
    const nestedCallbacks = (code.match(/function.*{[^}]*function.*{[^}]*function/g) || []).length;
    if (nestedCallbacks > 0) {
      issues.push(`Nested callbacks detected (${nestedCallbacks}). Consider using async/await.`);
    }

    return {
      complexity,
      issues,
      metrics: {
        functionCount: functions.length,
        avgFunctionLength: Math.round(avgLength * 10) / 10,
        maxFunctionLength: maxLength,
        branchCount
      }
    };
  }

  private extractFunctions(code: string): Array<{ name: string; body: string }> {
    const functions: Array<{ name: string; body: string }> = [];

    // Match function declarations, arrow functions, and methods
    const patterns = [
      /function\s+(\w+)\s*\([^)]*\)\s*{([^}]*)}/g,
      /const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*{([^}]*)}/g,
      /(\w+)\s*\([^)]*\)\s*{([^}]*)}/g
    ];

    for (const pattern of patterns) {
      let match;
      while ((match = pattern.exec(code)) !== null) {
        functions.push({
          name: match[1],
          body: match[2] || ''
        });
      }
    }

    return functions;
  }

  private calculateConfidence(findings: AnalysisFindings, code: string): number {
    let confidence = 0.7; // Base confidence

    // More code = more confident in metrics
    if (code.length > 500) confidence += 0.1;
    if (code.length > 1000) confidence += 0.1;

    // Functions found = structure analysis worked
    if (findings.metrics.functionCount > 0) confidence += 0.1;

    return Math.min(confidence, 1.0);
  }

  private buildReasoning(findings: AnalysisFindings): string {
    const parts: string[] = [];

    parts.push(`Analyzed code with complexity score of ${findings.complexity}`);
    parts.push(`Found ${findings.metrics.functionCount} functions, avg length ${findings.metrics.avgFunctionLength} lines`);

    if (findings.issues.length === 0) {
      parts.push('No major issues detected');
    } else {
      parts.push(`Identified ${findings.issues.length} issues requiring attention`);
    }

    return parts.join('. ');
  }

  private suggestNextSteps(findings: AnalysisFindings): string[] {
    const steps: string[] = [];

    if (findings.issues.length > 0) {
      steps.push('review: Address identified code quality issues');
    }

    if (findings.complexity > 15) {
      steps.push('refactor: Break down complex logic into smaller functions');
    }

    if (findings.metrics.functionCount > 0) {
      steps.push('test: Generate unit tests for extracted functions');
    }

    if (findings.issues.length === 0 && findings.complexity < 10) {
      steps.push('document: Code quality is good, focus on documentation');
    }

    return steps;
  }
}
