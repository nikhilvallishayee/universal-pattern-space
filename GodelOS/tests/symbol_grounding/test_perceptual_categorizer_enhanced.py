"""
Enhanced unit tests for the PerceptualCategorizer component.

This file extends the basic tests in test_perceptual_categorizer.py with more thorough
testing of complex methods and edge cases, as identified in the test plan.
"""

import unittest
from unittest.mock import MagicMock, patch
import math
import copy

from godelOS.symbol_grounding.perceptual_categorizer import (
    PerceptualCategorizer,
    FeatureExtractor,
    ColorExtractor,
    ShapeExtractor,
    SpatialRelationExtractor,
    TouchFeatureExtractor,
    FeatureMatcher,
    PerceptualCategorizationRule,
    ObjectTracker
)

# Mock classes from simulated_environment_new to avoid import errors
class MockPose:
    def __init__(self, x=0.0, y=0.0, z=0.0, orientation=(1.0, 0.0, 0.0, 0.0)):
        self.x = x
        self.y = y
        self.z = z
        self.orientation = orientation
    
    def distance_to(self, other):
        return ((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)**0.5

class MockRawSensorData:
    def __init__(self, modality="", data=None):
        self.modality = modality
        self.data = data or {}

class MockSimObject:
    def __init__(self, object_id="", object_type="", pose=None, visual_features=None, physical_properties=None):
        self.object_id = object_id
        self.object_type = object_type
        self.pose = pose or MockPose()
        self.visual_features = visual_features or {}
        self.physical_properties = physical_properties or {}

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode


class TestObjectTrackerEnhanced(unittest.TestCase):
    """Enhanced tests for the ObjectTracker class focusing on complex scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ObjectTracker()
        
        # Create some test objects
        self.obj1 = {
            "object_id": "obj1",
            "object_type": "box",
            "distance": 2.0,
            "angle": 0.0,
            "visual_features": {"color": "red", "shape": "cube"}
        }
        
        self.obj2 = {
            "object_id": "obj2",
            "object_type": "sphere",
            "distance": 5.0,
            "angle": 90.0,
            "visual_features": {"color": "blue", "shape": "sphere"}
        }
    
    def test_position_similarity_calculation(self):
        """Test the position similarity calculation method."""
        # Test with identical positions
        obj1 = {"distance": 2.0, "angle": 0.0}
        obj2 = {"distance": 2.0, "angle": 0.0}
        similarity = self.tracker._calculate_position_similarity(obj1, obj2)
        self.assertEqual(similarity, 1.0, "Identical positions should have similarity 1.0")
        
        # Test with positions at distance threshold
        obj1 = {"distance": 0.0, "angle": 0.0}  # At origin
        obj2 = {"distance": self.tracker.distance_threshold, "angle": 0.0}  # At threshold distance
        similarity = self.tracker._calculate_position_similarity(obj1, obj2)
        self.assertAlmostEqual(similarity, 0.0, places=5, 
                              msg="Positions at distance threshold should have similarity 0.0")
        
        # Test with positions beyond distance threshold
        obj1 = {"distance": 0.0, "angle": 0.0}  # At origin
        obj2 = {"distance": self.tracker.distance_threshold * 2, "angle": 0.0}  # Beyond threshold
        similarity = self.tracker._calculate_position_similarity(obj1, obj2)
        self.assertEqual(similarity, 0.0, "Positions beyond threshold should have similarity 0.0")
        
        # Test with positions at half distance threshold
        obj1 = {"distance": 0.0, "angle": 0.0}  # At origin
        obj2 = {"distance": self.tracker.distance_threshold / 2, "angle": 0.0}  # At half threshold
        similarity = self.tracker._calculate_position_similarity(obj1, obj2)
        self.assertAlmostEqual(similarity, 0.5, places=5, 
                              msg="Positions at half threshold should have similarity 0.5")
    
    def test_feature_similarity_calculation(self):
        """Test the feature similarity calculation method."""
        # Test with identical features
        obj1 = {
            "object_type": "box",
            "visual_features": {"color": "red", "shape": "cube", "size": "large"}
        }
        obj2 = copy.deepcopy(obj1)
        similarity = self.tracker._calculate_feature_similarity(obj1, obj2)
        self.assertEqual(similarity, 1.0, "Identical features should have similarity 1.0")
        
        # Test with completely different features
        obj1 = {
            "object_type": "box",
            "visual_features": {"color": "red", "shape": "cube"}
        }
        obj2 = {
            "object_type": "sphere",
            "visual_features": {"color": "blue", "shape": "sphere"}
        }
        similarity = self.tracker._calculate_feature_similarity(obj1, obj2)
        self.assertEqual(similarity, 0.0, "Different object types should have similarity 0.0")
        
        # Test with partially matching features
        obj1 = {
            "object_type": "box",
            "visual_features": {"color": "red", "shape": "cube", "size": "large"}
        }
        obj2 = {
            "object_type": "box",
            "visual_features": {"color": "red", "shape": "pyramid", "texture": "smooth"}
        }
        # 2 out of 4 unique features match (color and object_type)
        similarity = self.tracker._calculate_feature_similarity(obj1, obj2)
        self.assertAlmostEqual(similarity, 0.5, places=5, 
                              msg="Partially matching features should have proportional similarity")
        
        # Test with no features to compare
        obj1 = {"object_type": "box"}
        obj2 = {"object_type": "box"}
        similarity = self.tracker._calculate_feature_similarity(obj1, obj2)
        self.assertEqual(similarity, 0.5, "Default similarity should be used when no features to compare")
    
    def test_update_with_ambiguous_objects(self):
        """Test updating with ambiguous objects (similar but not identical)."""
        # First update to establish tracking
        first_mapping = self.tracker.update(
            {"obj1": self.obj1, "obj2": self.obj2},
            1.0
        )
        
        # Create a new object that's similar to obj1 but not identical
        similar_obj = dict(self.obj1)
        similar_obj["object_id"] = "similar_obj"
        similar_obj["distance"] = 2.5  # Slightly different position
        similar_obj["visual_features"] = {"color": "red", "shape": "cube", "size": "medium"}  # Added a feature
        
        # Second update with original obj2 and the similar object
        second_mapping = self.tracker.update(
            {"similar_obj": similar_obj, "obj2": self.obj2},
            1.0
        )
        
        # Check that the similar object was matched to obj1's tracked ID
        self.assertEqual(first_mapping["obj1"], second_mapping["similar_obj"], 
                        "Similar object should be tracked as the same object")
        
        # Check that obj2 keeps its tracked ID
        self.assertEqual(first_mapping["obj2"], second_mapping["obj2"], 
                        "Unrelated object should maintain its tracked ID")
    
    def test_update_with_multiple_similar_objects(self):
        """Test updating with multiple similar objects to ensure correct disambiguation."""
        # Create three similar red cubes at different positions
        red_cube1 = {
            "object_id": "red_cube1",
            "object_type": "box",
            "distance": 2.0,
            "angle": 0.0,
            "visual_features": {"color": "red", "shape": "cube"}
        }
        
        red_cube2 = {
            "object_id": "red_cube2",
            "object_type": "box",
            "distance": 3.0,
            "angle": 30.0,
            "visual_features": {"color": "red", "shape": "cube"}
        }
        
        red_cube3 = {
            "object_id": "red_cube3",
            "object_type": "box",
            "distance": 4.0,
            "angle": 60.0,
            "visual_features": {"color": "red", "shape": "cube"}
        }
        
        # First update to establish tracking
        first_mapping = self.tracker.update(
            {"red_cube1": red_cube1, "red_cube2": red_cube2, "red_cube3": red_cube3},
            1.0
        )
        
        # Slightly move each cube
        moved_cube1 = dict(red_cube1)
        moved_cube1["distance"] = 2.2
        
        moved_cube2 = dict(red_cube2)
        moved_cube2["distance"] = 3.2
        
        moved_cube3 = dict(red_cube3)
        moved_cube3["distance"] = 4.2
        
        # Second update with moved cubes
        second_mapping = self.tracker.update(
            {"moved_cube1": moved_cube1, "moved_cube2": moved_cube2, "moved_cube3": moved_cube3},
            1.0
        )
        
        # Check that each cube was matched to its corresponding tracked ID
        tracked_ids = set(first_mapping.values())
        new_tracked_ids = set(second_mapping.values())
        
        # All three original tracked IDs should be reused
        self.assertEqual(tracked_ids, new_tracked_ids, 
                        "All three similar objects should maintain their distinct tracked IDs")
        
        # The specific mapping is harder to test without knowing the exact implementation details,
        # but we can check that we have three distinct tracked IDs
        self.assertEqual(len(new_tracked_ids), 3, 
                        "Should have three distinct tracked IDs for three similar objects")
    
    def test_object_disappearance_and_reappearance(self):
        """Test tracking when objects disappear and then reappear."""
        # First update to establish tracking
        first_mapping = self.tracker.update(
            {"obj1": self.obj1, "obj2": self.obj2},
            1.0
        )
        
        obj1_tracked_id = first_mapping["obj1"]
        
        # Second update with only obj2
        self.tracker.update(
            {"obj2": self.obj2},
            1.0
        )
        
        # Check that obj1 is still being tracked (but not seen recently)
        self.assertIn(obj1_tracked_id, self.tracker.tracked_objects, 
                     "Object should still be tracked after disappearing for one frame")
        
        # Third update with obj1 reappearing
        third_mapping = self.tracker.update(
            {"obj1": self.obj1},
            1.0
        )
        
        # Check that obj1 was matched to its original tracked ID
        self.assertEqual(obj1_tracked_id, third_mapping["obj1"], 
                        "Reappearing object should be matched to its original tracked ID")
        
        # Now test with a longer disappearance that exceeds max_age
        # Advance time significantly
        self.tracker.current_time += self.tracker.max_age + 1
        
        # Update with only obj1
        fourth_mapping = self.tracker.update(
            {"obj1": self.obj1},
            1.0
        )
        
        # Check that obj1 got a new tracked ID
        self.assertNotEqual(obj1_tracked_id, fourth_mapping["obj1"], 
                           "Object reappearing after max_age should get a new tracked ID")


class TestPerceptualCategorizerEnhanced(unittest.TestCase):
    """Enhanced tests for the PerceptualCategorizer class focusing on complex scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock KR interface and type system
        self.kr_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.kr_interface.list_contexts.return_value = []
        
        self.type_system = MagicMock(spec=TypeSystemManager)
        self.entity_type = MagicMock()
        self.bool_type = MagicMock()
        self.prop_type = MagicMock()
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Object": self.entity_type,
            "Boolean": self.bool_type,
            "Proposition": self.prop_type
        }.get(name)
        
        # Create the perceptual categorizer
        self.pc = PerceptualCategorizer(self.kr_interface, self.type_system)
    
    def test_process_perceptual_input_with_missing_features(self):
        """Test processing input with missing features."""
        # Create mock vision data with incomplete features
        vision_data = MockRawSensorData(
            modality="vision",
            data=[
                {
                    "object_id": "obj1",
                    "object_type": "box",
                    "distance": 2.0,
                    "angle": 0.0,
                    "visual_features": {"color": "red"}  # Missing shape
                },
                {
                    "object_id": "obj2",
                    "object_type": "unknown",
                    "distance": 5.0,
                    "angle": 90.0,
                    "visual_features": {"shape": "sphere"}  # Missing color
                }
            ]
        )
        
        # Process the vision data
        facts = self.pc.process_perceptual_input(
            "agent1",
            {"vision_sensor": vision_data}
        )
        
        # Check that facts were generated for the available features
        has_color_fact = False
        has_shape_fact = False
        
        for fact in facts:
            if isinstance(fact, ApplicationNode) and isinstance(fact.operator, ConstantNode):
                if fact.operator.name == "HasColor":
                    has_color_fact = True
                elif fact.operator.name == "HasShape":
                    has_shape_fact = True
        
        self.assertTrue(has_color_fact, "Should generate color facts for objects with color")
        self.assertTrue(has_shape_fact, "Should generate shape facts for objects with shape")
        
        # Verify the correct number of facts were added to the KR system
        # We expect at least 2 facts (one for color, one for shape)
        self.assertGreaterEqual(self.kr_interface.add_statement.call_count, 2)
    
    def test_process_perceptual_input_with_noisy_data(self):
        """Test processing input with noisy or invalid data."""
        # Create mock vision data with some invalid entries
        vision_data = MockRawSensorData(
            modality="vision",
            data=[
                {
                    "object_id": "obj1",
                    "object_type": "box",
                    "distance": 2.0,
                    "angle": 0.0,
                    "visual_features": {"color": "red", "shape": "cube"}
                },
                {
                    # Missing object_id
                    "object_type": "sphere",
                    "distance": 5.0,
                    "angle": 90.0,
                    "visual_features": {"color": "blue", "shape": "sphere"}
                },
                {
                    "object_id": "obj3",
                    # Missing distance/angle
                    "object_type": "cylinder",
                    "visual_features": {"color": "green", "shape": "cylinder"}
                },
                "not_a_dict"  # Completely invalid data
            ]
        )
        
        # Process the vision data
        facts = self.pc.process_perceptual_input(
            "agent1",
            {"vision_sensor": vision_data}
        )
        
        # Check that facts were generated for the valid object
        self.assertGreater(len(facts), 0, "Should generate facts for valid objects despite noise")
        
        # Check that the system didn't crash with invalid data
        # This is implicitly tested by reaching this point without exceptions
    
    def test_process_perceptual_input_with_ambiguous_features(self):
        """Test processing input with ambiguous features (e.g., colors that are similar)."""
        # Create a custom color extractor that can handle ambiguous colors
        class AmbiguousColorExtractor(ColorExtractor):
            def extract(self, raw_data):
                features = super().extract(raw_data)
                
                # Add confidence scores for ambiguous colors
                if "color" in features:
                    if features["color"] == "reddish-orange":
                        features["color_confidence"] = 0.7
                        features["color_alternatives"] = {"red": 0.6, "orange": 0.4}
                
                return features
        
        # Replace the color extractor in the perceptual categorizer
        for i, extractor in enumerate(self.pc.feature_extractors["vision"]):
            if isinstance(extractor, ColorExtractor):
                self.pc.feature_extractors["vision"][i] = AmbiguousColorExtractor()
        
        # Create mock vision data with ambiguous colors
        vision_data = MockRawSensorData(
            modality="vision",
            data=[
                {
                    "object_id": "obj1",
                    "object_type": "box",
                    "distance": 2.0,
                    "angle": 0.0,
                    "visual_features": {"color": "reddish-orange", "shape": "cube"}
                }
            ]
        )
        
        # Process the vision data
        facts = self.pc.process_perceptual_input(
            "agent1",
            {"vision_sensor": vision_data}
        )
        
        # Check that facts were generated
        self.assertGreater(len(facts), 0, "Should generate facts for objects with ambiguous features")
        
        # The exact behavior with ambiguous features depends on the implementation
        # In a more sophisticated system, we might generate multiple facts with confidence scores,
        # but the current implementation will just use the primary color
    
    def test_process_perceptual_input_with_multiple_modalities(self):
        """Test processing input from multiple modalities simultaneously."""
        # Create mock vision data
        vision_data = MockRawSensorData(
            modality="vision",
            data=[
                {
                    "object_id": "obj1",
                    "object_type": "box",
                    "distance": 2.0,
                    "angle": 0.0,
                    "visual_features": {"color": "red", "shape": "cube"}
                }
            ]
        )
        
        # Create mock touch data for the same object
        touch_data = MockRawSensorData(
            modality="touch",
            data=[
                {
                    "object_id": "obj1",
                    "object_type": "box",
                    "distance": 0.1,
                    "force": 0.5,
                    "physical_properties": {"texture": "rough", "temperature": "warm"}
                }
            ]
        )
        
        # Process both modalities
        facts = self.pc.process_perceptual_input(
            "agent1",
            {"vision_sensor": vision_data, "touch_sensor": touch_data}
        )
        
        # Check that facts were generated for both modalities
        has_color_fact = False
        has_shape_fact = False
        has_touch_fact = False
        
        for fact in facts:
            if isinstance(fact, ApplicationNode) and isinstance(fact.operator, ConstantNode):
                if fact.operator.name == "HasColor":
                    has_color_fact = True
                elif fact.operator.name == "HasShape":
                    has_shape_fact = True
                elif fact.operator.name == "IsTouched":
                    has_touch_fact = True
        
        self.assertTrue(has_color_fact, "Should generate color facts from vision")
        self.assertTrue(has_shape_fact, "Should generate shape facts from vision")
        self.assertTrue(has_touch_fact, "Should generate touch facts from touch")
    
    def test_integration_with_object_tracker(self):
        """Test integration between perceptual categorizer and object tracker."""
        # Process perceptual input in multiple time steps to test tracking
        
        # Time step 1: Two objects
        vision_data_1 = MockRawSensorData(
            modality="vision",
            data=[
                {
                    "object_id": "obj1_t1",
                    "object_type": "box",
                    "distance": 2.0,
                    "angle": 0.0,
                    "visual_features": {"color": "red", "shape": "cube"}
                },
                {
                    "object_id": "obj2_t1",
                    "object_type": "sphere",
                    "distance": 5.0,
                    "angle": 90.0,
                    "visual_features": {"color": "blue", "shape": "sphere"}
                }
            ]
        )
        
        facts_1 = self.pc.process_perceptual_input(
            "agent1",
            {"vision_sensor": vision_data_1}
        )
        
        # Time step 2: Same objects with slightly different positions and different IDs
        vision_data_2 = MockRawSensorData(
            modality="vision",
            data=[
                {
                    "object_id": "obj1_t2",  # Different ID but same object
                    "object_type": "box",
                    "distance": 2.2,  # Slightly moved
                    "angle": 5.0,  # Slightly moved
                    "visual_features": {"color": "red", "shape": "cube"}
                },
                {
                    "object_id": "obj2_t2",  # Different ID but same object
                    "object_type": "sphere",
                    "distance": 5.2,  # Slightly moved
                    "angle": 85.0,  # Slightly moved
                    "visual_features": {"color": "blue", "shape": "sphere"}
                }
            ]
        )
        
        facts_2 = self.pc.process_perceptual_input(
            "agent1",
            {"vision_sensor": vision_data_2}
        )
        
        # Check that the object tracker maintained consistent IDs
        # We can't directly check the internal IDs, but we can check that facts were generated
        # and that the KR system was updated
        self.assertGreater(len(facts_1), 0, "Should generate facts in first time step")
        self.assertGreater(len(facts_2), 0, "Should generate facts in second time step")
        
        # The tracked objects should be maintained across time steps
        self.assertEqual(len(self.pc.object_tracker.tracked_objects), 2, 
                        "Should track two objects across time steps")


if __name__ == '__main__':
    unittest.main()