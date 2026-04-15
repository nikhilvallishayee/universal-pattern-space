#!/usr/bin/env python3
"""
Knowledge Import Demo

This script demonstrates importing foundational knowledge into GödelOS
to enable actual reasoning demonstrations.
"""

import asyncio
import aiohttp
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"

# Sample foundational knowledge to import
FOUNDATIONAL_KNOWLEDGE = [
    {
        "title": "Artificial Intelligence Fundamentals",
        "content": """
Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans. 

Key concepts in AI include:

1. Machine Learning: AI systems that can learn and improve from experience without being explicitly programmed for every task.

2. Neural Networks: Computing systems inspired by biological neural networks, consisting of interconnected nodes that process information.

3. Natural Language Processing (NLP): The ability of computers to understand, interpret, and generate human language.

4. Computer Vision: The field of AI that enables computers to interpret and understand visual information from the world.

5. Reasoning Systems: AI systems that can draw logical conclusions from available information, similar to human reasoning processes.

6. Knowledge Representation: Methods for encoding facts, rules, and relationships in a form that computers can process and reason about.

AI systems can be categorized as:
- Narrow AI: Systems designed for specific tasks (like chess playing or image recognition)
- General AI: Hypothetical systems with human-like cognitive abilities across all domains
- Superintelligence: AI that surpasses human intelligence in all areas

The goal of AI research is to create systems that can perform tasks that typically require human intelligence, such as learning, reasoning, problem-solving, perception, and language understanding.
        """,
        "category": "technology"
    },
    {
        "title": "Logic and Reasoning Principles",
        "content": """
Logic and reasoning form the foundation of rational thought and problem-solving.

Types of Reasoning:

1. Deductive Reasoning: Drawing specific conclusions from general premises. If the premises are true, the conclusion must be true.
   Example: All humans are mortal. Socrates is human. Therefore, Socrates is mortal.

2. Inductive Reasoning: Drawing general conclusions from specific observations. The conclusion is probable but not certain.
   Example: Every swan I've seen is white. Therefore, all swans are probably white.

3. Abductive Reasoning: Finding the best explanation for a set of observations.
   Example: The grass is wet. It probably rained last night.

Logical Principles:

1. Law of Identity: A thing is identical to itself (A = A)
2. Law of Non-Contradiction: Something cannot be both true and false at the same time
3. Law of Excluded Middle: A statement is either true or false, with no middle ground

Problem-Solving Strategies:

1. Break down complex problems into smaller, manageable parts
2. Identify patterns and relationships
3. Use analogies and examples from similar situations
4. Consider multiple perspectives and approaches
5. Test hypotheses systematically
6. Learn from mistakes and iterate

Critical thinking involves questioning assumptions, evaluating evidence, considering alternative explanations, and drawing well-reasoned conclusions.
        """,
        "category": "philosophy"
    },
    {
        "title": "Mathematics and Computation",
        "content": """
Mathematics provides the foundation for computation and logical reasoning in artificial intelligence systems.

Key Mathematical Concepts:

1. Set Theory: The study of collections of objects, fundamental to computer science and logic.

2. Probability Theory: Mathematical framework for reasoning under uncertainty.
   - Bayes' Theorem: P(A|B) = P(B|A) * P(A) / P(B)
   - Used in machine learning for classification and prediction

3. Graph Theory: Study of graphs (networks of nodes and edges)
   - Used in knowledge representation, social networks, and pathfinding algorithms

4. Linear Algebra: Study of vectors, matrices, and linear transformations
   - Essential for machine learning algorithms and neural networks

5. Calculus: Study of rates of change and accumulation
   - Used in optimization algorithms for training AI systems

6. Discrete Mathematics: Mathematics dealing with discrete objects
   - Includes combinatorics, number theory, and formal logic

Computational Concepts:

1. Algorithms: Step-by-step procedures for solving problems
2. Data Structures: Ways of organizing and storing data efficiently
3. Complexity Theory: Analysis of computational resource requirements
4. Recursion: Functions that call themselves to solve smaller instances of the same problem

The intersection of mathematics and computation enables:
- Optimization of AI system performance
- Formal verification of system properties
- Statistical analysis of data and results
- Development of new learning algorithms
        """,
        "category": "mathematics"
    },
    {
        "title": "Cognitive Science and Human Reasoning",
        "content": """
Cognitive science studies how humans think, learn, and process information, providing insights for AI development.

Human Cognitive Processes:

1. Perception: How we interpret sensory information from our environment
2. Attention: The mechanism that focuses cognitive resources on specific information
3. Memory: Systems for encoding, storing, and retrieving information
   - Working Memory: Temporary storage for active information processing
   - Long-term Memory: Permanent storage of knowledge and experiences

4. Language Processing: How humans understand and produce language
5. Problem Solving: Mental processes used to find solutions to challenges
6. Decision Making: Processes for choosing between alternatives

Cognitive Biases and Limitations:

1. Confirmation Bias: Tendency to search for information that confirms existing beliefs
2. Availability Heuristic: Judging probability by how easily examples come to mind
3. Anchoring Bias: Over-relying on the first piece of information encountered
4. Overconfidence Effect: Tendency to overestimate one's own knowledge or abilities

Learning Mechanisms:

1. Classical Conditioning: Learning through association
2. Operant Conditioning: Learning through consequences
3. Observational Learning: Learning by watching others
4. Cognitive Learning: Learning through mental processes like reasoning and problem-solving

Understanding human cognition helps in:
- Designing AI systems that complement human thinking
- Identifying areas where AI can augment human capabilities
- Creating more intuitive human-AI interfaces
- Developing AI systems that can explain their reasoning to humans
        """,
        "category": "psychology"
    }
]

