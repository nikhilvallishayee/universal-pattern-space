"""
Discourse State Manager (DM) for GödelOS NLU Pipeline.

This module provides functionality for:
1. Tracking discourse entities and their properties
2. Maintaining context for interpretation
3. Supporting anaphora resolution
4. Tracking dialogue state

It serves as a component in the NLU pipeline that maintains state across
utterances, enabling context-aware interpretation of natural language.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
from enum import Enum, auto
from collections import defaultdict, deque
import uuid

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
    Token, Entity, Span, Sentence, SyntacticParseOutput
)
from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    IntermediateSemanticRepresentation, SemanticNode, Predicate, 
    SemanticArgument, SemanticRelation, LogicalOperator, RelationType, SemanticRole
)


class DialogueActType(Enum):
    """Enumeration of dialogue act types."""
    STATEMENT = auto()         # Declarative statement
    QUESTION = auto()          # Question
    REQUEST = auto()           # Request for action
    GREETING = auto()          # Greeting
    FAREWELL = auto()          # Farewell
    ACKNOWLEDGMENT = auto()    # Acknowledgment
    CLARIFICATION = auto()     # Clarification request
    CONFIRMATION = auto()      # Confirmation
    REJECTION = auto()         # Rejection
    UNKNOWN = auto()           # Unknown dialogue act


@dataclass
class DialogueAct:
    """
    Represents a dialogue act in the conversation.
    
    A dialogue act is a functional unit in conversation, such as a statement,
    question, or request.
    """
    act_type: DialogueActType
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscourseEntity:
    """
    Represents an entity in the discourse.
    
    A discourse entity is an object that is being discussed in the conversation,
    such as a person, place, or thing.
    """
    id: str
    name: str
    type: Optional[str] = None
    mentions: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    salience: float = 1.0  # How salient/important the entity is in the discourse
    first_mention_time: Optional[float] = None
    last_mention_time: Optional[float] = None
    
    def add_mention(self, mention: str, time: Optional[float] = None) -> None:
        """
        Add a mention of this entity.
        
        Args:
            mention: The text of the mention
            time: The time of the mention
        """
        self.mentions.append(mention)
        if time is not None:
            if self.first_mention_time is None:
                self.first_mention_time = time
            self.last_mention_time = time
    
    def add_property(self, property_name: str, property_value: Any) -> None:
        """
        Add a property to this entity.
        
        Args:
            property_name: The name of the property
            property_value: The value of the property
        """
        self.properties[property_name] = property_value
    
    def update_salience(self, time: float, decay_factor: float = 0.9) -> None:
        """
        Update the salience of this entity based on time.
        
        Args:
            time: The current time
            decay_factor: The factor by which salience decays over time
        """
        if self.last_mention_time is not None:
            time_since_last_mention = time - self.last_mention_time
            self.salience *= decay_factor ** time_since_last_mention
        else:
            self.salience = 0.1  # Default low salience for entities never mentioned


@dataclass
class DiscourseRelation:
    """
    Represents a relation between discourse entities.
    
    A discourse relation describes how entities are related to each other in the
    discourse, such as one entity being a part of another.
    """
    id: str
    relation_type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def add_property(self, property_name: str, property_value: Any) -> None:
        """
        Add a property to this relation.
        
        Args:
            property_name: The name of the property
            property_value: The value of the property
        """
        self.properties[property_name] = property_value


@dataclass
class DialogueState:
    """
    Represents the state of the dialogue.
    
    The dialogue state tracks the current state of the conversation, including
    the current topic, user goals, and system state.
    """
    current_topic: Optional[str] = None
    user_goals: List[str] = field(default_factory=list)
    system_state: Dict[str, Any] = field(default_factory=dict)
    dialogue_history: List[DialogueAct] = field(default_factory=list)
    turn_count: int = 0
    
    def add_dialogue_act(self, act: DialogueAct) -> None:
        """
        Add a dialogue act to the history.
        
        Args:
            act: The dialogue act to add
        """
        self.dialogue_history.append(act)
        self.turn_count += 1
    
    def set_topic(self, topic: str) -> None:
        """
        Set the current topic of the dialogue.
        
        Args:
            topic: The new topic
        """
        self.current_topic = topic
    
    def add_user_goal(self, goal: str) -> None:
        """
        Add a user goal to the dialogue state.
        
        Args:
            goal: The user goal to add
        """
        if goal not in self.user_goals:
            self.user_goals.append(goal)
    
    def update_system_state(self, key: str, value: Any) -> None:
        """
        Update the system state.
        
        Args:
            key: The key to update
            value: The new value
        """
        self.system_state[key] = value


@dataclass
class DiscourseContext:
    """
    Represents the context of the discourse.
    
    The discourse context tracks entities, relations, and the dialogue state
    across utterances, enabling context-aware interpretation.
    """
    entities: Dict[str, DiscourseEntity] = field(default_factory=dict)
    relations: Dict[str, DiscourseRelation] = field(default_factory=dict)
    dialogue_state: DialogueState = field(default_factory=DialogueState)
    
    # Recent mentions for anaphora resolution
    recent_mentions: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Temporal context
    current_time: float = 0.0
    
    def add_entity(self, entity: DiscourseEntity) -> None:
        """
        Add an entity to the discourse context.
        
        Args:
            entity: The entity to add
        """
        self.entities[entity.id] = entity
    
    def add_relation(self, relation: DiscourseRelation) -> None:
        """
        Add a relation to the discourse context.
        
        Args:
            relation: The relation to add
        """
        self.relations[relation.id] = relation
    
    def add_mention(self, entity_id: str, mention: str) -> None:
        """
        Add a mention of an entity.
        
        Args:
            entity_id: The ID of the entity
            mention: The text of the mention
        """
        if entity_id in self.entities:
            self.entities[entity_id].add_mention(mention, self.current_time)
            self.recent_mentions.append((entity_id, mention))
    
    def update_time(self, time_increment: float = 1.0) -> None:
        """
        Update the current time.
        
        Args:
            time_increment: The amount to increment the time by
        """
        self.current_time += time_increment
        
        # Update entity salience
        for entity in self.entities.values():
            entity.update_salience(self.current_time)
    
    def get_most_salient_entities(self, n: int = 5) -> List[DiscourseEntity]:
        """
        Get the most salient entities in the discourse.
        
        Args:
            n: The number of entities to return
            
        Returns:
            The n most salient entities
        """
        return sorted(self.entities.values(), key=lambda e: e.salience, reverse=True)[:n]
    
    def get_entity_by_mention(self, mention: str) -> Optional[DiscourseEntity]:
        """
        Get an entity by one of its mentions.
        
        Args:
            mention: The mention to look for
            
        Returns:
            The entity with the given mention, or None if not found
        """
        for entity in self.entities.values():
            if mention in entity.mentions:
                return entity
        return None
    
    def get_relations_for_entity(self, entity_id: str) -> List[DiscourseRelation]:
        """
        Get all relations involving an entity.
        
        Args:
            entity_id: The ID of the entity
            
        Returns:
            A list of relations involving the entity
        """
        return [r for r in self.relations.values() if r.source_id == entity_id or r.target_id == entity_id]


class DiscourseStateManager:
    """
    Manages the discourse state across utterances.
    
    This class is responsible for tracking discourse entities and their properties,
    maintaining context for interpretation, supporting anaphora resolution, and
    tracking dialogue state.
    """
    
    def __init__(self):
        """Initialize the discourse state manager."""
        self.context = DiscourseContext()
        self.logger = logging.getLogger(__name__)
    
    def process_utterance(self, parse_output: SyntacticParseOutput, 
                         isr: IntermediateSemanticRepresentation) -> DiscourseContext:
        """
        Process an utterance to update the discourse context.
        
        Args:
            parse_output: The output of the syntactic parser
            isr: The Intermediate Semantic Representation
            
        Returns:
            The updated discourse context
        """
        # Update the time
        self.context.update_time()
        
        # Extract entities from the parse output
        self._extract_entities(parse_output)
        
        # Extract relations from the ISR
        self._extract_relations(isr)
        
        # Determine the dialogue act
        dialogue_act = self._determine_dialogue_act(parse_output)
        self.context.dialogue_state.add_dialogue_act(dialogue_act)
        
        # Update the dialogue state
        self._update_dialogue_state(parse_output, isr)
        
        return self.context
    
    def resolve_anaphora(self, token: Token) -> Optional[DiscourseEntity]:
        """
        Resolve an anaphoric reference.
        
        Args:
            token: The token representing the anaphoric reference
            
        Returns:
            The entity being referred to, or None if not found
        """
        # This is a simplified implementation of anaphora resolution
        # For a more sophisticated approach, we would need to consider more factors
        
        # Only handle pronouns for now
        if token.pos != "PRON":
            return None
        
        # Get the most salient entities
        salient_entities = self.context.get_most_salient_entities()
        
        # If there are no salient entities, return None
        if not salient_entities:
            return None
        
        # For simplicity, just return the most salient entity
        # In a more sophisticated implementation, we would consider agreement in gender, number, etc.
        return salient_entities[0]
    
    def _extract_entities(self, parse_output: SyntacticParseOutput) -> None:
        """
        Extract entities from the parse output and add them to the discourse context.
        
        Args:
            parse_output: The output of the syntactic parser
        """
        # Process named entities
        for entity in parse_output.entities:
            # Check if this entity already exists in the context
            existing_entity = self.context.get_entity_by_mention(entity.text)
            
            if existing_entity:
                # Update the existing entity
                existing_entity.add_mention(entity.text, self.context.current_time)
                existing_entity.salience += 0.5  # Increase salience for mentioned entities
            else:
                # Create a new entity
                entity_id = str(uuid.uuid4())
                discourse_entity = DiscourseEntity(
                    id=entity_id,
                    name=entity.text,
                    type=entity.label,
                    mentions=[entity.text],
                    first_mention_time=self.context.current_time,
                    last_mention_time=self.context.current_time,
                    salience=1.0  # New entities start with high salience
                )
                
                self.context.add_entity(discourse_entity)
                self.context.recent_mentions.append((entity_id, entity.text))
        
        # Process noun phrases that aren't named entities
        for np in parse_output.noun_phrases:
            # Skip noun phrases that are already covered by named entities
            if any(e.start_token <= np.start_token and e.end_token >= np.end_token for e in parse_output.entities):
                continue
            
            # Check if this noun phrase already exists in the context
            existing_entity = self.context.get_entity_by_mention(np.text)
            
            if existing_entity:
                # Update the existing entity
                existing_entity.add_mention(np.text, self.context.current_time)
                existing_entity.salience += 0.3  # Increase salience for mentioned entities
            else:
                # Create a new entity
                entity_id = str(uuid.uuid4())
                discourse_entity = DiscourseEntity(
                    id=entity_id,
                    name=np.text,
                    type="NOUN_PHRASE",
                    mentions=[np.text],
                    first_mention_time=self.context.current_time,
                    last_mention_time=self.context.current_time,
                    salience=0.8  # New noun phrases start with medium salience
                )
                
                self.context.add_entity(discourse_entity)
                self.context.recent_mentions.append((entity_id, np.text))
    
    def _extract_relations(self, isr: IntermediateSemanticRepresentation) -> None:
        """
        Extract relations from the ISR and add them to the discourse context.
        
        Args:
            isr: The Intermediate Semantic Representation
        """
        # Process semantic relations in the ISR
        for node in isr.nodes:
            for relation in node.relations:
                # Skip relations that don't involve entities
                if not isinstance(relation.source, SemanticNode) or not isinstance(relation.target, SemanticNode):
                    continue
                
                source_node = cast(SemanticNode, relation.source)
                target_node = cast(SemanticNode, relation.target)
                
                # Skip nodes that don't have content
                if not source_node.content or not target_node.content:
                    continue
                
                # Get the entity IDs
                source_id = source_node.id
                target_id = target_node.id
                
                # Create a new relation
                relation_id = str(uuid.uuid4())
                discourse_relation = DiscourseRelation(
                    id=relation_id,
                    relation_type=relation.relation_type.name,
                    source_id=source_id,
                    target_id=target_id,
                    confidence=relation.confidence
                )
                
                self.context.add_relation(discourse_relation)
    
    def _determine_dialogue_act(self, parse_output: SyntacticParseOutput) -> DialogueAct:
        """
        Determine the dialogue act of the utterance.
        
        Args:
            parse_output: The output of the syntactic parser
            
        Returns:
            The dialogue act
        """
        # This is a simplified implementation of dialogue act classification
        # For a more sophisticated approach, we would use a machine learning model
        
        # Check if the utterance is a question
        is_question = False
        for sentence in parse_output.sentences:
            # Check if the sentence ends with a question mark
            if sentence.text.strip().endswith("?"):
                is_question = True
                break
            
            # Check if the sentence starts with a wh-word or auxiliary verb
            first_token = sentence.tokens[0] if sentence.tokens else None
            if first_token and (first_token.tag.startswith("W") or first_token.dep == "aux"):
                is_question = True
                break
        
        if is_question:
            act_type = DialogueActType.QUESTION
        else:
            # For simplicity, assume all other utterances are statements
            act_type = DialogueActType.STATEMENT
        
        # Create a dialogue act
        return DialogueAct(
            act_type=act_type,
            content=parse_output.text
        )
    
    def _update_dialogue_state(self, parse_output: SyntacticParseOutput, 
                              isr: IntermediateSemanticRepresentation) -> None:
        """
        Update the dialogue state based on the utterance.
        
        Args:
            parse_output: The output of the syntactic parser
            isr: The Intermediate Semantic Representation
        """
        # This is a simplified implementation of dialogue state tracking
        # For a more sophisticated approach, we would use a more complex model
        
        # Try to determine the topic of the utterance
        topic = self._determine_topic(parse_output, isr)
        if topic:
            self.context.dialogue_state.set_topic(topic)
        
        # If the utterance is a question, add a user goal to answer it
        last_act = self.context.dialogue_state.dialogue_history[-1] if self.context.dialogue_state.dialogue_history else None
        if last_act and last_act.act_type == DialogueActType.QUESTION:
            self.context.dialogue_state.add_user_goal(f"answer_question: {last_act.content}")
    
    def _determine_topic(self, parse_output: SyntacticParseOutput, 
                        isr: IntermediateSemanticRepresentation) -> Optional[str]:
        """
        Determine the topic of the utterance.
        
        Args:
            parse_output: The output of the syntactic parser
            isr: The Intermediate Semantic Representation
            
        Returns:
            The topic of the utterance, or None if not determined
        """
        # This is a simplified implementation of topic detection
        # For a more sophisticated approach, we would use a more complex model
        
        # For simplicity, just use the most frequent noun as the topic
        noun_counts = defaultdict(int)
        for token in parse_output.tokens:
            if token.pos in ("NOUN", "PROPN"):
                noun_counts[token.lemma] += 1
        
        if not noun_counts:
            return None
        
        # Return the most frequent noun
        return max(noun_counts.items(), key=lambda x: x[1])[0]