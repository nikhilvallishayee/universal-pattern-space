"""
Perceptual Categorizer (PC) for GödelOS.

This module implements the PerceptualCategorizer component (Module 4.2) of the Symbol Grounding System,
which is responsible for converting raw sensory data from SimulatedEnvironment into low-level symbolic
predicates (perceptual schemas) and asserting them into a dedicated "PerceptualContext" in the KR System.

The PerceptualCategorizer performs:
1. Basic feature extraction from raw sensor data if not already provided by SimEnv
2. Segmentation of the perceptual field into discrete objects or regions of interest
3. Assignment of symbolic labels (predicates) to these segments based on their features
4. Assertion of symbolic perceptual facts into the KR System
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import math

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode

# Define our own classes to avoid import issues
class RawSensorData:
    """
    Represents raw data from a sensor in the simulated environment.
    
    Attributes:
        modality: The sensory modality (e.g., "vision", "touch", "audio", "proprioception")
        data: The actual sensor data, which could be a pixel buffer, feature list, contact list, etc.
    """
    def __init__(self, modality="", data=None):
        self.modality = modality
        self.data = data or {}

class SimObject:
    """
    Represents an object in the simulated environment.
    
    Attributes:
        object_id: Unique identifier for the object
        object_type: Type of the object
        pose: Pose of the object in the world
        visual_features: Visual features of the object (e.g., color, shape)
        physical_properties: Physical properties of the object (e.g., mass, friction)
    """
    def __init__(self, object_id="", object_type="", pose=None, visual_features=None, physical_properties=None):
        self.object_id = object_id
        self.object_type = object_type
        self.pose = pose
        self.visual_features = visual_features or {}
        self.physical_properties = physical_properties or {}

logger = logging.getLogger(__name__)

# Type aliases for clarity
FeatureVector = Dict[str, Any]
PerceptualFact = AST_Node  # Typically an ApplicationNode representing a predicate


class FeatureExtractor:
    """
    Base class for feature extractors that process raw sensor data to extract features.
    
    Feature extractors convert raw sensor data into feature vectors that can be used
    by the perceptual categorizer to generate symbolic predicates.
    """
    
    def __init__(self, name: str, modality: str):
        """
        Initialize a feature extractor.
        
        Args:
            name: Name of the feature extractor
            modality: Sensory modality this extractor works with (e.g., "vision", "touch")
        """
        self.name = name
        self.modality = modality
    
    def extract(self, raw_data: Any) -> FeatureVector:
        """
        Extract features from raw sensor data.
        
        Args:
            raw_data: Raw sensor data to extract features from
            
        Returns:
            A feature vector (dictionary mapping feature names to values)
        """
        raise NotImplementedError("Subclasses must implement extract()")


class ColorExtractor(FeatureExtractor):
    """Feature extractor for color information from vision data."""
    
    def __init__(self):
        """Initialize a color extractor."""
        super().__init__("color_extractor", "vision")
    
    def extract(self, raw_data: Any) -> FeatureVector:
        """
        Extract color features from vision data.
        
        Args:
            raw_data: Raw vision data, expected to be a feature list with visual_features
            
        Returns:
            Feature vector with color information
        """
        features = {}
        
        # If the data already contains color information, use it directly
        if isinstance(raw_data, dict) and "visual_features" in raw_data:
            if "color" in raw_data["visual_features"]:
                features["color"] = raw_data["visual_features"]["color"]
        
        return features


class ShapeExtractor(FeatureExtractor):
    """Feature extractor for shape information from vision data."""
    
    def __init__(self):
        """Initialize a shape extractor."""
        super().__init__("shape_extractor", "vision")
    
    def extract(self, raw_data: Any) -> FeatureVector:
        """
        Extract shape features from vision data.
        
        Args:
            raw_data: Raw vision data, expected to be a feature list with visual_features
            
        Returns:
            Feature vector with shape information
        """
        features = {}
        
        # If the data already contains shape information, use it directly
        if isinstance(raw_data, dict) and "visual_features" in raw_data:
            if "shape" in raw_data["visual_features"]:
                features["shape"] = raw_data["visual_features"]["shape"]
        
        return features


class SpatialRelationExtractor(FeatureExtractor):
    """Feature extractor for spatial relations between objects."""
    
    def __init__(self):
        """Initialize a spatial relation extractor."""
        super().__init__("spatial_relation_extractor", "vision")
        self.proximity_threshold = 3.0  # Objects closer than this are considered "near"
    
    def extract(self, raw_data: Any) -> FeatureVector:
        """
        This extractor doesn't work on individual objects but on pairs of objects.
        It will be used differently by the PerceptualCategorizer.
        """
        return {}
    
    def extract_relation(self, obj1_data: Dict[str, Any], obj2_data: Dict[str, Any]) -> FeatureVector:
        """
        Extract spatial relation features between two objects.
        
        Args:
            obj1_data: Data for the first object
            obj2_data: Data for the second object
            
        Returns:
            Feature vector with spatial relation information
        """
        features = {}
        
        # Calculate distance between objects
        if "distance" in obj1_data and "angle" in obj1_data and "distance" in obj2_data and "angle" in obj2_data:
            # Convert polar to Cartesian coordinates (simplified)
            x1 = obj1_data["distance"] * math.cos(math.radians(obj1_data["angle"]))
            y1 = obj1_data["distance"] * math.sin(math.radians(obj1_data["angle"]))
            
            x2 = obj2_data["distance"] * math.cos(math.radians(obj2_data["angle"]))
            y2 = obj2_data["distance"] * math.sin(math.radians(obj2_data["angle"]))
            
            # Calculate Euclidean distance
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            features["distance"] = distance
            
            # Determine if objects are near each other
            features["is_near"] = distance < self.proximity_threshold
            
            # Determine relative position (simplified)
            features["relative_position"] = "left" if x2 < x1 else "right"
        
        return features


class TouchFeatureExtractor(FeatureExtractor):
    """Feature extractor for touch information."""
    
    def __init__(self):
        """Initialize a touch feature extractor."""
        super().__init__("touch_extractor", "touch")
    
    def extract(self, raw_data: Any) -> FeatureVector:
        """
        Extract touch features from touch data.
        
        Args:
            raw_data: Raw touch data, expected to be a dictionary with contact information
            
        Returns:
            Feature vector with touch information
        """
        features = {}
        
        if isinstance(raw_data, dict):
            if "force" in raw_data:
                features["touch_force"] = raw_data["force"]
                features["is_touching"] = raw_data["force"] > 0.1  # Threshold for touch detection
            
            if "physical_properties" in raw_data:
                props = raw_data["physical_properties"]
                if "texture" in props:
                    features["texture"] = props["texture"]
                if "temperature" in props:
                    features["temperature"] = props["temperature"]
        
        return features


class FeatureMatcher:
    """
    Class for matching feature vectors against conditions.
    
    Feature matchers define conditions that feature vectors must satisfy
    to trigger the generation of specific symbolic predicates.
    """
    
    def __init__(self, feature_name: str, match_function: Callable[[Any], bool], description: str = ""):
        """
        Initialize a feature matcher.
        
        Args:
            feature_name: Name of the feature to match
            match_function: Function that takes a feature value and returns True if it matches
            description: Optional description of the matcher
        """
        self.feature_name = feature_name
        self.match_function = match_function
        self.description = description
    
    def matches(self, feature_vector: FeatureVector) -> bool:
        """
        Check if the feature vector matches the condition.
        
        Args:
            feature_vector: Feature vector to check
            
        Returns:
            True if the feature vector matches the condition, False otherwise
        """
        if self.feature_name not in feature_vector:
            return False
        
        return self.match_function(feature_vector[self.feature_name])


class PerceptualCategorizationRule:
    """
    Rule for mapping feature vectors to symbolic predicates.
    
    Each rule defines a set of conditions (feature matchers) that must be satisfied
    for the rule to fire, and a template for the symbolic predicate to generate.
    """
    
    def __init__(self, name: str, conditions: List[FeatureMatcher], 
                 predicate_template: Callable[[str, Dict[str, Any]], AST_Node]):
        """
        Initialize a perceptual categorization rule.
        
        Args:
            name: Name of the rule
            conditions: List of feature matchers that must all be satisfied for the rule to fire
            predicate_template: Function that takes an object ID and feature vector and returns an AST node
        """
        self.name = name
        self.conditions = conditions
        self.predicate_template = predicate_template
    
    def applies(self, feature_vector: FeatureVector) -> bool:
        """
        Check if the rule applies to the given feature vector.
        
        Args:
            feature_vector: Feature vector to check
            
        Returns:
            True if all conditions are satisfied, False otherwise
        """
        return all(condition.matches(feature_vector) for condition in self.conditions)
    
    def generate_predicate(self, object_id: str, feature_vector: FeatureVector) -> AST_Node:
        """
        Generate a symbolic predicate for the given object and feature vector.
        
        Args:
            object_id: ID of the object
            feature_vector: Feature vector for the object
            
        Returns:
            AST node representing the symbolic predicate
        """
        return self.predicate_template(object_id, feature_vector)


class ObjectTracker:
    """
    System for maintaining identity of perceived objects across time.
    
    The object tracker uses simple heuristics (proximity, feature similarity)
    to match objects between consecutive perceptual frames.
    """
    
    def __init__(self):
        """Initialize the object tracker."""
        self.tracked_objects = {}  # Maps tracked_id -> {object_data, last_seen_time}
        self.current_time = 0
        self.max_age = 10  # Maximum number of time steps to track an object without seeing it
        self.distance_threshold = 2.0  # Maximum distance for considering an object the same
        self.feature_similarity_threshold = 0.7  # Minimum similarity for considering an object the same
    
    def update(self, current_objects: Dict[str, Dict[str, Any]], time_step: float) -> Dict[str, str]:
        """
        Update object tracking with new perceptual data.
        
        Args:
            current_objects: Dictionary mapping object IDs to object data
            time_step: Current time step
            
        Returns:
            Dictionary mapping original object IDs to tracked IDs
        """
        self.current_time += time_step
        
        # Remove old tracked objects before matching
        self._prune_old_objects()
        
        # Maps original object IDs to tracked IDs
        id_mapping = {}
        
        # For each current object, find the best match in tracked objects
        for obj_id, obj_data in current_objects.items():
            best_match_id = None
            best_match_score = 0
            
            for tracked_id, tracked_info in self.tracked_objects.items():
                tracked_data = tracked_info["object_data"]
                
                # Calculate position-based similarity
                pos_similarity = self._calculate_position_similarity(obj_data, tracked_data)
                
                # Calculate feature-based similarity
                feature_similarity = self._calculate_feature_similarity(obj_data, tracked_data)
                
                # Combined score
                score = 0.7 * pos_similarity + 0.3 * feature_similarity
                
                if score > best_match_score and score > 0.5:
                    best_match_score = score
                    best_match_id = tracked_id
            
            if best_match_id:
                # Update existing tracked object
                self.tracked_objects[best_match_id] = {
                    "object_data": obj_data,
                    "last_seen_time": self.current_time
                }
                id_mapping[obj_id] = best_match_id
            else:
                # Create new tracked object
                tracked_id = f"tracked_{uuid.uuid4()}"
                self.tracked_objects[tracked_id] = {
                    "object_data": obj_data,
                    "last_seen_time": self.current_time
                }
                id_mapping[obj_id] = tracked_id
        
        return id_mapping
    
    def _calculate_position_similarity(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> float:
        """
        Calculate similarity based on position.
        
        Args:
            obj1: First object data
            obj2: Second object data
            
        Returns:
            Similarity score between 0 and 1
        """
        # If we have distance and angle, use them to calculate position
        if "distance" in obj1 and "angle" in obj1 and "distance" in obj2 and "angle" in obj2:
            # Convert polar to Cartesian coordinates (simplified)
            x1 = obj1["distance"] * math.cos(math.radians(obj1["angle"]))
            y1 = obj1["distance"] * math.sin(math.radians(obj1["angle"]))
            
            x2 = obj2["distance"] * math.cos(math.radians(obj2["angle"]))
            y2 = obj2["distance"] * math.sin(math.radians(obj2["angle"]))
            
            # Calculate Euclidean distance
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            
            # Convert distance to similarity score (1 when distance is 0, 0 when distance >= threshold)
            similarity = max(0, 1 - distance / self.distance_threshold)
            return similarity
        
        return 0
    
    def _calculate_feature_similarity(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> float:
        """
        Calculate similarity based on features.
        
        Args:
            obj1: First object data
            obj2: Second object data
            
        Returns:
            Similarity score between 0 and 1
        """
        # Check if objects have the same type
        if "object_type" in obj1 and "object_type" in obj2:
            if obj1["object_type"] != obj2["object_type"]:
                return 0
        
        # Check visual features
        if "visual_features" in obj1 and "visual_features" in obj2:
            vf1 = obj1["visual_features"]
            vf2 = obj2["visual_features"]
            
            # Count matching features
            matches = 0
            total = 0
            
            for key in set(vf1.keys()) & set(vf2.keys()):
                total += 1
                if vf1[key] == vf2[key]:
                    matches += 1
            
            if total > 0:
                return matches / total
        
        return 0.5  # Default similarity if no features to compare
    
    def _prune_old_objects(self):
        """Remove tracked objects that haven't been seen recently."""
        to_remove = []
        
        for tracked_id, tracked_info in self.tracked_objects.items():
            age = self.current_time - tracked_info["last_seen_time"]
            if age > self.max_age:
                to_remove.append(tracked_id)
        
        for tracked_id in to_remove:
            del self.tracked_objects[tracked_id]


