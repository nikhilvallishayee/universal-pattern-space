#!/usr/bin/env python3
"""
LLM Knowledge Miner - Bootstrap Knowledge Graph from LLM

This service queries the LLM to generate structured knowledge (concepts, entities, 
relationships) and feeds it into the Knowledge Graph to provide initial seeding data.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime

from backend.llm_cognitive_driver import get_llm_cognitive_driver
from backend.core.knowledge_graph_evolution import (
    KnowledgeGraphEvolution, 
    EvolutionTrigger,
    RelationshipType
)

logger = logging.getLogger(__name__)

@dataclass
class MinedConcept:
    """A concept mined from the LLM"""
    name: str
    description: str
    concept_type: str
    properties: Dict[str, Any]
    domains: List[str]
    confidence: float = 0.8

@dataclass
class MinedRelationship:
    """A relationship mined from the LLM"""
    source_concept: str
    target_concept: str
    relationship_type: str
    strength: float
    evidence: List[str]

class LLMKnowledgeMiner:
    """
    Mines structured knowledge from LLM to bootstrap Knowledge Graph
    """
    
    def __init__(self, llm_driver=None, knowledge_graph=None):
        self.llm_driver = llm_driver
        self.knowledge_graph = knowledge_graph or KnowledgeGraphEvolution(llm_driver)
        self.mined_concepts: Dict[str, MinedConcept] = {}
        self.mined_relationships: List[MinedRelationship] = []
        
    async def initialize(self):
        """Initialize the knowledge miner"""
        if not self.llm_driver:
            self.llm_driver = await get_llm_cognitive_driver()
        logger.info("LLM Knowledge Miner initialized")
        
    async def mine_domain_knowledge(self, domain: str, depth: int = 2) -> Dict[str, Any]:
        """
        Mine comprehensive knowledge about a specific domain
        
        Args:
            domain: The domain to mine (e.g., "artificial intelligence", "cognitive science")
            depth: How deep to mine (1=basic, 2=intermediate, 3=comprehensive)
            
        Returns:
            Dictionary with mining results and statistics
        """
        logger.info(f"Mining knowledge for domain: {domain} at depth {depth}")
        
        # Step 1: Get core concepts for this domain
        concepts = await self._mine_core_concepts(domain, depth)
        logger.info(f"Mined {len(concepts)} core concepts")
        
        # Step 2: Get relationships between concepts
        relationships = await self._mine_relationships(concepts)
        logger.info(f"Mined {len(relationships)} relationships")
        
        # Step 3: Expand with detailed knowledge for each concept
        if depth >= 2:
            for concept in concepts[:10]:  # Limit expansion to prevent explosion
                await self._expand_concept_knowledge(concept)
        
        # Step 4: Add all to knowledge graph
        added_concepts = await self._add_to_knowledge_graph(concepts, relationships)
        
        return {
            "domain": domain,
            "concepts_mined": len(concepts),
            "relationships_mined": len(relationships),
            "concepts_added": added_concepts,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _mine_core_concepts(self, domain: str, depth: int) -> List[MinedConcept]:
        """Mine core concepts for a domain from the LLM"""
        
        prompt = f"""
Generate comprehensive knowledge about the domain: {domain}

Provide a structured list of key concepts in this domain. For each concept include:
1. Name (concise, 2-4 words)
2. Description (detailed, 1-2 sentences)
3. Type (one of: fundamental, intermediate, advanced, tool, method, theory, application)
4. Properties (key attributes as a dictionary)
5. Related domains/subfields

Depth level: {depth} (1=basic, 2=intermediate, 3=expert)
Number of concepts: {10 if depth == 1 else 20 if depth == 2 else 30}

