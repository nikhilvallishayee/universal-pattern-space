import { AgentRole, AgentTask, TaskOutput } from '../orchestrator/types';

export abstract class BaseAgent {
  readonly id: string;
  readonly role: AgentRole;
  readonly name: string;
  private busy = false;

  constructor(role: AgentRole, name: string) {
    this.id = crypto.randomUUID();
    this.role = role;
    this.name = name;
  }

  get isBusy(): boolean {
    return this.busy;
  }

  async execute(task: AgentTask): Promise<TaskOutput> {
    this.busy = true;
    const startTime = Date.now();
    try {
      const output = await this.process(task);
      return {
        ...output,
        reasoning: `[${this.name}] ${output.reasoning} (${Date.now() - startTime}ms)`
      };
    } finally {
      this.busy = false;
    }
  }

  protected abstract process(task: AgentTask): Promise<TaskOutput>;
}
