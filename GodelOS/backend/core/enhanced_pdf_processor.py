"""
Enhanced PDF Content Processor

Advanced PDF processing with meaningful concept extraction, entity recognition,
and structured knowledge graph integration for better PDF content understanding.
"""

import logging
import re
import uuid
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from collections import Counter, defaultdict
import asyncio

# Optional NLP imports
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    spacy = None

logger = logging.getLogger(__name__)

@dataclass
class PDFSection:
    """Represents a logical section of a PDF document."""
    title: str
    content: str
    page_range: Tuple[int, int]
    section_type: str  # 'header', 'paragraph', 'list', 'table', 'conclusion'
    confidence: float

@dataclass
class SemanticConcept:
    """Represents a semantically meaningful concept extracted from PDF content."""
    concept: str
    semantic_type: str  # 'entity', 'topic', 'process', 'methodology', 'finding', 'technology'
    confidence: float
    context: str
    importance_score: float  # Based on position, frequency, and semantic context
    related_terms: List[str]
    source_section: str
    domain_relevance: float

@dataclass
class ConceptRelationship:
    """Represents a relationship between two concepts."""
    source_concept: str
    target_concept: str
    relationship_type: str  # 'describes', 'implements', 'analyzes', 'results_in', 'part_of'
    confidence: float
    context: str

@dataclass
class PDFProcessingResult:
    """Comprehensive result of PDF processing."""
    raw_text: str
    sections: List[PDFSection]
    concepts: List[SemanticConcept]
    concept_relationships: List[ConceptRelationship]
    entities: List[Dict[str, Any]]
    key_phrases: List[str]
    summary: str
    topics: List[str]
    technical_terms: List[str]
    domain_classification: str
    metadata: Dict[str, Any]

