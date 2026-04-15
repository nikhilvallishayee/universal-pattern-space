"""
Lexical Analyzer and Syntactic Parser (LAP) for GödelOS NLU Pipeline.

This module provides functionality for:
1. Tokenizing input text into words, punctuation, and other meaningful units
2. Performing Part-of-Speech (POS) tagging
3. Performing Named Entity Recognition (NER)
4. Conducting syntactic parsing (dependency parsing)

It serves as the first stage in the NLU pipeline, converting raw text into
structured linguistic representations that can be further processed by
downstream components.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field

try:
    import spacy
    from spacy.tokens import Doc, Token as SpacyToken
    _SPACY_AVAILABLE = True
except ImportError:
    spacy = None  # type: ignore[assignment]
    Doc = None  # type: ignore[assignment,misc]
    SpacyToken = None  # type: ignore[assignment,misc]
    _SPACY_AVAILABLE = False

# Dependency-label heuristic groups for head inference fallback.
VERB_DEP_LABELS = {
    "nsubj", "nsubjpass", "dobj", "iobj", "prep", "advmod", "punct",
    "cc", "conj", "aux", "auxpass", "neg", "ccomp", "xcomp", "advcl",
    "attr", "agent", "oprd", "acomp", "prt", "mark", "expl",
    "npadvmod", "intj", "csubj", "csubjpass", "dative",
}
NOUN_DEP_LABELS = {"det", "amod", "compound", "nummod", "poss", "nmod",
                   "appos", "acl", "relcl", "case"}
PREP_OBJECT_DEP_LABELS = {"pobj"}


@dataclass
class Token:
    """
    Represents a token in the input text with its linguistic properties.
    
    A token is the basic unit of text processing, typically a word, punctuation mark,
    or other meaningful unit.
    """
    text: str
    lemma: str
    pos: str  # Part of speech tag
    tag: str  # Detailed part of speech tag
    dep: str  # Dependency relation
    is_stop: bool  # Whether the token is a stop word
    is_punct: bool  # Whether the token is punctuation
    is_space: bool  # Whether the token is whitespace
    is_ent: bool  # Whether the token is part of a named entity
    ent_type: str  # Entity type if part of a named entity
    ent_iob: str  # IOB (Inside, Outside, Beginning) code for entity
    idx: int  # Character offset in the original text
    i: int  # Token index in the document
    
    # Additional properties that might be useful
    is_alpha: bool = False  # Whether the token consists of alphabetic characters
    is_digit: bool = False  # Whether the token consists of digits
    is_lower: bool = False  # Whether the token is lowercase
    is_upper: bool = False  # Whether the token is uppercase
    is_title: bool = False  # Whether the token is titlecase
    is_sent_start: Optional[bool] = None  # Whether the token starts a sentence
    
    # Morphological features
    morphology: Dict[str, str] = field(default_factory=dict)
    
    # Reference to parent sentence
    sent_idx: Optional[int] = None
    
    # Head token index (populated from spaCy)
    head_i: Optional[int] = None
    
    @classmethod
    def from_spacy_token(cls, token: SpacyToken, sent_idx: Optional[int] = None) -> 'Token':
        """
        Create a Token from a spaCy Token.
        
        Args:
            token: The spaCy Token to convert
            sent_idx: The index of the sentence this token belongs to
            
        Returns:
            A new Token instance
        """
        return cls(
            text=token.text,
            lemma=token.lemma_,
            pos=token.pos_,
            tag=token.tag_,
            dep=token.dep_,
            is_stop=token.is_stop,
            is_punct=token.is_punct,
            is_space=token.is_space,
            is_ent=token.ent_type_ != "",
            ent_type=token.ent_type_,
            ent_iob=token.ent_iob_,
            idx=token.idx,
            i=token.i,
            is_alpha=token.is_alpha,
            is_digit=token.is_digit,
            is_lower=token.is_lower,
            is_upper=token.is_upper,
            is_title=token.is_title,
            is_sent_start=token.is_sent_start,
            morphology=token.morph.to_dict(),
            sent_idx=sent_idx,
            head_i=token.head.i
        )


@dataclass
class Entity:
    """
    Represents a named entity in the text.
    
    Named entities are real-world objects like persons, locations, organizations, etc.
    that can be denoted with a proper name.
    """
    text: str
    label: str  # Entity type (e.g., PERSON, ORG, GPE)
    start_char: int  # Character offset for entity start
    end_char: int  # Character offset for entity end
    start_token: int  # Token index for entity start
    end_token: int  # Token index for entity end (exclusive)
    tokens: List[Token] = field(default_factory=list)  # Tokens that make up this entity


@dataclass
class Span:
    """
    Represents a span of tokens in the text.
    
    A span is a sequence of tokens that form a linguistic unit, such as a phrase or clause.
    """
    text: str
    start_token: int
    end_token: int  # Exclusive
    tokens: List[Token] = field(default_factory=list)
    label: Optional[str] = None  # For labeled spans like noun phrases, verb phrases


@dataclass
class Sentence:
    """
    Represents a sentence in the text.
    
    A sentence is a linguistic unit consisting of words arranged to express a statement,
    question, exclamation, request, command, or suggestion.
    """
    text: str
    start_char: int
    end_char: int
    tokens: List[Token] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    noun_phrases: List[Span] = field(default_factory=list)
    verb_phrases: List[Span] = field(default_factory=list)
    root_token: Optional[Token] = None


@dataclass
class SyntacticParseOutput:
    """
    Output of the syntactic parsing process.
    
    Contains the structured linguistic representation of the input text,
    including tokens, sentences, entities, and syntactic dependencies.
    """
    text: str
    tokens: List[Token] = field(default_factory=list)
    sentences: List[Sentence] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    noun_phrases: List[Span] = field(default_factory=list)
    verb_phrases: List[Span] = field(default_factory=list)
    
    # Document-level metadata
    doc_metadata: Dict[str, Any] = field(default_factory=dict)


class LexicalAnalyzerParser:
    """
    Performs lexical analysis and syntactic parsing on natural language text.
    
    This class is responsible for the initial processing of natural language input,
    converting raw text into structured linguistic representations that can be
    further processed by downstream components of the NLU pipeline.
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize the lexical analyzer and parser.
        
        Args:
            model_name: The name of the spaCy model to use
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            # If the model is not found, download it
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)
            self.nlp = spacy.load(model_name)
    
    def process(self, text: str) -> SyntacticParseOutput:
        """
        Process the input text to produce a syntactic parse.
        
        Args:
            text: The input text to process
            
        Returns:
            A SyntacticParseOutput containing the structured linguistic representation
        """
        # Process the text with spaCy
        doc = self.nlp(text)
        
        # Create the output object
        output = SyntacticParseOutput(text=text)
        
        # Process sentences
        for sent_idx, sent in enumerate(doc.sents):
            sentence = Sentence(
                text=sent.text,
                start_char=sent.start_char,
                end_char=sent.end_char
            )
            
            # Process tokens in the sentence
            for token in sent:
                token_obj = Token.from_spacy_token(token, sent_idx)
                sentence.tokens.append(token_obj)
                output.tokens.append(token_obj)
                
                # Identify the root token of the sentence
                if token.dep_ == "ROOT":
                    sentence.root_token = token_obj
            
            # Add the sentence to the output
            output.sentences.append(sentence)
        
        # Process entities
        for ent in doc.ents:
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
                start_token=ent.start,
                end_token=ent.end
            )
            
            # Add the tokens that make up this entity
            for token in ent:
                token_obj = Token.from_spacy_token(token)
                entity.tokens.append(token_obj)
            
            # Add the entity to the output and to its sentence
            output.entities.append(entity)
            
            # Find which sentence this entity belongs to and add it there
            for sentence in output.sentences:
                if entity.start_char >= sentence.start_char and entity.end_char <= sentence.end_char:
                    sentence.entities.append(entity)
                    break
        
        # Process noun phrases
        for np in doc.noun_chunks:
            span = Span(
                text=np.text,
                start_token=np.start,
                end_token=np.end,
                label="NP"
            )
            
            # Add the tokens that make up this noun phrase
            for token in np:
                token_obj = Token.from_spacy_token(token)
                span.tokens.append(token_obj)
            
            # Add the noun phrase to the output
            output.noun_phrases.append(span)
            
            # Find which sentence this noun phrase belongs to and add it there
            for sentence in output.sentences:
                if np.start_char >= sentence.start_char and np.end_char <= sentence.end_char:
                    sentence.noun_phrases.append(span)
                    break
        
        # Extract verb phrases (this is a simplification; spaCy doesn't directly provide verb phrases)
        for sentence in output.sentences:
            for token in sentence.tokens:
                if token.pos == "VERB":
                    # Find all tokens that depend on this verb
                    verb_phrase_tokens = [t for t in sentence.tokens if self._is_dependent_on(t, token, sentence.tokens)]
                    
                    if verb_phrase_tokens:
                        # Sort tokens by their position in the text
                        verb_phrase_tokens.sort(key=lambda t: t.i)
                        
                        span = Span(
                            text=" ".join([t.text for t in verb_phrase_tokens]),
                            start_token=min(t.i for t in verb_phrase_tokens),
                            end_token=max(t.i for t in verb_phrase_tokens) + 1,
                            tokens=verb_phrase_tokens,
                            label="VP"
                        )
                        
                        # Add the verb phrase to the output and to its sentence
                        output.verb_phrases.append(span)
                        sentence.verb_phrases.append(span)
        
        return output
    
    def _is_dependent_on(self, token: Token, head_token: Token, all_tokens: List[Token]) -> bool:
        """
        Check if a token is directly or indirectly dependent on a head token.
        
        Args:
            token: The token to check
            head_token: The potential head token
            all_tokens: All tokens in the sentence
            
        Returns:
            True if token is dependent on head_token, False otherwise
        """
        # If the token is the head token itself, return True
        if token.i == head_token.i:
            return True
        
        # Use head_i if available
        if token.head_i is not None:
            if token.head_i == token.i:
                # ROOT or self-referencing token
                return False
            if token.head_i == head_token.i:
                return True
            # Recursively check if the token's head is dependent on head_token
            for t in all_tokens:
                if t.i == token.head_i:
                    return self._is_dependent_on(t, head_token, all_tokens)
            return False
        
        # Fallback heuristic when head_i is not available:
        # Use dependency labels to infer the tree structure.
        
        # ROOT tokens only depend on themselves (already handled above)
        if token.dep == "ROOT":
            return False
        
        # Find the head using heuristic
        inferred_head_i = self._infer_head(token, all_tokens,
                                           VERB_DEP_LABELS,
                                           NOUN_DEP_LABELS,
                                           PREP_OBJECT_DEP_LABELS)
        if inferred_head_i is not None:
            if inferred_head_i == head_token.i:
                return True
            for t in all_tokens:
                if t.i == inferred_head_i:
                    return self._is_dependent_on(t, head_token, all_tokens)
        
        return False
    
    @staticmethod
    def _infer_head(token: Token, all_tokens: List[Token],
                    verb_deps: set, noun_deps: set, prep_obj_deps: set) -> Optional[int]:
        """Infer the head token index from dependency label heuristics."""
        if token.dep in verb_deps:
            # Look for the ROOT token
            for t in all_tokens:
                if t.dep == "ROOT":
                    return t.i
        elif token.dep in noun_deps:
            # Look for the nearest noun/propn to the right
            best = None
            for t in all_tokens:
                if (t.i > token.i and t.pos in ("NOUN", "PROPN")
                        and t.dep not in noun_deps):
                    if best is None or t.i < best:
                        best = t.i
            if best is not None:
                return best
            # Fallback: look for the ROOT
            for t in all_tokens:
                if t.dep == "ROOT":
                    return t.i
        elif token.dep in prep_obj_deps:
            # Look for the nearest preposition (ADP) to the left
            best = None
            for t in all_tokens:
                if t.i < token.i and t.pos == "ADP":
                    if best is None or t.i > best:
                        best = t.i
            if best is not None:
                return best
        
        # Default: assume dependent on ROOT
        for t in all_tokens:
            if t.dep == "ROOT":
                return t.i
        return None
