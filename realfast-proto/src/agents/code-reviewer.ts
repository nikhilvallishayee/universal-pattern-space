import { BaseAgent } from './base-agent';
import { AgentTask, TaskOutput, Artifact } from '../orchestrator/types';

interface ReviewItem {
  category: 'error-handling' | 'security' | 'style' | 'typing' | 'best-practice';
  status: 'pass' | 'fail' | 'warning';
  message: string;
  line?: number;
}

interface ReviewResult {
  passed: number;
  failed: number;
  warnings: number;
  items: ReviewItem[];
  overallScore: number;
}

export class CodeReviewer extends BaseAgent {
  constructor(name: string = 'CodeReviewer') {
    super('reviewer', name);
  }

  protected async process(task: AgentTask): Promise<TaskOutput> {
    const code = task.input.code as string || '';

    const review = this.reviewCode(code);
    const confidence = this.calculateConfidence(review, code);

    const artifact: Artifact = {
      type: 'review',
      content: this.formatReview(review),
      metadata: {
        score: review.overallScore,
        passed: review.passed,
        failed: review.failed,
        warnings: review.warnings
      }
    };

    return {
      artifacts: [artifact],
      reasoning: this.buildReasoning(review),
      confidence,
      nextSteps: this.suggestNextSteps(review)
    };
  }

  private reviewCode(code: string): ReviewResult {
    const items: ReviewItem[] = [];

    // Error Handling Checks
    items.push(...this.checkErrorHandling(code));

    // Security Checks
    items.push(...this.checkSecurity(code));

    // Style Checks
    items.push(...this.checkStyle(code));

    // Typing Checks
    items.push(...this.checkTyping(code));

    // Best Practice Checks
    items.push(...this.checkBestPractices(code));

    const passed = items.filter(i => i.status === 'pass').length;
    const failed = items.filter(i => i.status === 'fail').length;
    const warnings = items.filter(i => i.status === 'warning').length;

    const overallScore = items.length > 0
      ? Math.round(((passed + warnings * 0.5) / items.length) * 100)
      : 50;

    return { passed, failed, warnings, items, overallScore };
  }

  private checkErrorHandling(code: string): ReviewItem[] {
    const items: ReviewItem[] = [];

    // Check for try-catch blocks
    const hasTryCatch = code.includes('try') && code.includes('catch');
    const hasAsync = code.includes('async');

    if (hasAsync && !hasTryCatch) {
      items.push({
        category: 'error-handling',
        status: 'fail',
        message: 'Async functions should have try-catch for error handling'
      });
    } else if (hasAsync && hasTryCatch) {
      items.push({
        category: 'error-handling',
        status: 'pass',
        message: 'Proper async error handling detected'
      });
    }

    // Check for empty catch blocks
    const emptyCatch = /catch\s*\([^)]*\)\s*{\s*}/g.test(code);
    if (emptyCatch) {
      items.push({
        category: 'error-handling',
        status: 'fail',
        message: 'Empty catch blocks found - errors should be logged or handled'
      });
    }

    // Check for promise rejections
    const hasPromise = code.includes('Promise') || code.includes('.then(');
    const hasCatch = code.includes('.catch(');
    if (hasPromise && !hasCatch && !hasTryCatch) {
      items.push({
        category: 'error-handling',
        status: 'warning',
        message: 'Promises should handle rejections with .catch() or try-catch'
      });
    }

