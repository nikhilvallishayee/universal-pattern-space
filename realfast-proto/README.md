# RealFast Proto - AI Agent Orchestration Platform

**Prototype demonstration of multi-agent AI orchestration with quality gates and human oversight.**

Inspired by [RealFast.ai's Vayu platform](https://realfast.ai) - "An Iron Man suit for IT services teams"

## 🎯 What This Demonstrates

This prototype showcases a production-ready pattern for orchestrating AI agents with:

- **Multi-stage pipelines** - Complex workflows broken into stages with dependencies
- **Quality gates** - Automated quality checks with configurable thresholds
- **Human-in-the-loop** - Automatic escalation for medium-quality outputs
- **Complete audit trail** - Full transparency and traceability
- **Agent pool management** - Reusable agents with role-based specialization

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Pipeline Orchestrator                    │
│  - Stage execution                                          │
│  - Dependency resolution                                    │
│  - Quality gate integration                                 │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼──────┐       ┌───────▼──────────┐
│  Agent Pool  │       │  Quality Gate    │
│              │       │                  │
│ • Analyzer   │       │ • Auto-approve   │
│ • Tester     │       │ • Auto-reject    │
│ • Reviewer   │       │ • Human review   │
│ • Documenter │       │ • Audit logging  │
└──────────────┘       └──────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 20+
- npm 9+

### Installation

```bash
# Install dependencies
npm install

# Run the demo
npm run demo

# Run tests
npm test

# Build for production
npm run build
```

## 📋 Demo Output

The demo runs a full code analysis pipeline:

```
Stage 1: analyze
  → Code analyzer examines sample function
  → Quality gate checks completeness & correctness
  → Auto-approved if score > 0.85

Stage 2: generate-tests
  → Test generator creates test skeletons
  → Quality gate validates test coverage
  → Human review if score between 0.50-0.85

Stage 3: review
  → Code reviewer checks for issues
  → Quality gate enforces security standards
  → Auto-rejected if score < 0.50

Stage 4: document
  → Doc generator extracts API documentation
  → Quality gate verifies documentation coverage
  → Complete audit trail generated
```

## 🧪 Testing

Comprehensive test suite covering:

- **Orchestrator tests** - Pipeline execution, dependencies, quality integration
- **Agent tests** - Each agent role's core capabilities
- **Quality gate tests** - Thresholds, human review, audit logging

```bash
# Run all tests
npm test

# Watch mode for development
npm run test:watch

# Type checking only
npm run typecheck
```

## 📁 Project Structure

```
realfast-proto/
├── src/
│   ├── agents.ts          # AI agent pool and agent implementations
│   ├── orchestrator.ts    # Pipeline orchestration engine
│   ├── quality-gate.ts    # Quality checking and audit system
│   └── demo.ts            # Live demonstration script
├── tests/
│   ├── agents.test.ts
│   ├── orchestrator.test.ts
│   └── quality-gate.test.ts
├── package.json
├── tsconfig.json
└── README.md
```

## 🎨 Key Features

### 1. Multi-Agent System

Four specialized agent roles:

- **Code Analyzer** - Complexity analysis, issue detection
- **Test Generator** - Test skeleton creation, coverage estimation
- **Code Reviewer** - Quality scoring, best practice checks
- **Doc Generator** - API documentation, signature extraction

### 2. Quality Gates

Three-tier quality system:

- **Auto-approve** (score ≥ 0.85) - High quality, proceed automatically
- **Human review** (0.50 ≤ score < 0.85) - Manual verification required
- **Auto-reject** (score < 0.50) - Below quality threshold

### 3. Pipeline Orchestration

- **Stage dependencies** - Enforce execution order
- **Metadata tracking** - Agent ID, timing, duration
- **Error handling** - Graceful failure management
- **Flexible input/output** - Typed stage connections

### 4. Audit Trail

Complete transparency:

- Timestamp for every quality check
- Decision history (approved/rejected/review)
- Issue tracking and resolution
- Reviewer attribution (system vs. human)

## 🔧 Configuration

Quality gate can be configured with custom thresholds:

```typescript
const qualityGate = new QualityGate({
  autoApproveThreshold: 0.85,  // Auto-approve above this
  autoRejectThreshold: 0.50,   // Auto-reject below this
  requiredChecks: ['completeness', 'correctness', 'security'],
});
```

Agent pool supports dynamic agent allocation:

```typescript
const pool = new AgentPool();
pool.addAgent('code-analyzer');
pool.addAgent('test-generator');
pool.addAgent('code-reviewer');
```

## 🎯 Use Cases

This pattern works for:

- **Code review automation** - Multi-stage code analysis pipelines
- **Document generation** - Analysis → Generation → Review → Publish
- **Data processing** - Extract → Transform → Validate → Load
- **Content moderation** - Analyze → Score → Review → Approve
- **Testing workflows** - Generate → Execute → Report → Fix

## 🚧 Production Considerations

To deploy this pattern in production:

1. **Replace mock agents** with real LLM calls (OpenAI, Anthropic, etc.)
2. **Add persistent storage** for audit logs and pipeline state
3. **Implement human review UI** for medium-quality outputs
4. **Add monitoring/metrics** for agent performance and quality scores
5. **Scale agent pool** with worker queues and load balancing
6. **Secure API keys** with proper secret management
7. **Add retry logic** for transient failures
8. **Implement rate limiting** for API calls

## 📚 Next Steps

Ready to extend this prototype:

- [ ] Add MCP server integration for tool use
- [ ] Connect to real LLM providers
- [ ] Build human review dashboard
- [ ] Add pipeline templates library
- [ ] Implement agent learning from feedback
- [ ] Add cost tracking and optimization
- [ ] Build web UI for pipeline visualization

## 🤝 Contributing

This is a demonstration prototype. For production use:

1. Fork the repository
2. Replace mock implementations with real integrations
3. Add comprehensive error handling
4. Implement proper authentication/authorization
5. Scale the agent pool architecture
6. Add monitoring and observability

## 📄 License

MIT - Free for commercial and personal use

## 🙏 Inspiration

This prototype is inspired by [RealFast.ai's Vayu platform](https://realfast.ai), which provides enterprise-grade AI agent orchestration for IT services teams.

---

**Built with TypeScript, Node.js, and a vision for human-AI collaboration.**
