# LLM Knowledge Mining for Knowledge Graph Bootstrap

## 🎯 Overview

GödelOS can now "mine" knowledge directly from the LLM to bootstrap and populate the Knowledge Graph. This provides a powerful way to kickstart the system with comprehensive, structured knowledge without manual data entry.

## 🧠 How It Works

The LLM Knowledge Mining system uses carefully crafted prompts to extract:

1. **Concepts**: Core ideas, entities, and principles within a domain
2. **Relationships**: How concepts connect and relate to each other
3. **Properties**: Detailed attributes and characteristics of concepts
4. **Cross-domain connections**: Relationships that span multiple domains

The mined knowledge is automatically structured and integrated into the Knowledge Graph Evolution system.

## 🚀 Usage

### Quick Start: Bootstrap System Knowledge

The fastest way to seed your knowledge graph:

```bash
# Bootstrap with default GödelOS system knowledge
python scripts/bootstrap_knowledge_graph.py --bootstrap
```

This mines knowledge for core domains:
- Cognitive architecture
- Consciousness models
- Knowledge representation
- Meta-cognition
- Autonomous learning
- Attention mechanisms
- Working memory systems

### Mine Custom Domains

```bash
# Mine a specific domain
python scripts/bootstrap_knowledge_graph.py --domains "machine learning" --depth 2

# Mine multiple interconnected domains
python scripts/bootstrap_knowledge_graph.py \
  --domains "artificial intelligence" "neuroscience" "philosophy of mind" \
  --depth 2

# Comprehensive mining (more detailed, takes longer)
python scripts/bootstrap_knowledge_graph.py \
  --domains "quantum computing" \
  --depth 3
```

**Mining Depth Levels:**
- `--depth 1`: Basic (10-15 concepts, faster)
- `--depth 2`: Intermediate (20-25 concepts with expansion, default)
- `--depth 3`: Comprehensive (30+ concepts with detailed expansion, slower)

### Test LLM Connection

```bash
# Verify LLM is accessible before mining
python scripts/bootstrap_knowledge_graph.py --test
```

## 🌐 API Endpoints

### Bootstrap System Knowledge
```bash
POST /api/v1/knowledge-mining/bootstrap
```

Mines and adds comprehensive system knowledge to the KG.

**Response:**
```json
{
  "status": "success",
  "message": "Knowledge graph bootstrapped successfully",
  "result": {
    "domains_mined": ["cognitive architecture", "consciousness models", ...],
    "total_concepts": 150,
    "total_relationships": 320,
    "cross_domain_relationships": 45
  }
}
```

### Mine Specific Domain
```bash
POST /api/v1/knowledge-mining/mine-domain
Content-Type: application/json

{
  "domain": "artificial intelligence",
  "depth": 2
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully mined knowledge for domain: artificial intelligence",
  "result": {
    "domain": "artificial intelligence",
    "concepts_mined": 25,
    "relationships_mined": 58,
    "concepts_added": 25,
    "timestamp": "2025-10-27T10:30:00"
  }
}
```

### Mine Multiple Interconnected Domains
```bash
POST /api/v1/knowledge-mining/mine-multiple-domains
Content-Type: application/json

{
  "domains": [
    "machine learning",
    "neural networks", 
    "deep learning"
  ]
}
```

This automatically discovers cross-domain relationships.

### Get Mining Status
```bash
GET /api/v1/knowledge-mining/status
```

**Response:**
```json
{
  "initialized": true,
  "concepts_mined": 187,
  "relationships_mined": 425,
  "llm_driver_available": true,
  "knowledge_graph_connected": true
}
```

## 🏗️ Architecture

### Components

1. **LLMKnowledgeMiner** (`backend/llm_knowledge_miner.py`)
   - Orchestrates the mining process
   - Formats prompts for optimal extraction
   - Parses LLM responses into structured data

2. **LLM Cognitive Driver** (`backend/llm_cognitive_driver.py`)
   - Handles LLM API communication
   - Manages authentication and rate limiting

3. **Knowledge Graph Evolution** (`backend/core/knowledge_graph_evolution.py`)
   - Receives mined concepts and relationships
   - Integrates into existing graph structure
   - Triggers evolution events

