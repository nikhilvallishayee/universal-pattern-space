"""
Domain Reasoning Engine for GödelOS

Handles cross-domain knowledge integration and reasoning.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Set
import logging

logger = logging.getLogger(__name__)

class DomainReasoningEngine:
    def __init__(self):
        self.domain_ontology = {
            "physics": {
                "core_concepts": ["quantum", "mechanics", "relativity", "particle", "wave", "energy"],
                "related_domains": ["mathematics", "technology", "philosophy"],
                "reasoning_patterns": ["causal", "mathematical", "experimental"]
            },
            "consciousness": {
                "core_concepts": ["awareness", "experience", "qualia", "phenomenal", "subjective"],
                "related_domains": ["philosophy", "psychology", "biology", "technology"],
                "reasoning_patterns": ["phenomenological", "introspective", "behavioral"]
            },
            "philosophy": {
                "core_concepts": ["existence", "reality", "truth", "ethics", "meaning", "knowledge"],
                "related_domains": ["consciousness", "mathematics", "physics"],
                "reasoning_patterns": ["logical", "analytical", "dialectical"]
            },
            "mathematics": {
                "core_concepts": ["equation", "proof", "theorem", "logic", "geometry", "algebra"],
                "related_domains": ["physics", "technology", "philosophy"],
                "reasoning_patterns": ["deductive", "axiomatic", "formal"]
            },
            "biology": {
                "core_concepts": ["life", "organism", "evolution", "brain", "neural", "genetics"],
                "related_domains": ["psychology", "consciousness", "technology"],
                "reasoning_patterns": ["evolutionary", "systemic", "empirical"]
            },
            "technology": {
                "core_concepts": ["computer", "algorithm", "digital", "software", "system", "artificial"],
                "related_domains": ["mathematics", "physics", "consciousness"],
                "reasoning_patterns": ["computational", "systematic", "iterative"]
            },
            "psychology": {
                "core_concepts": ["behavior", "cognitive", "mental", "emotion", "learning", "memory"],
                "related_domains": ["biology", "consciousness", "philosophy"],
                "reasoning_patterns": ["behavioral", "cognitive", "statistical"]
            }
        }
        
        self.cross_domain_bridges = {
            ("physics", "consciousness"): {
                "bridge_concepts": ["quantum_consciousness", "measurement_problem", "observer_effect"],
                "connection_strength": 0.7,
                "novelty_level": 0.9
            },
            ("mathematics", "consciousness"): {
                "bridge_concepts": ["computational_theory", "information_integration", "complexity"],
                "connection_strength": 0.6,
                "novelty_level": 0.8
            },
            ("biology", "consciousness"): {
                "bridge_concepts": ["neural_correlates", "brain_states", "emergence"],
                "connection_strength": 0.9,
                "novelty_level": 0.4
            },
            ("technology", "consciousness"): {
                "bridge_concepts": ["artificial_consciousness", "machine_consciousness", "ai_awareness"],
                "connection_strength": 0.8,
                "novelty_level": 0.9
            },
            ("philosophy", "physics"): {
                "bridge_concepts": ["nature_of_reality", "determinism", "causation"],
                "connection_strength": 0.7,
                "novelty_level": 0.5
            }
        }

    async def analyze_cross_domain_query(self, query: str, context: Dict = None) -> Dict:
        """Analyze a query for cross-domain reasoning opportunities"""
        domains = self.identify_domains(query)
        
        if len(domains) < 2:
            return {
                "is_cross_domain": False,
                "domains": domains,
                "reasoning_approach": "single_domain"
            }
        
        # Find domain pairs and their relationships
        domain_pairs = []
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                pair_key = tuple(sorted([domain1, domain2]))
                pair_info = self.cross_domain_bridges.get(pair_key, {
                    "bridge_concepts": [],
                    "connection_strength": 0.3,
                    "novelty_level": 0.5
                })
                
                domain_pairs.append({
                    "domains": [domain1, domain2],
                    "bridge_concepts": pair_info["bridge_concepts"],
                    "connection_strength": pair_info["connection_strength"],
                    "novelty_level": pair_info["novelty_level"]
                })
        
        # Determine best reasoning approach
        strongest_pair = max(domain_pairs, key=lambda p: p["connection_strength"]) if domain_pairs else None
        
        return {
            "is_cross_domain": True,
            "domains": domains,
            "domain_pairs": domain_pairs,
            "strongest_connection": strongest_pair,
            "reasoning_approach": "cross_domain_synthesis",
            "complexity_level": len(domains) * 0.3 + (strongest_pair["novelty_level"] if strongest_pair else 0)
        }

    async def synthesize_cross_domain_response(self, query: str, domains: List[str], context: Dict = None) -> Dict:
        """Generate a cross-domain synthesis response"""
        domain_perspectives = {}
        
        # Generate perspective from each domain
        for domain in domains:
            perspective = await self._generate_domain_perspective(query, domain)
            domain_perspectives[domain] = perspective
        
        # Find connections between perspectives
        connections = await self._find_perspective_connections(domain_perspectives)
        
        # Synthesize integrated response
        synthesis = await self._synthesize_perspectives(query, domain_perspectives, connections)
        
        return {
            "domain_perspectives": domain_perspectives,
            "cross_domain_connections": connections,
            "synthesis": synthesis,
            "domains_integrated": len(domains),
            "novel_connections": len([c for c in connections if c["novelty"] > 0.6]),
            "integration_quality": synthesis["quality_score"]
        }

    async def _generate_domain_perspective(self, query: str, domain: str) -> Dict:
        """Generate a perspective on the query from a specific domain"""
        domain_info = self.domain_ontology.get(domain, {})
        core_concepts = domain_info.get("core_concepts", [])
        reasoning_patterns = domain_info.get("reasoning_patterns", ["analytical"])
        
        # Analyze query through domain lens
        relevant_concepts = [concept for concept in core_concepts if concept in query.lower()]
        
        # Generate domain-specific insights
        if domain == "physics":
            perspective = self._physics_perspective(query, relevant_concepts)
        elif domain == "consciousness":
            perspective = self._consciousness_perspective(query, relevant_concepts)
        elif domain == "philosophy":
            perspective = self._philosophy_perspective(query, relevant_concepts)
        elif domain == "mathematics":
            perspective = self._mathematics_perspective(query, relevant_concepts)
        elif domain == "biology":
            perspective = self._biology_perspective(query, relevant_concepts)
        elif domain == "technology":
            perspective = self._technology_perspective(query, relevant_concepts)
        elif domain == "psychology":
            perspective = self._psychology_perspective(query, relevant_concepts)
        else:
            perspective = self._generic_perspective(query, domain, relevant_concepts)
        
        return {
            "domain": domain,
            "relevant_concepts": relevant_concepts,
            "reasoning_pattern": reasoning_patterns[0] if reasoning_patterns else "analytical",
            "perspective": perspective,
            "confidence": min(1.0, len(relevant_concepts) / 3.0 + 0.3)
        }

    def _physics_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate physics domain perspective"""
        if "quantum" in concepts:
            return "From a quantum physics perspective, this involves fundamental questions about measurement, observation, and the nature of reality at the quantum scale."
        elif "energy" in concepts:
            return "From an energy perspective, this relates to the conservation and transformation of energy in physical systems."
        elif "relativity" in concepts:
            return "From a relativity perspective, this involves considerations of spacetime, reference frames, and the fundamental nature of physical reality."
        else:
            return "From a physics perspective, this involves understanding the fundamental laws and principles that govern physical phenomena."

    def _consciousness_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate consciousness domain perspective"""
        if "awareness" in concepts:
            return "From a consciousness perspective, this involves the subjective experience of awareness and the phenomenal aspects of mental states."
        elif "qualia" in concepts:
            return "From a qualia perspective, this concerns the qualitative, subjective aspects of conscious experience that are difficult to capture objectively."
        elif "phenomenal" in concepts:
            return "From a phenomenological perspective, this involves the first-person, experiential aspects of consciousness and mental phenomena."
        else:
            return "From a consciousness perspective, this relates to the nature of subjective experience and the hard problem of consciousness."

    def _philosophy_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate philosophy domain perspective"""
        if "existence" in concepts:
            return "From an existential perspective, this raises fundamental questions about the nature of being and existence."
        elif "truth" in concepts:
            return "From an epistemological perspective, this involves questions about the nature of truth, knowledge, and justified belief."
        elif "ethics" in concepts:
            return "From an ethical perspective, this involves moral considerations and questions of right and wrong."
        else:
            return "From a philosophical perspective, this involves fundamental questions about reality, knowledge, and human existence."

    def _mathematics_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate mathematics domain perspective"""
        if "proof" in concepts:
            return "From a mathematical perspective, this involves formal logical structures and the rigorous proof of propositions."
        elif "logic" in concepts:
            return "From a logical perspective, this involves formal reasoning systems and the principles of valid inference."
        else:
            return "From a mathematical perspective, this involves formal structures, relationships, and quantitative analysis."

    def _biology_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate biology domain perspective"""
        if "brain" in concepts or "neural" in concepts:
            return "From a neurobiological perspective, this involves understanding brain mechanisms and neural processes."
        elif "evolution" in concepts:
            return "From an evolutionary perspective, this involves understanding how traits and behaviors emerge through natural selection."
        else:
            return "From a biological perspective, this involves understanding living systems and their mechanisms."

    def _technology_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate technology domain perspective"""
        if "algorithm" in concepts:
            return "From a computational perspective, this involves algorithmic approaches and systematic problem-solving methods."
        elif "artificial" in concepts:
            return "From an AI perspective, this involves questions about artificial intelligence and machine capabilities."
        else:
            return "From a technological perspective, this involves systematic approaches and computational methods."

    def _psychology_perspective(self, query: str, concepts: List[str]) -> str:
        """Generate psychology domain perspective"""
        if "cognitive" in concepts:
            return "From a cognitive psychology perspective, this involves mental processes like perception, memory, and reasoning."
        elif "behavior" in concepts:
            return "From a behavioral perspective, this involves observable actions and their underlying mechanisms."
        else:
            return "From a psychological perspective, this involves understanding mental processes and human behavior."

    def _generic_perspective(self, query: str, domain: str, concepts: List[str]) -> str:
        """Generate generic domain perspective"""
        return f"From a {domain} perspective, this involves domain-specific considerations and specialized knowledge."

    async def _find_perspective_connections(self, perspectives: Dict[str, Dict]) -> List[Dict]:
        """Find connections between different domain perspectives"""
        connections = []
        domains = list(perspectives.keys())
        
        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                connection = await self._analyze_perspective_connection(
                    perspectives[domain1], perspectives[domain2]
                )
                if connection["strength"] > 0.3:
                    connections.append(connection)
        
        return connections

    async def _analyze_perspective_connection(self, perspective1: Dict, perspective2: Dict) -> Dict:
        """Analyze connection between two domain perspectives"""
        domain1 = perspective1["domain"]
        domain2 = perspective2["domain"]
        
        # Check for explicit bridge concepts
        pair_key = tuple(sorted([domain1, domain2]))
        bridge_info = self.cross_domain_bridges.get(pair_key, {})
        
        # Analyze textual overlap
        text1 = perspective1["perspective"].lower()
        text2 = perspective2["perspective"].lower()
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        overlap = len(words1.intersection(words2)) / len(words1.union(words2)) if words1.union(words2) else 0
        
        # Calculate connection strength
        bridge_strength = bridge_info.get("connection_strength", 0.3)
        text_strength = overlap * 0.5
        concept_strength = (len(perspective1["relevant_concepts"]) + len(perspective2["relevant_concepts"])) / 10.0
        
        total_strength = min(1.0, bridge_strength + text_strength + concept_strength)
        
        return {
            "domain1": domain1,
            "domain2": domain2,
            "strength": total_strength,
            "novelty": bridge_info.get("novelty_level", 0.5),
            "bridge_concepts": bridge_info.get("bridge_concepts", []),
            "text_overlap": overlap,
            "connection_type": "explicit" if total_strength > 0.7 else "implicit"
        }

    async def _synthesize_perspectives(self, query: str, perspectives: Dict, connections: List[Dict]) -> Dict:
        """Synthesize multiple domain perspectives into an integrated response"""
        # Extract key insights from each perspective
        domain_insights = []
        for domain, perspective_data in perspectives.items():
            insight = {
                "domain": domain,
                "key_point": perspective_data["perspective"][:100] + "...",
                "confidence": perspective_data["confidence"]
            }
            domain_insights.append(insight)
        
        # Identify synthesis opportunities
        strong_connections = [c for c in connections if c["strength"] > 0.6]
        novel_connections = [c for c in connections if c["novelty"] > 0.7]
        
        # Generate synthesized response
        if strong_connections:
            synthesis_text = f"Integrating insights from {len(perspectives)} domains reveals interesting connections. "
            
            for connection in strong_connections[:2]:  # Top 2 connections
                synthesis_text += f"The relationship between {connection['domain1']} and {connection['domain2']} "
                if connection["bridge_concepts"]:
                    synthesis_text += f"through concepts like {', '.join(connection['bridge_concepts'][:2])} "
                synthesis_text += "provides a unified perspective. "
            
            if novel_connections:
                synthesis_text += f"This analysis reveals {len(novel_connections)} novel cross-domain insights that haven't been extensively explored."
        else:
            synthesis_text = f"While {len(perspectives)} domains offer different perspectives, finding deep connections requires further investigation."
        
        # Calculate quality score
        quality_factors = [
            len(perspectives) / 5.0,  # More domains = higher quality
            len(strong_connections) / 3.0,  # Strong connections improve quality
            len(novel_connections) / 2.0,  # Novel insights boost quality
            sum(p["confidence"] for p in perspectives.values()) / len(perspectives)  # Average confidence
        ]
        
        quality_score = min(1.0, sum(quality_factors) / len(quality_factors))
        
        return {
            "synthesis_text": synthesis_text,
            "quality_score": quality_score,
            "integration_level": len(strong_connections),
            "novelty_level": len(novel_connections),
            "domain_insights": domain_insights
        }

    def identify_domains(self, text: str) -> List[str]:
        """Identify knowledge domains present in text"""
        if not text:
            return []
            
        text_lower = text.lower()
        detected_domains = []
        
        for domain, domain_info in self.domain_ontology.items():
            core_concepts = domain_info.get("core_concepts", [])
            domain_score = sum(1 for concept in core_concepts if concept in text_lower)
            if domain_score > 0:
                detected_domains.append(domain)
        
        return detected_domains

    async def evaluate_domain_integration_quality(self, response: str, expected_domains: List[str]) -> Dict:
        """Evaluate the quality of domain integration in a response"""
        response_domains = self.identify_domains(response)
        
        # Coverage: how many expected domains are covered
        coverage = len(set(response_domains).intersection(set(expected_domains))) / len(expected_domains) if expected_domains else 0
        
        # Depth: how well each domain is represented
        domain_depths = {}
        for domain in response_domains:
            core_concepts = self.domain_ontology.get(domain, {}).get("core_concepts", [])
            concept_count = sum(1 for concept in core_concepts if concept in response.lower())
            domain_depths[domain] = min(1.0, concept_count / 3.0)
        
        avg_depth = sum(domain_depths.values()) / len(domain_depths) if domain_depths else 0
        
        # Integration: evidence of cross-domain synthesis
        integration_indicators = ["relates to", "connects with", "similar to", "in contrast", "building on"]
        integration_score = min(1.0, sum(1 for indicator in integration_indicators if indicator in response.lower()) / 3.0)
        
        return {
            "coverage_score": coverage,
            "depth_score": avg_depth,
            "integration_score": integration_score,
            "overall_quality": (coverage + avg_depth + integration_score) / 3,
            "domains_covered": response_domains,
            "domain_depths": domain_depths
        }

# Global instance
domain_reasoning_engine = DomainReasoningEngine()
