"""
Dynamic Knowledge Processor

Implements comprehensive document processing that extracts hierarchical concepts
from aggregated principles down to atomic elements, creating dynamic knowledge graphs
and connecting to live reasoning sessions.
"""

import asyncio
import json
import logging
import re
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
from pathlib import Path

import spacy
from textstat import flesch_reading_ease, flesch_kincaid_grade

logger = logging.getLogger(__name__)

@dataclass
class ConceptNode:
    """Represents a concept in the knowledge hierarchy."""
    id: str
    name: str
    type: str  # 'atomic', 'aggregated', 'meta', 'domain'
    level: int  # 0=atomic, 1=basic, 2=complex, 3=meta
    description: str
    examples: List[str]
    relations: List[str]  # IDs of related concepts
    confidence: float
    source_documents: List[str]
    extraction_method: str
    metadata: Dict[str, Any]

@dataclass
class ConceptRelation:
    """Represents a relationship between concepts."""
    id: str
    source_id: str
    target_id: str
    relation_type: str  # 'part_of', 'depends_on', 'exemplifies', 'generalizes', etc.
    strength: float
    evidence: List[str]
    source_sentences: List[str]
    confidence: float

@dataclass
class DocumentProcessingResult:
    """Result of processing a document."""
    document_id: str
    title: str
    concepts: List[ConceptNode]
    relations: List[ConceptRelation]
    atomic_principles: List[ConceptNode]
    aggregated_concepts: List[ConceptNode]
    meta_concepts: List[ConceptNode]
    domain_categories: List[str]
    processing_metrics: Dict[str, Any]
    knowledge_graph: Dict[str, Any]

