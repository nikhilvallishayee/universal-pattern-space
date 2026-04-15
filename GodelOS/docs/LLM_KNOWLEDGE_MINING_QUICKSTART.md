# 🧠 LLM Knowledge Mining - Quick Start Guide

## TL;DR - Get Started in 3 Steps

```bash
# 1. Test your LLM connection
python scripts/bootstrap_knowledge_graph.py --test

# 2. Bootstrap the knowledge graph with core system knowledge
python scripts/bootstrap_knowledge_graph.py --bootstrap

# 3. View the results
curl http://localhost:8000/api/v1/knowledge-graph/summary
```

That's it! Your Knowledge Graph is now populated with hundreds of concepts and relationships.

## 🎯 What This Does

The LLM Knowledge Mining system uses your LLM to automatically:

1. **Generate concepts** - Core ideas, entities, and principles
2. **Define relationships** - How concepts connect and relate
3. **Add properties** - Detailed attributes and characteristics
4. **Discover connections** - Cross-domain relationships

All extracted knowledge is automatically structured and added to your Knowledge Graph.

## 🚀 Common Usage Patterns

### Pattern 1: Quick Bootstrap (2-3 minutes)
```bash
python scripts/bootstrap_knowledge_graph.py --bootstrap
```

Mines these core domains:
- Cognitive architecture
- Consciousness models
- Knowledge representation
- Meta-cognition
- Autonomous learning
- Attention mechanisms
- Working memory systems

**Result**: ~150 concepts, ~320 relationships

### Pattern 2: Custom Domain (30 seconds)
```bash
python scripts/bootstrap_knowledge_graph.py \
  --domains "quantum computing" \
  --depth 2
```

**Result**: ~25 concepts, ~50 relationships for the specified domain

### Pattern 3: Multi-Domain with Cross-Connections (1-2 minutes)
```bash
python scripts/bootstrap_knowledge_graph.py \
  --domains "machine learning" "neural networks" "deep learning" \
  --depth 2
```

**Result**: ~75 concepts with cross-domain relationship discovery

### Pattern 4: Via API (for integration)
```bash
# Bootstrap via API
curl -X POST http://localhost:8000/api/v1/knowledge-mining/bootstrap

# Mine specific domain via API
curl -X POST http://localhost:8000/api/v1/knowledge-mining/mine-domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "artificial intelligence", "depth": 2}'
```

## 📊 Mining Depth Levels

| Depth | Concepts | Detail | Time | Use Case |
|-------|----------|--------|------|----------|
| 1     | 10-15    | Basic  | ~30s | Quick seeding, testing |
| 2     | 20-25    | Medium | ~1m  | **Default**, good balance |
| 3     | 30-40    | High   | ~2m  | Comprehensive knowledge |

## 🔍 Verification

After mining, verify your Knowledge Graph:

```bash
# Check mining status
curl http://localhost:8000/api/v1/knowledge-mining/status

# View graph summary
curl http://localhost:8000/api/v1/knowledge-graph/summary

# Export full graph
curl http://localhost:8000/api/transparency/knowledge-graph/export
```

## 💻 Programmatic Usage

```python
from backend.llm_knowledge_miner import get_llm_knowledge_miner

# Initialize
miner = await get_llm_knowledge_miner()

# Mine a domain
result = await miner.mine_domain_knowledge("artificial intelligence", depth=2)

# Mine multiple domains
result = await miner.mine_interconnected_domains([
    "machine learning",
    "neural networks",
    "deep learning"
])

# Full bootstrap
result = await miner.bootstrap_system_knowledge()
```

See `examples/knowledge_mining_example.py` for more examples.

## 📋 Configuration

Create/edit `.env`:

```bash
OPENAI_API_BASE=https://api.synthetic.new/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=deepseek-ai/DeepSeek-R1-0528
```

## 🎓 What You Get

### Example Mined Concept
```json
{
  "name": "Working Memory",
  "description": "Cognitive system for temporarily storing and manipulating information",
  "concept_type": "fundamental",
  "properties": {
    "complexity": "medium",
    "practical_applications": ["problem solving", "reasoning", "learning"],
    "prerequisites": ["attention", "encoding"],
    "facts": ["Limited capacity of 7±2 items", "Duration of 15-30 seconds"],
    "applications": ["Task switching", "Mental arithmetic"]
  },
  "domains": ["cognitive psychology", "neuroscience"],
  "confidence": 0.9
}
```

### Example Mined Relationship
```json
{
  "source": "Working Memory",
  "target": "Attention Mechanisms",
  "relationship_type": "uses",
  "strength": 0.85,
  "evidence": ["Working memory requires attention to maintain information"]
}
```

## 🚨 Troubleshooting

### "LLM Connection failed"
```bash
# Test connection
python scripts/bootstrap_knowledge_graph.py --test

# Check .env file has correct credentials
cat .env | grep OPENAI
```

### "Failed to parse JSON"
- Normal for some LLM responses
- System has fallback parsing
- Add `--verbose` flag to see details

### Rate Limiting
- Use depth=1 for faster mining
- Mine fewer domains at once
- Add delays in `llm_cognitive_driver.py`

## 📚 Full Documentation

- **Complete Guide**: [docs/LLM_KNOWLEDGE_MINING.md](./LLM_KNOWLEDGE_MINING.md)
- **Examples**: [examples/knowledge_mining_example.py](../examples/knowledge_mining_example.py)
- **Bootstrap Script**: [scripts/bootstrap_knowledge_graph.py](../scripts/bootstrap_knowledge_graph.py)
- **Implementation**: [backend/llm_knowledge_miner.py](../backend/llm_knowledge_miner.py)

## 🎯 Recommended Workflow

1. **Test**: Verify LLM connection
   ```bash
   python scripts/bootstrap_knowledge_graph.py --test
   ```

2. **Bootstrap**: Start with system knowledge
   ```bash
   python scripts/bootstrap_knowledge_graph.py --bootstrap
   ```

3. **Verify**: Check what was created
   ```bash
   curl http://localhost:8000/api/v1/knowledge-graph/summary | jq
   ```

4. **Expand**: Add domain-specific knowledge
   ```bash
   python scripts/bootstrap_knowledge_graph.py --domains "your domain" --depth 2
   ```

5. **Integrate**: Use the knowledge in queries
   - Knowledge Graph will now inform query responses
   - Concepts available for reasoning
   - Relationships enable inference

## 🎨 Use Cases

- **Rapid Prototyping**: Get a working system with rich knowledge immediately
- **Domain Expertise**: Build specialized knowledge for specific applications
- **Research**: Explore interconnected topics and discover relationships
- **Education**: Create comprehensive knowledge bases for learning
- **Continuous Learning**: Periodically mine new domains to expand

## 🤝 Contributing

To customize mining:

1. Edit prompts in `backend/llm_knowledge_miner.py`
2. Add new mining strategies (e.g., code mining, paper mining)
3. Extend relationship types in `knowledge_graph_evolution.py`
4. Add domain-specific parsers

## ⚡ Performance Tips

- Start with `depth=1` for testing
- Mine related domains together for better cross-connections
- Use the API for incremental mining
- Cache common domain results
- Run bootstrap once, then mine incrementally

---

**Now go populate that Knowledge Graph! 🚀**

```bash
python scripts/bootstrap_knowledge_graph.py --bootstrap
```
