"""
Sentence Generator (SG) for GödelOS NLG Pipeline.

This module provides the SentenceGenerator class that converts MessageSpecification
into linguistic structures, determining sentence boundaries, planning grammatical
structures, and handling referring expressions.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
from enum import Enum, auto
from collections import defaultdict

from godelOS.nlu_nlg.nlg.content_planner import (
    MessageSpecification, ContentElement, MessageType
)


class ReferringExpressionType(Enum):
    """Enumeration of referring expression types."""
    PROPER_NAME = auto()        # Proper name (e.g., "John")
    DEFINITE_NP = auto()        # Definite noun phrase (e.g., "the cat")
    INDEFINITE_NP = auto()      # Indefinite noun phrase (e.g., "a cat")
    PRONOUN = auto()            # Pronoun (e.g., "he", "it")
    DEMONSTRATIVE = auto()      # Demonstrative (e.g., "this", "that")
    POSSESSIVE = auto()         # Possessive (e.g., "his", "its")
    REFLEXIVE = auto()          # Reflexive (e.g., "himself", "itself")


class GrammaticalRole(Enum):
    """Enumeration of grammatical roles."""
    SUBJECT = auto()            # Subject of the sentence
    OBJECT = auto()             # Direct object
    INDIRECT_OBJECT = auto()    # Indirect object
    COMPLEMENT = auto()         # Complement
    MODIFIER = auto()           # Modifier
    DETERMINER = auto()         # Determiner
    PREPOSITION = auto()        # Preposition
    CONJUNCTION = auto()        # Conjunction


class TenseAspect(Enum):
    """Enumeration of tense and aspect combinations."""
    SIMPLE_PRESENT = auto()     # Simple present (e.g., "walks")
    PRESENT_PROGRESSIVE = auto() # Present progressive (e.g., "is walking")
    SIMPLE_PAST = auto()        # Simple past (e.g., "walked")
    PAST_PROGRESSIVE = auto()   # Past progressive (e.g., "was walking")
    PRESENT_PERFECT = auto()    # Present perfect (e.g., "has walked")
    PAST_PERFECT = auto()       # Past perfect (e.g., "had walked")
    FUTURE = auto()             # Future (e.g., "will walk")
    FUTURE_PERFECT = auto()     # Future perfect (e.g., "will have walked")


@dataclass
class LinguisticConstituent:
    """
    Represents a linguistic constituent in a sentence.
    
    A linguistic constituent is a word or group of words that functions as a
    single unit within a hierarchical structure.
    """
    id: str
    constituent_type: str  # e.g., "NP", "VP", "PP", "S"
    head: Optional[str] = None  # The head word
    features: Dict[str, Any] = field(default_factory=dict)
    children: List['LinguisticConstituent'] = field(default_factory=list)
    content_element_id: Optional[str] = None  # Link to the content element
    
    def add_child(self, child: 'LinguisticConstituent') -> None:
        """Add a child constituent."""
        self.children.append(child)
    
    def add_feature(self, name: str, value: Any) -> None:
        """Add a feature to this constituent."""
        self.features[name] = value


@dataclass
class SentencePlan:
    """
    Represents a plan for a sentence.
    
    A sentence plan specifies the linguistic structure of a sentence,
    including its constituents, grammatical features, and referring expressions.
    """
    id: str
    root: LinguisticConstituent
    tense_aspect: TenseAspect
    voice: str  # "active" or "passive"
    mood: str  # "indicative", "imperative", "interrogative", "subjunctive"
    referring_expressions: Dict[str, ReferringExpressionType] = field(default_factory=dict)
    discourse_connectives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_referring_expression(self, content_element_id: str, 
                                expr_type: ReferringExpressionType) -> None:
        """Specify the type of referring expression for a content element."""
        self.referring_expressions[content_element_id] = expr_type
    
    def add_discourse_connective(self, connective: str) -> None:
        """Add a discourse connective to the sentence."""
        self.discourse_connectives.append(connective)


class SentenceGenerator:
    """
    Sentence Generator for the NLG Pipeline.
    
    This class converts MessageSpecification into linguistic structures,
    determining sentence boundaries, planning grammatical structures,
    and handling referring expressions.
    """
    
    def __init__(self):
        """Initialize the sentence generator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_sentence_plans(self, message_spec: MessageSpecification,
                              context: Optional[Dict[str, Any]] = None) -> List[SentencePlan]:
        """
        Generate sentence plans from a message specification.
        
        Args:
            message_spec: The message specification to convert
            context: Optional context information for sentence planning
            
        Returns:
            A list of sentence plans
        """
        context = context or {}
        
        # Determine sentence boundaries
        sentence_groups = self._determine_sentence_boundaries(message_spec)
        
        # Generate a sentence plan for each group
        sentence_plans = []
        for i, group in enumerate(sentence_groups):
            plan = self._generate_sentence_plan(i, group, message_spec, context)
            sentence_plans.append(plan)
        
        return sentence_plans
    
    def _determine_sentence_boundaries(self, 
                                     message_spec: MessageSpecification) -> List[List[str]]:
        """
        Determine sentence boundaries based on the message specification.
        
        Args:
            message_spec: The message specification
            
        Returns:
            A list of groups of content element IDs, where each group
            represents the content elements to be expressed in a single sentence
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would consider factors like
        # complexity, coherence, and discourse structure
        
        # For now, we'll use a simple heuristic:
        # - Put each main content element in its own sentence
        # - Group supporting content with the main content it supports
        
        sentence_groups = []
        
        # Create a mapping from main content to supporting content
        main_to_supporting = defaultdict(list)
        for relation_type, relations in message_spec.discourse_relations.items():
            for source_id, target_id in relations:
                # Check if source is a main content element and target is supporting
                source_is_main = any(e.id == source_id for e in message_spec.main_content)
                target_is_supporting = any(e.id == target_id for e in message_spec.supporting_content)
                
                if source_is_main and target_is_supporting:
                    main_to_supporting[source_id].append(target_id)
        
        # Create a sentence group for each main content element
        for element in message_spec.main_content:
            group = [element.id]
            group.extend(main_to_supporting[element.id])
            sentence_groups.append(group)
        
        return sentence_groups
    
    def _generate_sentence_plan(self, index: int, content_ids: List[str],
                              message_spec: MessageSpecification,
                              context: Dict[str, Any]) -> SentencePlan:
        """
        Generate a sentence plan for a group of content elements.
        
        Args:
            index: The index of the sentence
            content_ids: The IDs of the content elements to express
            message_spec: The message specification
            context: Context information for sentence planning
            
        Returns:
            A sentence plan
        """
        # Create a unique ID for this sentence plan
        plan_id = f"sentence_{index}"
        
        # Determine the tense, aspect, voice, and mood based on the message type
        tense_aspect, voice, mood = self._determine_sentence_features(message_spec.message_type)
        
        # Create the root constituent for the sentence
        root = LinguisticConstituent(
            id=f"{plan_id}_root",
            constituent_type="S"
        )
        
        # Build the sentence structure
        self._build_sentence_structure(root, content_ids, message_spec)
        
        # Create the sentence plan
        plan = SentencePlan(
            id=plan_id,
            root=root,
            tense_aspect=tense_aspect,
            voice=voice,
            mood=mood
        )
        
        # Determine referring expressions
        self._determine_referring_expressions(plan, content_ids, message_spec, context)
        
        # Add discourse connectives if needed
        self._add_discourse_connectives(plan, index, message_spec)
        
        return plan
    
    def _determine_sentence_features(self, 
                                   message_type: MessageType) -> Tuple[TenseAspect, str, str]:
        """
        Determine the tense, aspect, voice, and mood based on the message type.
        
        Args:
            message_type: The type of message
            
        Returns:
            A tuple of (tense_aspect, voice, mood)
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would consider more factors
        
        if message_type == MessageType.STATEMENT:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.QUESTION:
            return TenseAspect.SIMPLE_PRESENT, "active", "interrogative"
        elif message_type == MessageType.COMMAND:
            return TenseAspect.SIMPLE_PRESENT, "active", "imperative"
        elif message_type == MessageType.DEFINITION:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.CONDITIONAL:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.NEGATION:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.POSSIBILITY:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.NECESSITY:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.BELIEF:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        elif message_type == MessageType.KNOWLEDGE:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
        else:
            return TenseAspect.SIMPLE_PRESENT, "active", "indicative"
    
    def _build_sentence_structure(self, root: LinguisticConstituent,
                                content_ids: List[str],
                                message_spec: MessageSpecification) -> None:
        """
        Build the sentence structure for a group of content elements.
        
        Args:
            root: The root constituent of the sentence
            content_ids: The IDs of the content elements to express
            message_spec: The message specification
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would build a more complex
        # syntactic structure based on the content elements
        
        # Find the main content element in this group
        main_content_id = next((id for id in content_ids if any(
            e.id == id for e in message_spec.main_content)), None)
        
        if not main_content_id:
            self.logger.warning(f"No main content element found in group {content_ids}")
            return
        
        # Find the main content element
        main_element = next((e for e in message_spec.main_content if e.id == main_content_id), None)
        
        if not main_element:
            self.logger.warning(f"Main content element {main_content_id} not found")
            return
        
        # Create a simple subject-verb-object structure based on the content type
        if main_element.content_type == "predication":
            # Create a subject noun phrase
            subject = LinguisticConstituent(
                id=f"{root.id}_subject",
                constituent_type="NP",
                content_element_id=main_content_id
            )
            root.add_child(subject)
            
            # Create a verb phrase
            verb = LinguisticConstituent(
                id=f"{root.id}_verb",
                constituent_type="VP",
                head=main_element.properties.get("operator", "unknown"),
                content_element_id=main_content_id
            )
            root.add_child(verb)
            
            # Create an object noun phrase if there are arguments
            if "argument" in message_spec.discourse_relations:
                for source_id, target_id in message_spec.discourse_relations["argument"]:
                    if source_id == main_content_id and target_id in content_ids:
                        object_np = LinguisticConstituent(
                            id=f"{root.id}_object",
                            constituent_type="NP",
                            content_element_id=target_id
                        )
                        verb.add_child(object_np)
        
        elif main_element.content_type == "quantification":
            # Create a determiner phrase
            determiner = LinguisticConstituent(
                id=f"{root.id}_determiner",
                constituent_type="DET",
                head=self._quantifier_to_determiner(main_element.properties.get("quantifier_type", "")),
                content_element_id=main_content_id
            )
            root.add_child(determiner)
            
            # Create a noun phrase for the bound variable
            if "binding" in message_spec.discourse_relations:
                for source_id, target_id in message_spec.discourse_relations["binding"]:
                    if source_id == main_content_id and target_id in content_ids:
                        noun = LinguisticConstituent(
                            id=f"{root.id}_noun",
                            constituent_type="NP",
                            content_element_id=target_id
                        )
                        root.add_child(noun)
            
            # Create a verb phrase for the scope
            if "scope" in message_spec.discourse_relations:
                for source_id, target_id in message_spec.discourse_relations["scope"]:
                    if source_id == main_content_id and target_id in content_ids:
                        verb = LinguisticConstituent(
                            id=f"{root.id}_verb",
                            constituent_type="VP",
                            content_element_id=target_id
                        )
                        root.add_child(verb)
        
        elif main_element.content_type == "connective":
            # Handle different connective types
            conn_type = main_element.properties.get("connective_type", "")
            
            if conn_type == "AND" or conn_type == "OR":
                # Create constituents for each operand
                if "operand" in message_spec.discourse_relations:
                    operands = []
                    for source_id, target_id in message_spec.discourse_relations["operand"]:
                        if source_id == main_content_id and target_id in content_ids:
                            operand = LinguisticConstituent(
                                id=f"{root.id}_operand_{len(operands)}",
                                constituent_type="S",
                                content_element_id=target_id
                            )
                            operands.append(operand)
                    
                    # Add the operands to the root with a conjunction
                    for i, operand in enumerate(operands):
                        root.add_child(operand)
                        if i < len(operands) - 1:
                            conjunction = LinguisticConstituent(
                                id=f"{root.id}_conj_{i}",
                                constituent_type="CONJ",
                                head=conn_type.lower()
                            )
                            root.add_child(conjunction)
            
            elif conn_type == "IMPLIES":
                # Create constituents for the antecedent and consequent
                if "operand" in message_spec.discourse_relations:
                    operands = []
                    for source_id, target_id in message_spec.discourse_relations["operand"]:
                        if source_id == main_content_id and target_id in content_ids:
                            operand = LinguisticConstituent(
                                id=f"{root.id}_operand_{len(operands)}",
                                constituent_type="S",
                                content_element_id=target_id
                            )
                            operands.append(operand)
                    
                    if len(operands) >= 2:
                        # Add "if" before the first operand
                        if_marker = LinguisticConstituent(
                            id=f"{root.id}_if",
                            constituent_type="COMP",
                            head="if"
                        )
                        root.add_child(if_marker)
                        root.add_child(operands[0])
                        
                        # Add "then" before the second operand
                        then_marker = LinguisticConstituent(
                            id=f"{root.id}_then",
                            constituent_type="COMP",
                            head="then"
                        )
                        root.add_child(then_marker)
                        root.add_child(operands[1])
            
            elif conn_type == "NOT":
                # Create a negation marker
                negation = LinguisticConstituent(
                    id=f"{root.id}_not",
                    constituent_type="NEG",
                    head="not"
                )
                root.add_child(negation)
                
                # Create a constituent for the operand
                if "operand" in message_spec.discourse_relations:
                    for source_id, target_id in message_spec.discourse_relations["operand"]:
                        if source_id == main_content_id and target_id in content_ids:
                            operand = LinguisticConstituent(
                                id=f"{root.id}_operand",
                                constituent_type="S",
                                content_element_id=target_id
                            )
                            root.add_child(operand)
        
        elif main_element.content_type == "modal_operation":
            # Handle different modal operator types
            modal_op = main_element.properties.get("modal_operator", "")
            
            # Create a subject noun phrase for the agent if present
            if "agent" in message_spec.discourse_relations:
                for source_id, target_id in message_spec.discourse_relations["agent"]:
                    if source_id == main_content_id and target_id in content_ids:
                        subject = LinguisticConstituent(
                            id=f"{root.id}_subject",
                            constituent_type="NP",
                            content_element_id=target_id
                        )
                        root.add_child(subject)
            
            # Create a modal verb
            modal_verb = LinguisticConstituent(
                id=f"{root.id}_modal",
                constituent_type="MODAL",
                head=self._modal_operator_to_verb(modal_op)
            )
            root.add_child(modal_verb)
            
            # Create a constituent for the proposition
            if "proposition" in message_spec.discourse_relations:
                for source_id, target_id in message_spec.discourse_relations["proposition"]:
                    if source_id == main_content_id and target_id in content_ids:
                        proposition = LinguisticConstituent(
                            id=f"{root.id}_proposition",
                            constituent_type="S",
                            content_element_id=target_id
                        )
                        root.add_child(proposition)
    
    def _quantifier_to_determiner(self, quantifier_type: str) -> str:
        """
        Convert a quantifier type to a determiner.
        
        Args:
            quantifier_type: The type of quantifier
            
        Returns:
            The corresponding determiner
        """
        if quantifier_type == "FORALL":
            return "every"
        elif quantifier_type == "EXISTS":
            return "some"
        else:
            return "the"
    
    def _modal_operator_to_verb(self, modal_operator: str) -> str:
        """
        Convert a modal operator to a verb.
        
        Args:
            modal_operator: The modal operator
            
        Returns:
            The corresponding verb
        """
        if modal_operator == "KNOWS":
            return "knows that"
        elif modal_operator == "BELIEVES":
            return "believes that"
        elif modal_operator == "POSSIBLE_WORLD_TRUTH":
            return "it is possible that"
        elif modal_operator == "OBLIGATORY":
            return "must"
        else:
            return "is"
    
    def _determine_referring_expressions(self, plan: SentencePlan,
                                       content_ids: List[str],
                                       message_spec: MessageSpecification,
                                       context: Dict[str, Any]) -> None:
        """
        Determine the type of referring expression to use for each content element.
        
        Args:
            plan: The sentence plan to update
            content_ids: The IDs of the content elements in this sentence
            message_spec: The message specification
            context: Context information for sentence planning
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would consider factors like
        # discourse history, salience, and potential ambiguity
        
        # Get all content elements in this sentence
        elements = []
        for id in content_ids:
            element = next((e for e in message_spec.main_content if e.id == id), None)
            if element:
                elements.append(element)
            else:
                element = next((e for e in message_spec.supporting_content if e.id == id), None)
                if element:
                    elements.append(element)
        
        # Determine the referring expression type for each element
        for element in elements:
            if element.content_type == "entity":
                # Use a proper name for entities if they have a name
                if "name" in element.properties:
                    plan.add_referring_expression(element.id, ReferringExpressionType.PROPER_NAME)
                else:
                    plan.add_referring_expression(element.id, ReferringExpressionType.DEFINITE_NP)
            
            elif element.content_type == "variable":
                # Use an indefinite noun phrase for variables
                plan.add_referring_expression(element.id, ReferringExpressionType.INDEFINITE_NP)
            
            else:
                # Use a definite noun phrase for other content types
                plan.add_referring_expression(element.id, ReferringExpressionType.DEFINITE_NP)
    
    def _add_discourse_connectives(self, plan: SentencePlan,
                                 index: int,
                                 message_spec: MessageSpecification) -> None:
        """
        Add discourse connectives to the sentence plan.
        
        Args:
            plan: The sentence plan to update
            index: The index of the sentence
            message_spec: The message specification
        """
        # This is a simplified implementation
        # In a more sophisticated system, we would consider the discourse
        # relations between sentences
        
        # Add a discourse connective for the first sentence based on the message type
        if index == 0:
            if message_spec.message_type == MessageType.CONDITIONAL:
                plan.add_discourse_connective("If")
            elif message_spec.message_type == MessageType.NEGATION:
                plan.add_discourse_connective("Not")
        
        # Add discourse connectives for subsequent sentences
        elif index > 0:
            # Add a simple connective based on the message type
            if message_spec.message_type == MessageType.STATEMENT:
                plan.add_discourse_connective("Additionally")
            elif message_spec.message_type == MessageType.EXPLANATION:
                plan.add_discourse_connective("Because")
            elif message_spec.message_type == MessageType.COMPARISON:
                plan.add_discourse_connective("Similarly")