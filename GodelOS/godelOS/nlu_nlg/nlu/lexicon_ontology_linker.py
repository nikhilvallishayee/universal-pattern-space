"""
Lexicon & Ontology Linker (LOL) for GödelOS NLU Pipeline.

This module provides functionality for:
1. Mapping words to concepts in the ontology
2. Providing lexical-semantic knowledge
3. Supporting word sense disambiguation
4. Linking natural language terms to formal concepts

It serves as a component in the NLU pipeline that bridges the gap between
natural language and formal ontological concepts.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
from enum import Enum, auto
from collections import defaultdict
import re
import nltk
from nltk.corpus import wordnet as wn

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import Token


# Ensure NLTK resources are available
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')


class WordSense:
    """Enumeration of common word senses."""
    UNKNOWN = "unknown"


@dataclass
class LexicalEntry:
    """
    Represents an entry in the lexicon.
    
    A lexical entry contains information about a word, including its possible
    meanings, part of speech, and other linguistic properties.
    """
    lemma: str
    pos: str  # Part of speech
    senses: List[str] = field(default_factory=list)
    ontology_mappings: Dict[str, str] = field(default_factory=dict)  # Maps sense to ontology concept
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    hypernyms: List[str] = field(default_factory=list)
    hyponyms: List[str] = field(default_factory=list)
    meronyms: List[str] = field(default_factory=list)  # Part-of relations
    holonyms: List[str] = field(default_factory=list)  # Whole-of relations
    examples: List[str] = field(default_factory=list)
    
    def add_sense(self, sense: str, ontology_concept: Optional[str] = None) -> None:
        """
        Add a sense to this lexical entry.
        
        Args:
            sense: The sense to add
            ontology_concept: The corresponding ontology concept, if any
        """
        if sense not in self.senses:
            self.senses.append(sense)
            if ontology_concept:
                self.ontology_mappings[sense] = ontology_concept
    
    def add_synonym(self, synonym: str) -> None:
        """
        Add a synonym to this lexical entry.
        
        Args:
            synonym: The synonym to add
        """
        if synonym not in self.synonyms:
            self.synonyms.append(synonym)
    
    def add_antonym(self, antonym: str) -> None:
        """
        Add an antonym to this lexical entry.
        
        Args:
            antonym: The antonym to add
        """
        if antonym not in self.antonyms:
            self.antonyms.append(antonym)
    
    def add_hypernym(self, hypernym: str) -> None:
        """
        Add a hypernym to this lexical entry.
        
        Args:
            hypernym: The hypernym to add
        """
        if hypernym not in self.hypernyms:
            self.hypernyms.append(hypernym)
    
    def add_hyponym(self, hyponym: str) -> None:
        """
        Add a hyponym to this lexical entry.
        
        Args:
            hyponym: The hyponym to add
        """
        if hyponym not in self.hyponyms:
            self.hyponyms.append(hyponym)
    
    def add_meronym(self, meronym: str) -> None:
        """
        Add a meronym to this lexical entry.
        
        Args:
            meronym: The meronym to add
        """
        if meronym not in self.meronyms:
            self.meronyms.append(meronym)
    
    def add_holonym(self, holonym: str) -> None:
        """
        Add a holonym to this lexical entry.
        
        Args:
            holonym: The holonym to add
        """
        if holonym not in self.holonyms:
            self.holonyms.append(holonym)
    
    def add_example(self, example: str) -> None:
        """
        Add an example to this lexical entry.
        
        Args:
            example: The example to add
        """
        if example not in self.examples:
            self.examples.append(example)


@dataclass
class OntologyConcept:
    """
    Represents a concept in the ontology.
    
    An ontology concept is a formal representation of a concept in the domain,
    with properties, relations to other concepts, and lexical mappings.
    """
    id: str
    name: str
    description: Optional[str] = None
    parent_concepts: List[str] = field(default_factory=list)
    child_concepts: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    relations: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    lexical_mappings: List[str] = field(default_factory=list)  # Lemmas that map to this concept
    
    def add_parent_concept(self, parent_id: str) -> None:
        """
        Add a parent concept to this concept.
        
        Args:
            parent_id: The ID of the parent concept
        """
        if parent_id not in self.parent_concepts:
            self.parent_concepts.append(parent_id)
    
    def add_child_concept(self, child_id: str) -> None:
        """
        Add a child concept to this concept.
        
        Args:
            child_id: The ID of the child concept
        """
        if child_id not in self.child_concepts:
            self.child_concepts.append(child_id)
    
    def add_property(self, property_name: str, property_value: Any) -> None:
        """
        Add a property to this concept.
        
        Args:
            property_name: The name of the property
            property_value: The value of the property
        """
        self.properties[property_name] = property_value
    
    def add_relation(self, relation_type: str, target_id: str) -> None:
        """
        Add a relation to this concept.
        
        Args:
            relation_type: The type of the relation
            target_id: The ID of the target concept
        """
        if target_id not in self.relations[relation_type]:
            self.relations[relation_type].append(target_id)
    
    def add_lexical_mapping(self, lemma: str) -> None:
        """
        Add a lexical mapping to this concept.
        
        Args:
            lemma: The lemma to map to this concept
        """
        if lemma not in self.lexical_mappings:
            self.lexical_mappings.append(lemma)


class Lexicon:
    """
    A lexicon containing lexical entries.
    
    The lexicon provides access to lexical entries by lemma and part of speech,
    and supports operations like adding entries and retrieving entries.
    """
    
    def __init__(self):
        """Initialize the lexicon."""
        self.entries: Dict[Tuple[str, str], LexicalEntry] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_entry(self, entry: LexicalEntry) -> None:
        """
        Add an entry to the lexicon.
        
        Args:
            entry: The lexical entry to add
        """
        key = (entry.lemma, entry.pos)
        self.entries[key] = entry
    
    def get_entry(self, lemma: str, pos: str) -> Optional[LexicalEntry]:
        """
        Get a lexical entry by lemma and part of speech.
        
        Args:
            lemma: The lemma of the entry
            pos: The part of speech of the entry
            
        Returns:
            The lexical entry, or None if not found
        """
        key = (lemma, pos)
        return self.entries.get(key)
    
    def get_entries_by_lemma(self, lemma: str) -> List[LexicalEntry]:
        """
        Get all lexical entries with the given lemma.
        
        Args:
            lemma: The lemma to search for
            
        Returns:
            A list of lexical entries with the given lemma
        """
        return [entry for key, entry in self.entries.items() if key[0] == lemma]
    
    def get_all_entries(self) -> List[LexicalEntry]:
        """
        Get all lexical entries in the lexicon.
        
        Returns:
            A list of all lexical entries
        """
        return list(self.entries.values())


class Ontology:
    """
    An ontology containing concepts and their relations.
    
    The ontology provides access to concepts by ID and name, and supports
    operations like adding concepts and retrieving concepts.
    """
    
    def __init__(self):
        """Initialize the ontology."""
        self.concepts: Dict[str, OntologyConcept] = {}
        self.name_to_id: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_concept(self, concept: OntologyConcept) -> None:
        """
        Add a concept to the ontology.
        
        Args:
            concept: The concept to add
        """
        self.concepts[concept.id] = concept
        self.name_to_id[concept.name] = concept.id
    
    def get_concept(self, concept_id: str) -> Optional[OntologyConcept]:
        """
        Get a concept by ID.
        
        Args:
            concept_id: The ID of the concept
            
        Returns:
            The concept, or None if not found
        """
        return self.concepts.get(concept_id)
    
    def get_concept_by_name(self, name: str) -> Optional[OntologyConcept]:
        """
        Get a concept by name.
        
        Args:
            name: The name of the concept
            
        Returns:
            The concept, or None if not found
        """
        concept_id = self.name_to_id.get(name)
        if concept_id:
            return self.concepts.get(concept_id)
        return None
    
    def get_all_concepts(self) -> List[OntologyConcept]:
        """
        Get all concepts in the ontology.
        
        Returns:
            A list of all concepts
        """
        return list(self.concepts.values())


class WordNetLexicon(Lexicon):
    """
    A lexicon implementation that uses WordNet as a backend.
    
    This lexicon provides access to lexical entries from WordNet, including
    word senses, synonyms, antonyms, hypernyms, hyponyms, etc.
    """
    
    def __init__(self):
        """Initialize the WordNet lexicon."""
        super().__init__()
        self.pos_map = {
            'NOUN': wn.NOUN,
            'VERB': wn.VERB,
            'ADJ': wn.ADJ,
            'ADV': wn.ADV
        }
        self.reverse_pos_map = {v: k for k, v in self.pos_map.items()}
    
    def get_entry(self, lemma: str, pos: str) -> Optional[LexicalEntry]:
        """
        Get a lexical entry by lemma and part of speech.
        
        If the entry is not in the lexicon, try to create it from WordNet.
        
        Args:
            lemma: The lemma of the entry
            pos: The part of speech of the entry
            
        Returns:
            The lexical entry, or None if not found
        """
        key = (lemma, pos)
        if key in self.entries:
            return self.entries[key]
        
        # Try to create an entry from WordNet
        entry = self._create_entry_from_wordnet(lemma, pos)
        if entry:
            self.add_entry(entry)
            return entry
        
        return None
    
    def _create_entry_from_wordnet(self, lemma: str, pos: str) -> Optional[LexicalEntry]:
        """
        Create a lexical entry from WordNet.
        
        Args:
            lemma: The lemma of the entry
            pos: The part of speech of the entry
            
        Returns:
            A new lexical entry, or None if the word is not in WordNet
        """
        # Map the POS tag to WordNet POS
        wordnet_pos = self._map_pos_to_wordnet(pos)
        if not wordnet_pos:
            return None
        
        # Get the synsets for the lemma
        synsets = wn.synsets(lemma, pos=wordnet_pos)
        if not synsets:
            return None
        
        # Create a new lexical entry
        entry = LexicalEntry(lemma=lemma, pos=pos)
        
        # Add senses
        for synset in synsets:
            sense_name = synset.name()
            entry.add_sense(sense_name)
            
            # Add examples
            for example in synset.examples():
                entry.add_example(example)
            
            # Add synonyms (lemmas from the same synset)
            for lemma_obj in synset.lemmas():
                if lemma_obj.name() != lemma:
                    entry.add_synonym(lemma_obj.name())
            
            # Add antonyms
            for lemma_obj in synset.lemmas():
                for antonym in lemma_obj.antonyms():
                    entry.add_antonym(antonym.name())
            
            # Add hypernyms
            for hypernym in synset.hypernyms():
                for lemma_obj in hypernym.lemmas():
                    entry.add_hypernym(lemma_obj.name())
            
            # Add hyponyms
            for hyponym in synset.hyponyms():
                for lemma_obj in hyponym.lemmas():
                    entry.add_hyponym(lemma_obj.name())
            
            # Add meronyms
            for meronym in synset.part_meronyms() + synset.substance_meronyms():
                for lemma_obj in meronym.lemmas():
                    entry.add_meronym(lemma_obj.name())
            
            # Add holonyms
            for holonym in synset.part_holonyms() + synset.substance_holonyms():
                for lemma_obj in holonym.lemmas():
                    entry.add_holonym(lemma_obj.name())
        
        return entry
    
    def _map_pos_to_wordnet(self, pos: str) -> Optional[str]:
        """
        Map a part of speech tag to a WordNet part of speech.
        
        Args:
            pos: The part of speech tag
            
        Returns:
            The corresponding WordNet part of speech, or None if not mappable
        """
        # Map common POS tags to WordNet POS
        if pos in self.pos_map:
            return self.pos_map[pos]
        
        # Try to map based on the first character
        if pos.startswith('N'):
            return wn.NOUN
        elif pos.startswith('V'):
            return wn.VERB
        elif pos.startswith('J'):
            return wn.ADJ
        elif pos.startswith('R'):
            return wn.ADV
        
        return None


class LexiconOntologyLinker:
    """
    Links lexical entries to ontology concepts.
    
    This class is responsible for mapping words to concepts in the ontology,
    providing lexical-semantic knowledge, supporting word sense disambiguation,
    and linking natural language terms to formal concepts.
    """
    
    def __init__(self, lexicon: Optional[Lexicon] = None, ontology: Optional[Ontology] = None):
        """
        Initialize the lexicon-ontology linker.
        
        Args:
            lexicon: The lexicon to use, or None to create a new WordNetLexicon
            ontology: The ontology to use, or None to create a new Ontology
        """
        self.lexicon = lexicon or WordNetLexicon()
        self.ontology = ontology or Ontology()
        self.logger = logging.getLogger(__name__)
        
        # Cache for word sense disambiguation
        self.wsd_cache: Dict[Tuple[str, str, str], str] = {}
    
    def link_term_to_concept(self, token: Token, context_tokens: List[Token] = None) -> Optional[OntologyConcept]:
        """
        Link a term to an ontology concept.
        
        Args:
            token: The token to link
            context_tokens: Optional context tokens for word sense disambiguation
            
        Returns:
            The linked ontology concept, or None if not found
        """
        # Get the lexical entry for the token
        entry = self.lexicon.get_entry(token.lemma, token.pos)
        if entry:
            # If there's only one sense, use it
            if len(entry.senses) == 1:
                sense = entry.senses[0]
            else:
                # Otherwise, disambiguate the sense
                sense = self.disambiguate_sense(token, entry, context_tokens)
            
            # Check if the sense maps to an ontology concept
            if sense in entry.ontology_mappings:
                concept_id = entry.ontology_mappings[sense]
                return self.ontology.get_concept(concept_id)
        
        # Try to find a concept with a matching name or lexical mapping
        for concept in self.ontology.get_all_concepts():
            if token.lemma in concept.lexical_mappings or token.lemma == concept.name.lower():
                return concept
        
        return None
    
    def disambiguate_sense(self, token: Token, entry: LexicalEntry, 
                          context_tokens: List[Token] = None) -> str:
        """
        Disambiguate the sense of a word.
        
        Args:
            token: The token to disambiguate
            entry: The lexical entry for the token
            context_tokens: Optional context tokens for disambiguation
            
        Returns:
            The disambiguated sense
        """
        # If there are no senses, return unknown
        if not entry.senses:
            return WordSense.UNKNOWN
        
        # If there's only one sense, return it
        if len(entry.senses) == 1:
            return entry.senses[0]
        
        # Check the cache
        context_key = ""
        if context_tokens:
            context_key = " ".join(t.lemma for t in context_tokens)
        cache_key = (token.lemma, token.pos, context_key)
        if cache_key in self.wsd_cache:
            return self.wsd_cache[cache_key]
        
        # This is a simplified implementation of word sense disambiguation
        # For a more sophisticated approach, we would use a machine learning model
        
        # For now, just return the first sense
        sense = entry.senses[0]
        
        # Cache the result
        self.wsd_cache[cache_key] = sense
        
        return sense
    
    def get_concept_hierarchy(self, concept: OntologyConcept) -> Dict[str, Any]:
        """
        Get the hierarchy of a concept.
        
        Args:
            concept: The concept to get the hierarchy for
            
        Returns:
            A dictionary representing the concept hierarchy
        """
        hierarchy = {
            "id": concept.id,
            "name": concept.name,
            "parents": [],
            "children": []
        }
        
        # Add parent concepts
        for parent_id in concept.parent_concepts:
            parent = self.ontology.get_concept(parent_id)
            if parent:
                hierarchy["parents"].append({
                    "id": parent.id,
                    "name": parent.name
                })
        
        # Add child concepts
        for child_id in concept.child_concepts:
            child = self.ontology.get_concept(child_id)
            if child:
                hierarchy["children"].append({
                    "id": child.id,
                    "name": child.name
                })
        
        return hierarchy
    
    def get_lexical_relations(self, token: Token) -> Dict[str, List[str]]:
        """
        Get the lexical relations of a word.
        
        Args:
            token: The token to get relations for
            
        Returns:
            A dictionary of lexical relations
        """
        relations = {
            "synonyms": [],
            "antonyms": [],
            "hypernyms": [],
            "hyponyms": [],
            "meronyms": [],
            "holonyms": []
        }
        
        # Get the lexical entry for the token
        entry = self.lexicon.get_entry(token.lemma, token.pos)
        if not entry:
            return relations
        
        # Fill in the relations
        relations["synonyms"] = entry.synonyms
        relations["antonyms"] = entry.antonyms
        relations["hypernyms"] = entry.hypernyms
        relations["hyponyms"] = entry.hyponyms
        relations["meronyms"] = entry.meronyms
        relations["holonyms"] = entry.holonyms
        
        return relations
    
    def add_mapping(self, lemma: str, pos: str, sense: str, concept_id: str) -> None:
        """
        Add a mapping from a lexical sense to an ontology concept.
        
        Args:
            lemma: The lemma of the word
            pos: The part of speech of the word
            sense: The sense of the word
            concept_id: The ID of the ontology concept
        """
        # Get the lexical entry
        entry = self.lexicon.get_entry(lemma, pos)
        if not entry:
            # Create a new entry if it doesn't exist
            entry = LexicalEntry(lemma=lemma, pos=pos)
            self.lexicon.add_entry(entry)
        
        # Add the sense if it doesn't exist
        if sense not in entry.senses:
            entry.add_sense(sense)
        
        # Add the mapping
        entry.ontology_mappings[sense] = concept_id
        
        # Update the concept's lexical mappings
        concept = self.ontology.get_concept(concept_id)
        if concept:
            concept.add_lexical_mapping(lemma)
    
    def load_wordnet_lexicon(self) -> None:
        """
        Load lexical entries from WordNet.
        
        This method loads a subset of WordNet into the lexicon for common words.
        """
        # Load common words from WordNet
        common_words = [
            ("dog", "NOUN"), ("cat", "NOUN"), ("house", "NOUN"), ("car", "NOUN"),
            ("run", "VERB"), ("walk", "VERB"), ("eat", "VERB"), ("see", "VERB"),
            ("happy", "ADJ"), ("sad", "ADJ"), ("big", "ADJ"), ("small", "ADJ"),
            ("quickly", "ADV"), ("slowly", "ADV"), ("very", "ADV"), ("really", "ADV")
        ]
        
        for lemma, pos in common_words:
            self.lexicon.get_entry(lemma, pos)  # This will create the entry if it doesn't exist
    
    def create_basic_ontology(self) -> None:
        """
        Create a basic ontology with common concepts.
        
        This method creates a simple ontology with common concepts like Entity,
        Animal, Person, etc.
        """
        # Create the root concept (Entity)
        entity = OntologyConcept(id="entity", name="Entity", description="The root concept")
        self.ontology.add_concept(entity)
        
        # Create some basic concepts
        concepts = [
            OntologyConcept(id="animal", name="Animal", description="A living organism"),
            OntologyConcept(id="person", name="Person", description="A human being"),
            OntologyConcept(id="object", name="Object", description="A physical object"),
            OntologyConcept(id="event", name="Event", description="Something that happens"),
            OntologyConcept(id="location", name="Location", description="A place"),
            OntologyConcept(id="time", name="Time", description="A point or period in time")
        ]
        
        # Add the concepts to the ontology and set up the hierarchy
        for concept in concepts:
            self.ontology.add_concept(concept)
            concept.add_parent_concept("entity")
            entity.add_child_concept(concept.id)
        
        # Create some more specific concepts
        subconcepts = [
            (OntologyConcept(id="dog", name="Dog", description="A domestic canine"), "animal"),
            (OntologyConcept(id="cat", name="Cat", description="A domestic feline"), "animal"),
            (OntologyConcept(id="building", name="Building", description="A structure"), "object"),
            (OntologyConcept(id="vehicle", name="Vehicle", description="A means of transport"), "object"),
            (OntologyConcept(id="city", name="City", description="A large settlement"), "location"),
            (OntologyConcept(id="country", name="Country", description="A nation"), "location")
        ]
        
        # Add the subconcepts to the ontology and set up the hierarchy
        for subconcept, parent_id in subconcepts:
            self.ontology.add_concept(subconcept)
            subconcept.add_parent_concept(parent_id)
            parent = self.ontology.get_concept(parent_id)
            if parent:
                parent.add_child_concept(subconcept.id)