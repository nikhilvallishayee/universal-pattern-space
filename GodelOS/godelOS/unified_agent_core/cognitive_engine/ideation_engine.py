"""
Ideation Engine Implementation for GodelOS

This module implements the IdeationEngine class, which is responsible for
generating and evaluating ideas based on thoughts and reflections in the
cognitive system. The enhanced implementation includes creative combination
of existing thoughts, analogy-based idea generation, sophisticated evaluation
of idea novelty and utility, and feedback mechanisms for idea refinement.
"""

import logging
import time
import random
import re
from typing import Dict, List, Optional, Any, Tuple, Set
import asyncio
from collections import defaultdict
import math
import uuid

from godelOS.unified_agent_core.cognitive_engine.interfaces import (
    Thought, Reflection, Idea, CognitiveContext, IdeationEngineInterface
)

logger = logging.getLogger(__name__)


class IdeationEngine(IdeationEngineInterface):
    """
    Enhanced IdeationEngine implementation for GodelOS.
    
    The IdeationEngine is responsible for generating and evaluating ideas based on
    thoughts and reflections in the cognitive system.
    
    Features:
    1. Creative combination of existing thoughts
    2. Analogy-based idea generation
    3. Sophisticated evaluation of idea novelty and utility
    4. Feedback mechanisms for idea refinement
    """
    
    def __init__(self):
        """Initialize the ideation engine."""
        self.ideas: Dict[str, Idea] = {}
        self.thought_ideas: Dict[str, List[str]] = {}  # thought_id -> list of idea_ids
        self.lock = asyncio.Lock()
        
        # For creative combinations
        self.idea_combinations: Dict[str, List[Tuple[str, str]]] = {}  # idea_id -> list of (source1_id, source2_id)
        
        # For analogy generation
        self.analogies: Dict[str, Dict[str, Any]] = {}  # idea_id -> analogy information
        
        # For idea refinement
        self.idea_versions: Dict[str, List[str]] = {}  # original_idea_id -> list of refined_idea_ids
        self.idea_feedback: Dict[str, List[Dict[str, Any]]] = {}  # idea_id -> list of feedback
        
        # Knowledge store reference (will be set by the cognitive engine)
        self.knowledge_store = None
    
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The knowledge store
        """
        self.knowledge_store = knowledge_store
    
    async def generate_ideas(self, thought: Thought, reflection: Reflection, context: CognitiveContext) -> List[Idea]:
        """
        Generate ideas based on a thought and reflection using multiple generation strategies.
        
        Args:
            thought: The thought
            reflection: The reflection on the thought
            context: The cognitive context
            
        Returns:
            List of generated ideas
        """
        logger.debug(f"Generating ideas for thought {thought.id} based on reflection {reflection.id}")
        
        # Number of ideas to generate based on thought priority and cognitive load
        num_ideas = self._determine_idea_count(thought, context)
        
        ideas = []
        
        # Allocate idea generation across different strategies
        direct_count = max(1, num_ideas // 3)
        combination_count = max(1, num_ideas // 3)
        analogy_count = max(1, num_ideas - direct_count - combination_count)
        
        # 1. Generate direct ideas from thought and reflection
        direct_ideas = await self._generate_direct_ideas(thought, reflection, context, direct_count)
        ideas.extend(direct_ideas)
        
        # 2. Generate ideas by combining with other thoughts
        combination_ideas = await self._generate_combination_ideas(thought, reflection, context, combination_count)
        ideas.extend(combination_ideas)
        
        # 3. Generate ideas using analogies
        analogy_ideas = await self._generate_analogy_ideas(thought, reflection, context, analogy_count)
        ideas.extend(analogy_ideas)
        
        # Store all ideas
        async with self.lock:
            for idea in ideas:
                self.ideas[idea.id] = idea
                
                # Update thought-idea mapping
                if thought.id not in self.thought_ideas:
                    self.thought_ideas[thought.id] = []
                
                self.thought_ideas[thought.id].append(idea.id)
        
        logger.debug(f"Generated {len(ideas)} ideas for thought {thought.id}")
        return ideas
    
    async def evaluate_idea(self, idea: Idea, context: CognitiveContext) -> Dict[str, float]:
        """
        Perform comprehensive evaluation of an idea.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.debug(f"Evaluating idea {idea.id}")
        
        # Calculate core evaluation metrics
        novelty = await self._evaluate_novelty(idea, context)
        utility = await self._evaluate_utility(idea, context)
        feasibility = self._evaluate_feasibility(idea, context)
        relevance = self._evaluate_relevance(idea, context)
        
        # Calculate additional metrics
        adaptability = self._evaluate_adaptability(idea, context)
        complexity = self._evaluate_complexity(idea)
        
        # Calculate weighted overall score
        overall = (
            0.25 * novelty +
            0.30 * utility +
            0.20 * feasibility +
            0.15 * relevance +
            0.05 * adaptability +
            0.05 * (1.0 - complexity)  # Lower complexity is better
        )
        
        evaluation = {
            "novelty": novelty,
            "utility": utility,
            "feasibility": feasibility,
            "relevance": relevance,
            "adaptability": adaptability,
            "complexity": complexity,
            "overall": overall
        }
        
        # Update idea with evaluation results
        async with self.lock:
            if idea.id in self.ideas:
                # Store evaluation in metadata
                self.ideas[idea.id].metadata["evaluation"] = evaluation
                
                # Update the idea's scores with the calculated values
                self.ideas[idea.id].novelty_score = novelty
                self.ideas[idea.id].utility_score = utility
        
        return evaluation
    
    async def get_ideas_for_thought(self, thought_id: str,
                                   min_score: Optional[float] = None,
                                   sort_by: Optional[str] = None) -> List[Idea]:
        """
        Get all ideas for a thought with filtering and sorting options.
        
        Args:
            thought_id: The ID of the thought
            min_score: Optional minimum overall score to filter ideas
            sort_by: Optional metric to sort by ("novelty", "utility", "overall", etc.)
            
        Returns:
            List of ideas for the thought
        """
        async with self.lock:
            idea_ids = self.thought_ideas.get(thought_id, [])
            ideas = [self.ideas[iid] for iid in idea_ids if iid in self.ideas]
            
            # Filter by minimum score if specified
            if min_score is not None:
                ideas = [
                    idea for idea in ideas
                    if idea.metadata.get("evaluation", {}).get("overall", 0) >= min_score
                ]
            
            # Sort ideas if specified
            if sort_by:
                if sort_by in ["novelty_score", "utility_score"]:
                    # Sort by direct idea attributes
                    ideas.sort(key=lambda idea: getattr(idea, sort_by), reverse=True)
                elif sort_by in ["novelty", "utility", "feasibility", "relevance", "overall"]:
                    # Sort by evaluation metrics
                    ideas.sort(
                        key=lambda idea: idea.metadata.get("evaluation", {}).get(sort_by, 0),
                        reverse=True
                    )
            
            return ideas
    
    def _determine_idea_count(self, thought: Thought, context: CognitiveContext) -> int:
        """
        Determine the number of ideas to generate.
        
        Args:
            thought: The thought
            context: The cognitive context
            
        Returns:
            Number of ideas to generate
        """
        # Base number of ideas
        base_count = 3
        
        # Adjust based on thought priority
        priority_factor = max(1, int(thought.priority * 5))
        
        # Adjust based on cognitive load (generate fewer ideas when load is high)
        load_factor = max(1, int((1 - context.cognitive_load) * 3))
        
        return min(10, base_count * priority_factor * load_factor // 3)
    
    async def refine_idea(self, idea: Idea, feedback: Dict[str, Any], context: CognitiveContext) -> Idea:
        """
        Refine an idea based on feedback.
        
        Args:
            idea: The idea to refine
            feedback: Feedback information for refinement
            context: The cognitive context
            
        Returns:
            A refined version of the idea
        """
        logger.debug(f"Refining idea {idea.id} based on feedback")
        
        # Store feedback
        async with self.lock:
            if idea.id not in self.idea_feedback:
                self.idea_feedback[idea.id] = []
            
            self.idea_feedback[idea.id].append(feedback)
        
        # Generate refined content based on feedback
        refined_content = await self._apply_feedback_to_idea(idea, feedback, context)
        
        # Create refined idea
        refined_idea = Idea(
            thought_id=idea.thought_id,
            reflection_id=idea.reflection_id,
            content=refined_content,
            novelty_score=idea.novelty_score,
            utility_score=idea.utility_score,
            metadata={
                **idea.metadata,
                "refined_from": idea.id,
                "refinement_feedback": feedback,
                "refinement_timestamp": time.time()
            }
        )
        
        # Store the refined idea
        async with self.lock:
            self.ideas[refined_idea.id] = refined_idea
            
            # Update thought-idea mapping
            if idea.thought_id not in self.thought_ideas:
                self.thought_ideas[idea.thought_id] = []
            
            self.thought_ideas[idea.thought_id].append(refined_idea.id)
            
            # Update idea version history
            if idea.id not in self.idea_versions:
                self.idea_versions[idea.id] = []
            
            self.idea_versions[idea.id].append(refined_idea.id)
        
        # Evaluate the refined idea
        await self.evaluate_idea(refined_idea, context)
        
        return refined_idea
    
    async def get_idea_refinement_history(self, idea_id: str) -> List[Idea]:
        """
        Get the refinement history for an idea.
        
        Args:
            idea_id: The ID of the idea
            
        Returns:
            List of ideas in the refinement chain
        """
        async with self.lock:
            # Check if this is an original idea with refinements
            if idea_id in self.idea_versions:
                refined_ids = self.idea_versions[idea_id]
                refined_ideas = [self.ideas[rid] for rid in refined_ids if rid in self.ideas]
                return refined_ideas
            
            # Check if this is a refined idea
            for original_id, refined_ids in self.idea_versions.items():
                if idea_id in refined_ids:
                    # Get the original idea and all refinements
                    result = []
                    if original_id in self.ideas:
                        result.append(self.ideas[original_id])
                    
                    result.extend([self.ideas[rid] for rid in refined_ids if rid in self.ideas])
                    return result
            
            # No refinement history found
            return []
    
    async def _generate_direct_ideas(self, thought: Thought, reflection: Reflection,
                                    context: CognitiveContext, count: int) -> List[Idea]:
        """
        Generate ideas directly from thought and reflection with enhanced creativity.
        
        Args:
            thought: The thought
            reflection: The reflection
            context: The cognitive context
            count: Number of ideas to generate
            
        Returns:
            List of generated ideas
        """
        ideas = []
        
        # Define idea generation strategies based on thought type
        strategies = {
            "question": [
                "Answer the question directly",
                "Reframe the question from a different perspective",
                "Break the question down into sub-questions",
                "Consider the assumptions behind the question"
            ],
            "hypothesis": [
                "Test the hypothesis with a thought experiment",
                "Consider the opposite of the hypothesis",
                "Extend the hypothesis to a broader domain",
                "Apply the hypothesis to a specific case"
            ],
            "insight": [
                "Generalize the insight to other domains",
                "Apply the insight to solve a specific problem",
                "Identify implications of the insight",
                "Combine the insight with existing knowledge"
            ],
            "general": [
                "Extend the thought in a logical direction",
                "Consider practical applications",
                "Identify underlying principles",
                "Transform the thought into a question or hypothesis"
            ]
        }
        
        # Get strategies for this thought type
        thought_type = thought.type if thought.type in strategies else "general"
        type_strategies = strategies[thought_type]
        
        # Generate ideas using different strategies
        for i in range(count):
            # Select strategy based on index
            strategy = type_strategies[i % len(type_strategies)]
            
            # Generate idea content based on thought type, strategy, and reflection insights
            content = f"Idea based on {thought.type}: {thought.content}\n\n"
            content += f"Strategy: {strategy}\n\n"
            
            # Add reflection insights to the idea
            if reflection.insights:
                # Use more insights for later ideas to increase complexity
                num_insights = min(len(reflection.insights), 1 + i // 2)
                selected_insights = []
                
                for j in range(num_insights):
                    insight_index = (i + j) % len(reflection.insights)
                    selected_insights.append(reflection.insights[insight_index])
                
                content += "Considering insights:\n"
                for insight in selected_insights:
                    content += f"- {insight}\n"
                
                # Add elaboration based on the insights
                if selected_insights:
                    elaboration = self._elaborate_on_insight(selected_insights[0])
                    for j in range(1, len(selected_insights)):
                        elaboration += " " + self._connect_insights(selected_insights[0], selected_insights[j])
                    content += f"\nThis suggests: {elaboration}\n"
            
            # Add patterns from reflection if available
            if "patterns" in reflection.metadata and reflection.metadata["patterns"]:
                patterns = reflection.metadata["patterns"]
                if patterns:
                    # Use multiple patterns for later ideas
                    num_patterns = min(len(patterns), 1 + i // 2)
                    selected_patterns = []
                    
                    for j in range(num_patterns):
                        pattern_index = (i + j) % len(patterns)
                        selected_patterns.append(patterns[pattern_index])
                    
                    if selected_patterns:
                        content += "\nFollowing patterns:\n"
                        for pattern in selected_patterns:
                            content += f"- {pattern}\n"
            
            # Add knowledge store information if available
            if self.knowledge_store and i >= count // 2:  # Use knowledge for later ideas
                try:
                    query = {
                        "content": thought.content,
                        "type": thought.type,
                        "max_results": 1
                    }
                    
                    knowledge_items = await self.knowledge_store.query_knowledge(query)
                    
                    if hasattr(knowledge_items, 'items') and knowledge_items.items:
                        for item in knowledge_items.items[:1]:  # Just use the first item
                            if hasattr(item, 'content') and item.content:
                                content += f"\nIntegrating knowledge: {str(item.content)[:100]}...\n"
                except Exception as e:
                    logger.error(f"Error querying knowledge store: {e}")
            
            # Add specific implementation details based on strategy
            content += f"\nImplementation approach: {self._generate_implementation_approach(strategy, thought, reflection)}\n"
            
            # Calculate initial novelty and utility scores with more sophisticated approach
            base_novelty = 0.5
            base_utility = 0.6
            
            # Adjust based on strategy (some strategies produce more novel ideas)
            if "different perspective" in strategy or "opposite" in strategy:
                base_novelty += 0.15
            elif "specific case" in strategy or "practical applications" in strategy:
                base_utility += 0.15
            
            # Adjust based on number of insights used
            if reflection.insights:
                num_insights = min(len(reflection.insights), 1 + i // 2)
                base_novelty += 0.05 * num_insights
                base_utility += 0.05 * num_insights
            
            # Add randomness
            novelty_score = min(1.0, base_novelty + (random.random() * 0.2))
            utility_score = min(1.0, base_utility + (random.random() * 0.2))
            
            # Create the idea with enhanced metadata
            idea = Idea(
                thought_id=thought.id,
                reflection_id=reflection.id,
                content=content,
                novelty_score=novelty_score,
                utility_score=utility_score,
                metadata={
                    "generation_method": "direct",
                    "generation_strategy": strategy,
                    "generation_index": i,
                    "cognitive_load": context.cognitive_load,
                    "attention_focus": context.attention_focus,
                    "used_insights": [reflection.insights[i % len(reflection.insights)]] if reflection.insights else [],
                    "creation_timestamp": time.time()
                }
            )
            
            ideas.append(idea)
        
        return ideas
    
    def _connect_insights(self, insight1: str, insight2: str) -> str:
        """
        Generate text that connects two insights.
        
        Args:
            insight1: First insight
            insight2: Second insight
            
        Returns:
            Text connecting the insights
        """
        connectors = [
            f"Additionally, when considering that {insight2.lower()}, we can see a connection with the earlier point.",
            f"This relates to {insight2.lower()}, suggesting a broader pattern.",
            f"When combined with the observation that {insight2.lower()}, a more comprehensive picture emerges.",
            f"This insight complements the idea that {insight2.lower()}.",
            f"Looking at both insights together reveals a deeper understanding."
        ]
        
        return random.choice(connectors)
    
    async def _generate_combination_ideas(self, thought: Thought, reflection: Reflection,
                                         context: CognitiveContext, count: int) -> List[Idea]:
        """
        Generate ideas by creatively combining the current thought with other active thoughts.
        
        Args:
            thought: The thought
            reflection: The reflection
            context: The cognitive context
            count: Number of ideas to generate
            
        Returns:
            List of generated ideas
        """
        ideas = []
        
        # Get active thoughts from context
        active_thought_ids = context.active_thoughts
        
        # Skip if there are no other active thoughts
        if not active_thought_ids or len(active_thought_ids) < 2:
            return ideas
        
        # Define combination strategies
        combination_strategies = [
            "Synthesis - merge core concepts from both thoughts",
            "Contrast - explore the tension between opposing elements",
            "Extension - use one thought to extend or elaborate on the other",
            "Application - apply principles from one thought to the context of another",
            "Integration - build a framework that accommodates both thoughts",
            "Transformation - use one thought to transform or reframe the other"
        ]
        
        # Get other thoughts to combine with
        other_thought_ids = [tid for tid in active_thought_ids if tid != thought.id]
        
        # For more complex combinations, try combining with multiple thoughts
        if len(other_thought_ids) >= 3 and count >= 3:
            # Use one slot for a multi-thought combination
            multi_combination = True
            combination_count = min(count - 1, len(other_thought_ids))
        else:
            multi_combination = False
            combination_count = min(count, len(other_thought_ids))
        
        for i in range(combination_count):
            # Select another thought to combine with
            other_id = other_thought_ids[i % len(other_thought_ids)]
            
            # In a real implementation, we would retrieve the other thought
            # For now, we'll create a placeholder
            other_content = f"Content of thought {other_id}"
            other_type = "general"  # In a real implementation, we would get the actual type
            
            # Select a combination strategy based on thought types
            strategy_index = i % len(combination_strategies)
            strategy = combination_strategies[strategy_index]
            
            # Generate combination idea with the selected strategy
            combination = self._create_strategic_combination(thought.content, thought.type,
                                                           other_content, other_type, strategy)
            
            content = f"Combined idea using the '{strategy}' approach:\n\n"
            content += f"Primary thought: {thought.content}\n\n"
            content += f"Secondary thought: {other_content}\n\n"
            content += f"Strategic combination: {combination}\n"
            
            # Add reflection insights if available
            if reflection.insights:
                # Use multiple insights for more complex combinations
                num_insights = min(len(reflection.insights), 1 + i // 2)
                selected_insights = []
                
                for j in range(num_insights):
                    insight_index = (i + j) % len(reflection.insights)
                    selected_insights.append(reflection.insights[insight_index])
                
                if selected_insights:
                    content += "\nRelevant insights:\n"
                    for insight in selected_insights:
                        content += f"- {insight}\n"
                    
                    # Add explanation of how insights inform the combination
                    content += f"\nThese insights suggest that {self._explain_combination_relevance(strategy, selected_insights)}\n"
            
            # Add implementation steps
            content += f"\nImplementation approach:\n"
            implementation_steps = self._generate_combination_implementation(strategy, thought.type, other_type)
            for step_num, step in enumerate(implementation_steps, 1):
                content += f"{step_num}. {step}\n"
            
            # Calculate novelty and utility scores with sophisticated approach
            base_novelty = 0.6
            base_utility = 0.5
            
            # Adjust based on strategy
            if strategy == "Synthesis" or strategy == "Integration":
                base_utility += 0.15
            elif strategy == "Contrast" or strategy == "Transformation":
                base_novelty += 0.15
            
            # Adjust based on thought types (in a real implementation)
            # For now, add some randomness
            type_factor = random.random() * 0.1
            
            # Adjust based on number of insights used
            if reflection.insights:
                num_insights = min(len(reflection.insights), 1 + i // 2)
                insight_factor = 0.05 * num_insights
            else:
                insight_factor = 0
            
            # Calculate final scores
            novelty_score = min(1.0, base_novelty + type_factor + insight_factor + (random.random() * 0.1))
            utility_score = min(1.0, base_utility + type_factor + insight_factor + (random.random() * 0.1))
            
            # Create the idea with enhanced metadata
            idea = Idea(
                thought_id=thought.id,
                reflection_id=reflection.id,
                content=content,
                novelty_score=novelty_score,
                utility_score=utility_score,
                metadata={
                    "generation_method": "combination",
                    "combination_strategy": strategy,
                    "combined_with": other_id,
                    "cognitive_load": context.cognitive_load,
                    "attention_focus": context.attention_focus,
                    "used_insights": [reflection.insights[i % len(reflection.insights)]] if reflection.insights else [],
                    "creation_timestamp": time.time()
                }
            )
            
            # Store combination information
            self.idea_combinations[idea.id] = [(thought.id, other_id)]
            
            ideas.append(idea)
        
        # Add a multi-thought combination if appropriate
        if multi_combination and len(other_thought_ids) >= 3:
            # Select multiple thoughts to combine
            selected_ids = random.sample(other_thought_ids, min(3, len(other_thought_ids)))
            
            # Create placeholder contents
            other_contents = [f"Content of thought {tid}" for tid in selected_ids]
            
            # Generate multi-combination
            content = f"Complex combination of multiple thoughts:\n\n"
            content += f"Primary thought: {thought.content}\n\n"
            
            for i, other_content in enumerate(other_contents, 1):
                content += f"Related thought {i}: {other_content}\n\n"
            
            # Create an integrative framework
            content += "Integrative framework:\n"
            content += self._create_multi_thought_integration(thought.content, other_contents)
            
            # Add a synthesis section
            if reflection.insights and len(reflection.insights) > 0:
                content += f"\n\nSynthesis guided by insight: {reflection.insights[0]}\n"
            
            # Multi-combinations tend to be very novel but more complex
            novelty_score = 0.8 + (random.random() * 0.2)  # 0.8 to 1.0
            utility_score = 0.3 + (random.random() * 0.4)  # 0.3 to 0.7
            
            # Create the multi-combination idea
            idea = Idea(
                thought_id=thought.id,
                reflection_id=reflection.id,
                content=content,
                novelty_score=novelty_score,
                utility_score=utility_score,
                metadata={
                    "generation_method": "multi_combination",
                    "combined_with": selected_ids,
                    "cognitive_load": context.cognitive_load,
                    "attention_focus": context.attention_focus,
                    "creation_timestamp": time.time()
                }
            )
            
            # Store combination information
            self.idea_combinations[idea.id] = [(thought.id, tid) for tid in selected_ids]
            
            ideas.append(idea)
        
        return ideas
    
    async def _generate_analogy_ideas(self, thought: Thought, reflection: Reflection,
                                     context: CognitiveContext, count: int) -> List[Idea]:
        """
        Generate ideas using analogical reasoning.
        
        Args:
            thought: The thought
            reflection: The reflection
            context: The cognitive context
            count: Number of ideas to generate
            
        Returns:
            List of generated ideas
        """
        ideas = []
        
        # Define analogy domains
        analogy_domains = [
            "nature", "technology", "social systems", "art", "science",
            "history", "mathematics", "psychology", "biology", "physics"
        ]
        
        for i in range(count):
            # Select a domain for the analogy
            domain = analogy_domains[i % len(analogy_domains)]
            
            # Generate an analogy
            analogy = self._create_analogy(thought.content, domain)
            
            content = f"Idea by analogy from {domain}:\n\n"
            content += f"Original thought: {thought.content}\n\n"
            content += f"Analogous concept: {analogy['concept']}\n\n"
            content += f"Applied insight: {analogy['insight']}"
            
            # Add reflection insight if available
            if reflection.insights:
                insight = reflection.insights[i % len(reflection.insights)]
                content += f"\n\nEnhanced by insight: {insight}"
            
            # Calculate novelty and utility scores
            # Analogies tend to be very novel but may vary greatly in utility
            novelty_score = 0.8 + (random.random() * 0.2)  # 0.8 to 1.0
            utility_score = 0.3 + (random.random() * 0.6)  # 0.3 to 0.9
            
            # Create the idea
            idea = Idea(
                thought_id=thought.id,
                reflection_id=reflection.id,
                content=content,
                novelty_score=novelty_score,
                utility_score=utility_score,
                metadata={
                    "generation_method": "analogy",
                    "analogy_domain": domain,
                    "analogy_concept": analogy["concept"],
                    "cognitive_load": context.cognitive_load,
                    "attention_focus": context.attention_focus
                }
            )
            
            # Store analogy information
            self.analogies[idea.id] = analogy
            
            ideas.append(idea)
        
        return ideas
    
    def _evaluate_feasibility(self, idea: Idea, context: CognitiveContext) -> float:
        """
        Evaluate the feasibility of an idea.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Feasibility score (0.0 to 1.0)
        """
        # This is a simplified implementation
        # A real implementation would use more sophisticated evaluation
        
        # Base feasibility on utility score
        base_feasibility = idea.utility_score
        
        # Adjust based on cognitive load (higher load might lead to less feasible ideas)
        load_adjustment = -0.1 * context.cognitive_load
        
        return max(0.0, min(1.0, base_feasibility + load_adjustment))
    
    def _evaluate_relevance(self, idea: Idea, context: CognitiveContext) -> float:
        """
        Evaluate the relevance of an idea to the current context.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        # This is a simplified implementation
        # A real implementation would use more sophisticated evaluation
        
        # Base relevance
        base_relevance = 0.7
        
        # If the idea content mentions the current attention focus, increase relevance
        if context.attention_focus and context.attention_focus.lower() in idea.content.lower():
            base_relevance += 0.2
        
        # If the idea is based on an active thought, increase relevance
        if idea.thought_id in context.active_thoughts:
            base_relevance += 0.1
        
        return min(1.0, base_relevance)
    
    def _create_thought_combination(self, content1: str, content2: str) -> str:
        """
        Create a combination of two thought contents.
        
        Args:
            content1: Content of the first thought
            content2: Content of the second thought
            
        Returns:
            Combined content
        """
        # Extract key concepts from both contents
        concepts1 = set(re.findall(r'\b\w{5,}\b', content1.lower()))
        concepts2 = set(re.findall(r'\b\w{5,}\b', content2.lower()))
        
        # Find common concepts
        common_concepts = concepts1.intersection(concepts2)
        
        # Find unique concepts from each
        unique1 = concepts1 - common_concepts
        unique2 = concepts2 - common_concepts
        
        # Create combination
        if common_concepts:
            common_str = ", ".join(list(common_concepts)[:3])
            combination = f"Building on the shared concepts of {common_str}, "
        else:
            combination = "By connecting different domains, "
        
        if unique1 and unique2:
            unique1_str = ", ".join(list(unique1)[:2])
            unique2_str = ", ".join(list(unique2)[:2])
            combination += f"we can integrate {unique1_str} from the first thought with {unique2_str} from the second thought."
            combination += f" This suggests a new approach that combines both perspectives."
        else:
            # Fallback if we couldn't extract good concepts
            combination += f"we can synthesize elements from both thoughts to create a novel solution."
        
        return combination
    
    def _create_analogy(self, content: str, domain: str) -> Dict[str, str]:
        """
        Create a sophisticated analogy between the thought content and a concept from another domain.
        
        Args:
            content: The thought content
            domain: The analogy domain
            
        Returns:
            Dictionary with analogy information
        """
        # Extract key concepts from content
        content_concepts = set(re.findall(r'\b\w{5,}\b', content.lower()))
        key_concepts = list(content_concepts)[:5] if content_concepts else ["concept"]
        
        # Define domain-specific analogies (simplified - in a real system, this would be more sophisticated)
        domain_analogies = {
            "nature": [
                {"concept": "ecosystem balance", "pattern": "interdependent components that maintain equilibrium",
                 "principles": ["interconnectedness", "feedback regulation", "resource allocation"]},
                {"concept": "evolution", "pattern": "gradual adaptation and improvement over time",
                 "principles": ["selection pressure", "variation", "adaptation", "inheritance"]},
                {"concept": "symbiosis", "pattern": "mutually beneficial relationship between different entities",
                 "principles": ["mutual benefit", "specialization", "dependency", "co-evolution"]}
            ],
            "technology": [
                {"concept": "modular design", "pattern": "separating components for flexibility and maintainability",
                 "principles": ["encapsulation", "interfaces", "reusability", "separation of concerns"]},
                {"concept": "distributed systems", "pattern": "dividing responsibilities across multiple nodes",
                 "principles": ["fault tolerance", "scalability", "redundancy", "asynchronous communication"]},
                {"concept": "feedback loops", "pattern": "using output to refine and improve input",
                 "principles": ["iteration", "continuous improvement", "monitoring", "adjustment"]}
            ],
            "social systems": [
                {"concept": "community governance", "pattern": "collective decision-making processes",
                 "principles": ["representation", "consensus building", "accountability", "shared responsibility"]},
                {"concept": "social norms", "pattern": "implicit rules that guide behavior",
                 "principles": ["cultural transmission", "conformity pressure", "social sanctions", "identity formation"]},
                {"concept": "institutional memory", "pattern": "preserving knowledge across generations",
                 "principles": ["documentation", "mentorship", "cultural artifacts", "knowledge transfer"]}
            ],
            "art": [
                {"concept": "negative space", "pattern": "focusing on what's absent to highlight what's present",
                 "principles": ["contrast", "implied meaning", "context definition", "perceptual balance"]},
                {"concept": "perspective", "pattern": "viewing the same situation from different angles",
                 "principles": ["frame of reference", "subjective interpretation", "contextual understanding", "empathy"]},
                {"concept": "juxtaposition", "pattern": "placing contrasting elements side by side",
                 "principles": ["tension", "dialectic", "emergent meaning", "recontextualization"]}
            ],
            "science": [
                {"concept": "experimental method", "pattern": "systematic testing of hypotheses",
                 "principles": ["falsifiability", "controlled variables", "replicability", "empirical evidence"]},
                {"concept": "paradigm shifts", "pattern": "fundamental changes in basic assumptions",
                 "principles": ["conceptual revolution", "anomaly recognition", "theoretical crisis", "reframing"]},
                {"concept": "emergent properties", "pattern": "complex behaviors arising from simple rules",
                 "principles": ["complexity", "self-organization", "non-linearity", "hierarchy"]}
            ],
            "history": [
                {"concept": "cyclical patterns", "pattern": "recurring themes and situations over time",
                 "principles": ["pattern recognition", "historical parallels", "causal factors", "predictive modeling"]},
                {"concept": "watershed moments", "pattern": "critical events that change trajectories",
                 "principles": ["tipping points", "cascading effects", "path dependency", "historical contingency"]},
                {"concept": "revisionism", "pattern": "reinterpreting past events with new information",
                 "principles": ["perspective shift", "evidence reanalysis", "narrative construction", "historiography"]}
            ],
            "mathematics": [
                {"concept": "recursion", "pattern": "defining something in terms of itself",
                 "principles": ["self-reference", "base cases", "inductive reasoning", "nested structures"]},
                {"concept": "transformation", "pattern": "applying operations to change form while preserving essence",
                 "principles": ["invariants", "mapping", "isomorphism", "structural preservation"]},
                {"concept": "optimization", "pattern": "finding the best solution within constraints",
                 "principles": ["objective function", "constraint satisfaction", "search space", "local vs. global optima"]}
            ],
            "psychology": [
                {"concept": "cognitive bias", "pattern": "systematic patterns of deviation from norm or rationality",
                 "principles": ["heuristic thinking", "perceptual filtering", "mental shortcuts", "belief preservation"]},
                {"concept": "schema", "pattern": "mental framework that organizes and interprets information",
                 "principles": ["categorization", "expectation setting", "information filtering", "memory organization"]},
                {"concept": "flow state", "pattern": "optimal state of engagement and productivity",
                 "principles": ["skill-challenge balance", "focused attention", "immediate feedback", "intrinsic motivation"]}
            ],
            "biology": [
                {"concept": "homeostasis", "pattern": "maintaining internal stability despite external changes",
                 "principles": ["negative feedback", "set points", "regulatory mechanisms", "dynamic equilibrium"]},
                {"concept": "specialization", "pattern": "adaptation for specific functions or environments",
                 "principles": ["trade-offs", "niche optimization", "functional efficiency", "complementary roles"]},
                {"concept": "cell signaling", "pattern": "communication mechanisms between components",
                 "principles": ["signal transduction", "amplification", "specificity", "response coordination"]}
            ],
            "physics": [
                {"concept": "entropy", "pattern": "tendency toward disorder and equilibrium",
                 "principles": ["irreversibility", "information loss", "statistical probability", "energy dispersal"]},
                {"concept": "wave-particle duality", "pattern": "exhibiting characteristics of both forms",
                 "principles": ["complementarity", "measurement effects", "contextual behavior", "fundamental uncertainty"]},
                {"concept": "conservation laws", "pattern": "fundamental quantities that remain unchanged",
                 "principles": ["invariance", "symmetry", "closed systems", "balance equations"]}
            ]
        }
        
        # Try to find the most relevant analogy for the content
        best_analogy = None
        best_relevance = -1
        
        # Get analogies for the selected domain
        analogies = domain_analogies.get(domain, domain_analogies["nature"])
        
        for analogy in analogies:
            # Calculate relevance based on principle overlap with content concepts
            principles = set(analogy["principles"])
            overlap = sum(1 for concept in key_concepts if any(p in concept for p in principles))
            relevance = overlap / max(1, len(key_concepts))
            
            if relevance > best_relevance:
                best_relevance = relevance
                best_analogy = analogy
        
        # If no good match, just pick a random one
        if best_analogy is None or best_relevance == 0:
            best_analogy = random.choice(analogies)
        
        # Create detailed insight based on the analogy
        concept = best_analogy["concept"]
        pattern = best_analogy["pattern"]
        principles = best_analogy["principles"]
        
        # Create primary insight
        insight = f"Like {concept} in {domain}, this thought exhibits {pattern}. "
        
        # Add principle mapping
        principle_count = min(3, len(principles))
        selected_principles = principles[:principle_count]
        
        insight += f"We can apply {principle_count} key principles from this analogy:\n\n"
        
        for i, principle in enumerate(selected_principles, 1):
            # Try to map principle to a content concept
            mapped_concept = None
            for concept in key_concepts:
                if principle in concept or any(len(set(principle).intersection(set(c))) > 3 for c in key_concepts):
                    mapped_concept = concept
                    break
            
            if mapped_concept:
                insight += f"{i}. {principle.capitalize()}: Just as {principle} works in {best_analogy['concept']}, "
                insight += f"we can apply this to {mapped_concept} in our context by {self._generate_principle_application(principle)}.\n"
            else:
                insight += f"{i}. {principle.capitalize()}: This principle from {best_analogy['concept']} "
                insight += f"can be applied to our context by {self._generate_principle_application(principle)}.\n"
        
        # Add implementation guidance
        insight += f"\nTo implement this analogy effectively, we should {self._generate_analogy_implementation(domain, concept)}."
        
        return {
            "domain": domain,
            "concept": best_analogy["concept"],
            "pattern": best_analogy["pattern"],
            "principles": best_analogy["principles"],
            "insight": insight
        }
    
    def _generate_principle_application(self, principle: str) -> str:
        """
        Generate a specific application of an analogical principle.
        
        Args:
            principle: The principle to apply
            
        Returns:
            Application text
        """
        applications = {
            "interconnectedness": [
                "mapping dependencies between components to ensure changes propagate appropriately",
                "establishing clear communication channels between all system elements",
                "designing interfaces that acknowledge relationships between parts"
            ],
            "feedback": [
                "creating mechanisms to monitor outcomes and adjust processes accordingly",
                "implementing review cycles that inform future iterations",
                "establishing metrics that provide continuous performance data"
            ],
            "adaptation": [
                "building flexibility into the system to respond to changing conditions",
                "incorporating learning mechanisms that evolve with experience",
                "designing components that can be reconfigured as needs change"
            ],
            "modularity": [
                "dividing the system into independent, interchangeable components",
                "establishing clear boundaries and interfaces between elements",
                "enabling components to be developed, tested, and maintained separately"
            ],
            "specialization": [
                "optimizing components for their specific functions rather than general purposes",
                "allocating resources based on the unique requirements of each element",
                "developing expertise in particular domains rather than general knowledge"
            ],
            "redundancy": [
                "building backup systems for critical components",
                "distributing functionality to prevent single points of failure",
                "implementing alternative pathways to achieve key objectives"
            ]
        }
        
        # Find the most relevant application category
        best_category = "adaptation"  # Default
        best_similarity = 0
        
        for category in applications:
            # Simple string similarity
            similarity = sum(1 for c in category if c in principle) / max(len(category), len(principle))
            if similarity > best_similarity:
                best_similarity = similarity
                best_category = category
        
        # Get applications for the best category
        category_applications = applications.get(best_category, applications["adaptation"])
        
        return random.choice(category_applications)
    
    def _generate_analogy_implementation(self, domain: str, concept: str) -> str:
        """
        Generate implementation guidance for an analogy.
        
        Args:
            domain: The analogy domain
            concept: The analogical concept
            
        Returns:
            Implementation guidance
        """
        implementations = [
            f"first create a mapping between elements of {concept} and components of our system, then systematically apply the principles",
            f"identify the core mechanisms that make {concept} effective in {domain}, then translate those to our context with appropriate modifications",
            f"analyze how {concept} handles complexity and scale in {domain}, then apply similar structural patterns to our design",
            f"extract the essential relationships from {concept} in {domain}, then implement analogous relationships in our system",
            f"develop a step-by-step translation guide that moves from {domain} terminology to our domain while preserving the underlying principles"
        ]
        
        return random.choice(implementations)
    
    def _elaborate_on_insight(self, insight: str) -> str:
        """
        Elaborate on a reflection insight to generate idea content.
        
        Args:
            insight: The insight to elaborate on
            
        Returns:
            Elaborated content
        """
        # Extract key terms from the insight
        key_terms = re.findall(r'\b\w{5,}\b', insight.lower())
        
        if not key_terms:
            return "This insight suggests a new perspective on the problem that could lead to innovative solutions."
        
        # Select a random elaboration pattern
        elaboration_patterns = [
            "Expanding on this insight, we could develop a framework that addresses {term1} while considering {term2}.",
            "This suggests a novel approach where {term1} becomes the central focus, with {term2} as a supporting element.",
            "By reframing the problem around {term1}, we might discover solutions that leverage {term2} in unexpected ways.",
            "Considering {term1} from the perspective of {term2} opens up new possibilities for innovation.",
            "This insight points to an opportunity to bridge {term1} and {term2} in a way that hasn't been explored before."
        ]
        
        pattern = random.choice(elaboration_patterns)
        
        # Fill in the pattern with terms from the insight
        term1 = random.choice(key_terms) if key_terms else "this concept"
        term2 = random.choice([t for t in key_terms if t != term1]) if len(key_terms) > 1 else "related factors"
        
        return pattern.format(term1=term1, term2=term2)
    
    async def _apply_feedback_to_idea(self, idea: Idea, feedback: Dict[str, Any], context: CognitiveContext) -> str:
        """
        Apply feedback to refine an idea.
        
        Args:
            idea: The idea to refine
            feedback: Feedback information for refinement
            context: The cognitive context
            
        Returns:
            Refined idea content
        """
        content = idea.content
        
        # Extract feedback components
        feedback_text = feedback.get("text", "")
        feedback_type = feedback.get("type", "general")
        feedback_aspects = feedback.get("aspects", {})
        
        # Create refined content
        refined_content = [f"Refined idea (based on {feedback_type} feedback):", ""]
        refined_content.append(f"Original idea: {content}")
        refined_content.append("")
        refined_content.append("Refinements:")
        
        # Apply different refinement strategies based on feedback type
        if feedback_type == "critique":
            # Address critique points
            if "weaknesses" in feedback_aspects:
                for weakness in feedback_aspects["weaknesses"]:
                    refined_content.append(f"- Addressing {weakness}: {self._generate_improvement(weakness)}")
            
            # Preserve strengths
            if "strengths" in feedback_aspects:
                refined_content.append("")
                refined_content.append("Preserving strengths:")
                for strength in feedback_aspects["strengths"]:
                    refined_content.append(f"- Maintaining {strength}")
        
        elif feedback_type == "extension":
            # Extend the idea
            refined_content.append(f"- Extending the idea: {feedback_text}")
            
            # Add additional extensions based on context
            if context.attention_focus:
                refined_content.append(f"- Further considering {context.attention_focus}: {self._generate_extension(context.attention_focus)}")
        
        elif feedback_type == "simplification":
            # Simplify the idea
            refined_content.append("- Simplified version:")
            refined_content.append(f"  {self._simplify_content(content)}")
        
        else:  # general feedback
            refined_content.append(f"- General improvement: {feedback_text}")
            refined_content.append(f"- Additional refinement: {self._generate_general_refinement()}")
        
        # Add synthesis
        refined_content.append("")
        refined_content.append("Synthesis:")
        refined_content.append(f"This refined idea {self._generate_synthesis(feedback_type)}.")
        
        return "\n".join(refined_content)
    
    def _generate_improvement(self, weakness: str) -> str:
        """
        Generate an improvement to address a weakness.
        
        Args:
            weakness: The weakness to address
            
        Returns:
            Improvement text
        """
        improvement_templates = [
            "Restructuring the approach to mitigate {weakness} by incorporating more robust validation",
            "Addressing {weakness} by introducing a complementary mechanism that provides balance",
            "Reducing the impact of {weakness} by adding a fallback strategy that activates when needed",
            "Transforming {weakness} into a potential strength by reframing the context and expectations",
            "Minimizing {weakness} through incremental refinement and continuous feedback loops"
        ]
        
        template = random.choice(improvement_templates)
        return template.format(weakness=weakness)
    
    def _generate_extension(self, focus: str) -> str:
        """
        Generate an extension based on a focus area.
        
        Args:
            focus: The focus area
            
        Returns:
            Extension text
        """
        extension_templates = [
            "Expanding the scope to include additional aspects of {focus} that weren't initially considered",
            "Integrating {focus} more deeply into the core functionality to enhance overall coherence",
            "Creating a specialized module dedicated to optimizing {focus}-related operations",
            "Developing a layered approach where {focus} serves as a foundation for higher-level functions",
            "Establishing connections between {focus} and adjacent domains to leverage synergies"
        ]
        
        template = random.choice(extension_templates)
        return template.format(focus=focus)
    
    def _simplify_content(self, content: str) -> str:
        """
        Simplify content by extracting and summarizing key points.
        
        Args:
            content: The content to simplify
            
        Returns:
            Simplified content
        """
        # Extract sentences
        sentences = re.split(r'[.!?]\s+', content)
        
        # If very short already, return as is
        if len(sentences) <= 3:
            return content
        
        # Select key sentences (first, middle, last)
        key_sentences = [
            sentences[0],
            sentences[len(sentences) // 2],
            sentences[-1]
        ]
        
        # Join with appropriate punctuation
        return ". ".join(key_sentences) + "."
    
    def _generate_general_refinement(self) -> str:
        """
        Generate a general refinement suggestion.
        
        Returns:
            Refinement text
        """
        refinements = [
            "Enhancing clarity by restructuring the presentation of key concepts",
            "Improving coherence by establishing stronger logical connections between components",
            "Increasing practical applicability by providing more concrete implementation details",
            "Strengthening theoretical foundation by connecting to established frameworks",
            "Balancing innovation and feasibility by incorporating incremental adoption paths"
        ]
        
        return random.choice(refinements)
    
    def _generate_synthesis(self, feedback_type: str) -> str:
        """
        Generate a synthesis statement based on feedback type.
        
        Args:
            feedback_type: The type of feedback
            
        Returns:
            Synthesis text
        """
        synthesis_templates = {
            "critique": [
                "addresses the identified weaknesses while preserving core strengths",
                "transforms limitations into opportunities for differentiation",
                "resolves critical issues while maintaining the original vision"
            ],
            "extension": [
                "builds upon the original foundation to create a more comprehensive solution",
                "expands the scope to encompass a broader range of scenarios and use cases",
                "develops the initial concept into a more robust and versatile framework"
            ],
            "simplification": [
                "distills the essence of the original idea into a more focused and accessible form",
                "reduces complexity without sacrificing essential functionality",
                "clarifies the core value proposition by removing extraneous elements"
            ],
            "general": [
                "enhances the original concept while maintaining its distinctive character",
                "evolves the idea to better align with practical implementation considerations",
                "refines the approach to increase both effectiveness and efficiency"
            ]
        }
        
        templates = synthesis_templates.get(feedback_type, synthesis_templates["general"])
        return random.choice(templates)
    
    def _evaluate_adaptability(self, idea: Idea, context: CognitiveContext) -> float:
        """
        Evaluate how adaptable an idea is to different contexts.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Adaptability score (0.0 to 1.0)
        """
        # Base adaptability
        base_adaptability = 0.5
        
        # Ideas with broader concepts tend to be more adaptable
        content_words = set(re.findall(r'\b\w{5,}\b', idea.content.lower()))
        general_concepts = {"system", "framework", "approach", "method", "process", "structure", "pattern"}
        concept_overlap = len(content_words.intersection(general_concepts))
        
        if concept_overlap > 0:
            base_adaptability += 0.1 * min(3, concept_overlap)
        
        # Analogies tend to be more adaptable
        if idea.metadata.get("generation_method") == "analogy":
            base_adaptability += 0.2
        
        # Ideas that mention flexibility or adaptability concepts
        adaptability_terms = {"flexible", "adaptable", "modular", "extensible", "configurable", "customizable"}
        if any(term in content_words for term in adaptability_terms):
            base_adaptability += 0.15
        
        return min(1.0, base_adaptability)
    
    def _evaluate_complexity(self, idea: Idea) -> float:
        """
        Evaluate the complexity of an idea.
        
        Args:
            idea: The idea to evaluate
            
        Returns:
            Complexity score (0.0 to 1.0, where higher means more complex)
        """
        # Base complexity based on content length
        content_length = len(idea.content)
        base_complexity = min(1.0, content_length / 1000)  # Normalize to [0, 1]
        
        # Adjust based on sentence structure
        sentences = re.split(r'[.!?]\s+', idea.content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        sentence_complexity = min(1.0, avg_sentence_length / 25)  # Normalize to [0, 1]
        
        # Adjust based on vocabulary complexity
        complex_words = re.findall(r'\b\w{8,}\b', idea.content.lower())
        vocabulary_complexity = min(1.0, len(complex_words) / 20)  # Normalize to [0, 1]
        
        # Calculate weighted complexity
        complexity = (0.4 * base_complexity +
                      0.3 * sentence_complexity +
                      0.3 * vocabulary_complexity)
        
        return complexity
    
    async def _evaluate_novelty(self, idea: Idea, context: CognitiveContext) -> float:
        """
        Evaluate the novelty of an idea using multiple dimensions and contextual factors.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Novelty score (0.0 to 1.0)
        """
        # Initialize novelty components
        content_novelty = 0.0
        structural_novelty = 0.0
        contextual_novelty = 0.0
        conceptual_novelty = 0.0
        
        # 1. Content Novelty: Based on similarity to existing ideas
        similar_ideas_count = 0
        similarity_scores = []
        
        if idea.thought_id in self.thought_ideas:
            other_idea_ids = self.thought_ideas[idea.thought_id]
            for other_id in other_idea_ids:
                if other_id != idea.id and other_id in self.ideas:
                    other_idea = self.ideas[other_id]
                    similarity = self._calculate_content_similarity(idea.content, other_idea.content)
                    similarity_scores.append(similarity)
                    if similarity > 0.6:
                        similar_ideas_count += 1
        
        # Calculate content novelty based on similarity scores
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            content_novelty = 1.0 - avg_similarity
        else:
            content_novelty = 0.9  # Assume high novelty if no other ideas to compare
        
        # 2. Structural Novelty: Based on generation method and idea structure
        generation_method = idea.metadata.get("generation_method", "direct")
        
        if generation_method == "analogy":
            # Analogies tend to be structurally novel
            structural_novelty = 0.8 + (random.random() * 0.2)  # 0.8 to 1.0
            
            # Consider the domain of the analogy
            if "analogy_domain" in idea.metadata:
                domain = idea.metadata["analogy_domain"]
                # More unusual domains lead to higher novelty
                unusual_domains = ["mathematics", "physics", "art"]
                if domain in unusual_domains:
                    structural_novelty = min(1.0, structural_novelty + 0.1)
        
        elif generation_method == "combination":
            # Combinations have moderate structural novelty
            structural_novelty = 0.6 + (random.random() * 0.3)  # 0.6 to 0.9
            
            # Multi-combinations are more novel
            if generation_method == "multi_combination":
                structural_novelty = min(1.0, structural_novelty + 0.15)
        
        elif generation_method == "direct":
            # Direct ideas have lower structural novelty
            structural_novelty = 0.4 + (random.random() * 0.3)  # 0.4 to 0.7
            
            # Check if using a creative strategy
            if "generation_strategy" in idea.metadata:
                strategy = idea.metadata["generation_strategy"]
                if "different perspective" in strategy or "reframe" in strategy:
                    structural_novelty = min(1.0, structural_novelty + 0.2)
        
        # 3. Contextual Novelty: Based on current cognitive context
        # Ideas that diverge from current attention focus are more novel
        if context.attention_focus and context.attention_focus.lower() not in idea.content.lower():
            contextual_novelty = 0.7 + (random.random() * 0.3)  # 0.7 to 1.0
        else:
            contextual_novelty = 0.4 + (random.random() * 0.3)  # 0.4 to 0.7
        
        # 4. Conceptual Novelty: Based on knowledge store and concept rarity
        conceptual_novelty = 0.5  # Default
        
        # Extract key concepts from idea
        key_concepts = set(re.findall(r'\b\w{5,}\b', idea.content.lower()))
        
        # Check concept rarity
        rare_concepts = {"paradigm", "emergence", "recursion", "duality", "entropy", "isomorphism"}
        common_concepts = {"system", "process", "approach", "method", "solution", "problem"}
        
        rare_count = len(key_concepts.intersection(rare_concepts))
        common_count = len(key_concepts.intersection(common_concepts))
        
        # Adjust conceptual novelty based on concept rarity
        if rare_count > 0:
            conceptual_novelty = min(1.0, conceptual_novelty + (0.1 * rare_count))
        if common_count > 0:
            conceptual_novelty = max(0.1, conceptual_novelty - (0.05 * common_count))
        
        # If knowledge store is available, check for similar knowledge
        if self.knowledge_store:
            try:
                query = {
                    "content": idea.content,
                    "max_results": 5,
                    "threshold": 0.6  # Only return items with similarity above this threshold
                }
                
                knowledge_items = await self.knowledge_store.query_knowledge(query)
                
                # Calculate knowledge-based novelty
                if hasattr(knowledge_items, 'items'):
                    if len(knowledge_items.items) == 0:
                        # No similar knowledge found, very novel
                        conceptual_novelty = min(1.0, conceptual_novelty + 0.3)
                    elif len(knowledge_items.items) > 3:
                        # Many similar items, less novel
                        conceptual_novelty = max(0.1, conceptual_novelty - 0.2)
                    else:
                        # Some similar items, moderately novel
                        conceptual_novelty = max(0.2, conceptual_novelty - 0.1)
            except Exception as e:
                logger.error(f"Error querying knowledge store for novelty evaluation: {e}")
        
        # Calculate weighted overall novelty
        novelty = (
            0.35 * content_novelty +
            0.25 * structural_novelty +
            0.20 * contextual_novelty +
            0.20 * conceptual_novelty
        )
        
        # Log detailed novelty components for debugging
        logger.debug(f"Novelty evaluation for idea {idea.id}: " +
                    f"Content: {content_novelty:.2f}, " +
                    f"Structural: {structural_novelty:.2f}, " +
                    f"Contextual: {contextual_novelty:.2f}, " +
                    f"Conceptual: {conceptual_novelty:.2f}, " +
                    f"Overall: {novelty:.2f}")
        
        return novelty
    
    async def _evaluate_utility(self, idea: Idea, context: CognitiveContext) -> float:
        """
        Evaluate the utility of an idea using multiple dimensions including practical applicability,
        problem-solving potential, and alignment with goals.
        
        Args:
            idea: The idea to evaluate
            context: The cognitive context
            
        Returns:
            Utility score (0.0 to 1.0)
        """
        # Initialize utility components
        practical_applicability = 0.0
        problem_solving_potential = 0.0
        goal_alignment = 0.0
        implementation_feasibility = 0.0
        
        # Extract content features
        content_words = set(re.findall(r'\b\w+\b', idea.content.lower()))
        content_lower = idea.content.lower()
        
        # 1. Practical Applicability: Can this idea be put into practice?
        
        # Check for actionability
        action_verbs = {"implement", "create", "develop", "build", "establish", "design", "construct",
                       "apply", "use", "deploy", "execute", "perform", "operate"}
        action_verb_count = sum(1 for verb in action_verbs if verb in content_words)
        
        # Check for implementation details
        implementation_indicators = ["step", "process", "method", "approach", "technique", "procedure",
                                   "algorithm", "framework", "system", "tool"]
        implementation_indicator_count = sum(1 for indicator in implementation_indicators
                                           if indicator in content_words)
        
        # Calculate practical applicability score
        practical_applicability = 0.4 + (0.05 * min(action_verb_count, 3)) + (0.05 * min(implementation_indicator_count, 4))
        
        # Adjust based on specificity
        specificity_indicators = {"specifically", "exactly", "precisely", "in particular", "concrete",
                                 "detailed", "explicit", "clear", "definite"}
        if any(indicator in content_lower for indicator in specificity_indicators):
            practical_applicability = min(1.0, practical_applicability + 0.1)
        
        # 2. Problem-Solving Potential: Does this idea address a problem or need?
        
        # Check for problem-solution framing
        problem_indicators = {"problem", "challenge", "issue", "difficulty", "obstacle", "limitation",
                             "constraint", "gap", "need", "requirement"}
        solution_indicators = {"solution", "resolve", "address", "solve", "overcome", "mitigate",
                              "improve", "enhance", "optimize"}
        
        has_problem_framing = any(indicator in content_words for indicator in problem_indicators)
        has_solution_framing = any(indicator in content_words for indicator in solution_indicators)
        
        # Calculate problem-solving score
        if has_problem_framing and has_solution_framing:
            problem_solving_potential = 0.8  # Explicitly addresses a problem with a solution
        elif has_solution_framing:
            problem_solving_potential = 0.6  # Offers a solution without explicitly stating the problem
        elif has_problem_framing:
            problem_solving_potential = 0.4  # Identifies a problem without explicitly offering a solution
        else:
            problem_solving_potential = 0.3  # Neither explicitly mentions problems nor solutions
        
        # 3. Goal Alignment: How well does this align with current focus?
        
        # Check alignment with attention focus
        if context.attention_focus:
            if context.attention_focus.lower() in content_lower:
                # Direct mention of the attention focus
                goal_alignment = 0.9
            else:
                # Check for semantic similarity using key terms
                attention_terms = set(re.findall(r'\b\w{4,}\b', context.attention_focus.lower()))
                if attention_terms:
                    overlap = len(content_words.intersection(attention_terms)) / len(attention_terms)
                    goal_alignment = 0.5 + (0.4 * overlap)
                else:
                    goal_alignment = 0.5  # Default if no meaningful terms in attention focus
        else:
            goal_alignment = 0.5  # Default if no attention focus
        
        # 4. Implementation Feasibility: How feasible is this idea to implement?
        
        # Base feasibility on complexity and resource requirements
        complexity_indicators = {"complex", "complicated", "intricate", "sophisticated", "advanced"}
        resource_indicators = {"expensive", "costly", "resource-intensive", "time-consuming", "difficult"}
        
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in content_words)
        resource_count = sum(1 for indicator in resource_indicators if indicator in content_words)
        
        # Higher score means more feasible (less complex/resource-intensive)
        implementation_feasibility = 0.7 - (0.1 * complexity_count) - (0.1 * resource_count)
        implementation_feasibility = max(0.2, min(0.9, implementation_feasibility))
        
        # Adjust based on idea generation method
        generation_method = idea.metadata.get("generation_method", "direct")
        
        if generation_method == "direct":
            implementation_feasibility = min(1.0, implementation_feasibility + 0.1)  # Direct ideas tend to be more feasible
        elif generation_method == "analogy":
            implementation_feasibility = max(0.1, implementation_feasibility - 0.1)  # Analogies might be less feasible
        
        # If the idea is a refinement, it tends to be more feasible
        if idea.metadata.get("refined_from"):
            implementation_feasibility = min(1.0, implementation_feasibility + 0.15)
        
        # Calculate weighted overall utility score
        utility = (
            0.35 * practical_applicability +
            0.30 * problem_solving_potential +
            0.20 * goal_alignment +
            0.15 * implementation_feasibility
        )
        
        # Log detailed utility components for debugging
        logger.debug(f"Utility evaluation for idea {idea.id}: " +
                    f"Practical: {practical_applicability:.2f}, " +
                    f"Problem-solving: {problem_solving_potential:.2f}, " +
                    f"Goal alignment: {goal_alignment:.2f}, " +
                    f"Feasibility: {implementation_feasibility:.2f}, " +
                    f"Overall: {utility:.2f}")
        
        return utility
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Extract words from both contents
        words1 = set(re.findall(r'\b\w{4,}\b', content1.lower()))
        words2 = set(re.findall(r'\b\w{4,}\b', content2.lower()))
        
        # Calculate Jaccard similarity
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union