Return as JSON array:
[
  {{
    "name": "Concept Name",
    "description": "Detailed description of the concept",
    "concept_type": "fundamental|intermediate|advanced|tool|method|theory|application",
    "properties": {{
      "complexity": "low|medium|high",
      "practical_applications": ["app1", "app2"],
      "prerequisites": ["prereq1", "prereq2"]
    }},
    "domains": ["subdomain1", "subdomain2"],
    "confidence": 0.9
  }}
]
"""
        
        response = await self.llm_driver._call_llm(prompt, max_tokens=4000)
        
        try:
            # Parse JSON response
            concepts_data = self._extract_json(response)
            
            concepts = []
            for concept_data in concepts_data:
                concept = MinedConcept(
                    name=concept_data.get("name", "Unknown"),
                    description=concept_data.get("description", ""),
                    concept_type=concept_data.get("concept_type", "general"),
                    properties=concept_data.get("properties", {}),
                    domains=concept_data.get("domains", [domain]),
                    confidence=concept_data.get("confidence", 0.8)
                )
                concepts.append(concept)
                self.mined_concepts[concept.name] = concept
            
            return concepts
            
        except Exception as e:
            logger.error(f"Failed to parse concepts: {e}")
            return []
    
    async def _mine_relationships(self, concepts: List[MinedConcept]) -> List[MinedRelationship]:
        """Mine relationships between concepts from the LLM"""
        
        concept_names = [c.name for c in concepts[:30]]  # Limit to prevent token overflow
        
        prompt = f"""
Given these concepts, identify and describe the relationships between them:

Concepts: {', '.join(concept_names)}

For each meaningful relationship, provide:
1. Source concept name (must be from the list above)
2. Target concept name (must be from the list above)
3. Relationship type (causal, hierarchical, semantic, functional, associative, uses, includes, related_to)
4. Strength (0.0-1.0)
5. Evidence/reasoning for the relationship

Return as JSON array:
[
  {{
    "source": "Source Concept",
    "target": "Target Concept",
    "relationship_type": "causal|hierarchical|semantic|functional|associative|uses|includes|related_to",
    "strength": 0.8,
    "evidence": ["Reason for this relationship"]
  }}
]

Aim for {len(concepts) * 2} high-quality relationships. Focus on the most meaningful connections.
"""
        
        response = await self.llm_driver._call_llm(prompt, max_tokens=4000)
        
        try:
            relationships_data = self._extract_json(response)
            
            relationships = []
            for rel_data in relationships_data:
                source = rel_data.get("source", "")
                target = rel_data.get("target", "")
                
                # Validate that concepts exist
                if source in self.mined_concepts and target in self.mined_concepts:
                    relationship = MinedRelationship(
                        source_concept=source,
                        target_concept=target,
                        relationship_type=rel_data.get("relationship_type", "related_to"),
                        strength=rel_data.get("strength", 0.5),
                        evidence=rel_data.get("evidence", [])
                    )
                    relationships.append(relationship)
                    self.mined_relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Failed to parse relationships: {e}")
            return []
    
    async def _expand_concept_knowledge(self, concept: MinedConcept) -> Dict[str, Any]:
        """Expand a concept with more detailed knowledge"""
        
        prompt = f"""
Provide detailed knowledge about: {concept.name}

Description: {concept.description}

Generate:
1. Key facts and principles
2. Common misconceptions
3. Historical context
4. Practical applications
5. Related sub-concepts
6. Important examples

