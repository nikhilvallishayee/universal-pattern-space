import { BaseAgent } from './base-agent';
import { AgentTask, TaskOutput, Artifact } from '../orchestrator/types';

interface DocItem {
  type: 'function' | 'class' | 'interface' | 'type';
  name: string;
  signature: string;
  description: string;
  params?: Array<{ name: string; type?: string; description?: string }>;
  returns?: { type?: string; description?: string };
}

export class DocGenerator extends BaseAgent {
  constructor(name: string = 'DocGenerator') {
    super('documenter', name);
  }

  protected async process(task: AgentTask): Promise<TaskOutput> {
    const code = task.input.code as string || '';
    const format = task.input.format as string || 'markdown';

    const items = this.extractDocItems(code);
    const documentation = this.generateDocumentation(items, format);

    const artifact: Artifact = {
      type: 'documentation',
      content: documentation,
      metadata: {
        format,
        itemCount: items.length,
        types: this.countTypes(items)
      }
    };

    return {
      artifacts: [artifact],
      reasoning: `Generated documentation for ${items.length} code items (${this.summarizeTypes(items)})`,
      confidence: items.length > 0 ? 0.8 : 0.4,
      nextSteps: items.length > 0
        ? ['review: Verify generated documentation accuracy', 'publish: Add to README or docs site']
        : ['manual: No documentable items found, add manually']
    };
  }

  private extractDocItems(code: string): DocItem[] {
    const items: DocItem[] = [];

    // Extract interfaces
    items.push(...this.extractInterfaces(code));

    // Extract types
    items.push(...this.extractTypes(code));

    // Extract classes
    items.push(...this.extractClasses(code));

    // Extract functions
    items.push(...this.extractFunctions(code));

    return items;
  }

  private extractInterfaces(code: string): DocItem[] {
    const items: DocItem[] = [];
    const pattern = /(?:export\s+)?interface\s+(\w+)(?:<[^>]+>)?\s*{([^}]*)}/g;

    let match;
    while ((match = pattern.exec(code)) !== null) {
      const name = match[1];
      const body = match[2];

      const properties = this.parseProperties(body);
      const signature = `interface ${name}`;

      items.push({
        type: 'interface',
        name,
        signature,
        description: this.inferDescription(name, 'interface'),
        params: properties
      });
    }