class PerceptualCategorizer:
    """
    Perceptual Categorizer (PC) for GödelOS.
    
    The PerceptualCategorizer converts raw sensory data from SimulatedEnvironment
    into low-level symbolic predicates and asserts them into the KR System.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface, 
                 type_system: TypeSystemManager, 
                 feature_extractors_config: Optional[Dict[str, List[str]]] = None,
                 categorization_rules_path: Optional[str] = None):
        """
        Initialize the perceptual categorizer.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation System
            type_system: Type system manager
            feature_extractors_config: Optional configuration for feature extractors
            categorization_rules_path: Optional path to categorization rules configuration
        """
        self.kr_interface = kr_system_interface
        self.type_system = type_system
        self.object_tracker = ObjectTracker()
        
        # Create perceptual context if it doesn't exist
        if "PERCEPTUAL_CONTEXT" not in kr_system_interface.list_contexts():
            kr_system_interface.create_context("PERCEPTUAL_CONTEXT", None, "perceptual")
        
        # Initialize feature extractors
        self.feature_extractors = self._init_feature_extractors(feature_extractors_config)
        
        # Initialize categorization rules
        self.categorization_rules = self._init_categorization_rules()
        
        # Cache for object feature vectors
        self.object_feature_cache = {}
    
    def _init_feature_extractors(self, config: Optional[Dict[str, List[str]]]) -> Dict[str, List[FeatureExtractor]]:
        """
        Initialize feature extractors based on configuration.
        
        Args:
            config: Optional configuration for feature extractors
            
        Returns:
            Dictionary mapping modalities to lists of feature extractors
        """
        extractors = {
            "vision": [ColorExtractor(), ShapeExtractor(), SpatialRelationExtractor()],
            "touch": [TouchFeatureExtractor()]
        }
        
        # TODO: Use config to customize extractors if provided
        
        return extractors
    
    def _init_categorization_rules(self) -> List[PerceptualCategorizationRule]:
        """
        Initialize perceptual categorization rules.
        
        Returns:
            List of perceptual categorization rules
        """
        # Get necessary types from type system
        entity_type = self.type_system.get_type("Entity") or self.type_system.get_type("Object")
        bool_type = self.type_system.get_type("Boolean")
        prop_type = self.type_system.get_type("Proposition")
        
        # Create rules for color predicates
        color_rule = PerceptualCategorizationRule(
            name="color_rule",
            conditions=[
                FeatureMatcher("color", lambda color: isinstance(color, str), "Color is a string")
            ],
            predicate_template=lambda obj_id, features: ApplicationNode(
                operator=ConstantNode("HasColor", prop_type),
                arguments=[
                    ConstantNode(obj_id, entity_type),
                    ConstantNode(features["color"], entity_type)
                ],
                type_ref=prop_type
            )
        )
        
        # Create rules for shape predicates
        shape_rule = PerceptualCategorizationRule(
            name="shape_rule",
            conditions=[
                FeatureMatcher("shape", lambda shape: isinstance(shape, str), "Shape is a string")
            ],
            predicate_template=lambda obj_id, features: ApplicationNode(
                operator=ConstantNode("HasShape", prop_type),
                arguments=[
                    ConstantNode(obj_id, entity_type),
                    ConstantNode(features["shape"], entity_type)
                ],
                type_ref=prop_type
            )
        )
        
        # Create rules for spatial relation predicates
        near_rule = PerceptualCategorizationRule(
            name="near_rule",
            conditions=[
                FeatureMatcher("is_near", lambda is_near: is_near, "Objects are near each other")
            ],
            predicate_template=lambda obj_pair_id, features: ApplicationNode(
                operator=ConstantNode("Near", prop_type),
                arguments=[
                    ConstantNode(obj_pair_id.split("_and_")[0], entity_type),
                    ConstantNode(obj_pair_id.split("_and_")[1], entity_type)
                ],
                type_ref=prop_type
            )
        )
        
        # Create rules for touch predicates
        touch_rule = PerceptualCategorizationRule(
            name="touch_rule",
            conditions=[
                FeatureMatcher("is_touching", lambda is_touching: is_touching, "Object is being touched")
            ],
            predicate_template=lambda obj_id, features: ApplicationNode(
                operator=ConstantNode("IsTouched", prop_type),
                arguments=[
                    ConstantNode(obj_id, entity_type)
                ],
                type_ref=prop_type
            )
        )
        
        return [color_rule, shape_rule, near_rule, touch_rule]
    
    def process_perceptual_input(self, agent_id: str, all_sensor_data: Dict[str, RawSensorData]) -> Set[AST_Node]:
        """
        Process perceptual input from sensors and generate symbolic predicates.
        
        Args:
            agent_id: ID of the agent
            all_sensor_data: Dictionary mapping sensor IDs to raw sensor data
            
        Returns:
            Set of AST nodes representing symbolic perceptual facts
        """
        perceptual_facts = set()
        object_features = {}
        
        # Process each sensor's data
        for sensor_id, sensor_data in all_sensor_data.items():
            modality = sensor_data.modality
            
            # Skip if we don't have extractors for this modality
            if modality not in self.feature_extractors:
                continue
            
            # Extract features based on modality
            if modality == "vision":
                # Vision data is expected to be a list of object features
                if isinstance(sensor_data.data, list):
                    for obj_data in sensor_data.data:
                        if not isinstance(obj_data, dict):
                            continue
                        obj_id = obj_data.get("object_id")
                        if not obj_id:
                            continue
                        
                        # Extract features for this object
                        features = self._extract_object_features(modality, obj_data)
                        
                        # Store original object data and extracted features for tracking
                        object_features[obj_id] = {**obj_data, **features}
            
            elif modality == "touch":
                # Touch data is expected to be a list of contact information
                if isinstance(sensor_data.data, list):
                    for contact_data in sensor_data.data:
                        if not isinstance(contact_data, dict):
                            continue
                        obj_id = contact_data.get("object_id")
                        if not obj_id:
                            continue
                        
                        # Extract features for this contact
                        features = self._extract_object_features(modality, contact_data)
                        
                        # Merge with existing features for this object
                        if obj_id in object_features:
                            object_features[obj_id].update(features)
                        else:
                            object_features[obj_id] = {**contact_data, **features}
        
        # Track objects across time
        tracked_id_mapping = self.object_tracker.update(
            {obj_id: {"object_id": obj_id, **features} for obj_id, features in object_features.items()},
            1.0  # Assuming time step of 1.0
        )
        
        # Update object IDs to tracked IDs
        tracked_features = {}
        for obj_id, features in object_features.items():
            tracked_id = tracked_id_mapping.get(obj_id, obj_id)
            tracked_features[tracked_id] = features
        
        # Apply categorization rules to generate predicates
        for obj_id, features in tracked_features.items():
            # Apply single-object rules
            for rule in self.categorization_rules:
                if rule.name not in ["near_rule"]:  # Skip relation rules
                    if rule.applies(features):
                        predicate = rule.generate_predicate(obj_id, features)
                        perceptual_facts.add(predicate)
        
        # Apply spatial relation rules
        spatial_extractor = next((e for e in self.feature_extractors.get("vision", []) 
                                if isinstance(e, SpatialRelationExtractor)), None)
        
        if spatial_extractor:
            # Generate all pairs of objects
            obj_ids = list(tracked_features.keys())
            for i in range(len(obj_ids)):
                for j in range(i + 1, len(obj_ids)):
                    obj1_id = obj_ids[i]
                    obj2_id = obj_ids[j]
                    
                    # Extract relation features
                    relation_features = spatial_extractor.extract_relation(
                        tracked_features[obj1_id], tracked_features[obj2_id]
                    )
                    
                    # Apply relation rules
                    for rule in self.categorization_rules:
                        if rule.name == "near_rule":
                            if rule.applies(relation_features):
                                # Create a composite ID for the object pair
                                pair_id = f"{obj1_id}_and_{obj2_id}"
                                predicate = rule.generate_predicate(pair_id, relation_features)
                                perceptual_facts.add(predicate)
        
        # Assert perceptual facts to the KR system
        for fact in perceptual_facts:
            self.kr_interface.add_statement(fact, "PERCEPTUAL_CONTEXT")
        
        return perceptual_facts
    
    def _extract_object_features(self, modality: str, obj_data: Dict[str, Any]) -> FeatureVector:
        """
        Extract features for an object using all relevant extractors.
        
        Args:
            modality: Sensory modality
            obj_data: Object data from sensor
            
        Returns:
            Feature vector for the object
        """
        features = {}
        
        # Apply all extractors for this modality
        for extractor in self.feature_extractors.get(modality, []):
            if not isinstance(extractor, SpatialRelationExtractor):  # Skip relation extractors
                extracted = extractor.extract(obj_data)
                features.update(extracted)
        
        return features