Return as JSON:
{{
  "facts": ["fact1", "fact2", "fact3"],
  "misconceptions": ["misconception1", "misconception2"],
  "historical_context": "Brief history",
  "applications": ["app1", "app2", "app3"],
  "sub_concepts": ["sub1", "sub2"],
  "examples": ["example1", "example2"]
}}
"""
        
        response = await self.llm_driver._call_llm(prompt, max_tokens=2000)
        
        try:
            expansion_data = self._extract_json(response)
            
            # Update concept properties with expanded knowledge
            concept.properties.update({
                "facts": expansion_data.get("facts", []),
                "misconceptions": expansion_data.get("misconceptions", []),
                "historical_context": expansion_data.get("historical_context", ""),
                "applications": expansion_data.get("applications", []),
                "sub_concepts": expansion_data.get("sub_concepts", []),
                "examples": expansion_data.get("examples", [])
            })
            
            return expansion_data
            
        except Exception as e:
            logger.error(f"Failed to expand concept {concept.name}: {e}")
            return {}
    
    async def _add_to_knowledge_graph(self, 
                                     concepts: List[MinedConcept], 
                                     relationships: List[MinedRelationship]) -> int:
        """Add mined knowledge to the knowledge graph"""
        
        added_count = 0
        
        # Add concepts
        for concept in concepts:
            try:
                concept_data = {
                    "name": concept.name,
                    "description": concept.description,
                    "type": concept.concept_type,
                    "properties": concept.properties,
                    "domains": concept.domains,
                    "confidence": concept.confidence,
                    "activation_strength": 0.5,  # Initial activation
                    "evidence": ["llm_knowledge_mining"]
                }
                
                await self.knowledge_graph.add_concept(
                    concept_data=concept_data,
                    auto_connect=False  # We'll add explicit relationships
                )
                added_count += 1
                
            except Exception as e:
                logger.error(f"Failed to add concept {concept.name}: {e}")
        
        # Add relationships
        for rel in relationships:
            try:
                # Find concept IDs (may need to map names to IDs)
                source_concept = next((c for c in self.knowledge_graph.concepts.values() 
                                     if c.name == rel.source_concept), None)
                target_concept = next((c for c in self.knowledge_graph.concepts.values() 
                                     if c.name == rel.target_concept), None)
                
                if source_concept and target_concept:
                    # Map string relationship type to enum
                    rel_type = self._map_relationship_type(rel.relationship_type)
                    
                    await self.knowledge_graph.create_relationship(
                        source_id=source_concept.id,
                        target_id=target_concept.id,
                        relationship_type=rel_type,
                        strength=rel.strength,
                        evidence=rel.evidence
                    )
                    
            except Exception as e:
                logger.error(f"Failed to add relationship {rel.source_concept} -> {rel.target_concept}: {e}")
        
        # Trigger evolution to integrate new knowledge
        await self.knowledge_graph.evolve_knowledge_graph(
            trigger=EvolutionTrigger.NEW_INFORMATION,
            context={
                "source": "llm_knowledge_mining",
                "concepts_added": len(concepts),
                "relationships_added": len(relationships)
            }
        )
        
        logger.info(f"Added {added_count} concepts and {len(relationships)} relationships to knowledge graph")
        return added_count
    
    def _map_relationship_type(self, rel_type_str: str) -> RelationshipType:
        """Map string relationship type to enum"""
        mapping = {
            "causal": RelationshipType.CAUSAL,
            "hierarchical": RelationshipType.HIERARCHICAL,
            "semantic": RelationshipType.SEMANTIC,
            "functional": RelationshipType.FUNCTIONAL,
            "associative": RelationshipType.ASSOCIATIVE,
            "uses": RelationshipType.USES,
            "includes": RelationshipType.INCLUDES,
            "related_to": RelationshipType.RELATED_TO,
            "temporal": RelationshipType.TEMPORAL,
            "compositional": RelationshipType.COMPOSITIONAL
        }
        return mapping.get(rel_type_str.lower(), RelationshipType.RELATED_TO)
    
    def _extract_json(self, response: str) -> Any:
        """Extract JSON from LLM response"""
        try:
            # Try to find JSON in the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # Try object syntax
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
            # Try parsing whole response
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return [] if '[' in response else {}
    
    async def mine_interconnected_domains(self, domains: List[str]) -> Dict[str, Any]:
        """
        Mine multiple domains and discover cross-domain relationships
        
        Args:
            domains: List of domain names to mine
            
        Returns:
            Mining results with cross-domain insights
        """
        logger.info(f"Mining {len(domains)} interconnected domains")
        
        all_concepts = []
        domain_results = {}
        
        # Mine each domain
        for domain in domains:
            result = await self.mine_domain_knowledge(domain, depth=2)
            domain_results[domain] = result
            all_concepts.extend(self.mined_concepts.values())
        
        # Discover cross-domain relationships
        cross_domain_rels = await self._mine_cross_domain_relationships(domains)
        
        return {
            "domains_mined": domains,
            "total_concepts": len(all_concepts),
            "total_relationships": len(self.mined_relationships),
            "cross_domain_relationships": len(cross_domain_rels),
            "domain_results": domain_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _mine_cross_domain_relationships(self, domains: List[str]) -> List[MinedRelationship]:
        """Discover relationships that span multiple domains"""
        
        # Get concepts from each domain
        domain_concepts = {domain: [] for domain in domains}
        for concept in self.mined_concepts.values():
            for domain in concept.domains:
                if domain in domain_concepts:
                    domain_concepts[domain].append(concept.name)
        
        prompt = f"""
Identify cross-domain relationships and connections between these domains:

{json.dumps(domain_concepts, indent=2)}

