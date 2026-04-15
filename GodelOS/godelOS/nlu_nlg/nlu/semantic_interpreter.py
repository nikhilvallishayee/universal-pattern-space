"""
Semantic Interpreter (SI) for GödelOS NLU Pipeline.

This module provides functionality for:
1. Mapping syntactic structures to formal meaning representations
2. Resolving word sense ambiguities
3. Identifying semantic roles
4. Handling basic anaphora resolution

It serves as the second stage in the NLU pipeline, converting syntactic
structures into semantic representations that capture the meaning of the text.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
import logging
from enum import Enum, auto
from collections import defaultdict

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
    Token, Entity, Span, Sentence, SyntacticParseOutput,
    VERB_DEP_LABELS, NOUN_DEP_LABELS, PREP_OBJECT_DEP_LABELS,
)


class SemanticRole(Enum):
    """Enumeration of semantic roles."""
    AGENT = auto()       # The doer of the action
    PATIENT = auto()     # The receiver of the action
    THEME = auto()       # The thing affected by the action
    INSTRUMENT = auto()  # The means by which an action is performed
    LOCATION = auto()    # Where the action occurs
    TIME = auto()        # When the action occurs
    MANNER = auto()      # How the action is performed
    PURPOSE = auto()     # Why the action is performed
    CAUSE = auto()       # What caused the action
    RECIPIENT = auto()   # Who receives the theme
    SOURCE = auto()      # Where the action originates
    GOAL = auto()        # Where the action is directed
    EXPERIENCER = auto() # Who experiences a state
    STIMULUS = auto()    # What causes an experience
    UNKNOWN = auto()     # Role could not be determined


class LogicalOperator(Enum):
    """Enumeration of logical operators."""
    AND = auto()
    OR = auto()
    NOT = auto()
    IMPLIES = auto()
    EQUIVALENT = auto()
    FORALL = auto()
    EXISTS = auto()


class RelationType(Enum):
    """Enumeration of relation types between entities."""
    IS_A = auto()          # Hypernymy (e.g., "A dog is an animal")
    PART_OF = auto()       # Meronymy (e.g., "A wheel is part of a car")
    HAS_PROPERTY = auto()  # Attribution (e.g., "The ball is red")
    LOCATED_AT = auto()    # Spatial relation (e.g., "The book is on the table")
    TEMPORAL = auto()      # Temporal relation (e.g., "The meeting is after lunch")
    CAUSES = auto()        # Causation (e.g., "Rain causes wetness")
    AGENT_ACTION = auto()  # Agent performing action (e.g., "John runs")
    ACTION_PATIENT = auto() # Action affecting patient (e.g., "John kicked the ball")
    POSSESSES = auto()     # Possession (e.g., "John has a car")
    EQUAL = auto()         # Equality (e.g., "John is the teacher")
    CUSTOM = auto()        # For domain-specific relations


@dataclass
class SemanticArgument:
    """
    Represents a semantic argument in a predicate.
    
    A semantic argument is a participant in an event or state, such as the agent
    or patient of an action.
    """
    text: str
    role: SemanticRole
    tokens: List[Token] = field(default_factory=list)
    entity: Optional[Entity] = None
    span: Optional[Span] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Predicate:
    """
    Represents a predicate in the semantic representation.
    
    A predicate describes an action, event, or state and its participants.
    """
    text: str
    lemma: str
    arguments: List[SemanticArgument] = field(default_factory=list)
    negated: bool = False
    modality: Optional[str] = None  # e.g., "possible", "necessary", "obligatory"
    tense: Optional[str] = None     # e.g., "past", "present", "future"
    aspect: Optional[str] = None    # e.g., "simple", "progressive", "perfect"
    tokens: List[Token] = field(default_factory=list)


@dataclass
class SemanticRelation:
    """
    Represents a semantic relation between entities or concepts.
    
    A semantic relation describes how entities or concepts are related to each other.
    """
    relation_type: RelationType
    source: Union[SemanticArgument, 'SemanticNode']
    target: Union[SemanticArgument, 'SemanticNode']
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticNode:
    """
    Represents a node in the semantic graph.
    
    A semantic node can be a predicate, entity, or complex expression.
    """
    id: str
    node_type: str  # "predicate", "entity", "logical_expression"
    content: Union[Predicate, SemanticArgument, None] = None
    children: List['SemanticNode'] = field(default_factory=list)
    operator: Optional[LogicalOperator] = None
    relations: List[SemanticRelation] = field(default_factory=list)
    
    def add_child(self, child: 'SemanticNode') -> None:
        """Add a child node to this node."""
        self.children.append(child)
    
    def add_relation(self, relation: SemanticRelation) -> None:
        """Add a relation to this node."""
        self.relations.append(relation)


@dataclass
class IntermediateSemanticRepresentation:
    """
    Intermediate Semantic Representation (ISR) for the input text.
    
    The ISR captures the meaning of the text in a structured form that can be
    further processed by downstream components.
    """
    text: str
    nodes: List[SemanticNode] = field(default_factory=list)
    root_nodes: List[SemanticNode] = field(default_factory=list)
    entities: Dict[str, SemanticArgument] = field(default_factory=dict)
    predicates: Dict[str, Predicate] = field(default_factory=dict)
    anaphora_resolution: Dict[str, str] = field(default_factory=dict)  # Maps pronouns to referents
    
    # Document-level metadata
    doc_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: SemanticNode, is_root: bool = False) -> None:
        """
        Add a node to the ISR.
        
        Args:
            node: The node to add
            is_root: Whether this is a root node
        """
        self.nodes.append(node)
        if is_root:
            self.root_nodes.append(node)
    
    def add_entity(self, entity_id: str, entity: SemanticArgument) -> None:
        """
        Add an entity to the ISR.
        
        Args:
            entity_id: The ID of the entity
            entity: The entity to add
        """
        self.entities[entity_id] = entity
    
    def add_predicate(self, predicate_id: str, predicate: Predicate) -> None:
        """
        Add a predicate to the ISR.
        
        Args:
            predicate_id: The ID of the predicate
            predicate: The predicate to add
        """
        self.predicates[predicate_id] = predicate
    
    def resolve_anaphora(self, anaphor: str, referent: str) -> None:
        """
        Resolve an anaphoric reference.
        
        Args:
            anaphor: The anaphoric expression (e.g., a pronoun)
            referent: The entity being referred to
        """
        self.anaphora_resolution[anaphor] = referent


class SemanticInterpreter:
    """
    Interprets the syntactic parse to produce a semantic representation.
    
    This class is responsible for mapping syntactic structures to formal meaning
    representations, resolving word sense ambiguities, identifying semantic roles,
    and handling basic anaphora resolution.
    """
    
    def __init__(self):
        """Initialize the semantic interpreter."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize counters for generating unique IDs
        self._node_counter = 0
        self._entity_counter = 0
        self._predicate_counter = 0
    
    def interpret(self, parse_output: SyntacticParseOutput) -> IntermediateSemanticRepresentation:
        """
        Interpret the syntactic parse to produce a semantic representation.
        
        Args:
            parse_output: The output of the syntactic parser
            
        Returns:
            An IntermediateSemanticRepresentation capturing the meaning of the text
        """
        # Create the ISR
        isr = IntermediateSemanticRepresentation(text=parse_output.text)
        
        # Process each sentence
        for sentence in parse_output.sentences:
            self._process_sentence(sentence, isr)
        
        # Resolve anaphora across sentences
        self._resolve_anaphora(parse_output, isr)
        
        return isr
    
    def _process_sentence(self, sentence: Sentence, isr: IntermediateSemanticRepresentation) -> None:
        """
        Process a sentence to extract its semantic representation.
        
        Args:
            sentence: The sentence to process
            isr: The ISR to update
        """
        # Extract predicates and their arguments
        predicates = self._extract_predicates(sentence)
        
        # Process each predicate
        for predicate in predicates:
            # Generate a unique ID for the predicate
            predicate_id = f"pred_{self._predicate_counter}"
            self._predicate_counter += 1
            
            # Add the predicate to the ISR
            isr.add_predicate(predicate_id, predicate)
            
            # Create a semantic node for the predicate
            node = SemanticNode(
                id=predicate_id,
                node_type="predicate",
                content=predicate
            )
            
            # Add the node to the ISR
            isr.add_node(node, is_root=True)
            
            # Process the arguments of the predicate
            for arg in predicate.arguments:
                # Generate a unique ID for the entity
                entity_id = f"entity_{self._entity_counter}"
                self._entity_counter += 1
                
                # Add the entity to the ISR
                isr.add_entity(entity_id, arg)
                
                # Create a semantic node for the entity
                entity_node = SemanticNode(
                    id=entity_id,
                    node_type="entity",
                    content=arg
                )
                
                # Add the entity node to the ISR
                isr.add_node(entity_node)
                
                # Create a relation between the predicate and the entity
                relation_type = self._map_semantic_role_to_relation_type(arg.role)
                relation = SemanticRelation(
                    relation_type=relation_type,
                    source=node,
                    target=entity_node
                )
                
                # Add the relation to the predicate node
                node.add_relation(relation)
    
    def _extract_predicates(self, sentence: Sentence) -> List[Predicate]:
        """
        Extract predicates and their arguments from a sentence.
        
        Args:
            sentence: The sentence to process
            
        Returns:
            A list of Predicates with their arguments
        """
        predicates = []
        
        # Find the main verb (root) of the sentence
        root_token = sentence.root_token
        if root_token and root_token.pos == "VERB":
            # Create a predicate for the main verb
            predicate = Predicate(
                text=root_token.text,
                lemma=root_token.lemma,
                tokens=[root_token],
                tense=self._extract_tense(root_token),
                aspect=self._extract_aspect(root_token)
            )
            
            # Extract arguments for the predicate
            arguments = self._extract_arguments(root_token, sentence)
            predicate.arguments = arguments
            
            # Check if the predicate is negated
            predicate.negated = self._is_negated(root_token, sentence)
            
            # Extract modality
            predicate.modality = self._extract_modality(root_token, sentence)
            
            predicates.append(predicate)
            
            # Process subordinate clauses
            for token in sentence.tokens:
                if token.dep in ["ccomp", "xcomp", "advcl"] and token.pos == "VERB":
                    # Create a predicate for the subordinate verb
                    sub_predicate = Predicate(
                        text=token.text,
                        lemma=token.lemma,
                        tokens=[token],
                        tense=self._extract_tense(token),
                        aspect=self._extract_aspect(token)
                    )
                    
                    # Extract arguments for the subordinate predicate
                    sub_arguments = self._extract_arguments(token, sentence)
                    sub_predicate.arguments = sub_arguments
                    
                    # Check if the subordinate predicate is negated
                    sub_predicate.negated = self._is_negated(token, sentence)
                    
                    # Extract modality
                    sub_predicate.modality = self._extract_modality(token, sentence)
                    
                    predicates.append(sub_predicate)
        
        return predicates
    
    def _extract_arguments(self, verb_token: Token, sentence: Sentence) -> List[SemanticArgument]:
        """
        Extract arguments for a predicate.
        
        Args:
            verb_token: The verb token representing the predicate
            sentence: The sentence containing the predicate
            
        Returns:
            A list of SemanticArguments
        """
        arguments = []
        
        # Find all tokens that directly depend on the verb
        dependent_tokens = [t for t in sentence.tokens if self._is_dependent_on(t, verb_token, sentence.tokens)]
        
        # Group tokens by their dependency relation to the verb
        dep_groups = defaultdict(list)
        for token in dependent_tokens:
            if token.i != verb_token.i:  # Exclude the verb itself
                dep_groups[token.dep].append(token)
        
        # Process subject (typically the agent)
        if "nsubj" in dep_groups:
            subject_tokens = dep_groups["nsubj"]
            subject_span = self._get_noun_phrase_for_token(subject_tokens[0], sentence)
            
            # Create a semantic argument for the subject
            subject_arg = SemanticArgument(
                text=subject_span.text if subject_span else subject_tokens[0].text,
                role=SemanticRole.AGENT,
                tokens=subject_span.tokens if subject_span else subject_tokens,
                span=subject_span
            )
            
            arguments.append(subject_arg)
        
        # Process direct object (typically the patient/theme)
        if "dobj" in dep_groups:
            object_tokens = dep_groups["dobj"]
            object_span = self._get_noun_phrase_for_token(object_tokens[0], sentence)
            
            # Create a semantic argument for the direct object
            object_arg = SemanticArgument(
                text=object_span.text if object_span else object_tokens[0].text,
                role=SemanticRole.PATIENT,
                tokens=object_span.tokens if object_span else object_tokens,
                span=object_span
            )
            
            arguments.append(object_arg)
        
        # Process indirect object (typically the recipient)
        if "iobj" in dep_groups or "dative" in dep_groups:
            iobj_tokens = dep_groups.get("iobj", []) + dep_groups.get("dative", [])
            iobj_span = self._get_noun_phrase_for_token(iobj_tokens[0], sentence) if iobj_tokens else None
            
            if iobj_span or iobj_tokens:
                # Create a semantic argument for the indirect object
                iobj_arg = SemanticArgument(
                    text=iobj_span.text if iobj_span else iobj_tokens[0].text,
                    role=SemanticRole.RECIPIENT,
                    tokens=iobj_span.tokens if iobj_span else iobj_tokens,
                    span=iobj_span
                )
                
                arguments.append(iobj_arg)
        
        # Process prepositional phrases
        if "prep" in dep_groups:
            for prep_token in dep_groups["prep"]:
                # Find the object of the preposition
                pobj_tokens = [t for t in sentence.tokens if t.dep == "pobj" and self._is_dependent_on(t, prep_token, sentence.tokens)]
                
                if pobj_tokens:
                    pobj_span = self._get_noun_phrase_for_token(pobj_tokens[0], sentence)
                    
                    # Determine the semantic role based on the preposition
                    role = self._determine_prep_role(prep_token.text)
                    
                    # Create a semantic argument for the prepositional phrase
                    prep_arg = SemanticArgument(
                        text=f"{prep_token.text} {pobj_span.text if pobj_span else pobj_tokens[0].text}",
                        role=role,
                        tokens=[prep_token] + (pobj_span.tokens if pobj_span else pobj_tokens),
                        span=pobj_span
                    )
                    
                    arguments.append(prep_arg)
        
        return arguments
    
    def _get_noun_phrase_for_token(self, token: Token, sentence: Sentence) -> Optional[Span]:
        """
        Find the noun phrase that contains the given token.
        
        Args:
            token: The token to find a noun phrase for
            sentence: The sentence containing the token
            
        Returns:
            The noun phrase containing the token, or None if not found
        """
        for np in sentence.noun_phrases:
            if token.i >= np.start_token and token.i < np.end_token:
                return np
        return None
    
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
    
    def _determine_prep_role(self, preposition: str) -> SemanticRole:
        """
        Determine the semantic role based on the preposition.
        
        Args:
            preposition: The preposition
            
        Returns:
            The semantic role
        """
        # Map common prepositions to semantic roles
        prep_to_role = {
            "in": SemanticRole.LOCATION,
            "at": SemanticRole.LOCATION,
            "on": SemanticRole.LOCATION,
            "with": SemanticRole.INSTRUMENT,
            "by": SemanticRole.AGENT,
            "for": SemanticRole.PURPOSE,
            "to": SemanticRole.GOAL,
            "from": SemanticRole.SOURCE,
            "because of": SemanticRole.CAUSE,
            "due to": SemanticRole.CAUSE,
            "during": SemanticRole.TIME,
            "before": SemanticRole.TIME,
            "after": SemanticRole.TIME
        }
        
        return prep_to_role.get(preposition.lower(), SemanticRole.UNKNOWN)
    
    def _extract_tense(self, verb_token: Token) -> Optional[str]:
        """
        Extract the tense of a verb.
        
        Args:
            verb_token: The verb token
            
        Returns:
            The tense of the verb, or None if not determined
        """
        # Extract tense from the verb's morphological features
        if "Tense" in verb_token.morphology:
            tense = verb_token.morphology["Tense"]
            return tense.lower()
        
        # If not in morphology, try to infer from the tag
        if verb_token.tag.startswith("VB"):
            if verb_token.tag == "VBD":
                return "past"
            elif verb_token.tag == "VBP" or verb_token.tag == "VBZ":
                return "present"
            elif verb_token.tag == "VB" and verb_token.dep == "aux" and verb_token.text.lower() in ["will", "shall"]:
                return "future"
        
        return None
    
    def _extract_aspect(self, verb_token: Token) -> Optional[str]:
        """
        Extract the aspect of a verb.
        
        Args:
            verb_token: The verb token
            
        Returns:
            The aspect of the verb, or None if not determined
        """
        # Extract aspect from the verb's morphological features
        if "Aspect" in verb_token.morphology:
            aspect = verb_token.morphology["Aspect"]
            return aspect.lower()
        
        # If not in morphology, try to infer from the tag
        if verb_token.tag.startswith("VB"):
            if verb_token.tag == "VBG":
                return "progressive"
            elif verb_token.tag == "VBN":
                return "perfect"
        
        return "simple"  # Default to simple aspect
    
    def _is_negated(self, verb_token: Token, sentence: Sentence) -> bool:
        """
        Check if a verb is negated.
        
        Args:
            verb_token: The verb token
            sentence: The sentence containing the verb
            
        Returns:
            True if the verb is negated, False otherwise
        """
        # Check for direct negation
        for token in sentence.tokens:
            if token.dep == "neg" and self._is_dependent_on(token, verb_token, sentence.tokens):
                return True
        
        return False
    
    def _extract_modality(self, verb_token: Token, sentence: Sentence) -> Optional[str]:
        """
        Extract the modality of a verb.
        
        Args:
            verb_token: The verb token
            sentence: The sentence containing the verb
            
        Returns:
            The modality of the verb, or None if not determined
        """
        # Check for modal auxiliaries
        for token in sentence.tokens:
            if token.dep == "aux" and token.pos == "VERB" and self._is_dependent_on(token, verb_token, sentence.tokens):
                # Map common modal auxiliaries to modality types
                modal_map = {
                    "can": "possible",
                    "could": "possible",
                    "may": "possible",
                    "might": "possible",
                    "must": "necessary",
                    "should": "obligatory",
                    "ought": "obligatory",
                    "shall": "obligatory",
                    "will": "future"
                }
                
                return modal_map.get(token.text.lower())
        
        return None
    
    def _map_semantic_role_to_relation_type(self, role: SemanticRole) -> RelationType:
        """
        Map a semantic role to a relation type.
        
        Args:
            role: The semantic role
            
        Returns:
            The corresponding relation type
        """
        # Map semantic roles to relation types
        role_to_relation = {
            SemanticRole.AGENT: RelationType.AGENT_ACTION,
            SemanticRole.PATIENT: RelationType.ACTION_PATIENT,
            SemanticRole.THEME: RelationType.ACTION_PATIENT,
            SemanticRole.INSTRUMENT: RelationType.PART_OF,
            SemanticRole.LOCATION: RelationType.LOCATED_AT,
            SemanticRole.TIME: RelationType.TEMPORAL,
            SemanticRole.MANNER: RelationType.HAS_PROPERTY,
            SemanticRole.PURPOSE: RelationType.CAUSES,
            SemanticRole.CAUSE: RelationType.CAUSES,
            SemanticRole.RECIPIENT: RelationType.POSSESSES,
            SemanticRole.SOURCE: RelationType.LOCATED_AT,
            SemanticRole.GOAL: RelationType.LOCATED_AT,
            SemanticRole.EXPERIENCER: RelationType.AGENT_ACTION,
            SemanticRole.STIMULUS: RelationType.CAUSES
        }
        
        return role_to_relation.get(role, RelationType.CUSTOM)
    
    def _resolve_anaphora(self, parse_output: SyntacticParseOutput, isr: IntermediateSemanticRepresentation) -> None:
        """
        Resolve anaphoric references in the text.
        
        Args:
            parse_output: The output of the syntactic parser
            isr: The ISR to update
        """
        # This is a simplified implementation of anaphora resolution
        # For a more sophisticated approach, we would need a coreference resolution model
        
        # Track entities mentioned so far
        entities = []
        
        # Process each sentence
        for sentence in parse_output.sentences:
            # Extract entities from the sentence
            sentence_entities = []
            for np in sentence.noun_phrases:
                # Skip pronouns for now
                if not any(t.pos == "PRON" for t in np.tokens):
                    sentence_entities.append(np)
            
            # Process pronouns in the sentence
            for token in sentence.tokens:
                if token.pos == "PRON":
                    # Determine the type of pronoun
                    pronoun_type = self._determine_pronoun_type(token)
                    
                    # Find a suitable antecedent
                    antecedent = self._find_antecedent(token, pronoun_type, entities, sentence_entities)
                    
                    if antecedent:
                        # Resolve the anaphoric reference
                        isr.resolve_anaphora(token.text, antecedent.text)
            
            # Add entities from this sentence to the list
            entities.extend(sentence_entities)
    
    def _determine_pronoun_type(self, pronoun_token: Token) -> str:
        """
        Determine the type of a pronoun.
        
        Args:
            pronoun_token: The pronoun token
            
        Returns:
            The type of the pronoun
        """
        # Extract features from the pronoun's morphology
        person = pronoun_token.morphology.get("Person", "3")
        number = pronoun_token.morphology.get("Number", "Sing")
        gender = pronoun_token.morphology.get("Gender", "Neut")
        
        # Determine the pronoun type
        if person == "1":
            return "first_person"
        elif person == "2":
            return "second_person"
        elif person == "3":
            if number == "Sing":
                if gender == "Masc":
                    return "third_person_masc"
                elif gender == "Fem":
                    return "third_person_fem"
                else:
                    return "third_person_neut"
            else:
                return "third_person_plural"
        
        return "unknown"
    
    def _find_antecedent(self, pronoun_token: Token, pronoun_type: str, 
                         entities: List[Span], sentence_entities: List[Span]) -> Optional[Span]:
        """
        Find a suitable antecedent for a pronoun.
        
        Args:
            pronoun_token: The pronoun token
            pronoun_type: The type of the pronoun
            entities: All entities mentioned so far
            sentence_entities: Entities in the current sentence
            
        Returns:
            A suitable antecedent, or None if not found
        """
        # This is a simplified implementation of antecedent selection
        # For a more sophisticated approach, we would need to consider more factors
        
        # For first and second person pronouns, we can't resolve the antecedent
        if pronoun_type in ["first_person", "second_person"]:
            return None
        
        # For third person pronouns, look for a suitable antecedent
        candidates = []
        
        # First, look for entities in the current sentence that appear before the pronoun
        for entity in sentence_entities:
            if entity.start_token < pronoun_token.i:
                candidates.append(entity)
        
        # If no candidates found, look at entities from previous sentences
        if not candidates:
            candidates = entities.copy()
        
        # If still no candidates, return None
        if not candidates:
            return None
        
        # For now, simply return the most recent entity
        # In a more sophisticated implementation, we would consider agreement in gender, number, etc.
        return candidates[-1]
