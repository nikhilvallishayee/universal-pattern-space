"""
Advanced Query Processor for GödelOS

Handles sophisticated query analysis including knowledge gap detection,
novelty scoring, domain integration, and uncertainty quantification.
"""

import re
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedQueryProcessor:
    def __init__(self):
        self.knowledge_domains = {
            "physics": ["quantum", "mechanics", "particle", "wave", "energy", "relativity"],
            "consciousness": ["consciousness", "mind", "awareness", "experience", "qualia", "phenomenal"],
            "philosophy": ["philosophy", "existence", "reality", "truth", "ethics", "metaphysics"],
            "mathematics": ["math", "equation", "proof", "theorem", "logic", "geometry"],
            "biology": ["biology", "life", "organism", "evolution", "brain", "neural"],
            "technology": ["computer", "ai", "algorithm", "digital", "software", "system"],
            "psychology": ["psychology", "behavior", "cognitive", "mental", "emotion"],
            "linguistics": ["language", "communication", "syntax", "semantics", "grammar"]
        }
        
        self.uncertainty_indicators = [
            "probably", "likely", "might", "could", "possibly", "perhaps", "maybe",
            "uncertain", "unclear", "unknown", "difficult to say", "hard to determine"
        ]
        
        self.novelty_indicators = [
            "novel", "new", "innovative", "creative", "original", "unique", "unprecedented",
            "groundbreaking", "revolutionary", "cutting-edge", "breakthrough"
        ]
        
        self.knowledge_gap_patterns = [
            r"don't know", r"not sure", r"unclear", r"uncertain", r"would need to",
            r"requires further", r"beyond my knowledge", r"insufficient information"
        ]

    async def analyze_knowledge_gaps(self, query: str, response: str, context: Dict = None) -> Dict:
        """Analyze knowledge gaps and create acquisition plans"""
        gaps_identified = []
        acquisition_plan = []
        
        # 1. Detect explicit gap indicators in response
        for pattern in self.knowledge_gap_patterns:
            if re.search(pattern, response.lower()):
                gap = {
                    "type": "explicit_gap",
                    "indicator": pattern,
                    "context": query[:100],
                    "confidence": 0.9
                }
                gaps_identified.append(gap)
        
        # 2. Analyze query complexity vs response depth
        query_complexity = self._calculate_query_complexity(query)
        response_depth = self._calculate_response_depth(response)
        
        if query_complexity > response_depth * 1.5:
            gap = {
                "type": "complexity_gap", 
                "query_complexity": query_complexity,
                "response_depth": response_depth,
                "confidence": 0.7
            }
            gaps_identified.append(gap)
        
        # 3. Check for missing domain knowledge
        query_domains = self._identify_domains(query)
        response_domains = self._identify_domains(response)
        
        missing_domains = set(query_domains) - set(response_domains)
        for domain in missing_domains:
            gap = {
                "type": "domain_gap",
                "missing_domain": domain,
                "confidence": 0.8
            }
            gaps_identified.append(gap)
        
        # 4. Create acquisition plans for identified gaps
        for gap in gaps_identified:
            if gap["type"] == "explicit_gap":
                plan = {
                    "strategy": "targeted_research",
                    "target": gap["context"],
                    "method": "semantic_search_and_synthesis",
                    "priority": "high" if gap["confidence"] > 0.8 else "medium"
                }
                acquisition_plan.append(plan)
            
            elif gap["type"] == "complexity_gap":
                plan = {
                    "strategy": "complexity_analysis",
                    "target": "deeper_understanding",
                    "method": "multi_step_reasoning",
                    "priority": "medium"
                }
                acquisition_plan.append(plan)
            
            elif gap["type"] == "domain_gap":
                plan = {
                    "strategy": "domain_knowledge_acquisition",
                    "target": gap["missing_domain"],
                    "method": "cross_domain_learning",
                    "priority": "high"
                }
                acquisition_plan.append(plan)
        
        return {
            "knowledge_gaps_identified": len(gaps_identified),
            "gaps": gaps_identified,
            "acquisition_plan_created": len(acquisition_plan) > 0,
            "acquisition_strategies": acquisition_plan,
            "gap_analysis_confidence": sum(g["confidence"] for g in gaps_identified) / len(gaps_identified) if gaps_identified else 0.0
        }

    async def calculate_novelty_score(self, query: str, response: str, context: Dict = None) -> Dict:
        """Calculate novelty and feasibility scores for creative responses"""
        novelty_factors = []
        feasibility_factors = []
        
        # 1. Lexical novelty - presence of innovative terms
        novelty_terms = sum(1 for indicator in self.novelty_indicators if indicator in response.lower())
        lexical_novelty = min(1.0, novelty_terms / 5.0)  # Normalize to 0-1
        novelty_factors.append(("lexical", lexical_novelty))
        
        # 2. Conceptual novelty - combination of unusual concepts
        concepts = self._extract_concepts(response)
        domain_diversity = len(set(self._categorize_concepts(concepts)))
        conceptual_novelty = min(1.0, domain_diversity / 4.0)  # Max 4 domains
        novelty_factors.append(("conceptual", conceptual_novelty))
        
        # 3. Structural novelty - unconventional response structure
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        structural_complexity = min(1.0, avg_sentence_length / 20.0)  # Normalize by typical length
        novelty_factors.append(("structural", structural_complexity))
        
        # 4. Connection novelty - unusual domain combinations
        response_domains = self._identify_domains(response)
        if len(response_domains) > 1:
            connection_novelty = min(1.0, len(response_domains) / 3.0)  # 3+ domains = high novelty
        else:
            connection_novelty = 0.2  # Single domain = low novelty
        novelty_factors.append(("connection", connection_novelty))
        
        # Calculate overall novelty score
        novelty_score = sum(weight * score for _, score in novelty_factors) / len(novelty_factors)
        
        # 5. Feasibility assessment
        # Check for concrete, actionable elements
        actionable_terms = ["implement", "measure", "test", "apply", "use", "create", "build"]
        actionability = sum(1 for term in actionable_terms if term in response.lower()) / len(actionable_terms)
        feasibility_factors.append(("actionability", actionability))
        
        # Check for realistic constraints acknowledgment
        constraint_terms = ["however", "but", "limitation", "challenge", "difficulty", "requires"]
        realism = min(1.0, sum(1 for term in constraint_terms if term in response.lower()) / 3.0)
        feasibility_factors.append(("realism", realism))
        
        # Check for existing knowledge integration
        integration_score = min(1.0, len(concepts) / 10.0)  # More concepts = better integration
        feasibility_factors.append(("integration", integration_score))
        
        # Calculate overall feasibility score
        feasibility_score = sum(weight * score for _, score in feasibility_factors) / len(feasibility_factors)
        
        return {
            "novelty_score": round(novelty_score, 3),
            "feasibility_score": round(feasibility_score, 3),
            "novelty_breakdown": dict(novelty_factors),
            "feasibility_breakdown": dict(feasibility_factors),
            "creativity_index": round((novelty_score + feasibility_score) / 2, 3)
        }

    async def detect_domain_integration(self, query: str, response: str = None) -> Dict:
        """Detect cross-domain reasoning and novel connections"""
        query_domains = self._identify_domains(query)
        response_domains = self._identify_domains(response) if response else []
        
        # Find connections between domains
        connections = []
        if len(query_domains) > 1:
            for i, domain1 in enumerate(query_domains):
                for domain2 in query_domains[i+1:]:
                    connection = self._analyze_domain_connection(domain1, domain2, query, response)
                    if connection["strength"] > 0.3:
                        connections.append(connection)
        
        # Detect novel connections (unexpected domain combinations)
        novel_connections = []
        for connection in connections:
            if connection["novelty"] > 0.6:
                novel_connections.append(connection)
        
        return {
            "domains_integrated": len(set(query_domains + response_domains)),
            "query_domains": query_domains,
            "response_domains": response_domains,
            "novel_connections": len(novel_connections) > 0,
            "connection_details": connections,
            "novel_connection_details": novel_connections,
            "integration_depth": self._calculate_integration_depth(connections)
        }

    async def quantify_uncertainty(self, query: str, response: str, context: Dict = None) -> Dict:
        """Quantify and calibrate uncertainty in responses"""
        uncertainty_detected = False
        confidence_calibrated = False
        uncertainty_score = 0.0
        
        # 1. Detect explicit uncertainty expressions
        explicit_uncertainty = sum(1 for indicator in self.uncertainty_indicators if indicator in response.lower())
        if explicit_uncertainty > 0:
            uncertainty_detected = True
            uncertainty_score += min(1.0, explicit_uncertainty / 5.0) * 0.4  # 40% weight
        
        # 2. Analyze confidence expressions
        confidence_patterns = [
            r"(\d{1,3})%", r"very confident", r"certain", r"sure", r"confident",
            r"likely", r"probable", r"possible", r"unlikely", r"improbable"
        ]
        
        confidence_expressions = []
        for pattern in confidence_patterns:
            matches = re.findall(pattern, response.lower())
            confidence_expressions.extend(matches)
        
        if confidence_expressions:
            confidence_calibrated = True
            uncertainty_score += 0.3  # 30% weight for expressing confidence
        
        # 3. Check for probabilistic language
        probabilistic_terms = ["probability", "chance", "odds", "likelihood", "risk"]
        probabilistic_language = sum(1 for term in probabilistic_terms if term in response.lower())
        if probabilistic_language > 0:
            uncertainty_score += min(1.0, probabilistic_language / 3.0) * 0.3  # 30% weight
        
        # 4. Assess query ambiguity
        question_marks = query.count('?')
        ambiguous_terms = ["what", "how", "why", "when", "where", "which"]
        query_ambiguity = len([term for term in ambiguous_terms if term in query.lower()])
        
        if query_ambiguity > 2 and explicit_uncertainty > 0:
            uncertainty_score += 0.2  # Bonus for acknowledging ambiguous queries
        
        return {
            "uncertainty_expressed": uncertainty_detected,
            "confidence_calibrated": confidence_calibrated,
            "uncertainty_score": round(uncertainty_score, 3),
            "explicit_uncertainty_count": explicit_uncertainty,
            "confidence_expressions": confidence_expressions,
            "probabilistic_language_count": probabilistic_language,
            "query_ambiguity_level": query_ambiguity
        }

    def _identify_domains(self, text: str) -> List[str]:
        """Identify knowledge domains present in text"""
        if not text:
            return []
            
        text_lower = text.lower()
        detected_domains = []
        
        for domain, keywords in self.knowledge_domains.items():
            domain_score = sum(1 for keyword in keywords if keyword in text_lower)
            if domain_score > 0:
                detected_domains.append(domain)
        
        return detected_domains

    def _calculate_query_complexity(self, query: str) -> float:
        """Calculate complexity score for a query"""
        factors = [
            len(query.split()) / 20.0,  # Word count factor
            query.count('?') * 0.2,     # Multiple questions
            len(re.findall(r'\b(how|why|what|when|where|who)\b', query.lower())) * 0.1,
            len(re.findall(r'\b(and|or|but|however|therefore)\b', query.lower())) * 0.1,
            len(self._identify_domains(query)) * 0.2  # Multi-domain queries
        ]
        return min(1.0, sum(factors))

    def _calculate_response_depth(self, response: str) -> float:
        """Calculate depth/comprehensiveness of response"""
        if not response:
            return 0.0
            
        factors = [
            len(response.split()) / 100.0,  # Length factor
            len(response.split('.')) / 10.0,  # Number of sentences
            len(self._extract_concepts(response)) / 15.0,  # Concept density
            len(self._identify_domains(response)) / 5.0  # Domain coverage
        ]
        return min(1.0, sum(factors) / len(factors))

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        if not text:
            return []
            
        # Extract noun phrases and technical terms
        words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        
        # Filter out common words
        stop_words = {'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'have', 'their', 'said', 'each', 'which', 'such', 'into', 'most', 'some', 'time', 'very', 'when', 'much', 'more', 'only', 'over', 'also', 'just', 'through', 'should', 'could', 'would', 'these', 'there', 'many', 'where', 'being', 'during', 'before', 'after', 'under', 'above', 'between'}
        
        concepts = [word.lower() for word in words if word.lower() not in stop_words and len(word) > 3]
        return list(set(concepts))  # Remove duplicates

    def _categorize_concepts(self, concepts: List[str]) -> List[str]:
        """Categorize concepts by domain"""
        categories = []
        for concept in concepts:
            for domain, keywords in self.knowledge_domains.items():
                if concept in keywords:
                    categories.append(domain)
                    break
        return categories

    def _analyze_domain_connection(self, domain1: str, domain2: str, query: str, response: str) -> Dict:
        """Analyze the strength and novelty of connection between two domains"""
        # Common domain pairs (lower novelty)
        common_pairs = {
            ('physics', 'mathematics'), ('biology', 'psychology'), 
            ('technology', 'mathematics'), ('philosophy', 'consciousness')
        }
        
        domain_pair = tuple(sorted([domain1, domain2]))
        novelty = 0.3 if domain_pair in common_pairs else 0.8
        
        # Analyze connection strength based on context
        strength = 0.5  # Base strength
        
        # Look for connecting concepts
        domain1_keywords = set(self.knowledge_domains.get(domain1, []))
        domain2_keywords = set(self.knowledge_domains.get(domain2, []))
        
        text = (query + " " + (response or "")).lower()
        domain1_presence = sum(1 for kw in domain1_keywords if kw in text)
        domain2_presence = sum(1 for kw in domain2_keywords if kw in text)
        
        if domain1_presence > 0 and domain2_presence > 0:
            strength = min(1.0, (domain1_presence + domain2_presence) / 6.0)
        
        return {
            "domain1": domain1,
            "domain2": domain2,
            "strength": strength,
            "novelty": novelty,
            "connection_type": "explicit" if strength > 0.7 else "implicit"
        }

    def _calculate_integration_depth(self, connections: List[Dict]) -> float:
        """Calculate how deeply domains are integrated"""
        if not connections:
            return 0.0
        
        total_strength = sum(conn["strength"] for conn in connections)
        avg_strength = total_strength / len(connections)
        
        # Bonus for multiple connections
        connection_bonus = min(0.3, len(connections) * 0.1)
        
        return min(1.0, avg_strength + connection_bonus)

# Global instance
advanced_query_processor = AdvancedQueryProcessor()
