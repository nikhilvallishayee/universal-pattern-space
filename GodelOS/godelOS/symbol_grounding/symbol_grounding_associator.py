"""
Symbol Grounding Associator (SGA) for GödelOS.

This module implements the SymbolGroundingAssociator component (Module 4.4) of the Symbol Grounding System,
which is responsible for learning and maintaining bidirectional associations between abstract symbolic
concepts/predicates (from the ontology) and patterns in sub-symbolic data (perceptual features, action-effect
experiences).

The SymbolGroundingAssociator performs:
1. Learning associations between symbols and sub-symbolic patterns from experience
2. Enabling recognition of symbols from perceptual input
3. Enabling prediction of perceptual consequences from symbols
"""

import logging
import time
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import numpy as np
from datetime import datetime

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode

logger = logging.getLogger(__name__)


@dataclass
class GroundingLink:
    """
    Represents an association between a symbol and a sub-symbolic pattern.
    
    Attributes:
        symbol_ast_id: Identifier of the symbol AST node
        sub_symbolic_representation: The sub-symbolic representation (e.g., feature vector, model parameters)
        modality: The sensory modality (e.g., "visual_features", "proprioceptive_force")
        confidence: Confidence in the grounding
        update_count: Number of times this grounding has been updated
        last_updated: Timestamp of the last update
    """
    symbol_ast_id: str
    sub_symbolic_representation: Any
    modality: str
    confidence: float = 0.5
    update_count: int = 1
    last_updated: float = field(default_factory=time.time)


@dataclass
class GroundingPredictionError:
    """
    Prediction error for a symbol grounding activation.

    Captures the discrepancy between the prototype the grounder has learned
    for *symbol_ast_id* and the features actually observed.
    """
    symbol_ast_id: str
    modality: str
    timestamp: float = field(default_factory=time.time)
    predicted_features: Dict[str, float] = field(default_factory=dict)
    observed_features: Dict[str, float] = field(default_factory=dict)
    feature_errors: Dict[str, float] = field(default_factory=dict)
    error_norm: float = 0.0


@dataclass
class ExperienceTrace:
    """
    Represents a structured log entry for an experience.
    
    Attributes:
        timestamp: Time when the experience was recorded
        active_symbols_in_kb: Set of active symbols in the knowledge base
        raw_percepts_by_sensor: Dictionary mapping sensor IDs to raw percepts
        extracted_features_by_object: Dictionary mapping object IDs to feature vectors
        executed_action_ast: AST node representing the executed action, if any
        observed_effect_symbols: Set of observed effect symbols
        observed_effect_raw_sensors: Dictionary of raw sensor data after action execution
    """
    timestamp: float = field(default_factory=time.time)
    active_symbols_in_kb: Set[AST_Node] = field(default_factory=set)
    raw_percepts_by_sensor: Dict[str, Any] = field(default_factory=dict)
    extracted_features_by_object: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    executed_action_ast: Optional[AST_Node] = None
    observed_effect_symbols: Set[AST_Node] = field(default_factory=set)
    observed_effect_raw_sensors: Dict[str, Any] = field(default_factory=dict)


class GroundingModel:
    """
    Base class for grounding models that learn associations between symbols and sub-symbolic patterns.
    
    Grounding models implement the learning and prediction functionality for different types of
    associations (e.g., visual features to symbols, action effects to symbols).
    """
    
    def __init__(self, model_id: str, modality: str):
        """
        Initialize a grounding model.
        
        Args:
            model_id: Unique identifier for the model
            modality: Sensory modality this model works with
        """
        self.model_id = model_id
        self.modality = modality
    
    def learn(self, symbol_ast_id: str, examples: List[Any]) -> Any:
        """
        Learn a sub-symbolic representation for a symbol from examples.
        
        Args:
            symbol_ast_id: Identifier of the symbol AST node
            examples: List of examples to learn from
            
        Returns:
            The learned sub-symbolic representation
        """
        raise NotImplementedError("Subclasses must implement learn()")
    
    def predict(self, sub_symbolic_representation: Any, input_data: Any) -> float:
        """
        Predict the likelihood that input data matches a sub-symbolic representation.
        
        Args:
            sub_symbolic_representation: The sub-symbolic representation to match against
            input_data: The input data to evaluate
            
        Returns:
            Confidence score between 0 and 1
        """
        raise NotImplementedError("Subclasses must implement predict()")
    
    def update(self, sub_symbolic_representation: Any, new_example: Any) -> Any:
        """
        Update a sub-symbolic representation with a new example.
        
        Args:
            sub_symbolic_representation: The existing sub-symbolic representation
            new_example: The new example to incorporate
            
        Returns:
            The updated sub-symbolic representation
        """
        raise NotImplementedError("Subclasses must implement update()")


