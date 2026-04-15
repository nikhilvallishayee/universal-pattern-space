#!/usr/bin/env python3
"""
Quick example demonstrating LLM Knowledge Mining

This shows how to programmatically use the knowledge mining system
to populate your knowledge graph from the LLM.
"""

import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def example_basic_mining():
    """Example: Mine a single domain"""
    from backend.llm_knowledge_miner import get_llm_knowledge_miner
    
    logger.info("Example 1: Mining a single domain")
    logger.info("=" * 50)
    
    # Get the knowledge miner
    miner = await get_llm_knowledge_miner()
    
    # Mine knowledge about "artificial intelligence"
    result = await miner.mine_domain_knowledge(
        domain="artificial intelligence",
        depth=1  # Basic level for quick demo
    )
    
    logger.info(f"\n✅ Mined {result['concepts_mined']} concepts")
    logger.info(f"✅ Created {result['relationships_mined']} relationships")
    
    return result

async def example_multi_domain():
    """Example: Mine multiple interconnected domains"""
    from backend.llm_knowledge_miner import get_llm_knowledge_miner
    
    logger.info("\n\nExample 2: Mining interconnected domains")
    logger.info("=" * 50)
    
    miner = await get_llm_knowledge_miner()
    
    # Mine related domains that will have cross-connections
    domains = [
        "machine learning",
        "neural networks",
        "data science"
    ]
    
    result = await miner.mine_interconnected_domains(domains)
    
    logger.info(f"\n✅ Total concepts: {result['total_concepts']}")
    logger.info(f"✅ Total relationships: {result['total_relationships']}")
    logger.info(f"✅ Cross-domain connections: {result['cross_domain_relationships']}")
    
    return result

async def example_custom_expansion():
    """Example: Mine with concept expansion"""
    from backend.llm_knowledge_miner import get_llm_knowledge_miner
    
    logger.info("\n\nExample 3: Mining with detailed expansion")
    logger.info("=" * 50)
    
    miner = await get_llm_knowledge_miner()
    
    # Depth 2 includes concept expansion with facts, examples, applications
    result = await miner.mine_domain_knowledge(
        domain="cognitive psychology",
        depth=2
    )
    
    logger.info(f"\n✅ Mined {result['concepts_mined']} concepts with detailed properties")
    
    # Show example of expanded concept
    if miner.mined_concepts:
        example_concept = list(miner.mined_concepts.values())[0]
        logger.info(f"\nExample concept: {example_concept.name}")
        logger.info(f"Description: {example_concept.description[:100]}...")
        if example_concept.properties:
            logger.info(f"Properties: {list(example_concept.properties.keys())}")
    
    return result

async def example_inspect_results():
    """Example: Inspect mined knowledge"""
    from backend.llm_knowledge_miner import get_llm_knowledge_miner
    
    logger.info("\n\nExample 4: Inspecting mined knowledge")
    logger.info("=" * 50)
    
    miner = await get_llm_knowledge_miner()
    
    # Mine a small domain
    await miner.mine_domain_knowledge("natural language processing", depth=1)
    
    # Inspect concepts
    logger.info(f"\n📋 Mined Concepts ({len(miner.mined_concepts)}):")
    for i, (name, concept) in enumerate(list(miner.mined_concepts.items())[:5]):
        logger.info(f"  {i+1}. {name}")
        logger.info(f"     Type: {concept.concept_type}")
        logger.info(f"     Confidence: {concept.confidence}")
    
    # Inspect relationships
    logger.info(f"\n🔗 Mined Relationships ({len(miner.mined_relationships)}):")
    for i, rel in enumerate(miner.mined_relationships[:5]):
        logger.info(f"  {i+1}. {rel.source_concept} → {rel.relationship_type} → {rel.target_concept}")
        logger.info(f"     Strength: {rel.strength}")

async def example_bootstrap():
    """Example: Bootstrap entire system"""
    from backend.llm_knowledge_miner import get_llm_knowledge_miner
    
    logger.info("\n\nExample 5: Full system bootstrap")
    logger.info("=" * 50)
    logger.info("⚠️  This takes several minutes and makes multiple LLM calls")
    
    miner = await get_llm_knowledge_miner()
    
    # Bootstrap with comprehensive system knowledge
    result = await miner.bootstrap_system_knowledge()
    
    logger.info(f"\n✅ Bootstrapped {len(result['domains_mined'])} core domains")
    logger.info(f"✅ Total concepts: {result['total_concepts']}")
    logger.info(f"✅ Total relationships: {result['total_relationships']}")
    
    logger.info("\n📂 Domains covered:")
    for domain in result['domains_mined']:
        logger.info(f"  • {domain}")
    
    return result

async def main():
    """Run all examples"""
    logger.info("🧠 LLM Knowledge Mining Examples")
    logger.info("=" * 50)
    logger.info("\nThese examples show different ways to mine knowledge from the LLM")
    logger.info("to populate the GödelOS Knowledge Graph.\n")
    
    try:
        # Run examples
        await example_basic_mining()
        await example_multi_domain()
        await example_custom_expansion()
        await example_inspect_results()
        
        # Uncomment to run full bootstrap (takes longer)
        # await example_bootstrap()
        
        logger.info("\n\n" + "=" * 50)
        logger.info("✅ All examples completed successfully!")
        logger.info("=" * 50)
        
        logger.info("\n💡 Next steps:")
        logger.info("  1. Check the knowledge graph: GET /api/v1/knowledge-graph/summary")
        logger.info("  2. View concepts: GET /api/transparency/knowledge-graph/export")
        logger.info("  3. Mine more domains: POST /api/v1/knowledge-mining/mine-domain")
        logger.info("  4. Run full bootstrap: python scripts/bootstrap_knowledge_graph.py --bootstrap")
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Examples interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