Focus on:
1. Concepts from different domains that are related
2. Methods/techniques that apply across domains
3. Shared principles or theories
4. Applications that bridge domains

Return as JSON array of relationships:
[
  {{
    "source": "Concept from domain A",
    "target": "Concept from domain B",
    "relationship_type": "applies_to|bridges|shares_principle|enables",
    "strength": 0.7,
    "evidence": ["Cross-domain insight"],
    "domains_connected": ["domain_a", "domain_b"]
  }}
]
"""
        
        response = await self.llm_driver._call_llm(prompt, max_tokens=3000)
        
        try:
            cross_rels_data = self._extract_json(response)
            
            cross_rels = []
            for rel_data in cross_rels_data:
                source = rel_data.get("source", "")
                target = rel_data.get("target", "")
                
                if source in self.mined_concepts and target in self.mined_concepts:
                    rel = MinedRelationship(
                        source_concept=source,
                        target_concept=target,
                        relationship_type=rel_data.get("relationship_type", "related_to"),
                        strength=rel_data.get("strength", 0.6),
                        evidence=rel_data.get("evidence", []) + ["cross_domain_mining"]
                    )
                    cross_rels.append(rel)
                    self.mined_relationships.append(rel)
            
            # Add cross-domain relationships to graph
            await self._add_to_knowledge_graph([], cross_rels)
            
            return cross_rels
            
        except Exception as e:
            logger.error(f"Failed to mine cross-domain relationships: {e}")
            return []
    
    async def bootstrap_system_knowledge(self) -> Dict[str, Any]:
        """
        Bootstrap the knowledge graph with essential system knowledge
        
        This provides initial seeding for GödelOS-specific concepts
        """
        logger.info("Bootstrapping system knowledge")
        
        # Define core domains for GödelOS
        core_domains = [
            "cognitive architecture",
            "consciousness models",
            "knowledge representation",
            "meta-cognition",
            "autonomous learning",
            "attention mechanisms",
            "working memory systems"
        ]
        
        result = await self.mine_interconnected_domains(core_domains)
        
        # Add GödelOS-specific concepts
        await self._add_godelos_specific_knowledge()
        
        return result
    
    async def _add_godelos_specific_knowledge(self):
        """Add GödelOS-specific concepts to the knowledge graph"""
        
        prompt = """
Generate detailed knowledge about GödelOS - a consciousness-like AI architecture with these components:

- Real-time cognitive streaming
- Transparency dashboard
- LLM-driven cognitive control
- Phenomenal experience generator
- Meta-cognition modules
- Knowledge graph evolution
- Autonomous goal management

For each component, provide:
1. Name and description
2. Key capabilities
3. Relationships to other components
4. Consciousness manifestation aspects

Return as JSON with concepts and relationships.
"""
        
        response = await self.llm_driver._call_llm(prompt, max_tokens=3000)
        
        try:
            godelos_data = self._extract_json(response)
            
            # Parse and add GödelOS-specific concepts
            if "concepts" in godelos_data:
                concepts = [MinedConcept(
                    name=c["name"],
                    description=c.get("description", ""),
                    concept_type="system_component",
                    properties=c.get("properties", {}),
                    domains=["godelos_architecture"],
                    confidence=0.95
                ) for c in godelos_data["concepts"]]
                
                relationships = [MinedRelationship(
                    source_concept=r["source"],
                    target_concept=r["target"],
                    relationship_type=r.get("type", "related_to"),
                    strength=r.get("strength", 0.8),
                    evidence=["godelos_architecture_specification"]
                ) for r in godelos_data.get("relationships", [])]
                
                await self._add_to_knowledge_graph(concepts, relationships)
                
        except Exception as e:
            logger.error(f"Failed to add GödelOS-specific knowledge: {e}")


# Global instance
_llm_knowledge_miner: Optional[LLMKnowledgeMiner] = None

async def get_llm_knowledge_miner(llm_driver=None, knowledge_graph=None) -> LLMKnowledgeMiner:
    """Get or create the global LLM knowledge miner instance"""
    global _llm_knowledge_miner
    
    if _llm_knowledge_miner is None:
        _llm_knowledge_miner = LLMKnowledgeMiner(llm_driver, knowledge_graph)
        await _llm_knowledge_miner.initialize()
    
    return _llm_knowledge_miner