class PrototypeModel(GroundingModel):
    """
    A simple prototype-based grounding model.
    
    This model represents concepts as prototypes (average feature vectors) and
    computes similarity using Euclidean distance.
    """
    
    def __init__(self, modality: str):
        """Initialize a prototype model for the given modality."""
        super().__init__(f"prototype_{modality}", modality)
    
    def learn(self, symbol_ast_id: str, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Learn a prototype representation for a symbol from examples.
        
        Args:
            symbol_ast_id: Identifier of the symbol AST node
            examples: List of feature dictionaries to learn from
            
        Returns:
            The prototype feature dictionary
        """
        if not examples:
            return {}
        
        # Extract all feature keys
        all_keys = set()
        for example in examples:
            all_keys.update(example.keys())
        
        # Initialize prototype
        prototype = {}
        
        # Compute average for each feature
        for key in all_keys:
            # Collect values for this feature
            values = []
            for example in examples:
                if key in example:
                    values.append(example[key])
            
            if not values:
                continue
            
            # Compute average based on value type
            if all(isinstance(v, (int, float)) for v in values):
                # Numerical feature
                prototype[key] = sum(values) / len(values)
            elif all(isinstance(v, str) for v in values):
                # Categorical feature - use most common value
                from collections import Counter
                counter = Counter(values)
                prototype[key] = counter.most_common(1)[0][0]
        
        return prototype
    
    def predict(self, sub_symbolic_representation: Dict[str, Any], input_data: Dict[str, Any]) -> float:
        """
        Predict the likelihood that input data matches a prototype.
        
        Args:
            sub_symbolic_representation: The prototype feature dictionary
            input_data: The input feature dictionary to evaluate
            
        Returns:
            Confidence score between 0 and 1
        """
        if not sub_symbolic_representation or not input_data:
            return 0.0
        
        # Compute similarity based on shared features
        shared_keys = set(sub_symbolic_representation.keys()) & set(input_data.keys())
        if not shared_keys:
            return 0.0
        
        # Compute similarity for each shared feature
        similarities = []
        for key in shared_keys:
            proto_value = sub_symbolic_representation[key]
            input_value = input_data[key]
            
            # Compute similarity based on value type
            if isinstance(proto_value, (int, float)) and isinstance(input_value, (int, float)):
                # Numerical feature - use normalized difference
                # Assuming values typically range from 0 to 1; adjust scaling as needed
                diff = abs(proto_value - input_value)
                max_diff = max(1.0, abs(proto_value), abs(input_value))
                similarity = 1.0 - min(1.0, diff / max_diff)
            elif isinstance(proto_value, str) and isinstance(input_value, str):
                # Categorical feature - exact match
                similarity = 1.0 if proto_value == input_value else 0.0
            else:
                # Incompatible types
                similarity = 0.0
            
            similarities.append(similarity)
        
        # Overall similarity is the average of individual similarities
        return sum(similarities) / len(similarities)
    
    def update(self, sub_symbolic_representation: Dict[str, Any], new_example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a prototype with a new example.
        
        Args:
            sub_symbolic_representation: The existing prototype feature dictionary
            new_example: The new feature dictionary to incorporate
            
        Returns:
            The updated prototype feature dictionary
        """
        if not sub_symbolic_representation:
            return new_example.copy()
        
        # Create a copy of the prototype
        updated_prototype = sub_symbolic_representation.copy()
        
        # Update each feature in the new example
        for key, value in new_example.items():
            if key in updated_prototype:
                # Update existing feature
                proto_value = updated_prototype[key]
                
                if isinstance(proto_value, (int, float)) and isinstance(value, (int, float)):
                    # For numerical features, update running average (assuming equal weight)
                    # In a more sophisticated implementation, we might track the count
                    # and use a weighted average
                    updated_prototype[key] = (proto_value + value) / 2
                elif isinstance(proto_value, str) and isinstance(value, str):
                    # For categorical features, keep existing value
                    # In a more sophisticated implementation, we might track frequencies
                    # and use the most common value
                    pass
            else:
                # Add new feature
                updated_prototype[key] = value
        
        return updated_prototype

    @staticmethod
    def compute_prediction_error(
        predicted: Dict[str, Any], observed: Dict[str, Any]
    ) -> Tuple[Dict[str, float], float]:
        """
        Compute per-feature absolute errors and RMSE norm between *predicted*
        and *observed* feature dictionaries.

        Only shared keys whose values are both numeric are compared.

        Returns:
            (feature_errors, rmse_norm) — empty dict and 0.0 when no shared
            numerical keys exist.
        """
        feature_errors: Dict[str, float] = {}
        for key in predicted:
            if key not in observed:
                continue
            pv, ov = predicted[key], observed[key]
            if isinstance(pv, (int, float)) and isinstance(ov, (int, float)):
                feature_errors[key] = abs(float(pv) - float(ov))

        if not feature_errors:
            return {}, 0.0

        sum_sq = sum(e * e for e in feature_errors.values())
        rmse = (sum_sq / len(feature_errors)) ** 0.5
        return feature_errors, rmse


class ActionEffectModel(GroundingModel):
    """
    A model for learning and predicting action effects.
    
    This model associates action types and contexts with expected effects.
    """
    
    def __init__(self, modality: str):
        """Initialize an action effect model for the given modality."""
        super().__init__(f"action_effect_{modality}", modality)
    
    def learn(self, symbol_ast_id: str, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Learn an action effect model from examples.
        
        Args:
            symbol_ast_id: Identifier of the symbol AST node (action type)
            examples: List of action effect examples
            
        Returns:
            The learned action effect model
        """
        if not examples:
            return {}
        
        # Extract effect patterns
        effect_patterns = []
        for example in examples:
            if "effect" in example:
                effect_patterns.append(example["effect"])
        
        if not effect_patterns:
            return {}
        
        # For now, just use a simple prototype model for the effects
        prototype_model = PrototypeModel(self.modality)
        effect_prototype = prototype_model.learn(symbol_ast_id, effect_patterns)
        
        return {
            "action_type": symbol_ast_id,
            "effect_prototype": effect_prototype
        }
    
    def predict(self, sub_symbolic_representation: Dict[str, Any], input_data: Dict[str, Any]) -> float:
        """
        Predict the likelihood of an effect given an action context.
        
        Args:
            sub_symbolic_representation: The action effect model
            input_data: The action context to evaluate
            
        Returns:
            Confidence score between 0 and 1
        """
        if not sub_symbolic_representation or "effect_prototype" not in sub_symbolic_representation:
            return 0.0
        
        # Use the prototype model to predict similarity to the effect prototype
        prototype_model = PrototypeModel(self.modality)
        return prototype_model.predict(sub_symbolic_representation["effect_prototype"], input_data)
    
    def update(self, sub_symbolic_representation: Dict[str, Any], new_example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an action effect model with a new example.
        
        Args:
            sub_symbolic_representation: The existing action effect model
            new_example: The new action effect example to incorporate
            
        Returns:
            The updated action effect model
        """
        if not sub_symbolic_representation or "effect_prototype" not in sub_symbolic_representation:
            return self.learn(new_example.get("action_type", "unknown"), [new_example])
        
        # Update the effect prototype using the prototype model
        prototype_model = PrototypeModel(self.modality)
        effect_data = new_example.get("effect", new_example) if isinstance(new_example, dict) else new_example
        updated_effect_prototype = prototype_model.update(
            sub_symbolic_representation["effect_prototype"],
            effect_data
        )
        
        return {
            "action_type": sub_symbolic_representation.get("action_type", "unknown"),
            "effect_prototype": updated_effect_prototype
        }


class SymbolGroundingAssociator:
    """
    Symbol Grounding Associator (SGA) for GödelOS.
    
    The SymbolGroundingAssociator learns and maintains bidirectional associations between
    abstract symbolic concepts/predicates and patterns in sub-symbolic data.
    """
    
    def __init__(self, 
                 kr_system_interface: KnowledgeStoreInterface,
                 type_system: TypeSystemManager,
                 grounding_model_db_path: Optional[str] = None,
                 experience_buffer_size: int = 1000):
        """
        Initialize the symbol grounding associator.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation System
            type_system: Type system manager
            grounding_model_db_path: Optional path to store grounding models
            experience_buffer_size: Maximum size of the experience buffer
        """
        self.kr_interface = kr_system_interface
        self.type_system = type_system
        self.grounding_model_db_path = grounding_model_db_path
        self.experience_buffer_size = experience_buffer_size
        
        # Create grounding context if it doesn't exist
        if "GROUNDING_CONTEXT" not in kr_system_interface.list_contexts():
            kr_system_interface.create_context("GROUNDING_CONTEXT", None, "grounding")
        
        # Initialize grounding models
        self.grounding_models = {
            "visual_features": PrototypeModel("visual_features"),
            "proprioceptive_force": PrototypeModel("proprioceptive_force"),
            "action_effect": ActionEffectModel("action_effect")
        }
        
        # Initialize grounding links
        self.grounding_links: Dict[str, List[GroundingLink]] = {}
        
        # Initialize experience buffer
        self.experience_buffer: List[ExperienceTrace] = []
        
        # Load existing grounding links if available
        self._load_grounding_links()
    
    def _load_grounding_links(self) -> None:
        """Load grounding links from disk if available."""
        if not self.grounding_model_db_path or not os.path.exists(self.grounding_model_db_path):
            return
        
        try:
            with open(self.grounding_model_db_path, 'r') as f:
                data = json.load(f)
                
                # Convert the loaded data back to GroundingLink objects
                for symbol_ast_id, links_data in data.items():
                    self.grounding_links[symbol_ast_id] = []
                    for link_data in links_data:
                        link = GroundingLink(
                            symbol_ast_id=link_data["symbol_ast_id"],
                            sub_symbolic_representation=link_data["sub_symbolic_representation"],
                            modality=link_data["modality"],
                            confidence=link_data["confidence"],
                            update_count=link_data["update_count"],
                            last_updated=link_data["last_updated"]
                        )
                        self.grounding_links[symbol_ast_id].append(link)
            
            logger.info(f"Loaded {sum(len(links) for links in self.grounding_links.values())} grounding links")
        except Exception as e:
            logger.error(f"Error loading grounding links: {e}")
    
    def _save_grounding_links(self) -> None:
        """Save grounding links to disk."""
        if not self.grounding_model_db_path:
            return
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.grounding_model_db_path), exist_ok=True)
            
            # Convert GroundingLink objects to serializable dictionaries
            data = {}
            for symbol_ast_id, links in self.grounding_links.items():
                data[symbol_ast_id] = []
                for link in links:
                    data[symbol_ast_id].append({
                        "symbol_ast_id": link.symbol_ast_id,
                        "sub_symbolic_representation": link.sub_symbolic_representation,
                        "modality": link.modality,
                        "confidence": link.confidence,
                        "update_count": link.update_count,
                        "last_updated": link.last_updated
                    })
            
            with open(self.grounding_model_db_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {sum(len(links) for links in self.grounding_links.values())} grounding links")
        except Exception as e:
            logger.error(f"Error saving grounding links: {e}")
    
    def record_experience(self, trace: ExperienceTrace) -> None:
        """
        Record an experience in the buffer.
        
        Args:
            trace: The experience trace to record
        """
        # Add the trace to the buffer
        self.experience_buffer.append(trace)
        
        # Trim the buffer if it exceeds the maximum size
        if len(self.experience_buffer) > self.experience_buffer_size:
            self.experience_buffer = self.experience_buffer[-self.experience_buffer_size:]
        
        logger.debug(f"Recorded experience at {trace.timestamp}")
    
    def learn_groundings_from_buffer(self, learning_focus_symbols: Optional[List[str]] = None) -> None:
        """
        Learn groundings from the experience buffer.
        
        Args:
            learning_focus_symbols: Optional list of symbol AST IDs to focus learning on
        """
        if not self.experience_buffer:
            logger.info("No experiences in buffer to learn from")
            return
        
        # Collect all active symbols if no focus symbols are provided
        if learning_focus_symbols is None:
            learning_focus_symbols = set()
            for trace in self.experience_buffer:
                for symbol in trace.active_symbols_in_kb:
                    if isinstance(symbol, ConstantNode):
                        learning_focus_symbols.add(symbol.name)
                    elif isinstance(symbol, ApplicationNode) and isinstance(symbol.operator, ConstantNode):
                        learning_focus_symbols.add(symbol.operator.name)
            learning_focus_symbols = list(learning_focus_symbols)
        
        logger.info(f"Learning groundings for {len(learning_focus_symbols)} symbols")
        
        # Process each focus symbol
        for symbol_ast_id in learning_focus_symbols:
            self._learn_grounding_for_symbol(symbol_ast_id)
        
        # Save the updated grounding links
        self._save_grounding_links()
    
    def _learn_grounding_for_symbol(self, symbol_ast_id: str) -> None:
        """
        Learn groundings for a specific symbol.
        
        Args:
            symbol_ast_id: The symbol AST ID to learn groundings for
        """
        # Collect relevant experiences for this symbol
        relevant_experiences = []
        for trace in self.experience_buffer:
            found = False
            for symbol in trace.active_symbols_in_kb:
                if isinstance(symbol, ConstantNode) and symbol.name == symbol_ast_id:
                    found = True
                elif isinstance(symbol, ApplicationNode) and isinstance(symbol.operator, ConstantNode):
                    if symbol.operator.name == symbol_ast_id:
                        found = True
                    else:
                        for arg in symbol.arguments:
                            if isinstance(arg, ConstantNode) and arg.name == symbol_ast_id:
                                found = True
                                break
                if found:
                    relevant_experiences.append(trace)
                    break
        
        if not relevant_experiences:
            logger.debug(f"No relevant experiences found for symbol {symbol_ast_id}")
            return
        
        # Learn groundings for different modalities
        self._learn_visual_feature_grounding(symbol_ast_id, relevant_experiences)
        self._learn_action_effect_grounding(symbol_ast_id, relevant_experiences)
    
    def _learn_visual_feature_grounding(self, symbol_ast_id: str, experiences: List[ExperienceTrace]) -> None:
        """
        Learn visual feature groundings for a symbol.
        
        Args:
            symbol_ast_id: The symbol AST ID to learn groundings for
            experiences: List of relevant experiences
        """
        # Collect visual features from objects associated with this symbol
        visual_features = []
        
        for trace in experiences:
            # Look for objects that have this symbol as a predicate
            # For example, if symbol is "Red", look for objects with HasColor(obj, Red)
            for symbol in trace.active_symbols_in_kb:
                if isinstance(symbol, ApplicationNode) and isinstance(symbol.operator, ConstantNode):
                    # Check if this is a predicate application with our symbol as an argument
                    for arg in symbol.arguments:
                        if isinstance(arg, ConstantNode) and arg.name == symbol_ast_id:
                            # Found a predicate with our symbol as an argument
                            # The first argument is typically the object ID
                            if len(symbol.arguments) > 0 and isinstance(symbol.arguments[0], ConstantNode):
                                obj_id = symbol.arguments[0].name
                                if obj_id in trace.extracted_features_by_object:
                                    visual_features.append(trace.extracted_features_by_object[obj_id])
                                    break
        
        if not visual_features:
            return
        
        # Learn a visual feature grounding using the prototype model
        model = self.grounding_models["visual_features"]
        sub_symbolic_representation = model.learn(symbol_ast_id, visual_features)
        
        # Create or update the grounding link
        self._update_grounding_link(
            symbol_ast_id=symbol_ast_id,
            sub_symbolic_representation=sub_symbolic_representation,
            modality="visual_features",
            confidence=0.7,  # Initial confidence
            update_count=len(visual_features)
        )
    
    def _learn_action_effect_grounding(self, symbol_ast_id: str, experiences: List[ExperienceTrace]) -> None:
        """
        Learn action effect groundings for a symbol.
        
        Args:
            symbol_ast_id: The symbol AST ID to learn groundings for
            experiences: List of relevant experiences
        """
        # Collect action effects
        action_effects = []
        
        for trace in experiences:
            # Check if this trace has an executed action
            if trace.executed_action_ast is None:
                continue
            
            # Check if the action is of the type we're learning about
            if isinstance(trace.executed_action_ast, ApplicationNode) and \
               isinstance(trace.executed_action_ast.operator, ConstantNode) and \
               trace.executed_action_ast.operator.name == symbol_ast_id:
                # This is an action of the type we're learning about
                # Collect the effect
                effect = {
                    "action_type": symbol_ast_id,
                    "effect": {}
                }
                
                # Add observed effects
                for effect_symbol in trace.observed_effect_symbols:
                    if isinstance(effect_symbol, ApplicationNode) and \
                       isinstance(effect_symbol.operator, ConstantNode):
                        effect["effect"][effect_symbol.operator.name] = True
                
                # Add observed sensor changes
                for sensor_id, sensor_data in trace.observed_effect_raw_sensors.items():
                    effect["effect"][f"sensor_{sensor_id}"] = sensor_data
                
                action_effects.append(effect)
        
        if not action_effects:
            return
        
        # Learn an action effect grounding using the action effect model
        model = self.grounding_models["action_effect"]
        sub_symbolic_representation = model.learn(symbol_ast_id, action_effects)
        
        # Create or update the grounding link
        self._update_grounding_link(
            symbol_ast_id=symbol_ast_id,
            sub_symbolic_representation=sub_symbolic_representation,
            modality="action_effect",
            confidence=0.7,  # Initial confidence
            update_count=len(action_effects)
        )
    
    def _update_grounding_link(self, symbol_ast_id: str, sub_symbolic_representation: Any,
                              modality: str, confidence: float, update_count: int) -> None:
        """
        Create or update a grounding link.
        
        Args:
            symbol_ast_id: The symbol AST ID
            sub_symbolic_representation: The sub-symbolic representation
            modality: The sensory modality
            confidence: Confidence in the grounding
            update_count: Number of examples used to learn/update the grounding
        """
        # Check if we already have a grounding link for this symbol and modality
        if symbol_ast_id in self.grounding_links:
            for i, link in enumerate(self.grounding_links[symbol_ast_id]):
                if link.modality == modality:
                    # Update existing link
                    new_confidence = (link.confidence * link.update_count + confidence * update_count) / \
                                     (link.update_count + update_count)
                    new_update_count = link.update_count + update_count
                    
                    # Update the sub-symbolic representation
                    model = self.grounding_models.get(modality)
                    if model:
                        updated_representation = model.update(
                            link.sub_symbolic_representation,
                            sub_symbolic_representation
                        )
                    else:
                        updated_representation = sub_symbolic_representation
                    
                    # Create updated link
                    self.grounding_links[symbol_ast_id][i] = GroundingLink(
                        symbol_ast_id=symbol_ast_id,
                        sub_symbolic_representation=updated_representation,
                        modality=modality,
                        confidence=new_confidence,
                        update_count=new_update_count,
                        last_updated=time.time()
                    )
                    return
        
        # Create new link
        new_link = GroundingLink(
            symbol_ast_id=symbol_ast_id,
            sub_symbolic_representation=sub_symbolic_representation,
            modality=modality,
            confidence=confidence,
            update_count=update_count,
            last_updated=time.time()
        )
        
        if symbol_ast_id not in self.grounding_links:
            self.grounding_links[symbol_ast_id] = []
        
        self.grounding_links[symbol_ast_id].append(new_link)
    
    def get_grounding_for_symbol(self, symbol_ast_id: str, modality_filter: Optional[str] = None) -> List[GroundingLink]:
        """
        Get groundings for a symbol.
        
        Args:
            symbol_ast_id: The symbol AST ID to get groundings for
            modality_filter: Optional filter for specific modality
            
        Returns:
            List of grounding links for the symbol
        """
        if symbol_ast_id not in self.grounding_links:
            return []
        
        links = self.grounding_links[symbol_ast_id]
        
        if modality_filter:
            links = [link for link in links if link.modality == modality_filter]
        
        return links
    
    def get_symbols_for_features(self, feature_vector: Dict[str, Any], modality: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Get symbols for a feature vector.
        
        Args:
            feature_vector: The feature vector to match
            modality: The sensory modality
            top_k: Maximum number of symbols to return
            
        Returns:
            List of (symbol_ast_id, confidence) tuples
        """
        if not feature_vector:
            return []
        
        # Get the appropriate grounding model
        model = self.grounding_models.get(modality)
        if not model:
            logger.warning(f"No grounding model available for modality: {modality}")
            return []
        
        # Compute confidence for each symbol
        confidences = []
        
        for symbol_ast_id, links in self.grounding_links.items():
            for link in links:
                if link.modality == modality:
                    # Compute confidence using the model
                    confidence = model.predict(link.sub_symbolic_representation, feature_vector)
                    
                    # Adjust by the link's own confidence
                    confidence *= link.confidence
                    
                    confidences.append((symbol_ast_id, confidence))
                    break
        
        # Sort by confidence and return top-k
        confidences.sort(key=lambda x: x[1], reverse=True)
        return confidences[:top_k]

    def measure_prediction_error_at_activation(
        self,
        symbol_ast_id: str,
        observed_features: Dict[str, Any],
        modality: str = "visual_features",
    ) -> Optional[GroundingPredictionError]:
        """
        Compare the stored prototype for *symbol_ast_id* against
        *observed_features* and return a ``GroundingPredictionError``.

        Returns ``None`` when no grounding link exists for the symbol/modality
        pair (cold-start case).
        """
        links = self.get_grounding_for_symbol(symbol_ast_id, modality_filter=modality)
        if not links:
            return None

        prototype = links[0].sub_symbolic_representation
        if not isinstance(prototype, dict):
            return None

        # Extract only numeric features from the prototype for prediction
        predicted: Dict[str, float] = {
            k: float(v) for k, v in prototype.items()
            if isinstance(v, (int, float))
        }
        observed_numeric: Dict[str, float] = {
            k: float(v) for k, v in observed_features.items()
            if isinstance(v, (int, float))
        }

        feature_errors, error_norm = PrototypeModel.compute_prediction_error(
            predicted, observed_numeric
        )
        return GroundingPredictionError(
            symbol_ast_id=symbol_ast_id,
            modality=modality,
            predicted_features=predicted,
            observed_features=observed_numeric,
            feature_errors=feature_errors,
            error_norm=error_norm,
        )