class EnhancedPDFProcessor:
    """Enhanced processor for extracting meaningful information from PDF content."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common business/academic section patterns
        self.section_patterns = [
            (r'^(ABSTRACT|Abstract|SUMMARY|Summary)[\s\n]', 'abstract'),
            (r'^(INTRODUCTION|Introduction|OVERVIEW|Overview)[\s\n]', 'introduction'),
            (r'^(METHODOLOGY|Methodology|METHOD|Method|APPROACH|Approach)[\s\n]', 'methodology'),
            (r'^(RESULTS|Results|FINDINGS|Findings)[\s\n]', 'results'),
            (r'^(DISCUSSION|Discussion|ANALYSIS|Analysis)[\s\n]', 'discussion'),
            (r'^(CONCLUSION|Conclusion|CONCLUSIONS|Conclusions)[\s\n]', 'conclusion'),
            (r'^(REFERENCES|References|BIBLIOGRAPHY|Bibliography)[\s\n]', 'references'),
            (r'^(APPENDIX|Appendix|ANNEX|Annex)[\s\n]', 'appendix'),
            (r'^(\d+\.?\s+[A-Z][^\.]*?)[\s\n]', 'section'),
            (r'^([A-Z][A-Z\s]{2,20}?)[\s\n]', 'heading')
        ]
        
        # Technical term patterns
        self.technical_patterns = [
            r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b',  # Acronyms
            r'\b\w+(?:[-_]\w+)+\b',  # Hyphenated/underscore terms
            r'\b\w*(?:ology|ography|isation|ization|ment|ness|tion|sion)\b',  # Technical suffixes
            r'\b(?:AI|ML|API|SDK|HTTP|JSON|XML|SQL|HTML|CSS|JS)\b',  # Common tech terms
        ]
        
        # Stop words for concept extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'among', 'throughout', 'alongside', 'we', 'our', 'us', 'this',
            'that', 'these', 'those', 'i', 'me', 'my', 'myself', 'you', 'your', 'yourself',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
            'they', 'them', 'their', 'themselves', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }

    async def process_pdf_content(self, raw_text: str, title: str = None, metadata: Dict = None) -> PDFProcessingResult:
        """
        Process raw PDF text content into structured knowledge components.
        
        Args:
            raw_text: The raw text extracted from the PDF
            title: The document title 
            metadata: Additional metadata about the document
            
        Returns:
            PDFProcessingResult with structured information
        """
        try:
            self.logger.info(f"🔍 PDF PROCESSOR: Processing document '{title}' with {len(raw_text)} characters")
            
            # Clean and normalize the text
            cleaned_text = self._clean_text(raw_text)
            
            # Extract document sections
            sections = self._extract_sections(cleaned_text)
            
            # Extract concepts and entities
            concepts = self._extract_concepts(cleaned_text, sections)
            entities = self._extract_entities(cleaned_text)
            
            # Extract key phrases and technical terms
            key_phrases = self._extract_key_phrases(cleaned_text)
            technical_terms = self._extract_technical_terms(cleaned_text)
            
            # Generate topics and summary
            topics = self._extract_topics(concepts, sections)
            summary = self._generate_summary(sections, concepts)
            
            # Build comprehensive metadata
            processing_metadata = {
                'original_char_count': len(raw_text),
                'processed_char_count': len(cleaned_text),
                'sections_found': len(sections),
                'concepts_extracted': len(concepts),
                'entities_found': len(entities),
                'technical_terms': len(technical_terms),
                'processing_quality': self._assess_quality(cleaned_text, sections, concepts),
                **(metadata or {})
            }
            
            result = PDFProcessingResult(
                raw_text=raw_text,
                sections=sections,
                concepts=concepts,
                entities=entities,
                key_phrases=key_phrases,
                summary=summary,
                topics=topics,
                technical_terms=technical_terms,
                metadata=processing_metadata
            )
            
            self.logger.info(f"✅ PDF PROCESSOR: Successfully processed document with {len(concepts)} concepts and {len(sections)} sections")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ PDF PROCESSOR: Error processing document: {e}")
            # Return minimal result on error
            return PDFProcessingResult(
                raw_text=raw_text,
                sections=[],
                concepts=[],
                entities=[],
                key_phrases=[],
                summary=raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
                topics=[],
                technical_terms=[],
                metadata={'processing_error': str(e), **(metadata or {})}
            )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize PDF text content."""
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove page numbers and common PDF artifacts
        text = re.sub(r'(?:^|\n)\s*\d+\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'(?:^|\n)\s*Page\s+\d+\s*(?:of\s+\d+)?\s*$', '', text, flags=re.MULTILINE)
        
        # Remove header/footer patterns
        text = re.sub(r'(?:^|\n)\s*[-=]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()

    def _extract_sections(self, text: str) -> List[PDFSection]:
        """Extract logical sections from PDF text."""
        sections = []
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line matches a section pattern
            section_type = None
            for pattern, stype in self.section_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    section_type = stype
                    break
            
            if section_type:
                # Save previous section
                if current_section and current_content:
                    sections.append(PDFSection(
                        title=current_section,
                        content='\n'.join(current_content),
                        page_range=(0, 0),  # Would need page tracking for accurate ranges
                        section_type=section_type,
                        confidence=0.8
                    ))
                
                # Start new section
                current_section = line
                current_content = []
            else:
                # Add to current section content
                if current_section:
                    current_content.append(line)
                else:
                    # No section detected yet, start a general section
                    if not current_section:
                        current_section = "Introduction"
                        current_content = [line]
        
        # Add final section
        if current_section and current_content:
            sections.append(PDFSection(
                title=current_section,
                content='\n'.join(current_content),
                page_range=(0, 0),
                section_type='content',
                confidence=0.7
            ))
        
        # If no sections found, create one general section
        if not sections and text:
            sections.append(PDFSection(
                title="Document Content",
                content=text,
                page_range=(0, 0),
                section_type='content',
                confidence=0.6
            ))
        
        return sections

    def _extract_concepts(self, text: str, sections: List[PDFSection]) -> List[PDFConcept]:
        """Extract meaningful concepts from the text."""
        concepts = []
        word_freq = {}
        
        # Tokenize and count words
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            if len(word) > 2 and word not in self.stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Extract multi-word phrases (bigrams and trigrams)
        sentences = re.split(r'[.!?]+', text)
        phrase_freq = {}
        
        for sentence in sentences:
            sentence = sentence.strip().lower()
            words_in_sentence = re.findall(r'\b\w+\b', sentence)
            
            # Bigrams
            for i in range(len(words_in_sentence) - 1):
                bigram = ' '.join(words_in_sentence[i:i+2])
                if not any(word in self.stop_words for word in words_in_sentence[i:i+2]):
                    phrase_freq[bigram] = phrase_freq.get(bigram, 0) + 1
            
            # Trigrams
            for i in range(len(words_in_sentence) - 2):
                trigram = ' '.join(words_in_sentence[i:i+3])
                if not any(word in self.stop_words for word in words_in_sentence[i:i+3]):
                    phrase_freq[trigram] = phrase_freq.get(trigram, 0) + 1
        
        # Select top concepts
        all_terms = {**word_freq, **phrase_freq}
        top_terms = sorted(all_terms.items(), key=lambda x: x[1], reverse=True)[:20]
        
        for term, freq in top_terms:
            if freq >= 2:  # Must appear at least twice
                # Determine concept category
                category = 'keyword'
                if len(term.split()) > 1:
                    category = 'phrase'
                if any(re.search(pattern, term, re.IGNORECASE) for pattern in self.technical_patterns):
                    category = 'technical_term'
                
                # Find context for the concept
                context_match = re.search(rf'\b{re.escape(term)}\b.{0,50}', text, re.IGNORECASE)
                context = context_match.group(0) if context_match else term
                
                concepts.append(PDFConcept(
                    concept=term.title(),
                    category=category,
                    confidence=min(0.9, 0.5 + (freq / 10)),
                    context=context,
                    frequency=freq,
                    relationships=[]
                ))
        
        return concepts

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities and important terms."""
        entities = []
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({
                'text': email,
                'type': 'email',
                'confidence': 0.95
            })
        
        # Extract URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            entities.append({
                'text': url,
                'type': 'url',
                'confidence': 0.95
            })
        
        # Extract dates
        dates = re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b', text)
        for date in dates:
            entities.append({
                'text': date,
                'type': 'date',
                'confidence': 0.8
            })
        
        # Extract numbers/statistics
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', text)
        for number in numbers[:10]:  # Limit to first 10
            entities.append({
                'text': number,
                'type': 'number',
                'confidence': 0.7
            })
        
        return entities

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases that are likely to be important."""
        phrases = []
        
        # Extract phrases in quotes
        quoted_phrases = re.findall(r'"([^"]+)"', text)
        phrases.extend([phrase.strip() for phrase in quoted_phrases if len(phrase.strip()) > 3])
        
        # Extract capitalized phrases (likely important terms)
        cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        phrases.extend([phrase for phrase in cap_phrases if len(phrase) > 5])
        
        # Remove duplicates and limit
        unique_phrases = list(set(phrases))[:15]
        return unique_phrases

    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms and acronyms."""
        technical_terms = set()
        
        for pattern in self.technical_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 2:
                    technical_terms.add(match)
        
        return list(technical_terms)[:10]

    def _extract_topics(self, concepts: List[PDFConcept], sections: List[PDFSection]) -> List[str]:
        """Extract main topics from concepts and sections."""
        topics = []
        
        # Add section titles as topics
        for section in sections:
            if section.section_type in ['introduction', 'methodology', 'results', 'discussion', 'conclusion']:
                topics.append(section.title.title())
        
        # Add top concepts as topics
        top_concepts = sorted(concepts, key=lambda c: c.confidence * c.frequency, reverse=True)[:5]
        for concept in top_concepts:
            if concept.category in ['phrase', 'technical_term']:
                topics.append(concept.concept)
        
        return list(set(topics))[:8]

    def _generate_summary(self, sections: List[PDFSection], concepts: List[PDFConcept]) -> str:
        """Generate a summary of the document."""
        summary_parts = []
        
        # Use abstract or introduction if available
        for section in sections:
            if section.section_type in ['abstract', 'introduction']:
                # Take first few sentences
                sentences = re.split(r'[.!?]+', section.content)
                summary_parts.extend(sentences[:2])
                break
        
        # If no good sections, use top concepts
        if not summary_parts and concepts:
            top_concepts = [c.concept for c in concepts[:5]]
            summary_parts.append(f"This document discusses {', '.join(top_concepts[:-1])} and {top_concepts[-1]}.")
        
        # Fallback
        if not summary_parts:
            summary_parts.append("Document content processed successfully.")
        
        return ' '.join(summary_parts).strip()

    def _assess_quality(self, text: str, sections: List[PDFSection], concepts: List[PDFConcept]) -> float:
        """Assess the quality of the text extraction and processing."""
        quality_score = 0.5  # Base score
        
        # Length factor
        if len(text) > 1000:
            quality_score += 0.1
        if len(text) > 5000:
            quality_score += 0.1
        
        # Structure factor
        if len(sections) > 1:
            quality_score += 0.1
        if len(sections) > 3:
            quality_score += 0.1
        
        # Content richness factor
        if len(concepts) > 5:
            quality_score += 0.1
        if len(concepts) > 10:
            quality_score += 0.1
        
        return min(1.0, quality_score)

# Global instance
enhanced_pdf_processor = EnhancedPDFProcessor()
