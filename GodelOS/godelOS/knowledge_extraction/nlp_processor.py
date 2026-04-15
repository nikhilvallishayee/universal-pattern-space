"""
NLP Processor for GodelOS Knowledge Extraction.
"""

import logging
import subprocess
from typing import List, Dict, Any, Tuple

import spacy
from spacy.tokens import Doc
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

logger = logging.getLogger(__name__)

class NlpProcessor:
    """
    Processes text to extract named entities and their relationships.
    """

    def __init__(self, spacy_model: str = "en_core_web_sm", hf_relation_model: str = "distilbert-base-cased-distilled-squad"):
        """
        Initialize the NLP processor with fallback options for offline mode.

        Args:
            spacy_model: The name of the spaCy model to use for NER.
            hf_relation_model: The name of the Hugging Face model for relation extraction.
        """
        # Initialize spaCy model with fallback to basic tokenizer
        self.nlp = None
        try:
            self.nlp = spacy.load(spacy_model)
            logger.info(f"Successfully loaded spaCy model: {spacy_model}")
        except OSError:
            logger.warning(f"Spacy model '{spacy_model}' not found. Trying fallback options...")
            try:
                # Try to download if network available
                import subprocess
                result = subprocess.run(['python', '-m', 'spacy', 'download', spacy_model], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self.nlp = spacy.load(spacy_model)
                    logger.info(f"Downloaded and loaded spaCy model: {spacy_model}")
                else:
                    raise OSError(f"Failed to download model: {result.stderr}")
            except (subprocess.TimeoutExpired, OSError, Exception) as e:
                logger.warning(f"Could not download spaCy model ({e}). Using blank model with basic tokenizer.")
                self.nlp = spacy.blank("en")
                # Add basic components
                if "tokenizer" not in self.nlp.pipe_names:
                    self.nlp.add_pipe("tokenizer")

        # Initialize HuggingFace model with fallback to basic text processing
        self.relation_extractor = None
        try:
            # Test if we can access HuggingFace
            import requests
            response = requests.get("https://huggingface.co", timeout=5)
            logger.info(f"Loading Hugging Face relation extraction model: {hf_relation_model}")
            self.relation_extractor = pipeline("question-answering", model=hf_relation_model)
            logger.info("HuggingFace model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load HuggingFace model ({e}). Using basic relation extraction fallback.")
            self.relation_extractor = None

        logger.info("NLP Processor initialized with available components.")

    async def process(self, text: str) -> Dict[str, List[Any]]:
        """
        Process a single text document to extract entities and relationships.
        For large documents, automatically chunks the text to prevent hanging.

        Args:
            text: The text to process.

        Returns:
            A dictionary containing the extracted entities and relationships.
        """
        logger.info(f"🔍 NLP PROCESS: Starting to process text with {len(text)} characters")
        logger.info(f"🔍 NLP PROCESS: Text preview: {repr(text[:200])}")
        logger.info(f"🔍 NLP PROCESS: spaCy model type: {type(self.nlp)}")
        logger.info(f"🔍 NLP PROCESS: spaCy model name: {getattr(self.nlp.meta, 'name', 'unknown') if hasattr(self.nlp, 'meta') else 'no meta'}")
        logger.info(f"🔍 NLP PROCESS: Available pipeline components: {self.nlp.pipe_names if hasattr(self.nlp, 'pipe_names') else 'no pipe_names'}")
        
        # Optimized size limits for speed and efficiency
        MAX_CHUNK_SIZE = 15000  # 15K characters per chunk (much smaller for speed)
        MAX_TOTAL_SIZE = 100000  # 100K total character limit (aggressive truncation)
        
        # Check if text is too large
        if len(text) > MAX_TOTAL_SIZE:
            logger.warning(f"🔍 NLP PROCESS: Text too large ({len(text)} chars), truncating to {MAX_TOTAL_SIZE} characters")
            text = text[:MAX_TOTAL_SIZE]
        
        # Process in chunks if text is large
        if len(text) > MAX_CHUNK_SIZE:
            logger.info(f"🔍 NLP PROCESS: Large text detected, processing in chunks of {MAX_CHUNK_SIZE} characters")
            return await self._process_chunked_text(text, MAX_CHUNK_SIZE)
        
        # Process normally for smaller texts
        logger.info(f"🔍 NLP PROCESS: Processing text as single chunk")
        try:
            doc = self.nlp(text)
            logger.info(f"🔍 NLP PROCESS: Created spaCy doc with {len(doc)} tokens")
            logger.info(f"🔍 NLP PROCESS: Doc has {len(list(doc.sents))} sentences")
            logger.info(f"🔍 NLP PROCESS: Doc ents attribute exists: {hasattr(doc, 'ents')}")
            logger.info(f"🔍 NLP PROCESS: Doc ents count: {len(doc.ents) if hasattr(doc, 'ents') else 'no ents'}")
            
            entities = self._extract_entities(doc)
            relationships = self._extract_relationships(doc, entities)

            logger.info(f"🔍 NLP PROCESS: Final result - {len(entities)} entities, {len(relationships)} relationships")
            
            return {
                "entities": entities,
                "relationships": relationships
            }
        except Exception as e:
            logger.error(f"🔍 NLP PROCESS: Error processing text: {e}")
            # Fallback to basic processing if spaCy fails
            return await self._process_with_fallback(text)

    async def _process_chunked_text(self, text: str, chunk_size: int) -> Dict[str, List[Any]]:
        """
        Process large text by breaking it into smaller chunks with intelligent sampling.
        
        Args:
            text: The text to process
            chunk_size: Size of each chunk
            
        Returns:
            Combined results from all chunks
        """
        logger.info(f"🔍 NLP PROCESS: Starting optimized chunked processing")
        
        all_entities = []
        all_relationships = []
        
        # Use intelligent sampling for very large documents
        chunks = self._split_text_into_chunks_smart(text, chunk_size)
        logger.info(f"🔍 NLP PROCESS: Split text into {len(chunks)} optimized chunks")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"🔍 NLP PROCESS: Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            try:
                doc = self.nlp(chunk)
                entities = self._extract_entities(doc)
                relationships = self._extract_relationships(doc, entities)
                
                # Adjust entity positions to account for chunk offset
                chunk_start = sum(len(chunks[j]) for j in range(i))
                for entity in entities:
                    if 'start_char' in entity:
                        entity['start_char'] += chunk_start
                    if 'end_char' in entity:
                        entity['end_char'] += chunk_start
                
                all_entities.extend(entities)
                all_relationships.extend(relationships)
                
                logger.info(f"🔍 NLP PROCESS: Chunk {i+1} processed: {len(entities)} entities, {len(relationships)} relationships")
                
            except Exception as e:
                logger.error(f"🔍 NLP PROCESS: Error processing chunk {i+1}: {e}")
                continue
        
        logger.info(f"🔍 NLP PROCESS: Chunked processing complete: {len(all_entities)} total entities, {len(all_relationships)} total relationships")
        
        return {
            "entities": all_entities,
            "relationships": all_relationships
        }

    def _split_text_into_chunks_smart(self, text: str, chunk_size: int) -> List[str]:
        """
        Intelligently split text into chunks using strategic sampling for large documents.
        For very large documents, we sample key sections rather than processing everything.
        
        Args:
            text: Text to split
            chunk_size: Target size per chunk
            
        Returns:
            List of strategically sampled text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        # For very large documents, use intelligent sampling
        if len(text) > 200000:  # > 200K chars
            logger.info(f"🔍 SMART CHUNKING: Large document detected, using strategic sampling")
            return self._sample_key_sections(text, chunk_size)
        
        # For medium documents, use regular chunking with fewer chunks
        return self._split_text_into_chunks(text, chunk_size)
    
    def _sample_key_sections(self, text: str, chunk_size: int) -> List[str]:
        """
        Sample key sections from a very large document for efficient processing.
        
        Args:
            text: Full text
            chunk_size: Size per chunk
            
        Returns:
            Key sections sampled from the document
        """
        sections = []
        text_len = len(text)
        
        # Sample beginning (abstract, introduction)
        beginning = text[:chunk_size]
        sections.append(beginning)
        
        # Sample middle sections (every 10% of document)
        for i in range(1, 5):  # Sample at 25%, 50%, 75%
            start_pos = int(text_len * (i * 0.25))
            end_pos = min(start_pos + chunk_size, text_len)
            if end_pos > start_pos:
                sections.append(text[start_pos:end_pos])
        
        # Sample conclusion
        if text_len > chunk_size:
            conclusion_start = max(text_len - chunk_size, text_len // 2)
            sections.append(text[conclusion_start:])
        
        logger.info(f"🔍 SMART CHUNKING: Sampled {len(sections)} key sections from large document")
        return sections

    def _split_text_into_chunks(self, text: str, chunk_size: int) -> List[str]:
        """
        Split text into chunks, preferring to break at sentence boundaries.
        
        Args:
            text: Text to split
            chunk_size: Target size for each chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            end_pos = current_pos + chunk_size
            
            if end_pos >= len(text):
                # Last chunk
                chunks.append(text[current_pos:])
                break
            
            # Try to find a good break point (sentence end)
            break_pos = end_pos
            
            # Look for sentence endings within the last 20% of the chunk
            search_start = max(current_pos + int(chunk_size * 0.8), current_pos + 1)
            for i in range(end_pos, search_start, -1):
                if text[i-1:i+1] in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    break_pos = i
                    break
            
            chunks.append(text[current_pos:break_pos])
            current_pos = break_pos
        
        return chunks

    async def _process_with_fallback(self, text: str) -> Dict[str, List[Any]]:
        """
        Fallback processing when spaCy fails.
        
        Args:
            text: Text to process
            
        Returns:
            Basic entity extraction results
        """
        logger.info(f"🔍 NLP PROCESS: Using fallback processing")
        
        try:
            # Use basic entity extraction if available
            entities = self._extract_basic_entities(text)
            logger.info(f"🔍 NLP PROCESS: Fallback extracted {len(entities)} entities")
            
            return {
                "entities": entities,
                "relationships": []  # No relationship extraction in fallback
            }
        except Exception as e:
            logger.error(f"🔍 NLP PROCESS: Fallback processing failed: {e}")
            return {
                "entities": [],
                "relationships": []
            }

    def _extract_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Extract named entities from a spaCy Doc with fallback for basic models."""
        entities = []
        
        # Try to use NER if available
        if hasattr(doc, 'ents') and doc.ents:
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char
                })
        else:
            # Fallback: basic pattern matching for common entity types
            logger.info("Using basic pattern matching for entity extraction")
            entities = self._extract_basic_entities(doc.text)
            
        logger.info(f"Extracted {len(entities)} entities.")
        return entities
    
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
        }
        
        for label, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                entities.append({
                    "text": match.group(),
                    "label": label,
                    "start_char": match.start(),
                    "end_char": match.end()
                })
        
        return entities

    def _extract_relationships(self, doc: Doc, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships between entities in the same sentence."""
        relationships = []
        entity_map = {ent['text']: ent for ent in entities}

        for sent in doc.sents:
            sent_entities = [ent for ent in entities if sent.start_char <= ent['start_char'] < sent.end_char]
            if len(sent_entities) < 2:
                continue

            # Create all pairs of entities in the sentence
            for i in range(len(sent_entities)):
                for j in range(i + 1, len(sent_entities)):
                    entity1 = sent_entities[i]
                    entity2 = sent_entities[j]
                    
                    # Simple heuristic-based relation extraction for testing
                    # This avoids the NumPy dependency issue
                    relation_type = self._extract_simple_relation(sent.text, entity1['text'], entity2['text'])
                    
                    if relation_type:
                        relationships.append({
                            "source": entity1,
                            "target": entity2,
                            "relation": relation_type,
                            "sentence": sent.text
                        })

        logger.info(f"Extracted {len(relationships)} relationships.")
        return relationships
    
    def _extract_simple_relation(self, sentence: str, entity1: str, entity2: str) -> str:
        """Extract simple relationships using heuristic patterns."""
        sentence_lower = sentence.lower()
        entity1_lower = entity1.lower()
        entity2_lower = entity2.lower()
        
        # Simple relation patterns
        if "is the ceo of" in sentence_lower or "ceo of" in sentence_lower:
            if entity1_lower in sentence_lower and entity2_lower in sentence_lower:
                return "CEO_OF"
        elif "is based in" in sentence_lower or "located in" in sentence_lower:
            if entity1_lower in sentence_lower and entity2_lower in sentence_lower:
                return "BASED_IN"
        elif "works for" in sentence_lower or "employee of" in sentence_lower:
            if entity1_lower in sentence_lower and entity2_lower in sentence_lower:
                return "WORKS_FOR"
        elif "founded" in sentence_lower or "founder of" in sentence_lower:
            if entity1_lower in sentence_lower and entity2_lower in sentence_lower:
                return "FOUNDED"
        
        # Default relation for any two entities in the same sentence
        return "RELATED_TO"