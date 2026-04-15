"""
Enhanced NLP Processor for GodelOS Knowledge Extraction.

Replaces DistilBERT with spaCy en_core_web_sm + sentencizer for NER/parsing
and rule-based relation extraction. Includes chunker, categorizer, and 
optimized embedding pipeline.
"""

import logging
import os
import hashlib
import json
import threading
import multiprocessing
from typing import List, Dict, Any, Tuple, Set, Optional
from pathlib import Path
from functools import lru_cache
import pickle

import spacy
from spacy.tokens import Doc, Span
from spacy.matcher import DependencyMatcher, PhraseMatcher
import numpy as np
from diskcache import Cache
from tqdm import tqdm

# Try to import sentence transformers for categorizer
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    SentenceTransformer = None

logger = logging.getLogger(__name__)

# Set thread environment variables to physical cores
physical_cores = multiprocessing.cpu_count() // 2  # Assuming hyperthreading
os.environ["OMP_NUM_THREADS"] = str(physical_cores)
os.environ["MKL_NUM_THREADS"] = str(physical_cores)
os.environ["OPENBLAS_NUM_THREADS"] = str(physical_cores)
os.environ["VECLIB_MAXIMUM_THREADS"] = str(physical_cores)
os.environ["NUMEXPR_NUM_THREADS"] = str(physical_cores)

class TextChunker:
    """
    Intelligent text chunker that creates ~1k character chunks 
    with sentence boundary awareness.
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, nlp_model=None) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks respecting sentence boundaries.
        
        Args:
            text: Text to chunk
            nlp_model: Optional spaCy model for sentence detection
            
        Returns:
            List of chunk dictionaries with text, start, end positions
        """
        if not text or len(text) <= self.chunk_size:
            return [{
                'text': text,
                'start': 0,
                'end': len(text),
                'chunk_id': 0
            }]
        
        chunks = []
        chunk_id = 0
        start = 0
        
        # Use spaCy for sentence detection if available
        if nlp_model:
            doc = nlp_model(text)
            sentences = [sent for sent in doc.sents]
        else:
            # Fallback to simple sentence splitting
            sentences = self._simple_sentence_split(text)
        
        current_chunk = ""
        current_start = 0
        
        for i, sent in enumerate(sentences):
            sent_text = sent.text if hasattr(sent, 'text') else str(sent)
            
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sent_text) > self.chunk_size and current_chunk:
                # Create chunk
                chunks.append({
                    'text': current_chunk.strip(),
                    'start': current_start,
                    'end': current_start + len(current_chunk),
                    'chunk_id': chunk_id
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_start = max(0, current_start + len(current_chunk) - self.overlap)
                current_chunk = text[overlap_start:current_start + len(current_chunk)] + " " + sent_text
                current_start = overlap_start
            else:
                if not current_chunk:
                    current_start = sent.start_char if hasattr(sent, 'start_char') else start
                current_chunk += (" " if current_chunk else "") + sent_text
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'start': current_start,
                'end': current_start + len(current_chunk),
                'chunk_id': chunk_id
            })
        
        return chunks
    
    def _simple_sentence_split(self, text: str) -> List[str]:
        """Simple sentence splitting fallback."""
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class PhraseDuplicator:
    """
    Deduplicates phrases before embedding to reduce redundancy.
    """
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize deduplicator.
        
        Args:
            similarity_threshold: Similarity threshold for considering phrases duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.phrase_cache = {}
    
    def deduplicate_phrases(self, phrases: List[str]) -> Tuple[List[str], Dict[str, str]]:
        """
        Remove duplicate phrases.
        
        Args:
            phrases: List of phrases to deduplicate
            
        Returns:
            Tuple of (unique_phrases, duplicate_mapping)
        """
        unique_phrases = []
        duplicate_mapping = {}
        
        for phrase in phrases:
            phrase_norm = self._normalize_phrase(phrase)
            
            # Check for exact duplicates first
            if phrase_norm in self.phrase_cache:
                duplicate_mapping[phrase] = self.phrase_cache[phrase_norm]
                continue
            
            # Check for near duplicates
            is_duplicate = False
            for unique_phrase in unique_phrases:
                if self._is_similar(phrase_norm, self._normalize_phrase(unique_phrase)):
                    duplicate_mapping[phrase] = unique_phrase
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_phrases.append(phrase)
                self.phrase_cache[phrase_norm] = phrase
        
        return unique_phrases, duplicate_mapping
    
    def _normalize_phrase(self, phrase: str) -> str:
        """Normalize phrase for comparison."""
        return phrase.lower().strip()
    
    def _is_similar(self, phrase1: str, phrase2: str) -> bool:
        """Check if two phrases are similar using simple similarity."""
        # Simple character-based similarity
        if len(phrase1) == 0 or len(phrase2) == 0:
            return False
        
        # Jaccard similarity on character n-grams
        ngrams1 = set(phrase1[i:i+3] for i in range(len(phrase1)-2))
        ngrams2 = set(phrase2[i:i+3] for i in range(len(phrase2)-2))
        
        if not ngrams1 or not ngrams2:
            return phrase1 == phrase2
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union >= self.similarity_threshold