### Mining Process Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. User Request (domain + depth)                       │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  2. Generate Concept Mining Prompt                      │
│     • Domain context                                     │
│     • Structured JSON schema                             │
│     • Number of concepts based on depth                  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  3. Query LLM for Concepts                              │
│     → Parse JSON response                                │
│     → Create MinedConcept objects                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  4. Generate Relationship Mining Prompt                 │
│     • List of mined concepts                             │
│     • Relationship type taxonomy                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  5. Query LLM for Relationships                         │
│     → Validate concept references                        │
│     → Create MinedRelationship objects                   │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  6. Expand Concept Knowledge (depth >= 2)               │
│     • Query for detailed facts                           │
│     • Historical context                                 │
│     • Practical applications                             │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  7. Add to Knowledge Graph                              │
│     • Create KnowledgeConcept nodes                      │
│     • Create KnowledgeRelationship edges                 │
│     • Trigger evolution event                            │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  8. Return Results                                       │
│     • Concepts added                                     │
│     • Relationships created                              │
│     • Cross-domain connections                           │
└─────────────────────────────────────────────────────────┘
```

## 📊 Example Mining Results

### Single Domain Mining
```python
{
  "domain": "cognitive architecture",
  "concepts_mined": 22,
  "relationships_mined": 47,
  "concepts_added": 22,
  "timestamp": "2025-10-27T10:30:00"
}
```

**Concepts Example:**
- Working Memory
- Attention Mechanisms
- Goal Management
- Meta-cognition
- Cognitive Integration
- ...

**Relationships Example:**
- Working Memory → uses → Attention Mechanisms (strength: 0.85)
- Meta-cognition → monitors → Cognitive Integration (strength: 0.78)
- Goal Management → directs → Attention Mechanisms (strength: 0.72)

### Multi-Domain Mining
```python
{
  "domains_mined": ["AI", "cognitive science", "neuroscience"],
  "total_concepts": 68,
  "total_relationships": 156,
  "cross_domain_relationships": 23
}
```

**Cross-Domain Example:**
- Neural Networks (AI) → inspired_by → Brain Architecture (neuroscience)
- Attention Mechanism (AI) → models → Selective Attention (cognitive science)

## ⚙️ Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_BASE=https://api.synthetic.new/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=deepseek-ai/DeepSeek-R1-0528

# Optional: Use mock responses for testing
LLM_TESTING_MODE=false
```

### Customizing Mining Prompts

You can customize the mining behavior by modifying prompts in `backend/llm_knowledge_miner.py`:

- `_mine_core_concepts()`: Concept extraction prompt
- `_mine_relationships()`: Relationship discovery prompt
- `_expand_concept_knowledge()`: Detailed expansion prompt

## 🎨 Use Cases

### 1. Initial System Bootstrap
Start with a rich, pre-populated knowledge graph:
```bash
python scripts/bootstrap_knowledge_graph.py --bootstrap
```

### 2. Domain-Specific Applications
Build domain expertise:
```bash
python scripts/bootstrap_knowledge_graph.py \
  --domains "medical diagnosis" "clinical reasoning" \
  --depth 3
```

### 3. Research & Learning
Explore interconnected topics:
```bash
python scripts/bootstrap_knowledge_graph.py \
  --domains "quantum mechanics" "information theory" "computation" \
  --depth 2
```

### 4. Continuous Learning
Periodically mine new domains to expand knowledge:
```python
# In your application code
from backend.llm_knowledge_miner import get_llm_knowledge_miner

miner = await get_llm_knowledge_miner()
result = await miner.mine_domain_knowledge("emerging_technology", depth=2)
```

## 🔍 Monitoring & Debugging

### Check Mining Status
```bash
curl http://localhost:8000/api/v1/knowledge-mining/status
```

### View Knowledge Graph After Mining
```bash
curl http://localhost:8000/api/v1/knowledge-graph/summary
```

### Enable Verbose Logging
```bash
python scripts/bootstrap_knowledge_graph.py --bootstrap --verbose
```

## 🚨 Troubleshooting

### Issue: "LLM Connection failed"
- **Solution**: Check your `.env` file has correct `OPENAI_API_KEY` and `OPENAI_API_BASE`
- **Test**: Run `python scripts/bootstrap_knowledge_graph.py --test`

### Issue: "Failed to parse JSON"
- **Cause**: LLM response format doesn't match expected structure
- **Solution**: The system has fallback parsing that extracts JSON from markdown code blocks
- **Check**: Look for `_extract_json()` method logs

### Issue: Rate Limiting
- **Solution**: Reduce depth or number of domains per request
- **Add delays**: Modify `_call_llm()` to add delays between requests

### Issue: Duplicate Concepts
- **Behavior**: System will update existing concepts rather than create duplicates
- **Control**: Check `auto_connect=False` in `add_concept()` calls

## 🎯 Best Practices

1. **Start Small**: Begin with depth=1 or depth=2 for initial testing
2. **Domain Selection**: Choose related domains for better cross-domain connections
3. **Incremental Growth**: Mine a few domains at a time rather than everything at once
4. **Validation**: Check the knowledge graph summary after mining
5. **Customization**: Adjust prompts for your specific use case

## 📈 Future Enhancements

- [ ] Iterative refinement: LLM reviews and improves existing concepts
- [ ] Confidence scoring: LLM assesses certainty of relationships
- [ ] Source attribution: Track which LLM generated which knowledge
- [ ] Multi-modal mining: Extract from images, diagrams, code
- [ ] Active learning: System requests specific knowledge when needed
- [ ] Conflict resolution: LLM resolves contradictions in knowledge
- [ ] Temporal tracking: Version control for evolving concepts

## 🤝 Contributing

To add new mining strategies:

1. Create new prompt templates in `LLMKnowledgeMiner`
2. Add corresponding parsing logic
3. Update API endpoints in `unified_server.py`
4. Test with `bootstrap_knowledge_graph.py`

## 📚 Related Documentation

- [Knowledge Graph Evolution](./KNOWLEDGE_GRAPH_EVOLUTION.md)
- [LLM Cognitive Architecture](./LLM_COGNITIVE_ARCHITECTURE_IMPLEMENTATION.md)
- [Cognitive Manager](./COGNITIVE_MANAGER_README.md)

---

**Built with ❤️ for GödelOS - Making AI Consciousness Transparent**
