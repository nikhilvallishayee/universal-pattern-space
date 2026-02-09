import { BaseAgent } from './base-agent';
import { AgentTask, TaskOutput, Artifact } from '../orchestrator/types';

interface FunctionSignature {
  name: string;
  params: string[];
  returnType?: string;
  isAsync: boolean;
}

interface TestCase {
  description: string;
  setup: string;
  assertion: string;
}

export class TestGenerator extends BaseAgent {
  constructor(name: string = 'TestGenerator') {
    super('tester', name);
  }

  protected async process(task: AgentTask): Promise<TaskOutput> {
    const code = task.input.code as string || '';
    const testFramework = task.input.framework as string || 'vitest';

    const functions = this.extractFunctionSignatures(code);
    const testCode = this.generateTestSuite(functions, testFramework);

    const artifact: Artifact = {
      type: 'test',
      content: testCode,
      metadata: {
        framework: testFramework,
        functionCount: functions.length,
        testCount: functions.reduce((acc, f) => acc + this.generateTestCases(f).length, 0)
      }
    };

    return {
      artifacts: [artifact],
      reasoning: `Generated ${functions.length} test suites with ${artifact.metadata.testCount} test cases using ${testFramework}`,
      confidence: functions.length > 0 ? 0.85 : 0.5,
      nextSteps: functions.length > 0
        ? ['execute: Run generated tests', 'review: Verify test coverage']
        : ['manual: No functions found, write tests manually']
    };
  }

