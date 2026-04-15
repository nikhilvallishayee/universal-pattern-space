"""
Metacognitive Monitor Implementation for GodelOS

This module implements the MetacognitiveMonitor class, which is responsible for
monitoring the cognitive system's state, updating metacognitive metrics, and
making decisions about cognitive processes. The enhanced implementation includes
cognitive load estimation, attention allocation optimization, performance monitoring
and adaptation, and learning from past cognitive processes.
"""

import logging
import time
import math
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
import asyncio
from collections import defaultdict, deque
import re

from godelOS.unified_agent_core.cognitive_engine.interfaces import (
    Thought, Reflection, CognitiveContext, MetacognitiveMonitorInterface
)

logger = logging.getLogger(__name__)


class MetacognitiveMonitor(MetacognitiveMonitorInterface):
    """
    Enhanced MetacognitiveMonitor implementation for GodelOS.
    
    The MetacognitiveMonitor is responsible for monitoring the cognitive system's
    state, updating metacognitive metrics, and making decisions about cognitive
    processes.
    
    Features:
    1. Cognitive load estimation based on active thoughts
    2. Attention allocation optimization
    3. Performance monitoring and adaptation
    4. Learning from past cognitive processes
    """
    
    def __init__(self):
        """Initialize the metacognitive monitor."""
        # Basic metacognitive state
        self.cognitive_load = 0.0
        self.attention_allocation: Dict[str, float] = {}
        self.reflection_thresholds: Dict[str, float] = {
            "general": 0.3,
            "question": 0.6,
            "insight": 0.5,
            "hypothesis": 0.7
        }
        
        # State history
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # Performance monitoring
        self.performance_metrics: Dict[str, float] = {
            "reflection_quality": 0.5,  # Quality of reflections (0.0 to 1.0)
            "ideation_quality": 0.5,    # Quality of ideas generated (0.0 to 1.0)
            "thought_coherence": 0.5,   # Coherence between thoughts (0.0 to 1.0)
            "adaptation_rate": 0.5      # How quickly the system adapts (0.0 to 1.0)
        }
        
        # Learning and adaptation
        self.learning_rate = 0.1
        self.adaptation_history: List[Dict[str, Any]] = []
        self.max_adaptation_history = 50
        
        # Cognitive resource management
        self.resource_allocation: Dict[str, float] = {
            "reflection": 0.3,   # Resources allocated to reflection
            "ideation": 0.3,     # Resources allocated to ideation
            "perception": 0.2,   # Resources allocated to perception
            "execution": 0.2     # Resources allocated to execution
        }
        
        # Attention optimization
        self.focus_duration: Dict[str, int] = {}  # How long to focus on each area
        self.optimal_focus_count = 3  # Optimal number of focus areas
        
        # Thought pattern recognition
        self.thought_patterns: Dict[str, List[str]] = {}  # Pattern -> list of thought IDs
        self.recurring_themes: Dict[str, float] = {}  # Theme -> strength
        
        # Thread safety
        self.lock = asyncio.Lock()
        
        # Knowledge store reference (will be set by the cognitive engine)
        self.knowledge_store = None
    
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The knowledge store
        """
        self.knowledge_store = knowledge_store
    
    async def update_state(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Update the metacognitive state with enhanced monitoring and adaptation.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        logger.debug(f"Updating metacognitive state with thought {thought.id}")
        
        async with self.lock:
            # Update cognitive load with advanced estimation
            self._update_cognitive_load(thought, reflection, context)
            
            # Optimize attention allocation
            self._update_attention_allocation(thought, reflection, context)
            
            # Update performance metrics
            self._update_performance_metrics(thought, reflection, context)
            
            # Adapt resource allocation based on performance
            self._adapt_resource_allocation()
            
            # Recognize thought patterns
            self._recognize_thought_patterns(thought)
            
            # Learn from this cognitive cycle
            self._learn_from_cognitive_cycle(thought, reflection, context)
            
            # Store state in history
            self._store_state_in_history(thought, reflection, context)
    
    async def get_cognitive_load(self) -> float:
        """
        Get the current cognitive load.
        
        Returns:
            The cognitive load (0.0 to 1.0)
        """
        async with self.lock:
            return self.cognitive_load
    
    async def get_attention_allocation(self) -> Dict[str, float]:
        """
        Get the current attention allocation.
        
        Returns:
            Dictionary mapping focus areas to allocation values
        """
        async with self.lock:
            return self.attention_allocation.copy()
    
    async def get_cognitive_state_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the current cognitive state.
        
        Returns:
            Dictionary with cognitive state information
        """
        async with self.lock:
            return {
                "cognitive_load": self.cognitive_load,
                "attention_allocation": self.attention_allocation.copy(),
                "performance_metrics": self.performance_metrics.copy(),
                "resource_allocation": self.resource_allocation.copy(),
                "recurring_themes": {k: v for k, v in self.recurring_themes.items() if v > 0.3},
                "active_patterns": list(self.thought_patterns.keys())
            }
    
    async def optimize_cognitive_resources(self, context: CognitiveContext) -> Dict[str, float]:
        """
        Optimize allocation of cognitive resources based on current state and context.
        
        Args:
            context: The cognitive context
            
        Returns:
            Dictionary with optimized resource allocations
        """
        async with self.lock:
            # Analyze current state
            current_load = self.cognitive_load
            performance = self.performance_metrics
            
            # Adjust resource allocation based on load and performance
            if current_load > 0.8:  # Very high load
                # Prioritize execution and reduce reflection/ideation
                self.resource_allocation["reflection"] = max(0.1, self.resource_allocation["reflection"] - 0.1)
                self.resource_allocation["ideation"] = max(0.1, self.resource_allocation["ideation"] - 0.1)
                self.resource_allocation["execution"] = min(0.5, self.resource_allocation["execution"] + 0.1)
                self.resource_allocation["perception"] = min(0.3, self.resource_allocation["perception"] + 0.1)
            
            elif current_load < 0.3:  # Low load
                # Increase reflection and ideation
                self.resource_allocation["reflection"] = min(0.5, self.resource_allocation["reflection"] + 0.1)
                self.resource_allocation["ideation"] = min(0.5, self.resource_allocation["ideation"] + 0.1)
                self.resource_allocation["execution"] = max(0.1, self.resource_allocation["execution"] - 0.1)
                self.resource_allocation["perception"] = max(0.1, self.resource_allocation["perception"] - 0.1)
            
            # Adjust based on performance metrics
            if performance["reflection_quality"] < 0.4:
                # Reflection quality is low, allocate more resources
                self.resource_allocation["reflection"] = min(0.5, self.resource_allocation["reflection"] + 0.1)
            
            if performance["ideation_quality"] < 0.4:
                # Ideation quality is low, allocate more resources
                self.resource_allocation["ideation"] = min(0.5, self.resource_allocation["ideation"] + 0.1)
            
            # Normalize allocations to ensure they sum to 1.0
            total = sum(self.resource_allocation.values())
            if total > 0:
                for key in self.resource_allocation:
                    self.resource_allocation[key] /= total
            
            return self.resource_allocation.copy()
    
    async def should_reflect(self, thought: Thought, context: CognitiveContext) -> bool:
        """
        Determine if reflection should be performed on a thought with advanced criteria.
        
        Args:
            thought: The thought to consider
            context: The cognitive context
            
        Returns:
            True if reflection should be performed, False otherwise
        """
        # Get base threshold for thought type
        threshold = self.reflection_thresholds.get(thought.type, self.reflection_thresholds["general"])
        
        # Adjust threshold based on cognitive load
        # When load is high, be more selective about reflection
        load_adjustment = 0.3 * self.cognitive_load
        
        # Adjust threshold based on available resources for reflection
        resource_adjustment = -0.2 * self.resource_allocation["reflection"]  # More resources -> lower threshold
        
        # Adjust threshold based on thought's relation to current attention focus
        focus_adjustment = 0.0
        if context.attention_focus:
            if context.attention_focus.lower() in thought.content.lower():
                # Thought is related to current focus, lower threshold
                focus_adjustment = -0.2
            else:
                # Thought is unrelated to current focus, increase threshold
                focus_adjustment = 0.1
        
        # Adjust threshold based on thought's potential for insight
        insight_potential = self._estimate_insight_potential(thought)
        insight_adjustment = -0.3 * insight_potential  # Higher potential -> lower threshold
        
        # Calculate final adjusted threshold
        adjusted_threshold = threshold + load_adjustment + resource_adjustment + focus_adjustment + insight_adjustment
        
        # Ensure threshold is in valid range
        adjusted_threshold = max(0.1, min(0.9, adjusted_threshold))
        
        # Reflect if thought priority exceeds adjusted threshold
        should_reflect = thought.priority > adjusted_threshold
        
        logger.debug(f"Should reflect on thought {thought.id}: {should_reflect} (priority: {thought.priority}, threshold: {adjusted_threshold})")
        
        return should_reflect
    
    async def should_meta_reflect(self, reflections: List[Reflection], context: CognitiveContext) -> bool:
        """
        Determine if meta-reflection should be performed on a set of reflections.
        
        Args:
            reflections: The reflections to consider
            context: The cognitive context
            
        Returns:
            True if meta-reflection should be performed, False otherwise
        """
        # Need at least 3 reflections for meta-reflection
        if len(reflections) < 3:
            return False
        
        # Check cognitive load - meta-reflection is expensive
        if self.cognitive_load > 0.8:
            return False
        
        # Check for available reflection resources
        if self.resource_allocation["reflection"] < 0.2:
            return False
        
        # Check for potential contradictions or patterns in reflections
        has_contradictions = self._detect_reflection_contradictions(reflections)
        has_patterns = self._detect_reflection_patterns(reflections)
        
        # Meta-reflect if there are contradictions or patterns
        return has_contradictions or has_patterns
    
    def _update_cognitive_load(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Update the cognitive load metric with advanced estimation.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        # Get current load from context
        current_load = context.cognitive_load
        
        # Calculate active thoughts factor with diminishing returns
        active_thoughts_count = len(context.active_thoughts)
        active_thoughts_factor = 1.0 - math.exp(-0.05 * active_thoughts_count)
        
        # Calculate thought complexity factor
        thought_complexity = self._calculate_thought_complexity(thought)
        
        # Calculate cognitive diversity factor
        # Higher diversity of thought types increases load
        diversity_factor = self._calculate_thought_diversity(context.active_thoughts)
        
        # Calculate processing depth factor
        # Deeper processing (reflection, meta-reflection) increases load
        depth_factor = 0.0
        if reflection:
            depth_factor = 0.2
            if reflection.metadata.get("reflection_level", 1) > 1:
                # Meta-reflection
                depth_factor = 0.4
        
        # Calculate recency factor
        # More recent thoughts have higher impact on load
        recency_factor = self._calculate_recency_factor(thought)
        
        # Calculate new load with weighted factors
        new_load = (
            0.4 * current_load +            # 40% from current load
            0.2 * active_thoughts_factor +  # 20% from active thoughts
            0.15 * thought_complexity +     # 15% from thought complexity
            0.1 * diversity_factor +        # 10% from thought diversity
            0.1 * depth_factor +            # 10% from processing depth
            0.05 * recency_factor           # 5% from recency
        )
        
        # Apply cognitive efficiency adjustment
        efficiency = self.performance_metrics.get("adaptation_rate", 0.5)
        efficiency_adjustment = -0.1 * efficiency  # Higher efficiency reduces load
        
        new_load = new_load + efficiency_adjustment
        
        # Ensure load is in range [0.0, 1.0]
        self.cognitive_load = max(0.0, min(1.0, new_load))
    
    def _update_attention_allocation(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Update the attention allocation with optimization.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        # Extract focus areas from thought with enhanced extraction
        focus_areas = self._extract_focus_areas(thought)
        
        # Extract additional focus areas from reflection if available
        if reflection:
            reflection_focus_areas = self._extract_focus_areas_from_reflection(reflection)
            focus_areas.extend(reflection_focus_areas)
        
        # Prioritize focus areas based on relevance and importance
        prioritized_areas = self._prioritize_focus_areas(focus_areas, context)
        
        # Update focus duration for each area
        for area in prioritized_areas:
            if area in self.focus_duration:
                self.focus_duration[area] += 1
            else:
                self.focus_duration[area] = 1
        
        # Calculate optimal allocation based on prioritized areas
        total_priority = sum(1.0 / (i + 1) for i in range(len(prioritized_areas)))
        
        # Update attention allocation with priority weighting
        for i, area in enumerate(prioritized_areas):
            # Higher priority areas get more attention
            priority_weight = (1.0 / (i + 1)) / total_priority
            
            # Calculate allocation increase based on priority and duration
            duration_factor = min(1.0, self.focus_duration.get(area, 0) / 10)
            allocation_increase = 0.3 * priority_weight * (1.0 - 0.5 * duration_factor)
            
            # Increase allocation for this area
            current = self.attention_allocation.get(area, 0.0)
            self.attention_allocation[area] = min(1.0, current + allocation_increase)
        
        # Apply adaptive decay to other areas
        # Areas that have been in focus longer decay faster
        for area in list(self.attention_allocation.keys()):
            if area not in prioritized_areas:
                # Calculate decay rate based on duration
                duration = self.focus_duration.get(area, 0)
                base_decay = 0.9  # Base decay factor
                duration_decay = max(0.7, base_decay - 0.02 * duration)  # Longer duration -> faster decay
                
                self.attention_allocation[area] *= duration_decay
                
                # Remove areas with very low allocation
                if self.attention_allocation[area] < 0.05:
                    del self.attention_allocation[area]
                    if area in self.focus_duration:
                        del self.focus_duration[area]
        
        # Limit to optimal number of focus areas
        if len(self.attention_allocation) > self.optimal_focus_count:
            # Keep only the highest allocation areas
            sorted_areas = sorted(self.attention_allocation.items(), key=lambda x: x[1], reverse=True)
            for area, _ in sorted_areas[self.optimal_focus_count:]:
                del self.attention_allocation[area]
    
    def _extract_focus_areas(self, thought: Thought) -> List[str]:
        """
        Extract focus areas from a thought with improved extraction.
        
        Args:
            thought: The thought to extract focus areas from
            
        Returns:
            List of focus areas
        """
        focus_areas = []
        
        # Add thought type as a focus area
        focus_areas.append(thought.type)
        
        # Extract focus areas from metadata
        if "focus_areas" in thought.metadata:
            focus_areas.extend(thought.metadata["focus_areas"])
        
        # Extract focus areas from content using regex for better extraction
        # Find nouns and concepts (words of 5+ characters)
        content_lower = thought.content.lower()
        important_words = re.findall(r'\b[a-z]{5,}\b', content_lower)
        
        # Find noun phrases (simplified)
        noun_phrases = re.findall(r'\b(?:the|a|an)\s+[a-z]+\s+[a-z]{5,}\b', content_lower)
        
        # Add important words (limited to most relevant)
        # Count word frequency as a simple relevance metric
        word_counts = {}
        for word in important_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Add top words by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        focus_areas.extend([word for word, _ in sorted_words[:5]])
        
        # Add noun phrases
        for phrase in noun_phrases[:3]:
            # Extract the main noun from the phrase
            words = phrase.split()
            if len(words) >= 3:
                focus_areas.append(words[-1])  # Add the last word (likely the noun)
        
        return focus_areas
    
    def _extract_focus_areas_from_reflection(self, reflection: Reflection) -> List[str]:
        """
        Extract focus areas from a reflection.
        
        Args:
            reflection: The reflection to extract focus areas from
            
        Returns:
            List of focus areas
        """
        focus_areas = []
        
        # Extract from insights
        for insight in reflection.insights:
            # Find important terms in insights
            important_terms = re.findall(r'\b[a-z]{5,}\b', insight.lower())
            focus_areas.extend(important_terms[:2])  # Add up to 2 terms per insight
        
        # Extract from patterns if available
        if "patterns" in reflection.metadata:
            patterns = reflection.metadata["patterns"]
            focus_areas.extend(patterns)
        
        # Extract from contradictions if available
        if "contradictions" in reflection.metadata:
            contradictions = reflection.metadata["contradictions"]
            for _, reason in contradictions:
                # Extract key terms from contradiction reasons
                terms = re.findall(r'\b[a-z]{5,}\b', reason.lower())
                focus_areas.extend(terms[:1])  # Add up to 1 term per contradiction
        
        return focus_areas
    
    def _prioritize_focus_areas(self, focus_areas: List[str], context: CognitiveContext) -> List[str]:
        """
        Prioritize focus areas based on relevance and importance.
        
        Args:
            focus_areas: List of focus areas
            context: The cognitive context
            
        Returns:
            Prioritized list of focus areas
        """
        # Remove duplicates while preserving order
        unique_areas = []
        seen = set()
        for area in focus_areas:
            if area not in seen:
                unique_areas.append(area)
                seen.add(area)
        
        # Calculate priority scores for each area
        area_scores = {}
        for area in unique_areas:
            score = 0.0
            
            # Higher score for areas related to attention focus
            if context.attention_focus and area.lower() in context.attention_focus.lower():
                score += 2.0
            
            # Higher score for areas with existing allocation
            if area in self.attention_allocation:
                score += self.attention_allocation[area]
            
            # Higher score for areas related to active thoughts
            if any(area.lower() in active_id.lower() for active_id in context.active_thoughts):
                score += 1.0
            
            # Higher score for recurring themes
            if area in self.recurring_themes:
                score += self.recurring_themes[area]
            
            # Lower score for areas that have been in focus for too long
            duration_penalty = min(0.5, 0.1 * self.focus_duration.get(area, 0))
            score -= duration_penalty
            
            area_scores[area] = score
        
        # Sort areas by score
        prioritized_areas = sorted(unique_areas, key=lambda a: area_scores.get(a, 0.0), reverse=True)
        
        return prioritized_areas
    
    def _store_state_in_history(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Store the current state in history with enhanced information.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        # Create state snapshot with enhanced information
        state = {
            "timestamp": time.time(),
            "cognitive_load": self.cognitive_load,
            "attention_allocation": self.attention_allocation.copy(),
            "resource_allocation": self.resource_allocation.copy(),
            "performance_metrics": self.performance_metrics.copy(),
            "thought_id": thought.id,
            "thought_type": thought.type,
            "thought_priority": thought.priority,
            "thought_complexity": self._calculate_thought_complexity(thought),
            "reflection_id": reflection.id if reflection else None,
            "reflection_insights_count": len(reflection.insights) if reflection and hasattr(reflection, 'insights') else 0,
            "active_thoughts_count": len(context.active_thoughts),
            "active_thoughts": list(context.active_thoughts),
            "attention_focus": context.attention_focus,
            "recurring_themes": {k: v for k, v in self.recurring_themes.items() if v > 0.3}
        }
        
        # Add to history
        self.state_history.append(state)
        
        # Trim history if needed
        if len(self.state_history) > self.max_history_size:
            self.state_history = self.state_history[-self.max_history_size:]
    
    def _calculate_thought_complexity(self, thought: Thought) -> float:
        """
        Calculate the complexity of a thought.
        
        Args:
            thought: The thought to analyze
            
        Returns:
            Complexity score (0.0 to 1.0)
        """
        # Base complexity on content length
        content_length = len(thought.content)
        length_factor = min(1.0, content_length / 500)  # Normalize to [0, 1]
        
        # Analyze sentence structure
        sentences = re.split(r'[.!?]', thought.content)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        sentence_factor = min(1.0, avg_sentence_length / 20)  # Normalize to [0, 1]
        
        # Analyze vocabulary complexity
        complex_words = re.findall(r'\b[a-z]{8,}\b', thought.content.lower())
        vocabulary_factor = min(1.0, len(complex_words) / 10)  # Normalize to [0, 1]
        
        # Consider thought type complexity
        type_complexity = {
            "general": 0.3,
            "question": 0.4,
            "hypothesis": 0.7,
            "insight": 0.6,
            "meta_reflection": 0.9
        }
        type_factor = type_complexity.get(thought.type, 0.5)
        
        # Calculate weighted complexity
        complexity = (
            0.3 * length_factor +
            0.2 * sentence_factor +
            0.2 * vocabulary_factor +
            0.3 * type_factor
        )
        
        return complexity
    
    def _calculate_thought_diversity(self, active_thought_ids: List[str]) -> float:
        """
        Calculate the diversity of active thoughts.
        
        Args:
            active_thought_ids: List of active thought IDs
            
        Returns:
            Diversity score (0.0 to 1.0)
        """
        if not active_thought_ids or len(active_thought_ids) < 2:
            return 0.0
        
        # Count thought types
        type_counts = {}
        for thought_id in active_thought_ids:
            # In a real implementation, we would retrieve the thought
            # For now, extract type from ID (simplified)
            thought_type = "general"  # Default
            
            if self.state_history:
                # Get type from history if available
                for state in reversed(self.state_history):
                    if state.get("thought_id") == thought_id:
                        thought_type = state.get("thought_type", "general")
                        break
            
            type_counts[thought_type] = type_counts.get(thought_type, 0) + 1
        
        # Calculate diversity using normalized entropy
        total = len(active_thought_ids)
        entropy = 0.0
        for count in type_counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        # Normalize to [0, 1]
        max_entropy = math.log2(len(type_counts))
        if max_entropy > 0:
            normalized_diversity = entropy / max_entropy
        else:
            normalized_diversity = 0.0
        
        return normalized_diversity
    
    def _calculate_recency_factor(self, thought: Thought) -> float:
        """
        Calculate the recency factor for a thought.
        
        Args:
            thought: The thought to analyze
            
        Returns:
            Recency factor (0.0 to 1.0)
        """
        # Get creation time from thought or use current time
        creation_time = getattr(thought, "created_at", time.time())
        current_time = time.time()
        
        # Calculate time since creation in seconds
        time_diff = max(0, current_time - creation_time)
        
        # Apply exponential decay
        recency = math.exp(-0.0001 * time_diff)  # Decay factor
        
        return recency
    
    def _update_performance_metrics(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Update performance metrics based on current cognitive process.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        # Update reflection quality if reflection is available
        if reflection:
            # Assess reflection quality based on insights count and diversity
            insight_count = len(reflection.insights)
            
            # Calculate insight diversity (simplified)
            insight_diversity = 0.0
            if insight_count > 1:
                # Extract key terms from insights
                all_terms = []
                for insight in reflection.insights:
                    terms = re.findall(r'\b[a-z]{5,}\b', insight.lower())
                    all_terms.extend(terms)
                
                # Count unique terms
                unique_terms = len(set(all_terms))
                total_terms = len(all_terms)
                
                if total_terms > 0:
                    insight_diversity = unique_terms / total_terms
            
            # Calculate reflection quality
            reflection_quality = min(1.0, (0.1 * insight_count + 0.5 * insight_diversity))
            
            # Update metric with learning rate
            self.performance_metrics["reflection_quality"] = (
                (1 - self.learning_rate) * self.performance_metrics["reflection_quality"] +
                self.learning_rate * reflection_quality
            )
        
        # Update thought coherence
        if len(self.state_history) > 1:
            # Calculate coherence between this thought and previous thoughts
            coherence = self._calculate_thought_coherence(thought, context)
            
            # Update metric with learning rate
            self.performance_metrics["thought_coherence"] = (
                (1 - self.learning_rate) * self.performance_metrics["thought_coherence"] +
                self.learning_rate * coherence
            )
        
        # Update adaptation rate
        if len(self.adaptation_history) > 1:
            # Calculate rate of change in resource allocation
            adaptation_rate = self._calculate_adaptation_rate()
            
            # Update metric with learning rate
            self.performance_metrics["adaptation_rate"] = (
                (1 - self.learning_rate) * self.performance_metrics["adaptation_rate"] +
                self.learning_rate * adaptation_rate
            )
    
    def _calculate_thought_coherence(self, thought: Thought, context: CognitiveContext) -> float:
        """
        Calculate coherence between the current thought and previous thoughts.
        
        Args:
            thought: The current thought
            context: The cognitive context
            
        Returns:
            Coherence score (0.0 to 1.0)
        """
        if not self.state_history or len(context.active_thoughts) < 2:
            return 0.5  # Default
        
        # Get content of current thought
        current_content = thought.content.lower()
        
        # Get content of previous thoughts (simplified)
        # In a real implementation, we would retrieve the actual thoughts
        previous_contents = []
        for state in reversed(self.state_history[-5:]):  # Consider last 5 states
            if state.get("thought_id") != thought.id:
                # Use a placeholder for previous thought content
                previous_content = f"Content of thought {state.get('thought_id')}"
                previous_contents.append(previous_content.lower())
        
        if not previous_contents:
            return 0.5  # Default
        
        # Calculate content similarity (simplified)
        similarities = []
        for prev_content in previous_contents:
            # Extract words from both contents
            current_words = set(re.findall(r'\b[a-z]{4,}\b', current_content))
            prev_words = set(re.findall(r'\b[a-z]{4,}\b', prev_content))
            
            # Calculate Jaccard similarity
            if current_words and prev_words:
                intersection = len(current_words.intersection(prev_words))
                union = len(current_words.union(prev_words))
                similarity = intersection / union
                similarities.append(similarity)
        
        # Calculate average similarity
        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
        else:
            avg_similarity = 0.0
        
        return avg_similarity
    
    def _adapt_resource_allocation(self) -> None:
        """
        Adapt resource allocation based on performance metrics.
        """
        # Store current allocation in adaptation history
        adaptation_record = {
            "timestamp": time.time(),
            "resource_allocation": self.resource_allocation.copy(),
            "performance_metrics": self.performance_metrics.copy()
        }
        
        self.adaptation_history.append(adaptation_record)
        
        # Trim history if needed
        if len(self.adaptation_history) > self.max_adaptation_history:
            self.adaptation_history = self.adaptation_history[-self.max_adaptation_history:]
        
        # Adjust resource allocation based on performance trends
        if len(self.adaptation_history) >= 3:
            # Calculate performance trends
            reflection_trend = self._calculate_performance_trend("reflection_quality")
            ideation_trend = self._calculate_performance_trend("ideation_quality")
            coherence_trend = self._calculate_performance_trend("thought_coherence")
            
            # Adjust resources based on trends
            if reflection_trend < -0.1:  # Declining reflection quality
                # Increase reflection resources
                self.resource_allocation["reflection"] = min(0.5, self.resource_allocation["reflection"] + 0.05)
            elif reflection_trend > 0.1:  # Improving reflection quality
                # Can reduce reflection resources
                self.resource_allocation["reflection"] = max(0.1, self.resource_allocation["reflection"] - 0.03)
            
            if ideation_trend < -0.1:  # Declining ideation quality
                # Increase ideation resources
                self.resource_allocation["ideation"] = min(0.5, self.resource_allocation["ideation"] + 0.05)
            elif ideation_trend > 0.1:  # Improving ideation quality
                # Can reduce ideation resources
                self.resource_allocation["ideation"] = max(0.1, self.resource_allocation["ideation"] - 0.03)
            
            if coherence_trend < -0.1:  # Declining thought coherence
                # Increase perception resources
                self.resource_allocation["perception"] = min(0.4, self.resource_allocation["perception"] + 0.05)
            
            # Normalize allocations to ensure they sum to 1.0
            total = sum(self.resource_allocation.values())
            if total > 0:
                for key in self.resource_allocation:
                    self.resource_allocation[key] /= total
    
    def _calculate_performance_trend(self, metric_name: str) -> float:
        """
        Calculate trend in a performance metric.
        
        Args:
            metric_name: Name of the performance metric
            
        Returns:
            Trend value (-1.0 to 1.0, positive means improving)
        """
        if len(self.adaptation_history) < 3:
            return 0.0  # No trend
        
        # Get metric values from history
        values = []
        for record in self.adaptation_history[-3:]:
            if metric_name in record["performance_metrics"]:
                values.append(record["performance_metrics"][metric_name])
        
        if len(values) < 3:
            return 0.0  # Insufficient data
        
        # Calculate trend using linear regression slope (simplified)
        x = [0, 1, 2]  # Time points
        y = values
        
        # Calculate slope using least squares
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_xx = sum(x[i] * x[i] for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        
        return slope
    
    def _recognize_thought_patterns(self, thought: Thought) -> None:
        """
        Recognize patterns in thoughts.
        
        Args:
            thought: The current thought
        """
        # Extract key concepts from thought
        content_lower = thought.content.lower()
        concepts = set(re.findall(r'\b[a-z]{5,}\b', content_lower))
        
        # Update recurring themes
        for concept in concepts:
            if concept in self.recurring_themes:
                # Increase strength of recurring theme
                self.recurring_themes[concept] = min(1.0, self.recurring_themes[concept] + 0.2)
            else:
                # Add new theme with low initial strength
                self.recurring_themes[concept] = 0.2
        
        # Decay strength of themes not present in current thought
        for theme in list(self.recurring_themes.keys()):
            if theme not in concepts:
                self.recurring_themes[theme] *= 0.9
                
                # Remove themes with very low strength
                if self.recurring_themes[theme] < 0.1:
                    del self.recurring_themes[theme]
        
        # Identify thought patterns
        self._identify_thought_patterns(thought)
    
    def _identify_thought_patterns(self, thought: Thought) -> None:
        """
        Identify patterns in thought content and structure.
        
        Args:
            thought: The thought to analyze
        """
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
            (r'\bsimilar\s+to\s+\w+', "similarity_observation")
        ]
        
        # Check each pattern
        for pattern_regex, pattern_name in pattern_rules:
            if re.search(pattern_regex, content_lower):
                if pattern_name not in self.thought_patterns:
                    self.thought_patterns[pattern_name] = []
                
                if thought.id not in self.thought_patterns[pattern_name]:
                    self.thought_patterns[pattern_name].append(thought.id)
    
    def _learn_from_cognitive_cycle(self, thought: Thought, reflection: Optional[Reflection], context: CognitiveContext) -> None:
        """
        Learn from the current cognitive cycle to improve future processing.
        
        Args:
            thought: The current thought
            reflection: Optional reflection on the thought
            context: The cognitive context
        """
        # Adjust reflection thresholds based on success patterns
        if reflection and hasattr(reflection, 'insights') and reflection.insights:
            # If reflection produced valuable insights, adjust threshold
            if len(reflection.insights) >= 3:
                # Lower threshold for this thought type to encourage more reflection
                current_threshold = self.reflection_thresholds.get(thought.type, self.reflection_thresholds["general"])
                adjusted_threshold = max(0.1, current_threshold - 0.05)
                self.reflection_thresholds[thought.type] = adjusted_threshold
        
        # Adjust optimal focus count based on cognitive load and performance
        if self.cognitive_load > 0.8 and self.optimal_focus_count > 2:
            # High load, reduce optimal focus count
            self.optimal_focus_count -= 1
        elif self.cognitive_load < 0.3 and self.optimal_focus_count < 5:
            # Low load, increase optimal focus count
            self.optimal_focus_count += 1
        
        # Adjust learning rate based on performance stability
        if len(self.adaptation_history) >= 5:
            # Calculate performance stability
            performance_values = [
                record["performance_metrics"]["thought_coherence"]
                for record in self.adaptation_history[-5:]
                if "thought_coherence" in record["performance_metrics"]
            ]
            
            if len(performance_values) > 1:
                stability = 1.0 - statistics.stdev(performance_values)
                
                # Adjust learning rate based on stability
                if stability > 0.8:
                    # Stable performance, decrease learning rate
                    self.learning_rate = max(0.05, self.learning_rate - 0.01)
                elif stability < 0.3:
                    # Unstable performance, increase learning rate
                    self.learning_rate = min(0.3, self.learning_rate + 0.02)
    
    def _detect_reflection_contradictions(self, reflections: List[Reflection]) -> bool:
        """
        Detect contradictions between reflections.
        
        Args:
            reflections: List of reflections to check
            
        Returns:
            True if contradictions are detected, False otherwise
        """
        if len(reflections) < 2:
            return False
        
        # Extract insights from all reflections
        all_insights = []
        for reflection in reflections:
            if hasattr(reflection, 'insights'):
                all_insights.extend([(reflection.id, insight) for insight in reflection.insights])
        
        # Check for contradictory insights (simplified)
        for i, (r1_id, insight1) in enumerate(all_insights):
            for r2_id, insight2 in all_insights[i+1:]:
                if r1_id != r2_id:  # Only check between different reflections
                    # Check for direct contradictions (simplified)
                    if self._are_insights_contradictory(insight1, insight2):
                        return True
        
        return False
    
    def _detect_reflection_patterns(self, reflections: List[Reflection]) -> bool:
        """
        Detect patterns across reflections.
        
        Args:
            reflections: List of reflections to check
            
        Returns:
            True if patterns are detected, False otherwise
        """
        if len(reflections) < 3:
            return False
        
        # Check for recurring themes in insights
        all_terms = []
        for reflection in reflections:
            if hasattr(reflection, 'insights'):
                for insight in reflection.insights:
                    terms = re.findall(r'\b[a-z]{5,}\b', insight.lower())
                    all_terms.extend(terms)
        
        # Count term frequencies
        term_counts = {}
        for term in all_terms:
            term_counts[term] = term_counts.get(term, 0) + 1
        
        # Check for recurring terms (appearing in multiple reflections)
        recurring_terms = [term for term, count in term_counts.items() if count >= 3]
        
        return len(recurring_terms) > 0
    
    def _estimate_insight_potential(self, thought: Thought) -> float:
        """
        Estimate the potential for generating insights from a thought.
        
        Args:
            thought: The thought to analyze
            
        Returns:
            Insight potential (0.0 to 1.0)
        """
        # Base potential on thought type
        type_potential = {
            "question": 0.7,
            "hypothesis": 0.8,
            "insight": 0.6,
            "general": 0.4
        }
        base_potential = type_potential.get(thought.type, 0.5)
        
        # Adjust based on content complexity
        complexity = self._calculate_thought_complexity(thought)
        complexity_adjustment = 0.2 * complexity  # More complex thoughts have higher potential
        
        # Adjust based on novelty (approximated by checking recurring themes)
        content_lower = thought.content.lower()
        concepts = set(re.findall(r'\b[a-z]{5,}\b', content_lower))
        recurring_concepts = [c for c in concepts if c in self.recurring_themes]
        
        novelty_adjustment = 0.0
        if recurring_concepts and concepts:
            # Less novel thoughts have lower potential for new insights
            novelty_adjustment = -0.1 * min(1.0, len(recurring_concepts) / len(concepts))
        else:
            # Highly novel thoughts have higher potential
            novelty_adjustment = 0.2
        
        # Calculate final potential
        potential = base_potential + complexity_adjustment + novelty_adjustment
        
        # Ensure potential is in range [0.0, 1.0]
        return max(0.0, min(1.0, potential))
    
    def _are_insights_contradictory(self, insight1: str, insight2: str) -> bool:
        """
        Check if two insights are contradictory.
        
        Args:
            insight1: First insight
            insight2: Second insight
            
        Returns:
            True if insights are contradictory, False otherwise
        """
        # Simplified contradiction detection
        # In a real implementation, this would use more sophisticated NLP
        
        # Check for direct negation
        insight1_lower = insight1.lower()
        insight2_lower = insight2.lower()
        
        # Look for opposite statements
        negation_pairs = [
            ("increases", "decreases"),
            ("higher", "lower"),
            ("more", "less"),
            ("positive", "negative"),
            ("should", "should not"),
            ("can", "cannot"),
            ("always", "never"),
            ("true", "false")
        ]
        
        for pos, neg in negation_pairs:
            if pos in insight1_lower and neg in insight2_lower:
                return True
            if neg in insight1_lower and pos in insight2_lower:
                return True
        
        return False