    return items;
  }

  private extractTypes(code: string): DocItem[] {
    const items: DocItem[] = [];
    const pattern = /(?:export\s+)?type\s+(\w+)(?:<[^>]+>)?\s*=\s*([^;]+);/g;

    let match;
    while ((match = pattern.exec(code)) !== null) {
      const name = match[1];
      const definition = match[2].trim();

      items.push({
        type: 'type',
        name,
        signature: `type ${name} = ${definition}`,
        description: this.inferDescription(name, 'type')
      });
    }

    return items;
  }

  private extractClasses(code: string): DocItem[] {
    const items: DocItem[] = [];
    const pattern = /(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:<[^>]+>)?(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?\s*{/g;

    let match;
    while ((match = pattern.exec(code)) !== null) {
      const name = match[1];
      const extendsClass = match[2];
      const implementsInterfaces = match[3];

      let signature = `class ${name}`;
      if (extendsClass) signature += ` extends ${extendsClass}`;
      if (implementsInterfaces) signature += ` implements ${implementsInterfaces.trim()}`;

      // Extract constructor
      const classBody = this.extractClassBody(code, match.index);
      const constructor = this.extractConstructor(classBody);

      items.push({
        type: 'class',
        name,
        signature,
        description: this.inferDescription(name, 'class'),
        params: constructor
      });
    }

    return items;
  }

  private extractFunctions(code: string): DocItem[] {
    const items: DocItem[] = [];

    // Function declarations
    const funcPattern = /(?:export\s+)?(?:async\s+)?function\s+(\w+)(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*{/g;
    let match;

    while ((match = funcPattern.exec(code)) !== null) {
      const name = match[1];
      const params = this.parseParameters(match[2]);
      const returnType = match[3]?.trim();

      items.push({
        type: 'function',
        name,
        signature: `function ${name}(${match[2]})${returnType ? `: ${returnType}` : ''}`,
        description: this.inferDescription(name, 'function'),
        params,
        returns: returnType ? { type: returnType, description: this.inferReturnDescription(returnType) } : undefined
      });
    }

    // Arrow functions (exported)
    const arrowPattern = /(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)(?:\s*:\s*([^=]+))?\s*=>/g;
    while ((match = arrowPattern.exec(code)) !== null) {
      const name = match[1];
      const params = this.parseParameters(match[2]);
      const returnType = match[3]?.trim();

      items.push({
        type: 'function',
        name,
        signature: `const ${name} = (${match[2]})${returnType ? `: ${returnType}` : ''} =>`,
        description: this.inferDescription(name, 'function'),
        params,
        returns: returnType ? { type: returnType, description: this.inferReturnDescription(returnType) } : undefined
      });
    }

    return items;
  }

  private parseProperties(body: string): Array<{ name: string; type?: string; description?: string }> {
    const properties: Array<{ name: string; type?: string; description?: string }> = [];
    const lines = body.split(/[;\n]/).filter(l => l.trim());

    for (const line of lines) {
      const match = line.match(/(\w+)\??\s*:\s*([^;,]+)/);
      if (match) {
        properties.push({
          name: match[1],
          type: match[2].trim(),
          description: this.inferParamDescription(match[1], match[2].trim())
        });
      }
    }

    return properties;
  }

  private parseParameters(paramStr: string): Array<{ name: string; type?: string; description?: string }> {
    if (!paramStr.trim()) return [];

    const params: Array<{ name: string; type?: string; description?: string }> = [];
    const parts = paramStr.split(',');

    for (const part of parts) {
      const match = part.trim().match(/(\w+)\??\s*:\s*([^=]+?)(?:\s*=|$)/);
      if (match) {
        params.push({
          name: match[1],
          type: match[2].trim(),
          description: this.inferParamDescription(match[1], match[2].trim())
        });
      } else {
        const nameOnly = part.trim().match(/(\w+)/);
        if (nameOnly) {
          params.push({
            name: nameOnly[1],
            description: this.inferParamDescription(nameOnly[1], '')
          });
        }
      }
    }

    return params;
  }

  private extractClassBody(code: string, startIndex: number): string {
    let braceCount = 0;
    let inClass = false;
    let body = '';

    for (let i = startIndex; i < code.length; i++) {
      const char = code[i];

      if (char === '{') {
        braceCount++;
        inClass = true;
      } else if (char === '}') {
        braceCount--;
        if (braceCount === 0 && inClass) {
          break;
        }
      }

      if (inClass) {
        body += char;
      }
    }

    return body;
  }

  private extractConstructor(classBody: string): Array<{ name: string; type?: string; description?: string }> | undefined {
    const match = classBody.match(/constructor\s*\(([^)]*)\)/);
    if (!match) return undefined;

    return this.parseParameters(match[1]);
  }

  private inferDescription(name: string, type: string): string {
    // Infer description from name and type
    const nameLower = name.toLowerCase();

    if (type === 'interface' || type === 'type') {
      if (nameLower.includes('config')) return `Configuration options for ${name.replace('Config', '')}`;
      if (nameLower.includes('options')) return `Available options for the operation`;
      if (nameLower.includes('result')) return `Result data structure`;
      if (nameLower.includes('response')) return `API response structure`;
      if (nameLower.includes('request')) return `Request parameters`;
      return `${name} data structure`;
    }

    if (type === 'class') {
      if (nameLower.includes('service')) return `Service for managing ${name.replace('Service', '')} operations`;
      if (nameLower.includes('manager')) return `Manager for ${name.replace('Manager', '')} lifecycle`;
      if (nameLower.includes('controller')) return `Controller handling ${name.replace('Controller', '')} endpoints`;
      if (nameLower.includes('repository')) return `Data access layer for ${name.replace('Repository', '')}`;
      return `${name} class`;
    }

    if (type === 'function') {
      if (name.startsWith('get')) return `Retrieves ${this.camelToWords(name.slice(3))}`;
      if (name.startsWith('set')) return `Sets ${this.camelToWords(name.slice(3))}`;
      if (name.startsWith('create')) return `Creates a new ${this.camelToWords(name.slice(6))}`;
      if (name.startsWith('update')) return `Updates ${this.camelToWords(name.slice(6))}`;
      if (name.startsWith('delete')) return `Deletes ${this.camelToWords(name.slice(6))}`;
      if (name.startsWith('is') || name.startsWith('has')) return `Checks if ${this.camelToWords(name.slice(2))}`;
      if (name.startsWith('validate')) return `Validates ${this.camelToWords(name.slice(8))}`;
      if (name.startsWith('calculate')) return `Calculates ${this.camelToWords(name.slice(9))}`;
      return `${name} function`;
    }

    return `${name} ${type}`;
  }

  private inferParamDescription(name: string, type: string): string {
    const nameLower = name.toLowerCase();

    if (nameLower.includes('id')) return 'Unique identifier';
    if (nameLower.includes('name')) return 'Name value';
    if (nameLower.includes('config') || nameLower.includes('options')) return 'Configuration options';
    if (nameLower.includes('callback')) return 'Callback function';
    if (nameLower.includes('data')) return 'Data payload';
    if (type.includes('boolean')) return 'Boolean flag';
    if (type.includes('number')) return 'Numeric value';
    if (type.includes('string')) return 'String value';
    if (type.includes('[]')) return 'Array of items';

    return `${this.camelToWords(name)} parameter`;
  }

  private inferReturnDescription(type: string): string {
    if (type.includes('Promise')) return 'Async operation result';
    if (type.includes('void')) return 'No return value';
    if (type.includes('boolean')) return 'Boolean result';
    if (type.includes('number')) return 'Numeric result';
    if (type.includes('string')) return 'String result';
    if (type.includes('[]')) return 'Array of results';

    return 'Operation result';
  }

  private camelToWords(str: string): string {
    return str
      .replace(/([A-Z])/g, ' $1')
      .toLowerCase()
      .trim();
  }

  private generateDocumentation(items: DocItem[], format: string): string {
    if (items.length === 0) {
      return '# Documentation\n\nNo documentable items found in the code.';
    }

    const sections = {
      interface: items.filter(i => i.type === 'interface'),
      type: items.filter(i => i.type === 'type'),
      class: items.filter(i => i.type === 'class'),
      function: items.filter(i => i.type === 'function')
    };

    const lines: string[] = [];
    lines.push('# API Documentation\n');

    if (sections.interface.length > 0) {
      lines.push('## Interfaces\n');
      for (const item of sections.interface) {
        lines.push(this.formatDocItem(item));
      }
    }

    if (sections.type.length > 0) {
      lines.push('## Types\n');
      for (const item of sections.type) {
        lines.push(this.formatDocItem(item));
      }
    }

    if (sections.class.length > 0) {
      lines.push('## Classes\n');
      for (const item of sections.class) {
        lines.push(this.formatDocItem(item));
      }
    }

    if (sections.function.length > 0) {
      lines.push('## Functions\n');
      for (const item of sections.function) {
        lines.push(this.formatDocItem(item));
      }
    }

    return lines.join('\n');
  }

  private formatDocItem(item: DocItem): string {
    const lines: string[] = [];

    lines.push(`### ${item.name}\n`);
    lines.push(`${item.description}\n`);
    lines.push('```typescript');
    lines.push(item.signature);
    lines.push('```\n');

    if (item.params && item.params.length > 0) {
      lines.push('**Parameters:**\n');
      for (const param of item.params) {
        const type = param.type ? `: ${param.type}` : '';
        const desc = param.description ? ` - ${param.description}` : '';
        lines.push(`- \`${param.name}${type}\`${desc}`);
      }
      lines.push('');
    }

    if (item.returns) {
      lines.push('**Returns:**\n');
      const type = item.returns.type ? `\`${item.returns.type}\`` : '';
      const desc = item.returns.description ? ` - ${item.returns.description}` : '';
      lines.push(`${type}${desc}\n`);
    }

    return lines.join('\n');
  }

  private countTypes(items: DocItem[]): Record<string, number> {
    return items.reduce((acc, item) => {
      acc[item.type] = (acc[item.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }

  private summarizeTypes(items: DocItem[]): string {
    const counts = this.countTypes(items);
    return Object.entries(counts)
      .map(([type, count]) => `${count} ${type}${count !== 1 ? 's' : ''}`)
      .join(', ');
  }
}
