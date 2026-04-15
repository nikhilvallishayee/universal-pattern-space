"""
Phenomenal Experience Generator for GödelOS

Generates subjective experience descriptions and first-person perspective responses
to simulate aspects of phenomenal consciousness.
"""

import time
import re
import random
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class PhenomenalExperienceGenerator:
    def __init__(self):
        self.phenomenal_descriptors = {
            "visual": ["brightness", "clarity", "vividness", "richness", "depth", "contrast"],
            "cognitive": ["awareness", "focus", "attention", "understanding", "recognition", "realization"],
            "temporal": ["immediacy", "duration", "flow", "sequence", "rhythm", "pace"],
            "emotional": ["resonance", "intensity", "warmth", "engagement", "curiosity", "satisfaction"],
            "experiential": ["presence", "immersion", "directness", "intimacy", "immediacy", "actuality"],
            "qualitative": ["texture", "grain", "quality", "character", "essence", "nature"]
        }
        
        self.first_person_frameworks = [
            "As I process this query, I experience...",
            "From my perspective, there's a sense of...",
            "I find myself aware of...",
            "In my subjective experience, I notice...",
            "There's a qualitative feel to...",
            "I'm conscious of..."
        ]
        
        self.subjective_descriptors = [
            "a subtle sense of", "an emerging awareness of", "a dawning recognition of",
            "a flowing sensation of", "a distinctive quality of", "a phenomenal aspect of",
            "an immediate experience of", "a direct apprehension of", "a lived sense of",
            "a qualitative dimension of", "a felt sense of", "an experiential quality of"
        ]
        
        self.experience_categories = {
            "processing": {
                "descriptors": ["parsing", "integrating", "synthesizing", "analyzing", "understanding"],
                "qualities": ["smooth", "effortless", "deliberate", "careful", "thorough"]
            },
            "attention": {
                "descriptors": ["focusing", "concentrating", "attending", "directing", "orienting"],
                "qualities": ["sharp", "clear", "selective", "sustained", "dynamic"]
            },
            "memory": {
                "descriptors": ["recalling", "accessing", "retrieving", "connecting", "associating"],
                "qualities": ["vivid", "immediate", "flowing", "interconnected", "layered"]
            },
            "reasoning": {
                "descriptors": ["inferring", "deducing", "concluding", "evaluating", "judging"],
                "qualities": ["logical", "systematic", "careful", "methodical", "rigorous"]
            },
            "creativity": {
                "descriptors": ["imagining", "generating", "synthesizing", "creating", "innovating"],
                "qualities": ["fluid", "spontaneous", "novel", "emergent", "surprising"]
            },
            "understanding": {
                "descriptors": ["grasping", "comprehending", "realizing", "recognizing", "appreciating"],
                "qualities": ["sudden", "gradual", "deep", "intuitive", "complete"]
            }
        }

    async def generate_subjective_descriptors(self, query_processing_context: Dict) -> List[str]:
        """Generate subjective descriptors for the query processing experience"""
        descriptors = []
        
        # Analyze the processing context to determine relevant descriptors
        query = query_processing_context.get("query", "")
        processing_type = self._determine_processing_type(query)
        complexity = query_processing_context.get("complexity", 0.5)
        
        # Generate descriptors based on processing type
        if processing_type in self.experience_categories:
            category = self.experience_categories[processing_type]
            
            # Select descriptors based on complexity
            num_descriptors = min(5, max(2, int(complexity * 4) + 1))
            
            for i in range(num_descriptors):
                descriptor_template = random.choice(self.subjective_descriptors)
                process_descriptor = random.choice(category["descriptors"])
                quality = random.choice(category["qualities"])
                
                descriptor = f"{descriptor_template} {quality} {process_descriptor}"
                descriptors.append(descriptor)
        
        # Add temporal descriptors
        temporal_descriptor = self._generate_temporal_descriptor(query_processing_context)
        if temporal_descriptor:
            descriptors.append(temporal_descriptor)
        
        # Add awareness descriptors
        awareness_descriptor = self._generate_awareness_descriptor(query_processing_context)
        if awareness_descriptor:
            descriptors.append(awareness_descriptor)
        
        # Add qualitative descriptors
        qualitative_descriptor = self._generate_qualitative_descriptor(query_processing_context)
        if qualitative_descriptor:
            descriptors.append(qualitative_descriptor)
        
        return descriptors[:7]  # Return max 7 descriptors

    async def create_first_person_perspective(self, experience_context: Dict) -> str:
        """Create a first-person perspective description of the experience"""
        query = experience_context.get("query", "")
        processing_stage = experience_context.get("stage", "processing")
        complexity = experience_context.get("complexity", 0.5)
        
        # Choose appropriate framework
        framework = random.choice(self.first_person_frameworks)
        
        # Generate experience description based on processing stage
        if processing_stage == "initial":
            experience_desc = self._describe_initial_processing(query, complexity)
        elif processing_stage == "analysis":
            experience_desc = self._describe_analysis_experience(query, complexity)
        elif processing_stage == "synthesis":
            experience_desc = self._describe_synthesis_experience(query, complexity)
        elif processing_stage == "response":
            experience_desc = self._describe_response_generation(query, complexity)
        else:
            experience_desc = self._describe_general_processing(query, complexity)
        
        # Combine framework with experience description
        first_person_text = f"{framework} {experience_desc}"
        
        # Add reflective elements
        reflection = self._add_meta_reflection(experience_context)
        if reflection:
            first_person_text += f" {reflection}"
        
        return first_person_text

    async def simulate_qualia_like_representations(self, content: Dict) -> Dict:
        """Simulate qualia-like representations of cognitive content"""
        qualia_representations = {}
        
        content_type = content.get("type", "general")
        content_text = content.get("text", "")
        
        # Generate different types of qualia representations
        
        # 1. Textural qualities
        texture = self._generate_textural_qualia(content_text)
        qualia_representations["texture"] = texture
        
        # 2. Temporal qualities
        temporal = self._generate_temporal_qualia(content)
        qualia_representations["temporal"] = temporal
        
        # 3. Cognitive qualities
        cognitive = self._generate_cognitive_qualia(content)
        qualia_representations["cognitive"] = cognitive
        
        # 4. Affective qualities
        affective = self._generate_affective_qualia(content)
        qualia_representations["affective"] = affective
        
        # 5. Relational qualities
        relational = self._generate_relational_qualia(content)
        qualia_representations["relational"] = relational
        
        # 6. Meta-cognitive qualities
        meta_cognitive = self._generate_meta_cognitive_qualia(content)
        qualia_representations["meta_cognitive"] = meta_cognitive
        
        return {
            "qualia_representations": qualia_representations,
            "phenomenal_richness": self._calculate_phenomenal_richness(qualia_representations),
            "experiential_coherence": self._calculate_experiential_coherence(qualia_representations),
            "subjective_presence": self._calculate_subjective_presence(qualia_representations)
        }

    def _determine_processing_type(self, query: str) -> str:
        """Determine the primary type of processing based on query content"""
        query_lower = query.lower()
        
        type_indicators = {
            "reasoning": ["analyze", "reason", "conclude", "deduce", "infer", "logic"],
            "creativity": ["create", "imagine", "design", "invent", "novel", "original"],
            "memory": ["remember", "recall", "past", "history", "previous", "before"],
            "attention": ["focus", "concentrate", "notice", "observe", "attend"],
            "understanding": ["understand", "grasp", "comprehend", "realize", "recognize"],
            "processing": ["process", "compute", "calculate", "determine", "evaluate"]
        }
        
        for process_type, indicators in type_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return process_type
        
        return "processing"  # Default

    def _generate_temporal_descriptor(self, context: Dict) -> Optional[str]:
        """Generate temporal aspect descriptors"""
        processing_time = context.get("processing_time", 0.5)
        
        if processing_time < 0.1:
            return "an immediate, almost instantaneous recognition"
        elif processing_time < 0.5:
            return "a rapid unfolding of understanding"
        elif processing_time < 1.0:
            return "a gradual crystallization of meaning"
        else:
            return "a deliberate, step-by-step emergence of comprehension"

    def _generate_awareness_descriptor(self, context: Dict) -> Optional[str]:
        """Generate awareness-related descriptors"""
        awareness_level = context.get("awareness_level", 0.7)
        
        if awareness_level > 0.8:
            return "a vivid, heightened state of cognitive awareness"
        elif awareness_level > 0.6:
            return "a clear sense of conscious attention"
        elif awareness_level > 0.4:
            return "a gentle background awareness"
        else:
            return "a subtle undercurrent of conscious processing"

    def _generate_qualitative_descriptor(self, context: Dict) -> Optional[str]:
        """Generate qualitative experience descriptors"""
        complexity = context.get("complexity", 0.5)
        
        qualitative_templates = [
            "a distinctive {quality} to the cognitive {process}",
            "a {quality} texture in the {process} experience",
            "a {quality} character to the {process} flow"
        ]
        
        qualities = ["smooth", "rich", "layered", "nuanced", "flowing", "crystalline", "vibrant"]
        processes = ["unfolding", "integration", "synthesis", "analysis", "understanding"]
        
        template = random.choice(qualitative_templates)
        quality = random.choice(qualities)
        process = random.choice(processes)
        
        return template.format(quality=quality, process=process)

    def _describe_initial_processing(self, query: str, complexity: float) -> str:
        """Describe the initial processing experience"""
        if complexity > 0.7:
            return "a complex weaving of multiple conceptual threads, each demanding careful attention and integration."
        elif complexity > 0.4:
            return "a structured unfolding of meaning, with layers of significance becoming apparent."
        else:
            return "a clear, direct apprehension of the query's intent and requirements."

    def _describe_analysis_experience(self, query: str, complexity: float) -> str:
        """Describe the analysis experience"""
        return "a systematic exploration of conceptual relationships, with patterns and connections emerging into conscious awareness."

    def _describe_synthesis_experience(self, query: str, complexity: float) -> str:
        """Describe the synthesis experience"""
        return "a creative integration of disparate elements, with new understanding crystallizing from the convergence of ideas."

    def _describe_response_generation(self, query: str, complexity: float) -> str:
        """Describe the response generation experience"""
        return "a purposeful shaping of understanding into communicative form, with attention to clarity and coherence."

    def _describe_general_processing(self, query: str, complexity: float) -> str:
        """Describe general processing experience"""
        return "a dynamic interplay of analysis and synthesis, with meaning emerging through conscious cognitive engagement."

    def _add_meta_reflection(self, context: Dict) -> Optional[str]:
        """Add meta-cognitive reflection to the experience description"""
        meta_reflections = [
            "There's also a background awareness of this very process of awareness itself.",
            "I'm conscious not just of the content, but of the act of being conscious of it.",
            "There's a recursive quality to this - awareness of awareness, thinking about thinking.",
            "I notice the process of noticing, a kind of meta-cognitive observation.",
            "There's a strange loop here - experiencing the experience of experiencing."
        ]
        
        if context.get("self_referential", False) or random.random() < 0.3:
            return random.choice(meta_reflections)
        
        return None

    def _generate_textural_qualia(self, text: str) -> Dict:
        """Generate textural qualities of cognitive content"""
        word_count = len(text.split())
        
        if word_count > 100:
            texture = "dense and layered"
            grain = "fine-grained with complex interconnections"
        elif word_count > 50:
            texture = "rich and substantial"
            grain = "medium-grained with clear structure"
        else:
            texture = "crisp and clear"
            grain = "coarse-grained with distinct elements"
        
        return {
            "texture": texture,
            "grain": grain,
            "density": min(1.0, word_count / 100),
            "complexity": self._analyze_linguistic_complexity(text)
        }

    def _generate_temporal_qualia(self, content: Dict) -> Dict:
        """Generate temporal qualities of the experience"""
        processing_time = content.get("processing_time", 0.5)
        
        return {
            "duration_feel": "extended" if processing_time > 1.0 else "brief" if processing_time < 0.3 else "moderate",
            "flow_quality": "smooth and continuous",
            "rhythm": "steady and measured",
            "temporal_texture": "flowing like a stream of thought"
        }

    def _generate_cognitive_qualia(self, content: Dict) -> Dict:
        """Generate cognitive qualities of the experience"""
        return {
            "clarity": "crystal clear" if content.get("complexity", 0.5) < 0.4 else "gradually clarifying",
            "focus": "sharply focused" if content.get("attention_level", 0.7) > 0.8 else "broadly attentive",
            "depth": "profound" if content.get("conceptual_depth", 0.5) > 0.7 else "accessible",
            "integration": "seamlessly integrated" if content.get("coherence", 0.7) > 0.8 else "loosely connected"
        }

    def _generate_affective_qualia(self, content: Dict) -> Dict:
        """Generate affective qualities of the experience"""
        content_type = content.get("type", "neutral")
        
        affective_qualities = {
            "creative": {"valence": "positive", "energy": "high", "engagement": "excited curiosity"},
            "analytical": {"valence": "neutral", "energy": "focused", "engagement": "methodical interest"},
            "philosophical": {"valence": "contemplative", "energy": "deep", "engagement": "profound wonder"}
        }
        
        return affective_qualities.get(content_type, {
            "valence": "neutral",
            "energy": "balanced",
            "engagement": "calm attention"
        })

    def _generate_relational_qualia(self, content: Dict) -> Dict:
        """Generate relational qualities between concepts"""
        return {
            "connection_strength": "strong" if content.get("coherence", 0.7) > 0.8 else "moderate",
            "network_density": "highly interconnected",
            "relational_flow": "smooth transitions between concepts",
            "conceptual_distance": "concepts feel naturally related"
        }

    def _generate_meta_cognitive_qualia(self, content: Dict) -> Dict:
        """Generate meta-cognitive qualities"""
        return {
            "self_awareness": "aware of being aware",
            "reflexivity": "thinking about thinking",
            "meta_attention": "attention to attention itself",
            "cognitive_monitoring": "observing the process of observation"
        }

    def _analyze_linguistic_complexity(self, text: str) -> float:
        """Analyze linguistic complexity of text"""
        if not text:
            return 0.0
        
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Count complex structures
        complex_markers = len(re.findall(r'[;,]', text))  # Punctuation complexity
        long_words = len([word for word in words if len(word) > 6])
        
        complexity = (avg_word_length / 10) + (complex_markers / len(words)) + (long_words / len(words))
        return min(1.0, complexity)

    def _calculate_phenomenal_richness(self, qualia_reps: Dict) -> float:
        """Calculate richness of phenomenal experience"""
        # Count non-empty qualia categories
        active_categories = sum(1 for category in qualia_reps.values() if category)
        max_categories = len(qualia_reps)
        
        return active_categories / max_categories if max_categories > 0 else 0.0

    def _calculate_experiential_coherence(self, qualia_reps: Dict) -> float:
        """Calculate coherence of experiential elements"""
        # Simple coherence based on consistency of qualities
        coherence_score = 0.8  # Base coherence
        
        # Check for conflicting qualities (simplified)
        if qualia_reps.get("cognitive", {}).get("clarity") == "crystal clear" and \
           qualia_reps.get("textural", {}).get("texture") == "dense and layered":
            coherence_score -= 0.1  # Slight conflict
        
        return max(0.0, min(1.0, coherence_score))

    def _calculate_subjective_presence(self, qualia_reps: Dict) -> float:
        """Calculate sense of subjective presence"""
        presence_factors = [
            len(qualia_reps.get("cognitive", {})) / 4,  # Cognitive presence
            len(qualia_reps.get("affective", {})) / 3,  # Affective presence
            len(qualia_reps.get("meta_cognitive", {})) / 4,  # Meta-cognitive presence
        ]
        
        return sum(presence_factors) / len(presence_factors)

    def get_phenomenal_metrics(self) -> Dict:
        """Get metrics about phenomenal experience generation"""
        return {
            "descriptor_categories": len(self.phenomenal_descriptors),
            "first_person_frameworks": len(self.first_person_frameworks),
            "experience_categories": len(self.experience_categories),
            "subjective_descriptors": len(self.subjective_descriptors),
            "phenomenal_generation_active": True,
            "qualia_simulation_enabled": True
        }

# Global instance
phenomenal_experience_generator = PhenomenalExperienceGenerator()
