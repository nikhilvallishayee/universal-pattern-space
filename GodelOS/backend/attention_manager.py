"""
Attention Manager for GödelOS

Handles dynamic attention allocation and focus switching.
"""

import time
import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AttentionManager:
    def __init__(self):
        self.current_focus = None
        self.attention_history = []
        self.focus_weights = {}
        self.switch_threshold = 0.3
        self.attention_breadth = 1.0
        self.focus_strength = 0.5
        
    async def update_attention(self, query: str, context: Dict = None) -> Dict:
        """Update attention focus based on query"""
        new_focus = self._determine_focus(query)
        previous_focus = self.current_focus
        
        attention_shift_detected = False
        if self.current_focus and self.current_focus != new_focus:
            attention_shift_detected = True
            self._record_attention_switch(self.current_focus, new_focus)
            logger.info(f"Attention shift: {self.current_focus} -> {new_focus}")
        
        self.current_focus = new_focus
        self.focus_strength = self._calculate_focus_strength(query)
        self.attention_breadth = self._calculate_attention_breadth(query)
        
        return {
            "current_focus": new_focus,
            "previous_focus": previous_focus,
            "attention_shift_detected": attention_shift_detected,
            "focus_strength": self.focus_strength,
            "attention_breadth": self.attention_breadth,
            "switch_count": len(self.attention_history),
            "focus_duration": self._calculate_focus_duration()
        }
    
    def _determine_focus(self, query: str) -> str:
        """Determine attention focus from query content"""
        focus_keywords = {
            "technical": ["algorithm", "system", "technical", "implementation", "code", "function", "method"],
            "philosophical": ["consciousness", "mind", "think", "believe", "philosophy", "existence", "meaning"],
            "personal": ["you", "your", "yourself", "feeling", "experience", "remember", "favorite"],
            "factual": ["what", "when", "where", "who", "fact", "definition", "explain", "describe"],
            "creative": ["imagine", "create", "novel", "artistic", "design", "innovative", "original"],
            "analytical": ["analyze", "compare", "evaluate", "assess", "reason", "logic", "determine"],
            "mathematical": ["calculate", "equation", "number", "formula", "solve", "mathematics"],
            "social": ["people", "society", "relationship", "community", "culture", "social"],
            "temporal": ["time", "history", "future", "past", "when", "duration", "chronology"],
            "spatial": ["location", "place", "geography", "space", "position", "distance"]
        }
        
        query_lower = query.lower()
        focus_scores = {}
        
        for focus_type, keywords in focus_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            # Boost score for exact matches
            exact_matches = sum(1 for keyword in keywords if f" {keyword} " in f" {query_lower} ")
            score += exact_matches * 2
            
            if score > 0:
                focus_scores[focus_type] = score
        
        if focus_scores:
            return max(focus_scores, key=focus_scores.get)
        
        return "general"
    
    def _calculate_focus_strength(self, query: str) -> float:
        """Calculate how focused the attention is (0-1)"""
        # Longer, more specific queries tend to have stronger focus
        query_length_factor = min(1.0, len(query.split()) / 20)
        
        # Technical terms and specific vocabulary indicate stronger focus
        technical_indicators = len(re.findall(r'\b[A-Z][a-z]*[A-Z][a-z]*\b', query))  # CamelCase
        specific_indicators = len(re.findall(r'\b\w{8,}\b', query))  # Long words
        
        specificity_factor = min(1.0, (technical_indicators + specific_indicators) / 10)
        
        # Questions with multiple aspects have weaker focus
        question_count = query.count('?')
        conjunction_count = len(re.findall(r'\b(and|or|but|also|however)\b', query.lower()))
        
        complexity_penalty = min(0.5, (question_count + conjunction_count) * 0.1)
        
        focus_strength = (query_length_factor + specificity_factor) / 2 - complexity_penalty
        return max(0.1, min(1.0, focus_strength))
    
    def _calculate_attention_breadth(self, query: str) -> float:
        """Calculate breadth of attention (how many topics are being considered)"""
        # Count different types of concepts mentioned
        concept_types = [
            "abstract", "concrete", "temporal", "spatial", "emotional", 
            "logical", "creative", "technical", "social", "personal"
        ]
        
        breadth_indicators = {
            "abstract": ["concept", "idea", "theory", "principle", "philosophy"],
            "concrete": ["object", "thing", "item", "physical", "material"],
            "temporal": ["time", "when", "history", "future", "past", "moment"],
            "spatial": ["where", "location", "place", "position", "space"],
            "emotional": ["feel", "emotion", "mood", "sentiment", "affect"],
            "logical": ["because", "therefore", "logic", "reason", "proof"],
            "creative": ["imagine", "create", "artistic", "novel", "innovative"],
            "technical": ["system", "process", "method", "algorithm", "technical"],
            "social": ["people", "society", "relationship", "community", "group"],
            "personal": ["I", "me", "my", "personal", "individual", "self"]
        }
        
        query_lower = query.lower()
        active_types = 0
        
        for concept_type, indicators in breadth_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                active_types += 1
        
        # Normalize to 0-1 scale
        max_types = len(concept_types)
        breadth = active_types / max_types
        
        # Boost breadth for queries with multiple questions or complex conjunctions
        complexity_boost = min(0.3, len(re.findall(r'\?|,|;', query)) * 0.1)
        
        return min(1.0, breadth + complexity_boost)
    
    def _record_attention_switch(self, old_focus: str, new_focus: str):
        """Record attention switch event"""
        switch_event = {
            "timestamp": time.time(),
            "from_focus": old_focus,
            "to_focus": new_focus,
            "switch_speed": self._calculate_switch_speed(),
            "context_preserved": self._assess_context_preservation(old_focus, new_focus)
        }
        self.attention_history.append(switch_event)
        
        # Update focus weights
        self.focus_weights[new_focus] = self.focus_weights.get(new_focus, 0) + 1
        
        # Keep only recent history
        if len(self.attention_history) > 100:
            self.attention_history = self.attention_history[-50:]
    
    def _calculate_switch_speed(self) -> float:
        """Calculate how quickly attention switches are happening"""
        if len(self.attention_history) < 2:
            return 0.5
        
        recent_switches = self.attention_history[-5:]  # Last 5 switches
        if len(recent_switches) < 2:
            return 0.5
        
        time_deltas = []
        for i in range(1, len(recent_switches)):
            delta = recent_switches[i]["timestamp"] - recent_switches[i-1]["timestamp"]
            time_deltas.append(delta)
        
        avg_delta = sum(time_deltas) / len(time_deltas)
        
        # Faster switches (smaller deltas) = higher switch speed
        # Normalize: 1 second = very fast (1.0), 60 seconds = slow (0.1)
        switch_speed = max(0.1, min(1.0, 1.0 / (avg_delta + 1)))
        return switch_speed
    
    def _assess_context_preservation(self, old_focus: str, new_focus: str) -> float:
        """Assess how much context is preserved during attention switch"""
        # Related focuses preserve more context
        focus_relationships = {
            "technical": ["analytical", "mathematical", "factual"],
            "philosophical": ["analytical", "personal", "creative"],
            "personal": ["social", "emotional", "philosophical"],
            "factual": ["technical", "analytical", "temporal"],
            "creative": ["philosophical", "artistic", "innovative"],
            "analytical": ["technical", "logical", "mathematical"],
            "mathematical": ["technical", "analytical", "logical"],
            "social": ["personal", "cultural", "temporal"],
            "temporal": ["factual", "historical", "social"],
            "spatial": ["factual", "technical", "geographical"]
        }
        
        if old_focus in focus_relationships:
            related_focuses = focus_relationships[old_focus]
            if new_focus in related_focuses:
                return 0.8  # High context preservation
            else:
                return 0.3  # Low context preservation
        
        return 0.5  # Medium context preservation
    
    def _calculate_focus_duration(self) -> float:
        """Calculate how long current focus has been maintained"""
        if not self.attention_history:
            return 0.0
        
        last_switch = self.attention_history[-1]["timestamp"]
        current_time = time.time()
        duration = current_time - last_switch
        
        return duration
    
    def get_attention_metrics(self) -> Dict[str, Any]:
        """Get comprehensive attention metrics"""
        return {
            "current_focus": self.current_focus,
            "focus_strength": self.focus_strength,
            "attention_breadth": self.attention_breadth,
            "total_switches": len(self.attention_history),
            "focus_weights": self.focus_weights.copy(),
            "recent_switches": self.attention_history[-5:] if self.attention_history else [],
            "switch_speed": self._calculate_switch_speed(),
            "focus_duration": self._calculate_focus_duration(),
            "context_preservation_avg": self._calculate_avg_context_preservation()
        }
    
    def _calculate_avg_context_preservation(self) -> float:
        """Calculate average context preservation across recent switches"""
        if not self.attention_history:
            return 0.5
        
        recent_switches = self.attention_history[-10:]  # Last 10 switches
        if not recent_switches:
            return 0.5
        
        preservation_scores = [switch.get("context_preserved", 0.5) for switch in recent_switches]
        return sum(preservation_scores) / len(preservation_scores)

# Global instance
attention_manager = AttentionManager()