async def import_text_knowledge(session, knowledge_item):
    """Import a single text knowledge item."""
    try:
        url = f"{BASE_URL}/knowledge/import/text"
        
        payload = {
            "content": knowledge_item["content"],
            "title": knowledge_item["title"],
            "category": knowledge_item["category"]
        }
        
        logger.info(f"Importing: {knowledge_item['title']}")
        
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ Import started: {result.get('import_id')}")
                return result
            else:
                error_text = await response.text()
                logger.error(f"❌ Import failed: {response.status} - {error_text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Exception during import: {e}")
        return None

async def import_wikipedia_topic(session, topic, category="encyclopedia"):
    """Import knowledge from Wikipedia."""
    try:
        url = f"{BASE_URL}/knowledge/import/wikipedia"
        
        payload = {
            "topic": topic,
            "category": category
        }
        
        logger.info(f"Importing Wikipedia topic: {topic}")
        
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ Wikipedia import started: {result.get('import_id')}")
                return result
            else:
                error_text = await response.text()
                logger.error(f"❌ Wikipedia import failed: {response.status} - {error_text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Exception during Wikipedia import: {e}")
        return None

async def test_query_after_import(session, query):
    """Test a query to see if the imported knowledge is being used."""
    try:
        url = f"{BASE_URL}/query"
        
        payload = {
            "query": query,
            "include_reasoning": True,
            "max_response_length": 500
        }
        
        logger.info(f"Testing query: {query}")
        
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                logger.info(f"✅ Query successful")
                print(f"\n{'='*60}")
                print(f"QUERY: {query}")
                print(f"{'='*60}")
                print(f"RESPONSE: {result.get('response', 'No response')}")
                if result.get('reasoning'):
                    print(f"\nREASONING: {result.get('reasoning')}")
                print(f"{'='*60}\n")
                return result
            else:
                error_text = await response.text()
                logger.error(f"❌ Query failed: {response.status} - {error_text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Exception during query: {e}")
        return None

async def main():
    """Main function to import knowledge and test reasoning."""
    
    print("🚀 Starting GödelOS Knowledge Import Demo")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Import foundational knowledge
        print("\n📚 Importing foundational knowledge...")
        import_results = []
        
        for knowledge_item in FOUNDATIONAL_KNOWLEDGE:
            result = await import_text_knowledge(session, knowledge_item)
            if result:
                import_results.append(result)
            await asyncio.sleep(1)  # Small delay between imports
        
        # Import some Wikipedia topics for additional knowledge
        print("\n🌐 Importing Wikipedia knowledge...")
        wikipedia_topics = [
            ("Artificial intelligence", "technology"),
            ("Logic", "philosophy"),
            ("Cognitive science", "psychology")
        ]
        
        for topic, category in wikipedia_topics:
            result = await import_wikipedia_topic(session, topic, category)
            if result:
                import_results.append(result)
            await asyncio.sleep(1)
        
        print(f"\n✅ Import phase complete. {len(import_results)} imports initiated.")
        
        # Wait a bit for processing
        print("\n⏳ Waiting for knowledge processing...")
        await asyncio.sleep(5)
        
        # Test queries to demonstrate reasoning
        print("\n🧠 Testing reasoning capabilities...")
        
        test_queries = [
            "What is artificial intelligence?",
            "Explain the difference between deductive and inductive reasoning",
            "How does machine learning work?",
            "What are the key principles of logic?",
            "How do neural networks process information?",
            "What is the relationship between mathematics and computation in AI?",
            "Explain cognitive biases and how they affect human reasoning"
        ]
        
        for query in test_queries:
            await test_query_after_import(session, query)
            await asyncio.sleep(2)  # Pause between queries
        
        print("\n🎉 Knowledge import and reasoning demonstration complete!")
        print("The GödelOS system now has foundational knowledge for reasoning.")

if __name__ == "__main__":
    asyncio.run(main())