  private extractFunctionSignatures(code: string): FunctionSignature[] {
    const signatures: FunctionSignature[] = [];

    // Pattern 1: function declarations
    const functionPattern = /(async\s+)?function\s+(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?/g;
    let match;
    while ((match = functionPattern.exec(code)) !== null) {
      signatures.push({
        name: match[2],
        params: this.parseParams(match[3]),
        returnType: match[4]?.trim(),
        isAsync: !!match[1]
      });
    }

    // Pattern 2: const arrow functions
    const arrowPattern = /const\s+(\w+)\s*=\s*(async\s+)?\(([^)]*)\)(?:\s*:\s*([^=]+))?\s*=>/g;
    while ((match = arrowPattern.exec(code)) !== null) {
      signatures.push({
        name: match[1],
        params: this.parseParams(match[3]),
        returnType: match[4]?.trim(),
        isAsync: !!match[2]
      });
    }

    // Pattern 3: class methods
    const methodPattern = /(async\s+)?(\w+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*{/g;
    while ((match = methodPattern.exec(code)) !== null) {
      const name = match[2];
      // Skip constructor and common keywords
      if (name !== 'constructor' && !['if', 'for', 'while', 'switch', 'catch'].includes(name)) {
        signatures.push({
          name,
          params: this.parseParams(match[3]),
          returnType: match[4]?.trim(),
          isAsync: !!match[1]
        });
      }
    }

    // Deduplicate by name
    const unique = new Map<string, FunctionSignature>();
    signatures.forEach(sig => {
      if (!unique.has(sig.name)) {
        unique.set(sig.name, sig);
      }
    });

    return Array.from(unique.values());
  }

  private parseParams(paramStr: string): string[] {
    if (!paramStr.trim()) return [];

    return paramStr.split(',').map(p => {
      // Extract param name, removing type annotations
      const match = p.trim().match(/^(\w+)/);
      return match ? match[1] : '';
    }).filter(Boolean);
  }

  private generateTestSuite(functions: FunctionSignature[], framework: string): string {
    if (functions.length === 0) {
      return '// No functions found to test\n';
    }

    const imports = this.generateImports(framework);
    const suites = functions.map(f => this.generateFunctionTests(f, framework)).join('\n\n');

    return `${imports}\n\n${suites}`;
  }

  private generateImports(framework: string): string {
    const importMap: Record<string, string> = {
      vitest: "import { describe, it, expect, beforeEach } from 'vitest';",
      jest: "import { describe, it, expect, beforeEach } from '@jest/globals';",
      mocha: "import { describe, it, before } from 'mocha';\nimport { expect } from 'chai';"
    };

    return importMap[framework] || importMap['vitest'];
  }

  private generateFunctionTests(func: FunctionSignature, framework: string): string {
    const testCases = this.generateTestCases(func);

    const tests = testCases.map(tc => {
      const itFunc = func.isAsync ? 'it' : 'it';
      const awaitKeyword = func.isAsync ? 'await ' : '';

      return `  ${itFunc}('${tc.description}', ${func.isAsync ? 'async ' : ''}() => {
${tc.setup ? `    ${tc.setup}\n` : ''}    ${tc.assertion}
  });`;
    }).join('\n\n');

    return `describe('${func.name}', () => {
${tests}
});`;
  }

  private generateTestCases(func: FunctionSignature): TestCase[] {
    const cases: TestCase[] = [];

    // Happy path
    cases.push({
      description: `should ${this.inferBehavior(func.name)} with valid inputs`,
      setup: this.generateSetup(func, 'valid'),
      assertion: this.generateAssertion(func, 'valid')
    });

    // Edge cases based on params
    if (func.params.length > 0) {
      // Null/undefined params
      cases.push({
        description: 'should handle null/undefined parameters',
        setup: this.generateSetup(func, 'null'),
        assertion: this.generateAssertion(func, 'null')
      });

      // Empty params (for strings/arrays)
      if (this.likelyStringOrArrayParam(func)) {
        cases.push({
          description: 'should handle empty input',
          setup: this.generateSetup(func, 'empty'),
          assertion: this.generateAssertion(func, 'empty')
        });
      }
    }

    // Error cases
    if (func.name.includes('validate') || func.name.includes('check')) {
      cases.push({
        description: 'should throw error on invalid input',
        setup: this.generateSetup(func, 'invalid'),
        assertion: this.generateAssertion(func, 'error')
      });
    }

    // Async-specific cases
    if (func.isAsync) {
      cases.push({
        description: 'should handle async errors gracefully',
        setup: this.generateSetup(func, 'async-error'),
        assertion: this.generateAssertion(func, 'async-error')
      });
    }

    return cases;
  }

  private inferBehavior(funcName: string): string {
    // Infer verb from function name
    if (funcName.startsWith('get')) return 'retrieve data';
    if (funcName.startsWith('set') || funcName.startsWith('update')) return 'update state';
    if (funcName.startsWith('create') || funcName.startsWith('add')) return 'create new entity';
    if (funcName.startsWith('delete') || funcName.startsWith('remove')) return 'remove entity';
    if (funcName.startsWith('validate') || funcName.startsWith('check')) return 'validate input';
    if (funcName.startsWith('calculate') || funcName.startsWith('compute')) return 'compute result';
    if (funcName.startsWith('is') || funcName.startsWith('has')) return 'return boolean';

    return 'execute successfully';
  }

  private likelyStringOrArrayParam(func: FunctionSignature): boolean {
    return func.params.some(p =>
      p.includes('str') || p.includes('text') || p.includes('name') ||
      p.includes('arr') || p.includes('list') || p.includes('items')
    );
  }

  private generateSetup(func: FunctionSignature, scenario: string): string {
    if (func.params.length === 0) return '';

    const params = func.params.map((p, i) => {
      switch (scenario) {
        case 'valid':
          return this.generateValidParam(p, i);
        case 'null':
          return i === 0 ? 'null' : this.generateValidParam(p, i);
        case 'empty':
          return i === 0 ? this.generateEmptyParam(p) : this.generateValidParam(p, i);
        case 'invalid':
          return this.generateInvalidParam(p, i);
        case 'async-error':
          return this.generateValidParam(p, i);
        default:
          return this.generateValidParam(p, i);
      }
    });

    const paramList = params.join(', ');
    return `const result = ${func.isAsync ? 'await ' : ''}${func.name}(${paramList});`;
  }

  private generateValidParam(param: string, index: number): string {
    // Infer type from param name
    if (param.includes('id')) return `'test-id-${index}'`;
    if (param.includes('name')) return `'TestName${index}'`;
    if (param.includes('count') || param.includes('num')) return `${index + 1}`;
    if (param.includes('enabled') || param.includes('active')) return 'true';
    if (param.includes('data') || param.includes('config')) return '{}';
    if (param.includes('list') || param.includes('items')) return '[]';

    return `'param${index}'`;
  }

  private generateEmptyParam(param: string): string {
    if (param.includes('list') || param.includes('items') || param.includes('arr')) return '[]';
    return "''";
  }

  private generateInvalidParam(param: string, index: number): string {
    if (param.includes('id')) return "''";
    if (param.includes('count') || param.includes('num')) return '-1';
    if (param.includes('email')) return "'invalid-email'";

    return 'undefined';
  }

  private generateAssertion(func: FunctionSignature, scenario: string): string {
    const funcCall = `${func.name}`;

    switch (scenario) {
      case 'valid':
        if (func.returnType?.includes('void') || !func.returnType) {
          return 'expect(result).toBeUndefined();';
        }
        if (func.returnType?.includes('boolean') || func.name.startsWith('is') || func.name.startsWith('has')) {
          return 'expect(result).toBe(true);';
        }
        if (func.returnType?.includes('[]') || func.name.includes('list') || func.name.includes('get')) {
          return 'expect(result).toBeDefined();';
        }
        return 'expect(result).toBeDefined();';

      case 'null':
      case 'empty':
        if (func.name.includes('validate') || func.name.includes('check')) {
          return 'expect(result).toBe(false);';
        }
        return 'expect(result).toBeNull();';

      case 'error':
        const params = func.params.map((p, i) => this.generateInvalidParam(p, i)).join(', ');
        return `expect(() => ${funcCall}(${params})).toThrow();`;

      case 'async-error':
        return `expect(result).rejects.toThrow();`;

      default:
        return 'expect(result).toBeDefined();';
    }
  }
}
