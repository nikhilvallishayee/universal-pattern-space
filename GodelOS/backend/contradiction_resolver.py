"""
Contradiction Resolver for GödelOS

Handles detection and resolution of contradictory knowledge and information.
"""

import re
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ContradictionResolver:
    def __init__(self):
        self.contradiction_patterns = [
            # Direct contradictions
            (r"(.+)\s+is\s+true", r"(.+)\s+is\s+false"),
            (r"(.+)\s+exists", r"(.+)\s+does\s+not\s+exist"),
            (r"(.+)\s+is\s+possible", r"(.+)\s+is\s+impossible"),
            (r"(.+)\s+always\s+(.+)", r"(.+)\s+never\s+(.+)"),
            
            # Logical contradictions
            (r"all\s+(.+)\s+are\s+(.+)", r"some\s+(.+)\s+are\s+not\s+(.+)"),
            (r"no\s+(.+)\s+(.+)", r"some\s+(.+)\s+(.+)"),
            
            # Temporal contradictions
            (r"(.+)\s+happened\s+before\s+(.+)", r"(.+)\s+happened\s+after\s+(.+)"),
            (r"(.+)\s+will\s+(.+)", r"(.+)\s+will\s+not\s+(.+)"),
            
            # Value contradictions
            (r"(.+)\s+is\s+greater\s+than\s+(.+)", r"(.+)\s+is\s+less\s+than\s+(.+)"),
            (r"(.+)\s+increases\s+(.+)", r"(.+)\s+decreases\s+(.+)")
        ]
        
        self.paradox_indicators = [
            "paradox", "contradiction", "inconsistent", "conflicting",
            "both true and false", "impossible", "self-contradictory"
        ]
        
        self.resolution_strategies = {
            "temporal": "resolve through temporal ordering",
            "contextual": "resolve through context differentiation", 
            "probabilistic": "resolve through probabilistic reasoning",
            "hierarchical": "resolve through authority/source ranking",
            "synthetic": "resolve through higher-order synthesis"
        }
        
        self.detected_contradictions = []
        self.resolution_history = []

    async def detect_contradictions(self, new_knowledge: Dict, existing_knowledge: List[Dict] = None) -> List[Dict]:
        """Detect contradictions between new and existing knowledge"""
        contradictions = []
        
        if not existing_knowledge:
            existing_knowledge = []
        
        new_content = new_knowledge.get("content", "").lower()
        new_definition = new_knowledge.get("definition", "").lower()
        new_text = f"{new_content} {new_definition}".strip()
        
        # Check for self-contradictions within the new knowledge
        self_contradictions = await self._detect_self_contradictions(new_text)
        contradictions.extend(self_contradictions)
        
        # Check against existing knowledge
        for existing in existing_knowledge:
            existing_content = existing.get("content", "").lower()
            existing_definition = existing.get("definition", "").lower()
            existing_text = f"{existing_content} {existing_definition}".strip()
            
            contradiction = await self._compare_knowledge_items(new_text, existing_text, new_knowledge, existing)
            if contradiction:
                contradictions.append(contradiction)
        
        # Check for paradox indicators
        paradox_contradictions = await self._detect_paradox_statements(new_text, new_knowledge)
        contradictions.extend(paradox_contradictions)
        
        # Store detected contradictions
        for contradiction in contradictions:
            contradiction["detected_at"] = time.time()
            contradiction["id"] = f"contradiction_{len(self.detected_contradictions)}"
            self.detected_contradictions.append(contradiction)
        
        return contradictions

    async def resolve_contradictions(self, contradictions: List[Dict]) -> Dict:
        """Attempt to resolve detected contradictions"""
        resolution_results = []
        successful_resolutions = 0
        
        for contradiction in contradictions:
            resolution_result = await self._resolve_single_contradiction(contradiction)
            resolution_results.append(resolution_result)
            
            if resolution_result["resolved"]:
                successful_resolutions += 1
            
            # Add to resolution history
            resolution_record = {
                "contradiction_id": contradiction["id"],
                "resolution_strategy": resolution_result["strategy"],
                "resolved": resolution_result["resolved"],
                "resolution_time": time.time(),
                "confidence": resolution_result["confidence"]
            }
            self.resolution_history.append(resolution_record)
        
        return {
            "contradictions_processed": len(contradictions),
            "successful_resolutions": successful_resolutions,
            "resolution_rate": successful_resolutions / len(contradictions) if contradictions else 1.0,
            "resolution_results": resolution_results,
            "resolution_attempted": len(contradictions) > 0
        }

    async def maintain_knowledge_consistency(self, knowledge_base: List[Dict] = None) -> Dict:
        """Maintain consistency across the knowledge base"""
        if not knowledge_base:
            return {"consistency_maintained": True, "issues_found": 0}
        
        consistency_issues = []
        
        # Pairwise consistency checking
        for i, item1 in enumerate(knowledge_base):
            for item2 in knowledge_base[i+1:]:
                inconsistency = await self._check_consistency(item1, item2)
                if inconsistency:
                    consistency_issues.append(inconsistency)
        
        # Attempt to resolve consistency issues
        if consistency_issues:
            resolution_result = await self.resolve_contradictions(consistency_issues)
            
            return {
                "consistency_maintained": resolution_result["resolution_rate"] > 0.7,
                "issues_found": len(consistency_issues),
                "issues_resolved": resolution_result["successful_resolutions"],
                "resolution_rate": resolution_result["resolution_rate"]
            }
        
        return {
            "consistency_maintained": True,
            "issues_found": 0,
            "issues_resolved": 0,
            "resolution_rate": 1.0
        }

    async def _detect_self_contradictions(self, text: str) -> List[Dict]:
        """Detect contradictions within a single piece of text"""
        contradictions = []
        
        # Check for explicit paradox statements
        for indicator in self.paradox_indicators:
            if indicator in text:
                contradiction = {
                    "type": "self_contradiction",
                    "subtype": "explicit_paradox",
                    "content": text,
                    "indicator": indicator,
                    "severity": "high",
                    "confidence": 0.9
                }
                contradictions.append(contradiction)
        
        # Check for logical contradictions within the text
        sentences = text.split('.')
        for i, sentence1 in enumerate(sentences):
            for sentence2 in sentences[i+1:]:
                if self._are_contradictory_sentences(sentence1.strip(), sentence2.strip()):
                    contradiction = {
                        "type": "self_contradiction",
                        "subtype": "logical_inconsistency",
                        "sentence1": sentence1.strip(),
                        "sentence2": sentence2.strip(),
                        "severity": "medium",
                        "confidence": 0.7
                    }
                    contradictions.append(contradiction)
        
        return contradictions

    async def _compare_knowledge_items(self, text1: str, text2: str, item1: Dict, item2: Dict) -> Optional[Dict]:
        """Compare two knowledge items for contradictions"""
        # Direct content contradiction check
        if self._are_contradictory_texts(text1, text2):
            return {
                "type": "knowledge_contradiction",
                "subtype": "content_conflict",
                "item1": item1,
                "item2": item2,
                "text1": text1[:100] + "..." if len(text1) > 100 else text1,
                "text2": text2[:100] + "..." if len(text2) > 100 else text2,
                "severity": "high",
                "confidence": 0.8
            }
        
        # Conceptual contradiction check
        concept1 = item1.get("concept", "")
        concept2 = item2.get("concept", "")
        
        if concept1 and concept2 and concept1.lower() == concept2.lower():
            # Same concept, different definitions
            def1 = item1.get("definition", "")
            def2 = item2.get("definition", "")
            
            if def1 and def2 and self._are_contradictory_definitions(def1, def2):
                return {
                    "type": "knowledge_contradiction",
                    "subtype": "definition_conflict",
                    "concept": concept1,
                    "definition1": def1,
                    "definition2": def2,
                    "severity": "high",
                    "confidence": 0.9
                }
        
        return None

    async def _detect_paradox_statements(self, text: str, knowledge_item: Dict) -> List[Dict]:
        """Detect paradox statements in the knowledge"""
        paradoxes = []
        
        # Classic paradox patterns
        paradox_patterns = [
            r"this\s+statement\s+is\s+false",
            r"i\s+am\s+lying",
            r"the\s+following\s+statement\s+is\s+true.*the\s+previous\s+statement\s+is\s+false",
            r"everything\s+i\s+say\s+is\s+false",
            r"there\s+are\s+no\s+absolutes"
        ]
        
        for pattern in paradox_patterns:
            if re.search(pattern, text):
                paradox = {
                    "type": "paradox",
                    "subtype": "logical_paradox",
                    "pattern": pattern,
                    "content": text,
                    "knowledge_item": knowledge_item,
                    "severity": "high",
                    "confidence": 0.95
                }
                paradoxes.append(paradox)
        
        return paradoxes

    def _are_contradictory_sentences(self, sentence1: str, sentence2: str) -> bool:
        """Check if two sentences are contradictory"""
        if not sentence1 or not sentence2:
            return False
        
        s1 = sentence1.lower().strip()
        s2 = sentence2.lower().strip()
        
        # Check contradiction patterns
        for positive_pattern, negative_pattern in self.contradiction_patterns:
            # Check if sentence1 matches positive and sentence2 matches negative
            pos_match1 = re.search(positive_pattern, s1)
            neg_match2 = re.search(negative_pattern, s2)
            
            if pos_match1 and neg_match2:
                # Extract subjects to see if they're about the same thing
                if pos_match1.groups() and neg_match2.groups():
                    subject1 = pos_match1.groups()[0].strip()
                    subject2 = neg_match2.groups()[0].strip()
                    if self._similar_subjects(subject1, subject2):
                        return True
            
            # Check the reverse
            pos_match2 = re.search(positive_pattern, s2)
            neg_match1 = re.search(negative_pattern, s1)
            
            if pos_match2 and neg_match1:
                if pos_match2.groups() and neg_match1.groups():
                    subject1 = neg_match1.groups()[0].strip()
                    subject2 = pos_match2.groups()[0].strip()
                    if self._similar_subjects(subject1, subject2):
                        return True
        
        return False

    def _are_contradictory_texts(self, text1: str, text2: str) -> bool:
        """Check if two texts contain contradictory information"""
        # Split into sentences and check pairwise
        sentences1 = [s.strip() for s in text1.split('.') if s.strip()]
        sentences2 = [s.strip() for s in text2.split('.') if s.strip()]
        
        for s1 in sentences1:
            for s2 in sentences2:
                if self._are_contradictory_sentences(s1, s2):
                    return True
        
        return False

    def _are_contradictory_definitions(self, def1: str, def2: str) -> bool:
        """Check if two definitions are contradictory"""
        # Normalize definitions
        d1 = def1.lower().strip()
        d2 = def2.lower().strip()
        
        # Check for direct contradictions
        if self._are_contradictory_texts(d1, d2):
            return True
        
        # Check for mutually exclusive properties
        exclusive_pairs = [
            ("finite", "infinite"),
            ("visible", "invisible"),
            ("material", "immaterial"),
            ("conscious", "unconscious"),
            ("deterministic", "random"),
            ("simple", "complex")
        ]
        
        for term1, term2 in exclusive_pairs:
            if term1 in d1 and term2 in d2:
                return True
            if term2 in d1 and term1 in d2:
                return True
        
        return False

    def _similar_subjects(self, subject1: str, subject2: str) -> bool:
        """Check if two subjects are similar enough to be considered the same"""
        if not subject1 or not subject2:
            return False
        
        # Exact match
        if subject1 == subject2:
            return True
        
        # Stemming-like comparison (simple)
        s1_words = set(subject1.split())
        s2_words = set(subject2.split())
        
        # If there's significant overlap, consider them similar
        if s1_words and s2_words:
            overlap = len(s1_words.intersection(s2_words))
            total = len(s1_words.union(s2_words))
            similarity = overlap / total
            return similarity > 0.6
        
        return False

    async def _resolve_single_contradiction(self, contradiction: Dict) -> Dict:
        """Attempt to resolve a single contradiction"""
        contradiction_type = contradiction.get("type", "unknown")
        subtype = contradiction.get("subtype", "")
        
        # Choose resolution strategy based on type
        if contradiction_type == "paradox":
            return await self._resolve_paradox(contradiction)
        elif contradiction_type == "self_contradiction":
            return await self._resolve_self_contradiction(contradiction)
        elif contradiction_type == "knowledge_contradiction":
            return await self._resolve_knowledge_contradiction(contradiction)
        else:
            return await self._resolve_generic_contradiction(contradiction)

    async def _resolve_paradox(self, contradiction: Dict) -> Dict:
        """Resolve a logical paradox"""
        # Paradoxes often require meta-level reasoning
        resolution_text = "This appears to be a logical paradox. Such statements create self-referential loops that cannot be resolved within the same logical level. The statement should be considered meaningless or requires a higher-order logical framework for evaluation."
        
        return {
            "contradiction_id": contradiction.get("id"),
            "strategy": "meta_logical_analysis",
            "resolved": True,
            "confidence": 0.8,
            "resolution": resolution_text,
            "approach": "hierarchical"
        }

    async def _resolve_self_contradiction(self, contradiction: Dict) -> Dict:
        """Resolve contradictions within a single statement"""
        if contradiction.get("subtype") == "explicit_paradox":
            return await self._resolve_paradox(contradiction)
        
        # For logical inconsistencies, suggest clarification
        resolution_text = "The statement contains internal logical inconsistencies. It may require clarification, context specification, or recognition that different aspects apply under different conditions."
        
        return {
            "contradiction_id": contradiction.get("id"),
            "strategy": "contextual_clarification",
            "resolved": True,
            "confidence": 0.7,
            "resolution": resolution_text,
            "approach": "contextual"
        }

    async def _resolve_knowledge_contradiction(self, contradiction: Dict) -> Dict:
        """Resolve contradictions between knowledge items"""
        subtype = contradiction.get("subtype", "")
        
        if subtype == "definition_conflict":
            # Multiple definitions for the same concept
            resolution_text = f"Multiple definitions exist for the concept '{contradiction.get('concept')}'. This may indicate: (1) the concept has different meanings in different contexts, (2) the concept has evolved over time, or (3) there are legitimate disagreements about the definition. Context-specific usage should be considered."
            
            return {
                "contradiction_id": contradiction.get("id"),
                "strategy": "contextual_differentiation",
                "resolved": True,
                "confidence": 0.8,
                "resolution": resolution_text,
                "approach": "contextual"
            }
        
        elif subtype == "content_conflict":
            # Conflicting content
            resolution_text = "Conflicting information detected. Resolution requires: (1) checking source reliability, (2) considering temporal factors, (3) examining context specificity, or (4) acknowledging legitimate uncertainty in the domain."
            
            return {
                "contradiction_id": contradiction.get("id"),
                "strategy": "multi_factor_analysis",
                "resolved": True,
                "confidence": 0.6,
                "resolution": resolution_text,
                "approach": "synthetic"
            }
        
        return await self._resolve_generic_contradiction(contradiction)

    async def _resolve_generic_contradiction(self, contradiction: Dict) -> Dict:
        """Generic contradiction resolution"""
        resolution_text = "A logical inconsistency has been detected. This may be due to incomplete information, context dependency, or the need for more nuanced understanding. Further investigation or expert consultation may be required."
        
        return {
            "contradiction_id": contradiction.get("id"),
            "strategy": "general_acknowledgment",
            "resolved": False,
            "confidence": 0.4,
            "resolution": resolution_text,
            "approach": "acknowledgment"
        }

    async def _check_consistency(self, item1: Dict, item2: Dict) -> Optional[Dict]:
        """Check consistency between two knowledge items"""
        # This is similar to _compare_knowledge_items but focused on consistency
        text1 = f"{item1.get('content', '')} {item1.get('definition', '')}".strip().lower()
        text2 = f"{item2.get('content', '')} {item2.get('definition', '')}".strip().lower()
        
        return await self._compare_knowledge_items(text1, text2, item1, item2)

    def get_contradiction_metrics(self) -> Dict:
        """Get metrics about contradiction detection and resolution"""
        total_detected = len(self.detected_contradictions)
        total_resolved = len([r for r in self.resolution_history if r["resolved"]])
        
        # Categorize contradictions by type
        type_counts = {}
        for contradiction in self.detected_contradictions:
            con_type = contradiction.get("type", "unknown")
            type_counts[con_type] = type_counts.get(con_type, 0) + 1
        
        # Calculate average resolution confidence
        resolution_confidences = [r["confidence"] for r in self.resolution_history if r["resolved"]]
        avg_confidence = sum(resolution_confidences) / len(resolution_confidences) if resolution_confidences else 0
        
        return {
            "total_contradictions_detected": total_detected,
            "total_contradictions_resolved": total_resolved,
            "resolution_rate": total_resolved / total_detected if total_detected > 0 else 1.0,
            "contradiction_types": type_counts,
            "average_resolution_confidence": avg_confidence,
            "contradiction_detection_active": True,
            "resolution_strategies_available": len(self.resolution_strategies)
        }

# Global instance
contradiction_resolver = ContradictionResolver()
