"""
Reflection Engine Implementation for GodelOS

This module implements the ReflectionEngine class, which is responsible for
reflecting on thoughts in the cognitive system to generate insights and determine
if further ideation is needed. The enhanced implementation includes multi-level
reflection, contradiction detection, pattern-based insight generation, and
knowledge store integration.
"""

import logging
import time
import re
from typing import Dict, List, Optional, Any, Set, Tuple
import asyncio
from collections import defaultdict
import uuid

from godelOS.unified_agent_core.cognitive_engine.interfaces import (
    Thought, Reflection, CognitiveContext, ReflectionEngineInterface
)

logger = logging.getLogger(__name__)


class ReflectionEngine(ReflectionEngineInterface):
    """
    Enhanced ReflectionEngine implementation for GodelOS.
    
    The ReflectionEngine is responsible for reflecting on thoughts in the cognitive
    system to generate insights and determine if further ideation is needed.
    
    Features:
    1. Multi-level reflection (meta-reflection)
    2. Contradiction detection between thoughts
    3. Insight generation from thought patterns
    4. Integration with the knowledge store for context-aware reflection
    """
    
    def __init__(self):
        """Initialize the reflection engine."""
        self.reflections: Dict[str, Reflection] = {}
        self.thought_reflections: Dict[str, List[str]] = {}  # thought_id -> list of reflection_ids
        self.meta_reflections: Dict[str, List[str]] = {}  # reflection_id -> list of meta_reflection_ids
        self.lock = asyncio.Lock()
        
        # For contradiction detection
        self.contradictions: Dict[str, List[Tuple[str, str]]] = {}  # thought_id -> list of (contradicting_thought_id, reason)
        
        # For pattern recognition
        self.thought_patterns: Dict[str, List[str]] = {}  # pattern_name -> list of thought_ids
        
        # Knowledge store reference (will be set by the cognitive engine)
        self.knowledge_store = None
    
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The knowledge store
        """
        self.knowledge_store = knowledge_store
    
    async def reflect(self, thought: Thought, context: CognitiveContext,
                      previous_reflections: Optional[List[Reflection]] = None,
                      reflection_level: int = 1) -> Reflection:
        """
        Reflect on a thought with enhanced multi-level capabilities.
        
        Args:
            thought: The thought to reflect on
            context: The cognitive context
            previous_reflections: Optional list of previous reflections for meta-reflection
            reflection_level: The level of reflection (1 for base reflection, >1 for meta-reflection)
            
        Returns:
            A reflection on the thought
        """
        logger.debug(f"Reflecting on thought {thought.id} at level {reflection_level}")
        
        # Detect contradictions with other thoughts
        contradictions = await self._detect_contradictions(thought, context)
        
        # Identify thought patterns
        patterns = await self._identify_patterns(thought, context)
        
        # Generate insights with appropriate depth based on reflection level
        insights = await self._generate_insights(thought, context, contradictions, patterns, reflection_level)
        
        # For deeper reflections, analyze relationships between insights
        if reflection_level > 1 and previous_reflections:
            meta_insights = await self._generate_meta_insights(thought, previous_reflections, context)
            insights.extend(meta_insights)
        
        # Enrich with knowledge store information if available
        if self.knowledge_store:
            knowledge_insights = await self._generate_knowledge_based_insights(thought, context, reflection_level)
            insights.extend(knowledge_insights)
        
        # Determine if ideation should be performed
        should_ideate = await self._should_ideate(thought, context, contradictions, reflection_level)
        
        # Create reflection content with appropriate depth
        content = self._generate_reflection_content(thought, insights, contradictions, patterns, reflection_level)
        
        # Create a new reflection with enhanced metadata
        reflection = Reflection(
            thought_id=thought.id,
            content=content,
            insights=insights,
            should_ideate=should_ideate,
            metadata={
                "contradictions": contradictions,
                "patterns": patterns,
                "reflection_level": reflection_level,
                "cognitive_load": context.cognitive_load,
                "attention_focus": context.attention_focus,
                "previous_reflection_ids": [r.id for r in (previous_reflections or [])],
                "timestamp": time.time(),
                "insight_count": len(insights)
            }
        )
        
        # Store the reflection
        async with self.lock:
            self.reflections[reflection.id] = reflection
            
            # Update thought-reflection mapping
            if thought.id not in self.thought_reflections:
                self.thought_reflections[thought.id] = []
            
            self.thought_reflections[thought.id].append(reflection.id)
        
        # If this is a base reflection and automatic meta-reflection is enabled,
        # perform meta-reflection on existing reflections for this thought
        if reflection_level == 1 and len(self.thought_reflections.get(thought.id, [])) > 1:
            # Get all previous reflections for this thought
            previous_thought_reflections = []
            async with self.lock:
                for ref_id in self.thought_reflections[thought.id]:
                    if ref_id != reflection.id:  # Exclude the current reflection
                        prev_ref = self.reflections.get(ref_id)
                        if prev_ref:
                            previous_thought_reflections.append(prev_ref)
            
            # If we have enough previous reflections, perform meta-reflection
            if len(previous_thought_reflections) >= 2:
                meta_reflection = await self.reflect(
                    thought=thought,
                    context=context,
                    previous_reflections=previous_thought_reflections + [reflection],
                    reflection_level=2
                )
                
                # Store meta-reflection relationship
                async with self.lock:
                    if reflection.id not in self.meta_reflections:
                        self.meta_reflections[reflection.id] = []
                    
                    self.meta_reflections[reflection.id].append(meta_reflection.id)
                    
                    # Also link meta-reflection to previous reflections
                    for prev_ref in previous_thought_reflections:
                        if prev_ref.id not in self.meta_reflections:
                            self.meta_reflections[prev_ref.id] = []
                        self.meta_reflections[prev_ref.id].append(meta_reflection.id)
        
        logger.debug(f"Created reflection {reflection.id} for thought {thought.id}")
        return reflection
    
    async def get_reflection_by_id(self, reflection_id: str) -> Optional[Reflection]:
        """
        Get a reflection by ID.
        
        Args:
            reflection_id: The ID of the reflection to get
            
        Returns:
            The reflection, or None if not found
        """
        async with self.lock:
            reflection = self.reflections.get(reflection_id)
            
            # Update access metadata
            if reflection:
                if "last_accessed" not in reflection.metadata:
                    reflection.metadata["last_accessed"] = []
                reflection.metadata["last_accessed"].append(time.time())
            
            if reflection:
                # Update last accessed time in metadata
                reflection.metadata["last_accessed"] = time.time()
            
            return reflection
    
    async def get_reflections_for_thought(self, thought_id: str) -> List[Reflection]:
        """
        Get all reflections for a thought.
        
        Args:
            thought_id: The ID of the thought
            
        Returns:
            List of reflections for the thought
        """
        async with self.lock:
            reflection_ids = self.thought_reflections.get(thought_id, [])
            return [self.reflections[rid] for rid in reflection_ids if rid in self.reflections]
    
    async def _generate_insights(self, thought: Thought, context: CognitiveContext,
                                contradictions: List[Tuple[str, str]],
                                patterns: List[str],
                                reflection_level: int = 1) -> List[str]:
        """
        Generate advanced insights from a thought with varying depth based on reflection level.
        
        Args:
            thought: The thought to generate insights from
            context: The cognitive context
            contradictions: List of contradictions detected
            patterns: List of patterns identified
            reflection_level: The level of reflection (1 for base, >1 for meta)
            
        Returns:
            List of insights
        """
        insights = []
        
        # Basic insights based on thought type
        if thought.type == "question":
            insights.append(f"Question identifies a knowledge gap about: {thought.content}")
        elif thought.type == "hypothesis":
            insights.append(f"Hypothesis proposes a potential explanation: {thought.content}")
        elif thought.type == "insight":
            insights.append(f"Building on previous insight: {thought.content}")
        else:
            insights.append(f"General observation about: {thought.content}")
        
        # Add insights based on cognitive context
        if context.cognitive_load > 0.7:
            insights.append("Current cognitive load is high, consider simplifying the approach")
        elif context.cognitive_load < 0.3:
            insights.append("Current cognitive load is low, consider exploring more complex aspects")
        
        if context.attention_focus:
            insights.append(f"Current focus on {context.attention_focus} may influence interpretation")
        
        # Add insights based on contradictions
        if contradictions:
            insights.append(f"Found {len(contradictions)} contradictions with other thoughts")
            for contradicting_id, reason in contradictions[:3]:  # Limit to first 3
                insights.append(f"Contradiction: {reason}")
        
        # Add insights based on patterns
        if patterns:
            insights.append(f"Thought fits {len(patterns)} recognized patterns")
            for pattern in patterns[:3]:  # Limit to first 3
                insights.append(f"Pattern match: {pattern}")
        
        # Add insights based on thought content analysis
        content_insights = await self._analyze_thought_content(thought)
        insights.extend(content_insights)
        
        # Add insights based on relationships to other thoughts
        relationship_insights = await self._analyze_thought_relationships(thought, context)
        insights.extend(relationship_insights)
        
        # Add deeper insights based on reflection level
        if reflection_level > 1:
            # Add meta-level insights
            insights.append("At a meta-level, this thought represents a cognitive process that builds upon previous thinking.")
            
            if len(patterns) > 2:
                insights.append(f"This thought combines multiple patterns ({', '.join(patterns[:3])}...), suggesting complex cognitive processing.")
            
            if contradictions:
                insights.append("The presence of contradictions indicates an opportunity for cognitive growth through reconciliation.")
            
            # Add context-aware insights
            if context.cognitive_load > 0.7:
                insights.append("This thought emerged during high cognitive load, which may affect its quality or depth.")
            elif context.cognitive_load < 0.3:
                insights.append("This thought emerged during low cognitive load, potentially allowing for more creative or thorough processing.")
            
            if context.attention_focus:
                insights.append(f"This thought relates to the current attention focus on '{context.attention_focus}'.")
        
        # For even deeper reflection levels, add philosophical insights
        if reflection_level > 2:
            insights.append("This meta-reflection reveals patterns in how the cognitive system processes and evaluates its own thoughts.")
            insights.append("The recursive nature of this reflection demonstrates the system's capacity for self-awareness and metacognition.")
            
            if contradictions:
                insights.append("The contradictions present in thinking represent dialectical processes that can lead to synthesis and growth.")
        
        return insights
    
    async def _generate_meta_insights(self, thought: Thought, previous_reflections: List[Reflection],
                                    context: CognitiveContext) -> List[str]:
        """
        Generate meta-insights by analyzing patterns across multiple reflections.
        
        Args:
            thought: The thought being reflected on
            previous_reflections: List of previous reflections to analyze
            context: The cognitive context
            
        Returns:
            List of meta-insights
        """
        if not previous_reflections:
            return []
        
        meta_insights = []
        
        # Analyze reflection patterns
        reflection_count = len(previous_reflections)
        meta_insights.append(f"This thought has generated {reflection_count} previous reflections, indicating sustained cognitive engagement.")
        
        # Extract all insights from previous reflections
        all_insights = []
        for reflection in previous_reflections:
            all_insights.extend(reflection.insights)
        
        # Identify recurring themes
        if all_insights:
            common_themes = self._identify_common_themes(all_insights)
            if common_themes:
                meta_insights.append(f"Recurring themes across reflections: {', '.join(common_themes[:3])}")
        
        # Analyze reflection evolution
        if len(previous_reflections) >= 2:
            # Check for increasing complexity
            insight_counts = [len(r.insights) for r in previous_reflections]
            if insight_counts[-1] > insight_counts[0]:
                meta_insights.append("Reflections show increasing complexity over time, suggesting deepening understanding.")
            elif insight_counts[-1] < insight_counts[0]:
                meta_insights.append("Reflections show decreasing complexity over time, suggesting consolidation of understanding.")
            
            # Check for convergence or divergence
            early_reflections = previous_reflections[:len(previous_reflections)//2]
            late_reflections = previous_reflections[len(previous_reflections)//2:]
            
            early_insights = []
            for r in early_reflections:
                early_insights.extend(r.insights)
                
            late_insights = []
            for r in late_reflections:
                late_insights.extend(r.insights)
                
            convergence = self._calculate_insight_similarity(early_insights, late_insights)
            
            if convergence > 0.7:
                meta_insights.append("Reflections are converging toward a focused understanding.")
            elif convergence < 0.3:
                meta_insights.append("Reflections are diverging, exploring multiple perspectives.")
        
        # Analyze contradiction resolution
        contradiction_counts = [len(r.metadata.get("contradictions", [])) for r in previous_reflections if "contradictions" in r.metadata]
        if contradiction_counts and len(contradiction_counts) >= 2:
            if contradiction_counts[-1] < contradiction_counts[0]:
                meta_insights.append("Contradictions are being resolved over time, indicating cognitive integration.")
            elif contradiction_counts[-1] > contradiction_counts[0]:
                meta_insights.append("New contradictions are emerging, suggesting a need for further reconciliation.")
        
        # Analyze metacognitive awareness
        meta_reflection_count = sum(1 for r in previous_reflections if r.metadata.get("reflection_level", 1) > 1)
        if meta_reflection_count > 0:
            meta_insights.append(f"Previous thinking includes {meta_reflection_count} meta-reflections, showing metacognitive awareness.")
        
        return meta_insights
    
    def _calculate_insight_similarity(self, insights1: List[str], insights2: List[str]) -> float:
        """
        Calculate similarity between two sets of insights.
        
        Args:
            insights1: First set of insights
            insights2: Second set of insights
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not insights1 or not insights2:
            return 0.0
        
        # Extract terms from insights
        terms1 = set()
        for insight in insights1:
            terms1.update(re.findall(r'\b\w{4,}\b', insight.lower()))
        
        terms2 = set()
        for insight in insights2:
            terms2.update(re.findall(r'\b\w{4,}\b', insight.lower()))
        
        # Calculate Jaccard similarity
        if not terms1 or not terms2:
            return 0.0
            
        intersection = len(terms1.intersection(terms2))
        union = len(terms1.union(terms2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
    
    async def _should_ideate(self, thought: Thought, context: CognitiveContext,
                            contradictions: List[Tuple[str, str]],
                            reflection_level: int = 1) -> bool:
        """
        Determine if ideation should be performed on a thought with advanced criteria.
        
        Args:
            thought: The thought to consider
            context: The cognitive context
            contradictions: List of contradictions detected
            
        Returns:
            True if ideation should be performed, False otherwise
        """
        # Base criteria
        
        # Ideate on high-priority thoughts
        if thought.priority > 0.7:
            return True
        
        # Ideate on questions and hypotheses
        if thought.type in ["question", "hypothesis"]:
            return True
        
        # Ideate when cognitive load is low
        if context.cognitive_load < 0.5:
            return True
        
        # Advanced criteria
        
        # Ideate when contradictions are found (to resolve them)
        if contradictions:
            return True
        
        # Ideate on thoughts with specific metadata flags
        if thought.metadata.get("requires_ideation", False):
            return True
        
        if thought.metadata.get("important", False) and thought.priority > 0.4:
            return True
        
        # Ideate on thoughts related to current attention focus
        if context.attention_focus and context.attention_focus.lower() in thought.content.lower():
            return True
        
        # Don't ideate on low-priority thoughts when cognitive load is high
        if thought.priority < 0.3 and context.cognitive_load > 0.7:
            return False
        
        # Default to not ideating
        return False
    
    async def meta_reflect(self, reflections: List[Reflection], context: CognitiveContext) -> Reflection:
        """
        Perform meta-reflection on a set of reflections.
        
        Args:
            reflections: The reflections to meta-reflect on
            context: The cognitive context
            
        Returns:
            A meta-reflection
        """
        logger.debug(f"Performing meta-reflection on {len(reflections)} reflections")
        
        if not reflections:
            raise ValueError("Cannot perform meta-reflection on empty reflection list")
        
        # Create a synthetic thought representing the collection of reflections
        synthetic_thought = Thought(
            content=f"Meta-reflection on {len(reflections)} reflections",
            type="meta_reflection",
            priority=max(r.metadata.get("priority", 0.5) for r in reflections),
            metadata={
                "reflection_ids": [r.id for r in reflections],
                "thought_ids": [r.thought_id for r in reflections],
                "is_synthetic": True
            }
        )
        
        # Perform reflection on the synthetic thought, passing original reflections
        return await self.reflect(synthetic_thought, context, reflections)
    
    async def get_meta_reflections(self, reflection_id: str) -> List[Reflection]:
        """
        Get all meta-reflections for a reflection.
        
        Args:
            reflection_id: The ID of the reflection
            
        Returns:
            List of meta-reflections for the reflection
        """
        async with self.lock:
            meta_reflection_ids = self.meta_reflections.get(reflection_id, [])
            return [self.reflections[rid] for rid in meta_reflection_ids if rid in self.reflections]
    
    async def get_contradictions(self, thought_id: str) -> List[Tuple[str, str]]:
        """
        Get all contradictions for a thought.
        
        Args:
            thought_id: The ID of the thought
            
        Returns:
            List of tuples containing (contradicting_thought_id, reason)
        """
        async with self.lock:
            return self.contradictions.get(thought_id, [])
    
    async def _detect_contradictions(self, thought: Thought, context: CognitiveContext) -> List[Tuple[str, str]]:
        """
        Detect contradictions between the given thought and other thoughts.
        
        Args:
            thought: The thought to check for contradictions
            context: The cognitive context
            
        Returns:
            List of tuples containing (contradicting_thought_id, reason)
        """
        contradictions = []
        
        # Get active thoughts from context
        active_thought_ids = context.active_thoughts
        
        # Skip if no active thoughts or only one thought
        if not active_thought_ids or len(active_thought_ids) < 2:
            return contradictions
        
        # Check for direct contradictions in content
        content_lower = thought.content.lower()
        
        # Look for negation patterns
        negation_words = ["not", "no", "never", "isn't", "aren't", "doesn't", "don't", "can't", "cannot"]
        contains_negation = any(neg in content_lower.split() for neg in negation_words)
        
        # Extract key statements (simplified)
        statements = self._extract_statements(content_lower)
        
        # Check each active thought for contradictions
        for other_id in active_thought_ids:
            if other_id == thought.id:
                continue
                
            # Get the other thought from context (simplified - in a real system, we'd have a way to retrieve thoughts)
            # For now, we'll assume we have a way to get the thought content
            other_content = f"Other thought content for {other_id}"  # Placeholder
            other_content_lower = other_content.lower()
            
            # Check for direct statement contradictions
            for statement in statements:
                # Direct negation (simplified)
                negated_statement = f"not {statement}"
                if negated_statement in other_content_lower:
                    contradictions.append((other_id, f"Direct contradiction: '{statement}' vs '{negated_statement}'"))
                    continue
                
                # Opposite statements (simplified)
                if statement.startswith("is ") and f"is not {statement[3:]}" in other_content_lower:
                    contradictions.append((other_id, f"Opposite statements: '{statement}' vs 'is not {statement[3:]}'"))
            
            # Check for logical contradictions (simplified)
            if "always" in content_lower and "sometimes" in other_content_lower:
                contradictions.append((other_id, "Logical contradiction: 'always' vs 'sometimes'"))
            
            if "never" in content_lower and "sometimes" in other_content_lower:
                contradictions.append((other_id, "Logical contradiction: 'never' vs 'sometimes'"))
        
        # Store contradictions
        async with self.lock:
            self.contradictions[thought.id] = contradictions
        
        return contradictions
    
    def _extract_statements(self, content: str) -> List[str]:
        """
        Extract key statements from thought content.
        
        Args:
            content: The thought content
            
        Returns:
            List of key statements
        """
        # Simplified implementation - in a real system, this would use NLP
        statements = []
        
        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Simple heuristic: sentences with "is", "are", "should", etc. are statements
            statement_indicators = ["is ", "are ", "should ", "must ", "will ", "can "]
            if any(indicator in sentence for indicator in statement_indicators):
                statements.append(sentence)
        
        return statements
    
    async def _identify_patterns(self, thought: Thought, context: CognitiveContext) -> List[str]:
        """
        Identify patterns in the thought.
        
        Args:
            thought: The thought to identify patterns in
            context: The cognitive context
            
        Returns:
            List of pattern names
        """
        patterns = []
        content_lower = thought.content.lower()
        
        # Define pattern recognition rules
        pattern_rules = [
            # Question patterns
            (r'\bwhy\s+\w+\s+\w+', "why_question"),
            (r'\bhow\s+to\s+\w+', "how_to_question"),
            (r'\bwhat\s+is\s+\w+', "what_is_question"),
            
            # Hypothesis patterns
            (r'\bif\s+\w+\s+then\s+\w+', "if_then_hypothesis"),
            (r'\bmay\s+be\s+\w+', "possibility_hypothesis"),
            (r'\bcould\s+be\s+\w+', "possibility_hypothesis"),
            
            # Insight patterns
            (r'\brealized\s+\w+', "realization_insight"),
            (r'\bconnection\s+between\s+\w+', "connection_insight"),
            (r'\bpattern\s+of\s+\w+', "pattern_insight"),
            
            # Problem patterns
            (r'\bissue\s+with\s+\w+', "problem_identification"),
            (r'\bproblem\s+is\s+\w+', "problem_statement"),
            (r'\bchallenges?\s+\w+', "challenge_identification"),
            
            # Solution patterns
            (r'\bsolution\s+is\s+\w+', "solution_statement"),
            (r'\bapproach\s+to\s+\w+', "solution_approach"),
            (r'\bresolve\s+\w+\s+by\s+\w+', "solution_method"),
            
            # Comparative patterns
            (r'\bbetter\s+than\s+\w+', "comparative_judgment"),
            (r'\bworse\s+than\s+\w+', "comparative_judgment"),
            (r'\bsimilar\s+to\s+\w+', "similarity_observation"),
            
            # Causal patterns
            (r'\bbecause\s+\w+', "causal_explanation"),
            (r'\bresults?\s+in\s+\w+', "causal_effect"),
            (r'\bleads?\s+to\s+\w+', "causal_effect")
        ]
        
        # Check each pattern
        for pattern_regex, pattern_name in pattern_rules:
            if re.search(pattern_regex, content_lower):
                patterns.append(pattern_name)
                
                # Update thought patterns
                async with self.lock:
                    if pattern_name not in self.thought_patterns:
                        self.thought_patterns[pattern_name] = []
                    
                    if thought.id not in self.thought_patterns[pattern_name]:
                        self.thought_patterns[pattern_name].append(thought.id)
        
        return patterns
    
    async def _analyze_thought_content(self, thought: Thought) -> List[str]:
        """
        Analyze thought content for additional insights.
        
        Args:
            thought: The thought to analyze
            
        Returns:
            List of content-based insights
        """
        insights = []
        content_lower = thought.content.lower()
        
        # Check for uncertainty
        uncertainty_indicators = ["maybe", "perhaps", "possibly", "might", "could", "uncertain"]
        if any(indicator in content_lower.split() for indicator in uncertainty_indicators):
            insights.append("Expresses uncertainty, consider exploring confidence levels")
        
        # Check for certainty
        certainty_indicators = ["definitely", "certainly", "absolutely", "undoubtedly", "clearly"]
        if any(indicator in content_lower.split() for indicator in certainty_indicators):
            insights.append("Expresses high certainty, consider validating evidence")
        
        # Check for complexity
        if len(content_lower.split()) > 30:
            insights.append("Complex thought, consider breaking down into simpler components")
        
        # Check for vagueness
        vagueness_indicators = ["somehow", "something", "somewhat", "some", "things", "stuff"]
        if sum(1 for indicator in vagueness_indicators if indicator in content_lower.split()) >= 2:
            insights.append("Contains vague language, consider clarifying specific details")
        
        # Check for action orientation
        action_verbs = ["do", "implement", "create", "build", "develop", "act", "execute"]
        if any(verb in content_lower.split() for verb in action_verbs):
            insights.append("Action-oriented thought, consider implementation steps")
        
        return insights
    
    async def _analyze_thought_relationships(self, thought: Thought, context: CognitiveContext) -> List[str]:
        """
        Analyze relationships between the thought and other thoughts.
        
        Args:
            thought: The thought to analyze
            context: The cognitive context
            
        Returns:
            List of relationship-based insights
        """
        insights = []
        
        # Get active thoughts from context
        active_thought_ids = context.active_thoughts
        
        # Skip if no active thoughts or only one thought
        if not active_thought_ids or len(active_thought_ids) < 2:
            return insights

        # Count how many active thoughts are related to this one
        related_count = sum(1 for id in active_thought_ids if id != thought.id)
        
        if related_count > 3:
            insights.append(f"Connected to {related_count} other active thoughts, suggesting a central concept")
        
        # Check if this thought builds on previous ones
        if thought.metadata.get("builds_on", None):
            insights.append("Builds on previous thoughts, showing conceptual development")
        
        # Check if this is a novel direction
        if not thought.metadata.get("builds_on", None) and thought.type not in ["question", "hypothesis"]:
            insights.append("Represents a novel direction, consider exploring connections to existing thoughts")
        return insights

    async def _generate_knowledge_based_insights(self, thought: Thought, context: CognitiveContext,
                                              reflection_level: int = 1) -> List[str]:
        """
        Generate insights based on knowledge store information with varying depth based on reflection level.

        Args:
            thought: The thought to generate insights for
            context: The cognitive context
            reflection_level: The level of reflection (1 for base, >1 for meta)

        Returns:
            List of knowledge-based insights
        """
        if not self.knowledge_store:
            return []

        insights = []

        try:
            # Query knowledge store for relevant information with parameters based on reflection level
            query = {
                "content": thought.content,
                "type": thought.type,
                "max_results": 3 * reflection_level,  # More results for deeper reflections
                "min_confidence": 0.7 - (0.1 * (reflection_level - 1))  # Lower threshold for deeper reflections
            }

            # Add context information for more targeted queries
            if context:
                query["context"] = {
                    "cognitive_load": context.cognitive_load,
                    "attention_focus": context.attention_focus,
                    "active_thoughts": context.active_thoughts
                }

            # This is a simplified placeholder - in a real implementation,
            # we would use the actual knowledge store API
            knowledge_items = await self.knowledge_store.query_knowledge(query)

            # Generate insights based on knowledge items
            if hasattr(knowledge_items, 'items') and knowledge_items.items:
                for item in knowledge_items.items:
                    if hasattr(item, 'content') and item.content:
                        # Extract content
                        content_str = str(item.content)
                        truncated_content = content_str[:100] + "..." if len(content_str) > 100 else content_str

                        # Get type and confidence
                        item_type = getattr(item, "type", "unknown")
                        confidence = getattr(item, "confidence", 0.5)

                        # Generate appropriate insight based on item type
                        if item_type == "concept":
                            insights.append(f"This thought relates to the concept: {truncated_content}")
                        elif item_type == "fact":
                            insights.append(f"This thought connects to the established fact: {truncated_content}")
                        elif item_type == "rule":
                            insights.append(f"This thought may follow the rule: {truncated_content}")
                        elif item_type == "hypothesis":
                            insights.append(f"This thought aligns with the hypothesis: {truncated_content}")
                        else:
                            insights.append(f"This thought connects to existing knowledge: {truncated_content}")

                        # For deeper reflections, add confidence information
                        if reflection_level > 1:
                            insights[-1] += f" (confidence: {confidence:.2f})"

                # For deeper reflections, add meta-insights about knowledge connections
                if reflection_level > 1 and len(knowledge_items.items) > 0:
                    insights.append(f"This thought connects to {len(knowledge_items.items)} items in the knowledge store, suggesting it builds on existing understanding.")

                    if len(knowledge_items.items) > 3:
                        insights.append("The multiple knowledge connections indicate this is a rich area for further exploration.")

                # For even deeper reflections, add epistemological insights
                if reflection_level > 2 and len(knowledge_items.items) > 0:
                    insights.append("The pattern of knowledge connections reveals how new thoughts integrate with existing cognitive structures.")
                    insights.append("The relationship between this thought and prior knowledge demonstrates the incremental nature of cognitive development.")

                    # Add insights about knowledge confidence distribution
                    confidence_values = [getattr(item, "confidence", 0.5) for item in knowledge_items.items]
                    avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.5

                    if avg_confidence > 0.8:
                        insights.append("The high confidence in related knowledge suggests this thought builds on well-established foundations.")
                    elif avg_confidence < 0.4:
                        insights.append("The low confidence in related knowledge suggests this thought explores uncertain or speculative territory.")
        except Exception as e:
            logger.error(f"Error querying knowledge store: {e}")
            insights.append("Error accessing knowledge store, relying on internal processing only.")

        return insights

    def _generate_reflection_content(self, thought: Thought, insights: List[str],
                                    contradictions: List[Tuple[str, str]],
                                    patterns: List[str],
                                    reflection_level: int = 1) -> str:
        """
        Generate comprehensive reflection content with appropriate depth based on reflection level.

        Args:
            thought: The thought being reflected on
            insights: The generated insights
            contradictions: The detected contradictions
            patterns: The identified patterns
            reflection_level: The level of reflection (1 for base, >1 for meta)

        Returns:
            Formatted reflection content
        """
        # Create appropriate header based on reflection level
        if reflection_level == 1:
            content = [f"Reflection on: {thought.content}"]
        elif reflection_level == 2:
            content = [f"Meta-reflection on: {thought.content}"]
        else:
            content = [f"Level {reflection_level} meta-reflection on: {thought.content}"]

        # Add thought type and priority information
        content.append(f"\nThought Type: {thought.type}")
        content.append(f"Thought Priority: {thought.priority:.2f}")

        # Add pattern information with appropriate depth
        if patterns:
            content.append("\nIdentified patterns:")
            for pattern in patterns:
                content.append(f"- {pattern}")

            # Add pattern analysis for deeper reflections
            if reflection_level > 1 and len(patterns) > 1:
                content.append("\nPattern Analysis:")
                content.append(f"- This thought exhibits {len(patterns)} distinct patterns.")

                # Categorize patterns
                question_patterns = [p for p in patterns if "question" in p]
                hypothesis_patterns = [p for p in patterns if "hypothesis" in p]
                insight_patterns = [p for p in patterns if "insight" in p]
                problem_patterns = [p for p in patterns if "problem" in p]
                solution_patterns = [p for p in patterns if "solution" in p]

                if question_patterns:
                    content.append(f"- Contains {len(question_patterns)} question patterns, indicating inquiry orientation.")
                if hypothesis_patterns:
                    content.append(f"- Contains {len(hypothesis_patterns)} hypothesis patterns, indicating theoretical thinking.")
                if insight_patterns:
                    content.append(f"- Contains {len(insight_patterns)} insight patterns, indicating synthetic thinking.")
                if problem_patterns:
                    content.append(f"- Contains {len(problem_patterns)} problem patterns, indicating analytical thinking.")
                if solution_patterns:
                    content.append(f"- Contains {len(solution_patterns)} solution patterns, indicating practical thinking.")

        # Add contradiction information with appropriate depth
        if contradictions:
            content.append("\nDetected contradictions:")
            for contradicting_id, reason in contradictions:
                content.append(f"- {reason} (with thought {contradicting_id})")

            # Add contradiction analysis for deeper reflections
            if reflection_level > 1:
                content.append("\nContradiction Analysis:")
                content.append(f"- Found {len(contradictions)} contradictions that require resolution.")
                content.append("- Contradictions represent opportunities for cognitive growth through dialectical thinking.")

                if reflection_level > 2:
                    content.append("- The presence of contradictions indicates a complex thought space with competing perspectives.")
                    content.append("- Resolving these contradictions may require higher-order integration or paradigm shifts.")

        # Add insights with appropriate depth
        if insights:
            if reflection_level == 1:
                content.append("\nInsights:")
            elif reflection_level == 2:
                content.append("\nMeta-Insights:")
            else:
                content.append(f"\nLevel {reflection_level} Insights:")

            for insight in insights:
                content.append(f"- {insight}")

        # Add reflection summary for deeper reflections
        if reflection_level > 1:
            content.append("\nReflection Summary:")
            if patterns and contradictions:
                content.append("- This thought contains both identifiable patterns and contradictions, suggesting a rich cognitive landscape.")
            elif patterns:
                content.append("- This thought follows established patterns but lacks contradictions, suggesting coherent but potentially unchallenged thinking.")
            elif contradictions:
                content.append("- This thought contains contradictions without clear patterns, suggesting potentially disorganized or innovative thinking.")
            else:
                content.append("- This thought lacks both clear patterns and contradictions, suggesting either novel thinking or insufficient analysis.")

        return "\n".join(content)

    async def _perform_meta_reflection(self, reflection: Reflection,
                                     previous_reflections: List[Reflection],
                                     context: CognitiveContext) -> Reflection:
        """
        Perform meta-reflection on a reflection and its predecessors.

        Args:
            reflection: The current reflection
            previous_reflections: Previous reflections to consider
            context: The cognitive context

        Returns:
            A meta-reflection
        """
        logger.debug(f"Performing meta-reflection on reflection {reflection.id}")

        # Extract insights from all reflections
        all_insights = []
        for r in previous_reflections:
            all_insights.extend(r.insights)
        all_insights.extend(reflection.insights)

        # Find common themes
        common_themes = self._identify_common_themes(all_insights)

        # Identify progression of thought
        progression = self._identify_thought_progression(previous_reflections, reflection)

        # Generate meta-insights
        meta_insights = []

        if common_themes:
            meta_insights.append(f"Common themes across reflections: {', '.join(common_themes)}")

        if progression:
            meta_insights.append(f"Thought progression: {progression}")

        # Check for circular thinking
        if self._detect_circular_thinking(previous_reflections, reflection):
            meta_insights.append("Detected circular thinking pattern, consider new approaches")

        # Check for convergence or divergence
        convergence = self._assess_convergence(previous_reflections, reflection)
        if convergence > 0.7:
            meta_insights.append("Thinking is converging toward specific conclusions")
        elif convergence < 0.3:
            meta_insights.append("Thinking is diverging, exploring multiple directions")

        # Create meta-reflection content
        meta_content = f"Meta-reflection on {len(previous_reflections) + 1} reflections"
        if meta_insights:
            meta_content += "\n\nMeta-insights:\n" + "\n".join(f"- {insight}" for insight in meta_insights)

        # Create meta-reflection
        meta_reflection = Reflection(
            thought_id=reflection.thought_id,
            content=meta_content,
            insights=meta_insights,
            should_ideate=True,  # Meta-reflections often benefit from ideation
            metadata={
                "reflection_ids": [r.id for r in previous_reflections] + [reflection.id],
                "reflection_level": max(r.metadata.get("reflection_level", 1) for r in previous_reflections) + 1,
                "is_meta_reflection": True
            }
        )

        # Store the meta-reflection
        async with self.lock:
            self.reflections[meta_reflection.id] = meta_reflection

        return meta_reflection

    def _identify_common_themes(self, insights: List[str]) -> List[str]:
        """
        Identify common themes across insights.

        Args:
            insights: List of insights to analyze

        Returns:
            List of common themes
        """
        # Simplified implementation - in a real system, this would use NLP

        # Extract key terms from insights
        all_terms = []
        for insight in insights:
            # Split by spaces and punctuation
            terms = re.findall(r'\b\w{4,}\b', insight.lower())
            all_terms.extend(terms)

        # Count term frequencies
        term_counts = {}
        for term in all_terms:
            term_counts[term] = term_counts.get(term, 0) + 1

        # Identify common terms (occurring more than once)
        common_terms = [term for term, count in term_counts.items() if count > 1]

        # Group related terms (simplified)
        themes = []
        for term in common_terms:
            # Check if term is already part of an existing theme
            if not any(term in theme for theme in themes):
                # Find related terms
                related_terms = [t for t in common_terms if self._are_terms_related(term, t)]
                if related_terms:
                    themes.append(", ".join(related_terms))

        return themes[:5]  # Limit to top 5 themes

    def _are_terms_related(self, term1: str, term2: str) -> bool:
        """
        Determine if two terms are related.

        Args:
            term1: First term
            term2: Second term

        Returns:
            True if terms are related, False otherwise
        """
        # Simplified implementation - in a real system, this would use semantic similarity

        # Check for common prefix
        if term1.startswith(term2[:4]) or term2.startswith(term1[:4]):
            return True

        # Check for one term containing the other
        if term1 in term2 or term2 in term1:
            return True

        # Define some related term pairs (simplified)
        related_pairs = [
            ("problem", "solution"),
            ("question", "answer"),
            ("hypothesis", "evidence"),
            ("concept", "idea"),
            ("pattern", "structure")
        ]

        # Check if terms are in a related pair
        for pair in related_pairs:
            if (term1 in pair and term2 in pair):
                return True

        return False

    def _identify_thought_progression(self, previous_reflections: List[Reflection],
                                     current_reflection: Reflection) -> str:
        """
        Identify the progression of thought across reflections.

        Args:
            previous_reflections: Previous reflections
            current_reflection: Current reflection

        Returns:
            Description of thought progression
        """
        # Simplified implementation

        # Check for progression from question to hypothesis
        if any("why_question" in r.metadata.get("patterns", []) for r in previous_reflections) and \
           any("if_then_hypothesis" in p for p in [current_reflection.metadata.get("patterns", [])]):
            return "Progressed from questioning to hypothesis formation"

        # Check for progression from problem to solution
        if any("problem_identification" in r.metadata.get("patterns", []) for r in previous_reflections) and \
           any("solution_" in p for p in current_reflection.metadata.get("patterns", [])):
            return "Progressed from problem identification to solution proposal"

        # Check for increasing complexity
        if len(previous_reflections) > 1:
            insight_counts = [len(r.insights) for r in previous_reflections]
            current_count = len(current_reflection.insights)

            if current_count > max(insight_counts):
                return "Increasing complexity and insight generation"
            elif current_count < min(insight_counts):
                return "Converging toward simplification"

        # Default
        return "Ongoing exploration of the thought space"

    def _detect_circular_thinking(self, previous_reflections: List[Reflection],
                                 current_reflection: Reflection) -> bool:
        """
        Detect circular thinking patterns.

        Args:
            previous_reflections: Previous reflections
            current_reflection: Current reflection

        Returns:
            True if circular thinking is detected, False otherwise
        """
        # Simplified implementation

        # Extract key terms from current reflection
        current_content = current_reflection.content.lower()
        current_terms = set(re.findall(r'\b\w{5,}\b', current_content))

        if not current_terms:
            return False

        # Check for term overlap with early reflections
        if len(previous_reflections) >= 3:
            early_reflections = previous_reflections[:len(previous_reflections)//2]

            for early_reflection in early_reflections:
                early_content = early_reflection.content.lower()
                early_terms = set(re.findall(r'\b\w{5,}\b', early_content))

                # Calculate overlap
                if early_terms:
                    overlap = len(current_terms.intersection(early_terms)) / len(current_terms.union(early_terms))

                    # If significant overlap with early reflection, may indicate circular thinking
                    if overlap > 0.7:
                        return True

        return False

    def _assess_convergence(self, previous_reflections: List[Reflection],
                           current_reflection: Reflection) -> float:
        """
        Assess convergence or divergence in thinking.

        Args:
            previous_reflections: Previous reflections
            current_reflection: Current reflection

        Returns:
            Convergence score (0.0 to 1.0, higher means more convergent)
        """
        # Simplified implementation

        if not previous_reflections:
            return 0.5  # Neutral

        # Compare insights between reflections
        if len(previous_reflections) >= 2:
            # Get insights from last few reflections
            recent_reflections = previous_reflections[-min(3, len(previous_reflections)):]
            all_insights = []

            for r in recent_reflections:
                all_insights.extend(r.insights)

            current_insights = current_reflection.insights

            # Calculate similarity between current and previous insights
            similarity_scores = []

            for prev_insight in all_insights:
                prev_terms = set(re.findall(r'\b\w{4,}\b', prev_insight.lower()))

                for curr_insight in current_insights:
                    curr_terms = set(re.findall(r'\b\w{4,}\b', curr_insight.lower()))

                    if prev_terms and curr_terms:
                        # Jaccard similarity
                        intersection = len(prev_terms.intersection(curr_terms))
                        union = len(prev_terms.union(curr_terms))

                        if union > 0:
                            similarity_scores.append(intersection / union)

            if similarity_scores:
                # High average similarity indicates convergence
                return sum(similarity_scores) / len(similarity_scores)

        return 0.5  # Neutral default