class DynamicKnowledgeProcessor:
    """
    Advanced knowledge processor that extracts hierarchical concepts and relationships
    from documents, creating dynamic knowledge graphs with live reasoning integration.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the dynamic knowledge processor."""
        self.model_name = model_name
        self.nlp = None
        self.concept_store: Dict[str, ConceptNode] = {}
        self.relation_store: Dict[str, ConceptRelation] = {}
        self.processing_sessions: Dict[str, Dict] = {}
        self.domain_ontologies = self._load_domain_ontologies()
        self.concept_patterns = self._define_concept_patterns()
        self.relation_patterns = self._define_relation_patterns()
        self.atomic_indicators = self._define_atomic_indicators()
        
    async def initialize(self):
        """Initialize the NLP model and processing components."""
        try:
            logger.info("🔄 Initializing Dynamic Knowledge Processor...")
            self.nlp = spacy.load(self.model_name)
            
            # Add custom components for concept extraction
            # TODO: Implement concept_extractor component
            # if "concept_extractor" not in self.nlp.pipe_names:
            #     self.nlp.add_pipe("concept_extractor", last=True, config={})
            
            # Populate with initial knowledge from system components
            await self._populate_initial_knowledge()
                
            logger.info("✅ Dynamic Knowledge Processor initialized successfully")
        except OSError:
            logger.warning(f"SpaCy model {self.model_name} not found, using fallback processing")
            self.nlp = None
            # Still populate initial knowledge even without NLP
            await self._populate_initial_knowledge()
    
    async def _populate_initial_knowledge(self):
        """Populate the knowledge store with initial system knowledge."""
        logger.info("🔄 Populating initial knowledge base...")
        
        # Define core system concepts
        core_concepts = [
            {
                "name": "Consciousness",
                "type": "meta",
                "level": 3,
                "description": "Higher-order awareness and subjective experience in cognitive systems",
                "examples": ["self-awareness", "subjective experience", "qualia"],
                "metadata": {"concept_category": "philosophy", "domain": "consciousness_studies"}
            },
            {
                "name": "Cognitive Architecture",
                "type": "aggregated", 
                "level": 2,
                "description": "Structural framework for cognitive processing and reasoning",
                "examples": ["working memory", "attention mechanisms", "reasoning engines"],
                "metadata": {"concept_category": "technology", "domain": "artificial_intelligence"}
            },
            {
                "name": "Meta-cognition",
                "type": "aggregated",
                "level": 2, 
                "description": "Thinking about thinking processes and self-reflective analysis",
                "examples": ["self-monitoring", "cognitive reflection", "metacognitive awareness"],
                "metadata": {"concept_category": "psychology", "domain": "cognitive_science"}
            },
            {
                "name": "Working Memory",
                "type": "atomic",
                "level": 1,
                "description": "Active maintenance and manipulation of information during cognitive tasks",
                "examples": ["temporary storage", "information processing", "cognitive buffer"],
                "metadata": {"concept_category": "cognition", "domain": "memory_systems"}
            },
            {
                "name": "Attention Focus", 
                "type": "atomic",
                "level": 1,
                "description": "Selective concentration on specific aspects of information processing",
                "examples": ["selective attention", "focus control", "attentional filtering"],
                "metadata": {"concept_category": "cognition", "domain": "attention_systems"}
            },
            {
                "name": "Knowledge Graph",
                "type": "aggregated",
                "level": 2,
                "description": "Structured representation of knowledge entities and their relationships", 
                "examples": ["semantic networks", "entity relationships", "knowledge representation"],
                "metadata": {"concept_category": "technology", "domain": "knowledge_management"}
            },
            {
                "name": "Reasoning Process",
                "type": "aggregated",
                "level": 2,
                "description": "Logical inference and deductive cognitive processing mechanisms",
                "examples": ["logical inference", "deductive reasoning", "cognitive reasoning"],
                "metadata": {"concept_category": "cognition", "domain": "reasoning_systems"}
            },
            {
                "name": "Transparency",
                "type": "aggregated",
                "level": 2,
                "description": "System introspection and cognitive process visibility for analysis",
                "examples": ["cognitive monitoring", "process visibility", "introspective analysis"],
                "metadata": {"concept_category": "system", "domain": "system_architecture"}
            },
            {
                "name": "Autonomous Learning",
                "type": "aggregated",
                "level": 2, 
                "description": "Self-directed learning and knowledge acquisition mechanisms",
                "examples": ["self-improvement", "knowledge acquisition", "adaptive learning"],
                "metadata": {"concept_category": "learning", "domain": "machine_learning"}
            },
            {
                "name": "LLM Integration",
                "type": "aggregated",
                "level": 2,
                "description": "Integration layer for large language model cognitive processing",
                "examples": ["language processing", "neural integration", "cognitive enhancement"],
                "metadata": {"concept_category": "technology", "domain": "artificial_intelligence"}
            }
        ]
        
        # Create concept nodes
        for concept_data in core_concepts:
            concept_id = f"concept_{concept_data['name'].lower().replace(' ', '_').replace('-', '_')}"
            
            concept = ConceptNode(
                id=concept_id,
                name=concept_data["name"],
                type=concept_data["type"],
                level=concept_data["level"],
                description=concept_data["description"],
                examples=concept_data["examples"],
                relations=[],
                confidence=0.95,  # High confidence for core concepts
                source_documents=["system_initialization"],
                extraction_method="core_knowledge",
                metadata=concept_data["metadata"]
            )
            
            self.concept_store[concept_id] = concept
        
        # Define relationships between concepts
        relationships = [
            ("concept_consciousness", "concept_meta_cognition", "includes", 0.9),
            ("concept_consciousness", "concept_working_memory", "utilizes", 0.8),
            ("concept_cognitive_architecture", "concept_working_memory", "implements", 0.9),
            ("concept_cognitive_architecture", "concept_attention_focus", "implements", 0.9),
            ("concept_cognitive_architecture", "concept_reasoning_process", "supports", 0.8),
            ("concept_meta_cognition", "concept_reasoning_process", "enhances", 0.8),
            ("concept_knowledge_graph", "concept_reasoning_process", "supports", 0.7),
            ("concept_transparency", "concept_consciousness", "enables", 0.7),
            ("concept_autonomous_learning", "concept_meta_cognition", "requires", 0.8),
            ("concept_llm_integration", "concept_cognitive_architecture", "extends", 0.8),
            ("concept_llm_integration", "concept_reasoning_process", "augments", 0.9),
            ("concept_working_memory", "concept_attention_focus", "coordinates_with", 0.7),
            ("concept_transparency", "concept_reasoning_process", "monitors", 0.8),
            ("concept_autonomous_learning", "concept_knowledge_graph", "updates", 0.7)
        ]
        
        # Create relationship objects
        for source_id, target_id, relation_type, strength in relationships:
            if source_id in self.concept_store and target_id in self.concept_store:
                relation_id = f"rel_{source_id}_{target_id}_{relation_type}"
                
                relation = ConceptRelation(
                    id=relation_id,
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    strength=strength,
                    evidence=["system_architecture_analysis"],
                    source_sentences=[f"{self.concept_store[source_id].name} {relation_type.replace('_', ' ')} {self.concept_store[target_id].name}"],
                    confidence=strength
                )
                
                self.relation_store[relation_id] = relation
                
                # Update concept relations
                self.concept_store[source_id].relations.append(target_id)
                if target_id not in self.concept_store[target_id].relations:
                    self.concept_store[target_id].relations.append(source_id)
        
        logger.info(f"✅ Populated knowledge base with {len(self.concept_store)} concepts and {len(self.relation_store)} relationships")
    
    async def process_document(self, content: str, title: str = None, metadata: Dict = None) -> DocumentProcessingResult:
        """
        Process a document and extract hierarchical knowledge structures.
        
        Args:
            content: Document text content
            title: Document title
            metadata: Additional document metadata
            
        Returns:
            DocumentProcessingResult with extracted concepts and relationships
        """
        start_time = time.time()
        document_id = str(uuid.uuid4())
        session_id = f"processing_{document_id[:8]}"
        
        # Initialize processing session
        self.processing_sessions[session_id] = {
            "document_id": document_id,
            "title": title or "Untitled",
            "start_time": start_time,
            "status": "processing",
            "steps_completed": [],
            "current_step": "initialization"
        }
        
        try:
            logger.info(f"📄 Processing document: {title or 'Untitled'}")
            
            # Step 1: Text preprocessing and analysis
            await self._update_session(session_id, "text_preprocessing", "Preprocessing text content")
            preprocessed_text, text_metrics = await self._preprocess_text(content)
            
            # Step 2: Extract atomic principles
            await self._update_session(session_id, "atomic_extraction", "Extracting atomic principles")
            atomic_principles = await self._extract_atomic_principles(preprocessed_text, document_id)
            
            # Step 3: Extract aggregated concepts
            await self._update_session(session_id, "aggregated_extraction", "Extracting aggregated concepts")
            aggregated_concepts = await self._extract_aggregated_concepts(preprocessed_text, atomic_principles, document_id)
            
            # Step 4: Extract meta-concepts and domains
            await self._update_session(session_id, "meta_extraction", "Extracting meta-concepts and domains")
            meta_concepts, domain_categories = await self._extract_meta_concepts(preprocessed_text, aggregated_concepts, document_id)
            
            # Step 5: Build relationships
            await self._update_session(session_id, "relationship_building", "Building concept relationships")
            all_concepts = atomic_principles + aggregated_concepts + meta_concepts
            relations = await self._build_concept_relations(all_concepts, preprocessed_text, document_id)
            
            # Step 6: Create knowledge graph structure
            await self._update_session(session_id, "graph_construction", "Constructing knowledge graph")
            knowledge_graph = await self._create_knowledge_graph(all_concepts, relations)
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            processing_metrics = {
                "processing_time_seconds": processing_time,
                "content_length": len(content),
                "sentences_processed": len(list(self.nlp(preprocessed_text).sents)) if self.nlp else content.count('.'),
                "atomic_principles_count": len(atomic_principles),
                "aggregated_concepts_count": len(aggregated_concepts),
                "meta_concepts_count": len(meta_concepts),
                "total_concepts": len(all_concepts),
                "relations_count": len(relations),
                "domain_categories": domain_categories,
                "text_complexity": text_metrics,
                "extraction_coverage": self._calculate_coverage(content, all_concepts)
            }
            
            # Mark session as completed
            await self._update_session(session_id, "completed", "Document processing completed successfully")
            
            result = DocumentProcessingResult(
                document_id=document_id,
                title=title or "Untitled",
                concepts=all_concepts,
                relations=relations,
                atomic_principles=atomic_principles,
                aggregated_concepts=aggregated_concepts,
                meta_concepts=meta_concepts,
                domain_categories=domain_categories,
                processing_metrics=processing_metrics,
                knowledge_graph=knowledge_graph
            )
            
            logger.info(f"✅ Document processed successfully:")
            logger.info(f"   - Atomic principles: {len(atomic_principles)}")
            logger.info(f"   - Aggregated concepts: {len(aggregated_concepts)}")  
            logger.info(f"   - Meta-concepts: {len(meta_concepts)}")
            logger.info(f"   - Relations: {len(relations)}")
            logger.info(f"   - Processing time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            await self._update_session(session_id, "failed", f"Processing failed: {str(e)}")
            logger.error(f"❌ Document processing failed: {e}")
            raise
    
    async def _preprocess_text(self, content: str) -> Tuple[str, Dict]:
        """Preprocess text and extract basic metrics."""
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\"\'\/]', '', text)  # Remove unusual characters
        
        # Calculate text complexity metrics
        metrics = {
            "word_count": len(text.split()),
            "sentence_count": text.count('.') + text.count('!') + text.count('?'),
            "paragraph_count": text.count('\n\n') + 1,
            "reading_ease": flesch_reading_ease(text) if text else 0,
            "grade_level": flesch_kincaid_grade(text) if text else 0,
            "avg_sentence_length": len(text.split()) / max(text.count('.') + text.count('!') + text.count('?'), 1)
        }
        
        return text, metrics
    
    async def _extract_atomic_principles(self, text: str, document_id: str) -> List[ConceptNode]:
        """Extract atomic principles - the most fundamental concepts."""
        atomic_concepts = []
        
        # Use patterns to identify atomic principles
        for pattern, principle_type in self.atomic_indicators.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end())
                concept = ConceptNode(
                    id=f"atomic_{len(atomic_concepts)}_{document_id[:8]}",
                    name=match.group().strip(),
                    type="atomic",
                    level=0,
                    description=context,
                    examples=[match.group()],
                    relations=[],
                    confidence=0.8,
                    source_documents=[document_id],
                    extraction_method="pattern_matching",
                    metadata={"principle_type": principle_type, "position": match.start()}
                )
                atomic_concepts.append(concept)
        
        # Use spaCy NER if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "LAW"]:
                    concept = ConceptNode(
                        id=f"atomic_ner_{len(atomic_concepts)}_{document_id[:8]}",
                        name=ent.text,
                        type="atomic",
                        level=0,
                        description=f"{ent.label_}: {ent.text}",
                        examples=[ent.text],
                        relations=[],
                        confidence=0.9,
                        source_documents=[document_id],
                        extraction_method="named_entity_recognition",
                        metadata={"entity_label": ent.label_, "start": ent.start_char, "end": ent.end_char}
                    )
                    atomic_concepts.append(concept)
        
        return atomic_concepts[:50]  # Limit to prevent explosion
    
    async def _extract_aggregated_concepts(self, text: str, atomic_principles: List[ConceptNode], document_id: str) -> List[ConceptNode]:
        """Extract aggregated concepts that combine atomic principles."""
        aggregated_concepts = []
        
        # Look for concept patterns
        for pattern, concept_info in self.concept_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end(), window=100)
                
                # Find related atomic principles
                related_atomics = []
                for atomic in atomic_principles:
                    if atomic.name.lower() in context.lower():
                        related_atomics.append(atomic.id)
                
                concept = ConceptNode(
                    id=f"aggregated_{len(aggregated_concepts)}_{document_id[:8]}",
                    name=match.group().strip(),
                    type="aggregated",
                    level=1,
                    description=context,
                    examples=[match.group()],
                    relations=related_atomics,
                    confidence=0.7,
                    source_documents=[document_id],
                    extraction_method="pattern_matching",
                    metadata={
                        "concept_category": concept_info["category"],
                        "complexity": concept_info["complexity"],
                        "atomic_dependencies": len(related_atomics)
                    }
                )
                aggregated_concepts.append(concept)
        
        # Extract noun phrases as potential aggregated concepts
        if self.nlp:
            doc = self.nlp(text)
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1 and len(chunk.text) > 5:  # Multi-word concepts
                    related_atomics = []
                    for atomic in atomic_principles:
                        if any(word in chunk.text.lower() for word in atomic.name.lower().split()):
                            related_atomics.append(atomic.id)
                    
                    concept = ConceptNode(
                        id=f"aggregated_np_{len(aggregated_concepts)}_{document_id[:8]}",
                        name=chunk.text,
                        type="aggregated",
                        level=1,
                        description=f"Noun phrase concept: {chunk.text}",
                        examples=[chunk.text],
                        relations=related_atomics,
                        confidence=0.6,
                        source_documents=[document_id],
                        extraction_method="noun_phrase_extraction",
                        metadata={"start": chunk.start_char, "end": chunk.end_char}
                    )
                    aggregated_concepts.append(concept)
        
        return aggregated_concepts[:30]  # Limit to prevent explosion
    
    async def _extract_meta_concepts(self, text: str, aggregated_concepts: List[ConceptNode], document_id: str) -> Tuple[List[ConceptNode], List[str]]:
        """Extract meta-concepts and identify domain categories."""
        meta_concepts = []
        domain_categories = set()
        
        # Identify domains from aggregated concepts
        for concept in aggregated_concepts:
            for domain, keywords in self.domain_ontologies.items():
                if any(keyword in concept.name.lower() for keyword in keywords):
                    domain_categories.add(domain)
        
        # Extract high-level thematic concepts
        theme_patterns = [
            (r'\b(?:principle|theory|framework|methodology|approach|paradigm|model)\b', "methodological"),
            (r'\b(?:system|architecture|structure|organization|design)\b', "structural"),  
            (r'\b(?:process|workflow|procedure|method|technique)\b', "procedural"),
            (r'\b(?:goal|objective|purpose|aim|intent|target)\b', "teleological"),
            (r'\b(?:constraint|limitation|requirement|condition)\b', "conditional")
        ]
        
        for pattern, meta_type in theme_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end(), window=150)
                
                # Find related aggregated concepts
                related_concepts = []
                for agg_concept in aggregated_concepts:
                    if agg_concept.name.lower() in context.lower():
                        related_concepts.append(agg_concept.id)
                
                concept = ConceptNode(
                    id=f"meta_{len(meta_concepts)}_{document_id[:8]}",
                    name=f"{meta_type.title()} {match.group()}",
                    type="meta",
                    level=2,
                    description=context,
                    examples=[match.group()],
                    relations=related_concepts,
                    confidence=0.6,
                    source_documents=[document_id],
                    extraction_method="meta_pattern_matching",
                    metadata={
                        "meta_type": meta_type,
                        "aggregated_dependencies": len(related_concepts)
                    }
                )
                meta_concepts.append(concept)
        
        return meta_concepts[:20], list(domain_categories)  # Limit meta concepts
    
    async def _build_concept_relations(self, concepts: List[ConceptNode], text: str, document_id: str) -> List[ConceptRelation]:
        """Build relationships between concepts based on textual analysis."""
        relations = []
        
        # Build relation from existing concept.relations references
        for concept in concepts:
            for related_id in concept.relations:
                related_concept = next((c for c in concepts if c.id == related_id), None)
                if related_concept:
                    relation = ConceptRelation(
                        id=f"rel_{len(relations)}_{document_id[:8]}",
                        source_id=concept.id,
                        target_id=related_id,
                        relation_type="contains" if concept.level > related_concept.level else "part_of",
                        strength=0.8,
                        evidence=[f"Found in context of {concept.name}"],
                        source_sentences=[concept.description[:100] + "..."],
                        confidence=0.7
                    )
                    relations.append(relation)
        
        # Look for explicit relationship patterns in text
        for pattern, relation_info in self.relation_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(text, match.start(), match.end(), window=200)
                
                # Find concepts mentioned in this context
                mentioned_concepts = []
                for concept in concepts:
                    if concept.name.lower() in context.lower():
                        mentioned_concepts.append(concept)
                
                # Create relations between mentioned concepts
                if len(mentioned_concepts) >= 2:
                    for i, source_concept in enumerate(mentioned_concepts[:-1]):
                        target_concept = mentioned_concepts[i + 1]
                        relation = ConceptRelation(
                            id=f"rel_pattern_{len(relations)}_{document_id[:8]}",
                            source_id=source_concept.id,
                            target_id=target_concept.id,
                            relation_type=relation_info["type"],
                            strength=relation_info["strength"],
                            evidence=[match.group()],
                            source_sentences=[context],
                            confidence=0.6
                        )
                        relations.append(relation)
        
        return relations
    
    async def _create_knowledge_graph(self, concepts: List[ConceptNode], relations: List[ConceptRelation]) -> Dict[str, Any]:
        """Create a knowledge graph structure for visualization."""
        nodes = []
        edges = []
        
        # Convert concepts to graph nodes
        for concept in concepts:
            node = {
                "id": concept.id,
                "label": concept.name,
                "type": concept.type,
                "level": concept.level,
                "category": concept.metadata.get("concept_category", concept.type),
                "size": 10 + concept.level * 3,  # Size based on concept level
                "confidence": concept.confidence,
                "description": concept.description,
                "metadata": concept.metadata
            }
            nodes.append(node)
        
        # Convert relations to graph edges
        for relation in relations:
            edge = {
                "source": relation.source_id,
                "target": relation.target_id,
                "type": relation.relation_type,
                "weight": relation.strength,
                "label": relation.relation_type.replace("_", " ").title(),
                "confidence": relation.confidence,
                "evidence": relation.evidence
            }
            edges.append(edge)
        
        # Calculate graph statistics
        level_counts = Counter(concept.level for concept in concepts)
        category_counts = Counter(concept.metadata.get("concept_category", concept.type) for concept in concepts)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "atomic_concepts": level_counts.get(0, 0),
                "aggregated_concepts": level_counts.get(1, 0),
                "meta_concepts": level_counts.get(2, 0),
                "categories": dict(category_counts),
                "avg_connections": len(edges) / max(len(nodes), 1),
                "data_source": "dynamic_processing"
            }
        }
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract contextual text around a match."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _calculate_coverage(self, original_text: str, concepts: List[ConceptNode]) -> float:
        """Calculate how much of the original text is covered by extracted concepts."""
        total_chars = len(original_text)
        covered_chars = 0
        
        for concept in concepts:
            if concept.name.lower() in original_text.lower():
                covered_chars += len(concept.name)
        
        return min(covered_chars / max(total_chars, 1), 1.0)
    
    async def _update_session(self, session_id: str, step: str, description: str):
        """Update processing session status."""
        if session_id in self.processing_sessions:
            self.processing_sessions[session_id]["current_step"] = step
            self.processing_sessions[session_id]["steps_completed"].append({
                "step": step,
                "description": description,
                "timestamp": time.time()
            })
    
    def _load_domain_ontologies(self) -> Dict[str, List[str]]:
        """Load domain-specific keyword ontologies."""
        return {
            "technology": ["software", "system", "algorithm", "data", "network", "computer", "digital", "ai", "machine", "programming"],
            "science": ["research", "experiment", "hypothesis", "theory", "method", "analysis", "observation", "evidence", "study", "discovery"],
            "business": ["organization", "management", "strategy", "market", "customer", "revenue", "profit", "company", "enterprise", "business"],
            "education": ["learning", "teaching", "knowledge", "curriculum", "student", "education", "instruction", "pedagogy", "academic", "training"],
            "health": ["medical", "patient", "treatment", "diagnosis", "healthcare", "clinical", "therapy", "medicine", "health", "disease"],
            "philosophy": ["consciousness", "ethics", "morality", "existence", "reality", "truth", "knowledge", "belief", "value", "meaning"],
            "psychology": ["behavior", "cognitive", "mental", "emotion", "perception", "memory", "learning", "personality", "motivation", "development"]
        }
    
    def _define_concept_patterns(self) -> Dict[str, Dict]:
        """Define patterns for identifying aggregated concepts."""
        return {
            r'\b(?:cognitive|mental|intellectual)\s+(?:process|function|ability|capacity)\b': {"category": "cognitive", "complexity": 2},
            r'\b(?:system|framework|architecture|structure)\s+(?:design|implementation|approach)\b': {"category": "structural", "complexity": 3},
            r'\b(?:learning|knowledge|information)\s+(?:acquisition|processing|management|representation)\b': {"category": "informational", "complexity": 2},
            r'\b(?:decision|problem|conflict)\s+(?:making|solving|resolution)\b': {"category": "procedural", "complexity": 2},
            r'\b(?:social|cultural|organizational)\s+(?:norm|pattern|behavior|structure)\b': {"category": "social", "complexity": 2},
            r'\b(?:data|information|knowledge)\s+(?:structure|model|representation|schema)\b': {"category": "representational", "complexity": 3}
        }
    
    def _define_relation_patterns(self) -> Dict[str, Dict]:
        """Define patterns for identifying concept relationships."""
        return {
            r'\b(?:consists?\s+of|comprises?|includes?|contains?)\b': {"type": "contains", "strength": 0.8},
            r'\b(?:depends?\s+on|requires?|needs?|relies?\s+on)\b': {"type": "depends_on", "strength": 0.7},
            r'\b(?:leads?\s+to|causes?|results?\s+in|produces?)\b': {"type": "causes", "strength": 0.8},
            r'\b(?:similar\s+to|like|resembles?|analogous\s+to)\b': {"type": "similar_to", "strength": 0.6},
            r'\b(?:different\s+from|unlike|contrasts?\s+with)\b': {"type": "contrasts_with", "strength": 0.6},
            r'\b(?:example\s+of|instance\s+of|type\s+of|kind\s+of)\b': {"type": "instance_of", "strength": 0.9}
        }
    
    def _define_atomic_indicators(self) -> Dict[str, str]:
        """Define patterns for identifying atomic principles."""
        return {
            r'\b(?:fact|truth|axiom|principle|law|rule|constant|element|unit|atom|basic|fundamental)\b': "foundational",
            r'\b(?:name|term|word|label|identifier|symbol|token|sign)\b': "linguistic",
            r'\b(?:number|quantity|amount|measure|count|value|score|rating)\b': "quantitative",
            r'\b(?:property|attribute|characteristic|feature|quality|trait|aspect)\b': "descriptive",
            r'\b(?:action|event|activity|process|operation|function|behavior)\b': "behavioral"
        }

# Global instance
dynamic_knowledge_processor = DynamicKnowledgeProcessor()