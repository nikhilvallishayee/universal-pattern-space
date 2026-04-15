#!/usr/bin/env python3
"""
Bootstrap GödelOS Knowledge Graph from LLM

This script uses the LLM to mine initial knowledge and populate the
Knowledge Graph, providing a strong foundation for the system to start from.
"""

import asyncio
import argparse
import logging
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm_knowledge_miner import get_llm_knowledge_miner
from backend.llm_cognitive_driver import get_llm_cognitive_driver
from backend.core.knowledge_graph_evolution import KnowledgeGraphEvolution

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def bootstrap_system_knowledge():
    """Bootstrap the knowledge graph with core system knowledge"""
    logger.info("=" * 60)
    logger.info("🧠 GödelOS Knowledge Graph Bootstrap")
    logger.info("=" * 60)
    
    try:
        # Initialize LLM driver
        logger.info("\n1️⃣ Initializing LLM Cognitive Driver...")
        llm_driver = await get_llm_cognitive_driver()
        logger.info("✅ LLM driver ready")
        
        # Initialize knowledge graph
        logger.info("\n2️⃣ Initializing Knowledge Graph Evolution System...")
        knowledge_graph = KnowledgeGraphEvolution(llm_driver=llm_driver)
        logger.info("✅ Knowledge graph ready")
        
        # Initialize knowledge miner
        logger.info("\n3️⃣ Initializing LLM Knowledge Miner...")
        miner = await get_llm_knowledge_miner(
            llm_driver=llm_driver,
            knowledge_graph=knowledge_graph
        )
        logger.info("✅ Knowledge miner ready")
        
        # Bootstrap system knowledge
        logger.info("\n4️⃣ Mining System Knowledge from LLM...")
        logger.info("   This will take several minutes as we query the LLM for comprehensive knowledge...")
        
        result = await miner.bootstrap_system_knowledge()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Bootstrap Complete!")
        logger.info("=" * 60)
        logger.info(f"\n📊 Results:")
        logger.info(f"   • Domains mined: {len(result['domains_mined'])}")
        logger.info(f"   • Total concepts: {result['total_concepts']}")
        logger.info(f"   • Total relationships: {result['total_relationships']}")
        logger.info(f"   • Cross-domain connections: {result['cross_domain_relationships']}")
        
        logger.info(f"\n📂 Domains covered:")
        for domain in result['domains_mined']:
            domain_result = result['domain_results'].get(domain, {})
            logger.info(f"   • {domain}: {domain_result.get('concepts_mined', 0)} concepts")
        
        logger.info(f"\n✅ Knowledge graph is now seeded and ready to use!")
        
        return result
        
    except Exception as e:
        logger.error(f"\n❌ Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def mine_custom_domains(domains: list, depth: int = 2):
    """Mine knowledge for custom domains"""
    logger.info("=" * 60)
    logger.info("🔍 Mining Custom Domain Knowledge")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        logger.info("\n1️⃣ Initializing components...")
        llm_driver = await get_llm_cognitive_driver()
        knowledge_graph = KnowledgeGraphEvolution(llm_driver=llm_driver)
        miner = await get_llm_knowledge_miner(
            llm_driver=llm_driver,
            knowledge_graph=knowledge_graph
        )
        logger.info("✅ Components ready")
        
        # Mine each domain
        all_results = []
        for i, domain in enumerate(domains, 1):
            logger.info(f"\n{i}️⃣ Mining domain: '{domain}' (depth: {depth})...")
            result = await miner.mine_domain_knowledge(domain, depth)
            all_results.append(result)
            
            logger.info(f"   ✅ Mined {result['concepts_mined']} concepts")
            logger.info(f"   ✅ Mined {result['relationships_mined']} relationships")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Custom Domain Mining Complete!")
        logger.info("=" * 60)
        
        total_concepts = sum(r['concepts_mined'] for r in all_results)
        total_relationships = sum(r['relationships_mined'] for r in all_results)
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"   • Domains mined: {len(domains)}")
        logger.info(f"   • Total concepts: {total_concepts}")
        logger.info(f"   • Total relationships: {total_relationships}")
        
        return all_results
        
    except Exception as e:
        logger.error(f"\n❌ Domain mining failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_llm_connection():
    """Test the LLM connection"""
    logger.info("Testing LLM connection...")
    
    try:
        llm_driver = await get_llm_cognitive_driver()
        
        test_prompt = "Respond with 'OK' if you can receive this message."
        response = await llm_driver._call_llm(test_prompt, max_tokens=50)
        
        logger.info(f"✅ LLM Connection successful!")
        logger.info(f"   Response: {response[:100]}")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM Connection failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap GödelOS Knowledge Graph from LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bootstrap with default system knowledge
  python bootstrap_knowledge_graph.py --bootstrap
  
  # Mine specific domains
  python bootstrap_knowledge_graph.py --domains "machine learning" "neural networks" --depth 2
  
  # Mine at different depths (1=basic, 2=intermediate, 3=comprehensive)
  python bootstrap_knowledge_graph.py --domains "quantum computing" --depth 3
  
  # Test LLM connection
  python bootstrap_knowledge_graph.py --test
        """
    )
    
    parser.add_argument(
        '--bootstrap',
        action='store_true',
        help='Bootstrap with default GödelOS system knowledge'
    )
    
    parser.add_argument(
        '--domains',
        nargs='+',
        help='Custom domains to mine (e.g., "artificial intelligence" "neuroscience")'
    )
    
    parser.add_argument(
        '--depth',
        type=int,
        choices=[1, 2, 3],
        default=2,
        help='Mining depth: 1=basic, 2=intermediate (default), 3=comprehensive'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test LLM connection'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if we have any action to perform
    if not (args.bootstrap or args.domains or args.test):
        parser.print_help()
        sys.exit(0)
    
    # Run the appropriate action
    try:
        if args.test:
            asyncio.run(test_llm_connection())
        elif args.bootstrap:
            asyncio.run(bootstrap_system_knowledge())
        elif args.domains:
            asyncio.run(mine_custom_domains(args.domains, args.depth))
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Bootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