class PersistentCache:
    """
    Persistent cache for processed results to avoid recomputation.
    """
    
    def __init__(self, cache_dir: str = ".cache/nlp_processor"):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_lock = threading.Lock()
    
    def get_cache_key(self, text: str, options: Dict = None) -> str:
        """Generate cache key for text and options."""
        content = text + str(sorted((options or {}).items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, cache_key: str) -> Optional[Dict]:
        """Get cached result."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        with self._cache_lock:
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load cache {cache_key}: {e}")
                    # Remove corrupted cache file
                    cache_file.unlink(missing_ok=True)
        
        return None
    
    def set(self, cache_key: str, result: Dict) -> None:
        """Cache result."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        with self._cache_lock:
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
            except Exception as e:
                logger.warning(f"Failed to cache result {cache_key}: {e}")
    
    def clear(self) -> None:
        """Clear all cached results."""
        with self._cache_lock:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)


class EnhancedNlpProcessor:
    """
    Enhanced NLP processor that replaces DistilBERT with spaCy en_core_web_sm + sentencizer
    for NER/parsing and rule-based relation extraction.
    """

    def __init__(self, 
                 spacy_model: str = "en_core_web_sm",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 batch_size: int = 32,
                 max_length: int = 192,
                 cache_dir: str = ".cache/nlp_processor"):
        """
        Initialize the enhanced NLP processor.

        Args:
            spacy_model: The name of the spaCy model to use for NER.
            embedding_model: The name of the sentence transformer model for embeddings.
            batch_size: Batch size for embedding generation.
            max_length: Maximum sequence length for embeddings.
            cache_dir: Directory for persistent cache.
        """
        self.spacy_model_name = spacy_model
        self.embedding_model_name = embedding_model
        self.batch_size = batch_size
        self.max_length = max_length
        
        # Initialize components
        self.nlp = None
        self.embedding_model = None
        self.chunker = TextChunker()
        self.deduplicator = PhraseDuplicator()
        self.cache = PersistentCache(cache_dir)
        
        # Rule matchers
        self.dependency_matcher = None
        self.phrase_matcher = None
        
        # Initialization flag
        self._initialized = False
        
        logger.info("Enhanced NLP Processor created (call initialize() to load models)")

    async def initialize(self):
        """
        Initialize the NLP processor by loading models and setting up components.
        This is separated from __init__ to allow for async model loading.
        """
        if self._initialized:
            return
            
        logger.info("Initializing Enhanced NLP Processor...")
        
        # Initialize components
        self._initialize_spacy()
        self._initialize_embedding_model()
        self._initialize_matchers()
        
        self._initialized = True
        logger.info("Enhanced NLP Processor initialized successfully")

    def _initialize_spacy(self):
        """Initialize spaCy model with fallback options."""
        try:
            self.nlp = spacy.load(self.spacy_model_name)
            
            # Add sentencizer if not present
            if "sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("sentencizer")
            
            logger.info(f"Successfully loaded spaCy model: {self.spacy_model_name}")
        except OSError:
            logger.warning(f"Spacy model '{self.spacy_model_name}' not found. Trying to download...")
            try:
                import subprocess
                result = subprocess.run(['python', '-m', 'spacy', 'download', self.spacy_model_name], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.nlp = spacy.load(self.spacy_model_name)
                    if "sentencizer" not in self.nlp.pipe_names:
                        self.nlp.add_pipe("sentencizer")
                    logger.info(f"Downloaded and loaded spaCy model: {self.spacy_model_name}")
                else:
                    raise OSError(f"Failed to download model: {result.stderr}")
            except Exception as e:
                logger.warning(f"Could not download spaCy model ({e}). Using blank model.")
                self.nlp = spacy.blank("en")
                self.nlp.add_pipe("sentencizer")

    def _initialize_embedding_model(self):
        """Initialize sentence transformer model for categorization."""
        if not HAS_SENTENCE_TRANSFORMERS:
            logger.warning("sentence-transformers not available. Categorization disabled.")
            return
        
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Successfully loaded embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.warning(f"Could not load embedding model ({e}). Categorization disabled.")
            self.embedding_model = None

    def _initialize_matchers(self):
        """Initialize dependency and phrase matchers for rule-based relation extraction."""
        if self.nlp is None:
            return
        
        # Initialize dependency matcher
        self.dependency_matcher = DependencyMatcher(self.nlp.vocab)
        
        # Initialize phrase matcher
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
        
        # Add common relation patterns
        self._add_relation_patterns()
        
        logger.info("Rule matchers initialized")

    def _add_relation_patterns(self):
        """Add rule patterns for relation extraction."""
        if not self.dependency_matcher or not self.phrase_matcher:
            return
        
        # CEO/Leadership patterns
        ceo_pattern = [
            {"RIGHT_ID": "ceo", "RIGHT_ATTRS": {"LEMMA": {"IN": ["ceo", "president", "founder", "director"]}}},
            {"LEFT_ID": "ceo", "REL_OP": ">", "RIGHT_ID": "org", "RIGHT_ATTRS": {"ENT_TYPE": "ORG"}}
        ]
        self.dependency_matcher.add("CEO_OF", [ceo_pattern])
        
        # Location patterns
        location_pattern = [
            {"RIGHT_ID": "location_verb", "RIGHT_ATTRS": {"LEMMA": {"IN": ["base", "locate", "headquarter"]}}},
            {"LEFT_ID": "location_verb", "REL_OP": ">", "RIGHT_ID": "location", "RIGHT_ATTRS": {"ENT_TYPE": {"IN": ["GPE", "LOC"]}}}
        ]
        self.dependency_matcher.add("LOCATED_IN", [location_pattern])
        
        # Employment patterns
        work_pattern = [
            {"RIGHT_ID": "work_verb", "RIGHT_ATTRS": {"LEMMA": {"IN": ["work", "employ", "hire"]}}},
            {"LEFT_ID": "work_verb", "REL_OP": ">", "RIGHT_ID": "org", "RIGHT_ATTRS": {"ENT_TYPE": "ORG"}}
        ]
        self.dependency_matcher.add("WORKS_FOR", [work_pattern])
        
        # Add phrase patterns for common relations
        relation_phrases = [
            ("CEO_OF", ["chief executive officer of", "ceo of", "chief executive of"]),
            ("FOUNDED", ["founded", "established", "started", "created"]),
            ("ACQUIRED", ["acquired", "bought", "purchased", "took over"]),
            ("PARTNERSHIP", ["partnered with", "collaborated with", "joint venture with"])
        ]
        
        for relation, phrases in relation_phrases:
            patterns = [self.nlp.make_doc(phrase) for phrase in phrases]
            self.phrase_matcher.add(relation, patterns)

    async def process(self, text: str, enable_categorization: bool = True) -> Dict[str, Any]:
        """
        Process a text document with enhanced NLP pipeline.
        
        Args:
            text: The text to process.
            enable_categorization: Whether to enable categorization.

        Returns:
            A dictionary containing the extracted entities, relationships, and categories.
        """
        if not self._initialized:
            raise RuntimeError("Processor not initialized. Call initialize() first.")
            
        if not text or not text.strip():
            return {"entities": [], "relationships": [], "categories": [], "chunks": []}
        
        # Check cache first
        cache_key = self.cache.get_cache_key(text, {"categorization": enable_categorization})
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info("Returning cached result")
            return cached_result
        
        logger.info(f"🔍 Enhanced NLP processing text with {len(text)} characters")
        
        try:
            # Step 1: Chunk the text
            chunks = self.chunker.chunk_text(text, self.nlp)
            logger.info(f"Text split into {len(chunks)} chunks")
            
            # Step 2: Process each chunk
            all_entities = []
            all_relationships = []
            processed_chunks = []
            
            for chunk in chunks:
                chunk_result = await self._process_chunk(chunk)
                all_entities.extend(chunk_result["entities"])
                all_relationships.extend(chunk_result["relationships"])
                processed_chunks.append(chunk_result)
            
            # Step 3: Deduplicate entities
            entity_texts = [ent["text"] for ent in all_entities]
            unique_entity_texts, entity_mapping = self.deduplicator.deduplicate_phrases(entity_texts)
            
            # Update entities with deduplicated results
            unique_entities = []
            for ent in all_entities:
                if ent["text"] in unique_entity_texts:
                    unique_entities.append(ent)
            
            logger.info(f"Deduplicated {len(all_entities)} entities to {len(unique_entities)}")
            
            # Step 4: Categorize text if enabled
            categories = []
            if enable_categorization and self.embedding_model:
                categories = await self._categorize_text(text, unique_entities)
            
            result = {
                "entities": unique_entities,
                "relationships": all_relationships,
                "categories": categories,
                "chunks": processed_chunks,
                "deduplication_stats": {
                    "original_count": len(all_entities),
                    "unique_count": len(unique_entities),
                    "duplicates_removed": len(all_entities) - len(unique_entities)
                }
            }
            
            # Cache the result
            self.cache.set(cache_key, result)
            
            logger.info(f"Processing complete: {len(unique_entities)} entities, {len(all_relationships)} relationships, {len(categories)} categories")
            return result
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            # Return basic fallback result
            return await self._process_with_fallback(text)

    async def _process_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single chunk of text."""
        text = chunk["text"]
        
        try:
            # Process with spaCy
            doc = self.nlp(text)
            
            # Extract entities
            entities = self._extract_entities_with_spacy(doc, chunk["start"])
            
            # Extract relationships using rule-based approach
            relationships = self._extract_relationships_with_rules(doc, entities)
            
            return {
                "entities": entities,
                "relationships": relationships,
                "chunk_info": chunk
            }
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            return {"entities": [], "relationships": [], "chunk_info": chunk}

    def _extract_entities_with_spacy(self, doc: Doc, chunk_offset: int = 0) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy."""
        entities = []
        
        # Extract named entities
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start_char": ent.start_char + chunk_offset,
                "end_char": ent.end_char + chunk_offset,
                "confidence": getattr(ent, "_.confidence", 1.0),  # Default confidence
                "description": spacy.explain(ent.label_) or ent.label_
            })
        
        # Extract additional noun phrases as potential entities
        for np in doc.noun_chunks:
            # Skip if already covered by named entities
            if any(np.start >= ent.start and np.end <= ent.end for ent in doc.ents):
                continue
            
            # Filter meaningful noun phrases
            if len(np.text.strip()) > 2 and np.root.pos_ in ["NOUN", "PROPN"]:
                entities.append({
                    "text": np.text,
                    "label": "NOUN_PHRASE",
                    "start_char": np.start_char + chunk_offset,
                    "end_char": np.end_char + chunk_offset,
                    "confidence": 0.7,  # Lower confidence for noun phrases
                    "description": "Noun phrase"
                })
        
        return entities

    def _extract_relationships_with_rules(self, doc: Doc, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships using rule-based dependency and phrase matching."""
        relationships = []
        
        if not self.dependency_matcher or not self.phrase_matcher:
            return relationships
        
        # Extract relationships using dependency matcher
        dep_matches = self.dependency_matcher(doc)
        for match_id, matches in dep_matches:
            relation_label = self.nlp.vocab.strings[match_id]
            for match in matches:
                # Extract the matched tokens and create relationship
                token_ids = [match[1][token_id] for token_id in range(len(match[1]))]
                if len(token_ids) >= 2:
                    source_token = doc[token_ids[0]]
                    target_token = doc[token_ids[1]]
                    
                    relationships.append({
                        "source": {"text": source_token.text, "label": "ENTITY"},
                        "target": {"text": target_token.text, "label": "ENTITY"},
                        "relation": relation_label,
                        "confidence": 0.8,
                        "sentence": source_token.sent.text,
                        "source_span": (source_token.idx, source_token.idx + len(source_token.text)),
                        "target_span": (target_token.idx, target_token.idx + len(target_token.text))
                    })
        
        # Extract relationships using phrase matcher
        phrase_matches = self.phrase_matcher(doc)
        for match_id, start, end in phrase_matches:
            relation_label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            # Find entities near this phrase
            sent = span.sent
            sent_entities = [ent for ent in entities 
                           if sent.start_char <= ent["start_char"] < sent.end_char]
            
            # Create relationships between entities in the same sentence
            for i, ent1 in enumerate(sent_entities):
                for ent2 in sent_entities[i+1:]:
                    relationships.append({
                        "source": {"text": ent1["text"], "label": ent1["label"]},
                        "target": {"text": ent2["text"], "label": ent2["label"]},
                        "relation": relation_label,
                        "confidence": 0.7,
                        "sentence": sent.text,
                        "trigger_phrase": span.text,
                        "source_span": (ent1["start_char"], ent1["end_char"]),
                        "target_span": (ent2["start_char"], ent2["end_char"])
                    })
        
        return relationships

    async def _categorize_text(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize text using sentence transformer embeddings."""
        if not self.embedding_model:
            return []
        
        try:
            # Prepare text snippets for categorization
            snippets = []
            
            # Add main text (first paragraph or chunk)
            first_paragraph = text.split('\n\n')[0][:500]  # First 500 chars
            snippets.append(first_paragraph)
            
            # Add entity contexts
            for ent in entities[:10]:  # Limit to first 10 entities
                # Extract context around entity (±100 chars)
                start = max(0, ent["start_char"] - 100)
                end = min(len(text), ent["end_char"] + 100)
                context = text[start:end]
                snippets.append(context)
            
            # Generate embeddings with optimization settings
            embeddings = self.embedding_model.encode(
                snippets,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_tensor=False,
                normalize_embeddings=True
            )
            
            # Predefined categories with their characteristic embeddings
            predefined_categories = {
                "Technology": ["artificial intelligence", "machine learning", "software development", "computer science"],
                "Business": ["company", "corporation", "business strategy", "market analysis"],
                "Science": ["research", "scientific method", "experiment", "hypothesis"],
                "Healthcare": ["medical", "health", "hospital", "treatment"],
                "Education": ["learning", "teaching", "university", "academic"],
                "Politics": ["government", "policy", "political", "legislation"],
                "Sports": ["athlete", "game", "competition", "sports"],
                "Entertainment": ["movie", "music", "celebrity", "entertainment"]
            }
            
            # Calculate category similarities
            categories = []
            main_embedding = embeddings[0]  # Use first snippet as main representation
            
            for category, keywords in predefined_categories.items():
                category_embeddings = self.embedding_model.encode(
                    keywords,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_tensor=False,
                    normalize_embeddings=True
                )
                
                # Calculate similarity
                similarities = np.dot(main_embedding, category_embeddings.T)
                max_similarity = float(np.max(similarities))
                avg_similarity = float(np.mean(similarities))
                
                if max_similarity > 0.3:  # Threshold for category assignment
                    categories.append({
                        "category": category,
                        "confidence": max_similarity,
                        "avg_confidence": avg_similarity,
                        "matched_keywords": [keywords[i] for i, sim in enumerate(similarities) if sim > 0.3]
                    })
            
            # Sort by confidence
            categories.sort(key=lambda x: x["confidence"], reverse=True)
            
            return categories[:5]  # Return top 5 categories
            
        except Exception as e:
            logger.error(f"Error in categorization: {e}")
            return []

    async def _process_with_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback processing when main pipeline fails."""
        logger.info("Using fallback processing")
        
        try:
            # Basic entity extraction using simple patterns
            entities = self._extract_basic_entities(text)
            
            return {
                "entities": entities,
                "relationships": [],
                "categories": [],
                "chunks": [{"text": text, "start": 0, "end": len(text), "chunk_id": 0}],
                "deduplication_stats": {"original_count": len(entities), "unique_count": len(entities), "duplicates_removed": 0}
            }
        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return {
                "entities": [],
                "relationships": [],
                "categories": [],
                "chunks": [],
                "deduplication_stats": {"original_count": 0, "unique_count": 0, "duplicates_removed": 0}
            }

    def _extract_basic_entities(self, text: str) -> List[Dict[str, Any]]:
        """Basic entity extraction using simple patterns when full NLP models are unavailable."""
        import re
        entities = []
        
        # Simple patterns for common entities
        patterns = {
            "PERSON": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last name pattern
            "ORG": r'\b[A-Z][a-zA-Z]+ (?:Inc|Corp|LLC|Ltd|Company|Corporation)\b',  # Company names
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            "URL": r'https?://[^\s]+',  # URLs
            "MONEY": r'\$[\d,]+(?:\.\d{2})?',  # Money amounts
            "DATE": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Dates
        }
        
        for label, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                entities.append({
                    "text": match.group(),
                    "label": label,
                    "start_char": match.start(),
                    "end_char": match.end(),
                    "confidence": 0.6,  # Lower confidence for pattern-based extraction
                    "description": f"Pattern-detected {label}"
                })
        
        return entities

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            "cache_stats": {
                "cache_dir": str(self.cache.cache_dir),
                "cache_files": len(list(self.cache.cache_dir.glob("*.pkl")))
            },
            "model_info": {
                "spacy_model": self.spacy_model_name,
                "embedding_model": self.embedding_model_name,
                "has_embedding_model": self.embedding_model is not None,
                "batch_size": self.batch_size,
                "max_length": self.max_length
            },
            "thread_config": {
                "physical_cores": physical_cores,
                "omp_threads": os.environ.get("OMP_NUM_THREADS"),
                "mkl_threads": os.environ.get("MKL_NUM_THREADS")
            }
        }

    def clear_cache(self):
        """Clear the persistent cache."""
        self.cache.clear()
        logger.info("Cache cleared")