    return items;
  }

  private checkSecurity(code: string): ReviewItem[] {
    const items: ReviewItem[] = [];

    // Check for hardcoded secrets
    const secretPatterns = [
      /password\s*=\s*['"][^'"]+['"]/i,
      /api[_-]?key\s*=\s*['"][^'"]+['"]/i,
      /secret\s*=\s*['"][^'"]+['"]/i,
      /token\s*=\s*['"][^'"]+['"]/i
    ];

    for (const pattern of secretPatterns) {
      if (pattern.test(code)) {
        items.push({
          category: 'security',
          status: 'fail',
          message: 'Hardcoded secrets detected - use environment variables'
        });
        break;
      }
    }

    // Check for SQL injection vulnerabilities
    if (code.includes('SELECT') && code.includes('+')) {
      items.push({
        category: 'security',
        status: 'fail',
        message: 'Possible SQL injection - use parameterized queries'
      });
    }

    // Check for eval usage
    if (code.includes('eval(')) {
      items.push({
        category: 'security',
        status: 'fail',
        message: 'eval() is dangerous - avoid using it'
      });
    }

    // Check for unsafe innerHTML
    if (code.includes('innerHTML') && !code.includes('sanitize')) {
      items.push({
        category: 'security',
        status: 'warning',
        message: 'innerHTML usage detected - ensure input is sanitized to prevent XSS'
      });
    }

    // If no security issues found
    if (items.filter(i => i.category === 'security').length === 0) {
      items.push({
        category: 'security',
        status: 'pass',
        message: 'No obvious security vulnerabilities detected'
      });
    }

    return items;
  }

  private checkStyle(code: string): ReviewItem[] {
    const items: ReviewItem[] = [];

    // Check for consistent indentation
    const lines = code.split('\n');
    const indents = lines
      .filter(l => l.trim())
      .map(l => l.match(/^\s*/)?.[0].length || 0);

    const hasTabsAndSpaces = code.includes('\t') && /^[ ]{2,}/m.test(code);
    if (hasTabsAndSpaces) {
      items.push({
        category: 'style',
        status: 'fail',
        message: 'Mixed tabs and spaces - use consistent indentation'
      });
    } else {
      items.push({
        category: 'style',
        status: 'pass',
        message: 'Consistent indentation style'
      });
    }

    // Check for consistent naming (camelCase for functions/variables)
    const identifiers = code.match(/(?:function|const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)/g) || [];
    const snakeCase = identifiers.some(id => /_[a-z]/.test(id));
    if (snakeCase && !code.includes('python')) {
      items.push({
        category: 'style',
        status: 'warning',
        message: 'Consider using camelCase for JavaScript/TypeScript identifiers'
      });
    }

    // Check for trailing whitespace
    const hasTrailingWhitespace = /[ \t]+$/m.test(code);
    if (hasTrailingWhitespace) {
      items.push({
        category: 'style',
        status: 'warning',
        message: 'Trailing whitespace found - clean up formatting'
      });
    }

    return items;
  }

  private checkTyping(code: string): ReviewItem[] {
    const items: ReviewItem[] = [];

    // Only check if this is TypeScript
    const isTypeScript = code.includes('interface') || code.includes(': ') || code.includes('<T>');

    if (!isTypeScript) {
      return items;
    }

    // Check for excessive 'any' usage
    const anyCount = (code.match(/:\s*any\b/g) || []).length;
    if (anyCount > 3) {
      items.push({
        category: 'typing',
        status: 'fail',
        message: `Excessive use of 'any' type (${anyCount} occurrences) - add proper types`
      });
    } else if (anyCount > 0) {
      items.push({
        category: 'typing',
        status: 'warning',
        message: `Limited use of 'any' type (${anyCount} occurrences) - consider proper types`
      });
    } else {
      items.push({
        category: 'typing',
        status: 'pass',
        message: 'Good type coverage without "any"'
      });
    }

    // Check for untyped parameters
    const untypedParams = /\(([a-zA-Z_][a-zA-Z0-9_]*)\s*,|\(([a-zA-Z_][a-zA-Z0-9_]*)\s*\)/g;
    const matches = code.match(untypedParams) || [];
    if (matches.length > 0 && isTypeScript) {
      items.push({
        category: 'typing',
        status: 'warning',
        message: 'Some function parameters lack type annotations'
      });
    }

    // Check for return type annotations
    const functionsWithoutReturnType = /function\s+\w+\([^)]*\)\s*{/g.test(code);
    if (functionsWithoutReturnType) {
      items.push({
        category: 'typing',
        status: 'warning',
        message: 'Consider adding return type annotations to functions'
      });
    }

    return items;
  }

  private checkBestPractices(code: string): ReviewItem[] {
    const items: ReviewItem[] = [];

    // Check for magic numbers
    const magicNumbers = code.match(/\b\d{3,}\b/g);
    if (magicNumbers && magicNumbers.length > 0) {
      items.push({
        category: 'best-practice',
        status: 'warning',
        message: 'Magic numbers detected - consider using named constants'
      });
    }

    // Check for TODO/FIXME comments
    const todos = (code.match(/\/\/\s*(TODO|FIXME)/gi) || []).length;
    if (todos > 0) {
      items.push({
        category: 'best-practice',
        status: 'warning',
        message: `${todos} TODO/FIXME comment(s) - track as issues`
      });
    }

    // Check for proper async/await usage
    const hasAsyncAwait = code.includes('async') && code.includes('await');
    const hasThenCatch = code.includes('.then(') || code.includes('.catch(');
    if (hasAsyncAwait && hasThenCatch) {
      items.push({
        category: 'best-practice',
        status: 'warning',
        message: 'Mixed async/await and .then/.catch - choose one pattern'
      });
    }

    // Check for function length
    const functions = code.split(/\bfunction\b|\b=>\b/);
    const longFunctions = functions.filter(f => f.split('\n').length > 50);
    if (longFunctions.length > 0) {
      items.push({
        category: 'best-practice',
        status: 'warning',
        message: `${longFunctions.length} function(s) exceed 50 lines - consider refactoring`
      });
    }

    // Check for proper error types
    if (code.includes('throw new Error') || code.includes('throw Error')) {
      items.push({
        category: 'best-practice',
        status: 'pass',
        message: 'Proper error throwing detected'
      });
    }

    // Check for documentation
    const hasJsdoc = code.includes('/**') || code.includes('*/');
    if (hasJsdoc) {
      items.push({
        category: 'best-practice',
        status: 'pass',
        message: 'Documentation comments present'
      });
    } else if (code.split('\n').length > 50) {
      items.push({
        category: 'best-practice',
        status: 'warning',
        message: 'Large codebase lacks documentation comments'
      });
    }

    return items;
  }

  private calculateConfidence(review: ReviewResult, code: string): number {
    let confidence = 0.6; // Base confidence

    // More checks performed = higher confidence
    if (review.items.length > 10) confidence += 0.2;
    else if (review.items.length > 5) confidence += 0.1;

    // Larger codebase = more confident in analysis
    if (code.length > 1000) confidence += 0.1;

    // If we found specific patterns (good or bad) = more confident
    const specificFindings = review.items.filter(i => i.status !== 'pass').length;
    if (specificFindings > 0) confidence += 0.1;

    return Math.min(confidence, 1.0);
  }

  private formatReview(review: ReviewResult): string {
    const lines: string[] = [];

    lines.push(`# Code Review Report\n`);
    lines.push(`**Overall Score:** ${review.overallScore}/100\n`);
    lines.push(`**Results:** ${review.passed} passed, ${review.failed} failed, ${review.warnings} warnings\n`);

    const categories = ['error-handling', 'security', 'typing', 'style', 'best-practice'] as const;

    for (const category of categories) {
      const items = review.items.filter(i => i.category === category);
      if (items.length === 0) continue;

      lines.push(`\n## ${this.formatCategoryName(category)}\n`);

      for (const item of items) {
        const icon = item.status === 'pass' ? '✓' : item.status === 'fail' ? '✗' : '⚠';
        lines.push(`${icon} ${item.message}`);
      }
    }

    return lines.join('\n');
  }

  private formatCategoryName(category: string): string {
    return category
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  private buildReasoning(review: ReviewResult): string {
    const parts: string[] = [];

    parts.push(`Completed code review with ${review.items.length} checks`);
    parts.push(`Overall score: ${review.overallScore}/100`);

    if (review.failed > 0) {
      parts.push(`Found ${review.failed} critical issue(s) requiring immediate attention`);
    }

    if (review.warnings > 0) {
      parts.push(`${review.warnings} warning(s) for improvement`);
    }

    if (review.failed === 0 && review.warnings === 0) {
      parts.push('Code meets quality standards');
    }

    return parts.join('. ');
  }

  private suggestNextSteps(review: ReviewResult): string[] {
    const steps: string[] = [];

    if (review.failed > 0) {
      const securityFails = review.items.filter(i => i.category === 'security' && i.status === 'fail').length;
      if (securityFails > 0) {
        steps.push('security: Address critical security vulnerabilities immediately');
      }

      const errorHandlingFails = review.items.filter(i => i.category === 'error-handling' && i.status === 'fail').length;
      if (errorHandlingFails > 0) {
        steps.push('refactor: Improve error handling');
      }
    }

    if (review.warnings > 0) {
      steps.push('refactor: Address warnings to improve code quality');
    }

    if (review.overallScore < 70) {
      steps.push('refactor: Significant refactoring needed to meet quality standards');
    }

    if (review.overallScore >= 80) {
      steps.push('test: Code quality is good, ensure test coverage');
      steps.push('document: Add documentation for public APIs');
    }

    return steps;
  }
}
