"""
Unit tests for the SymbolGroundingAssociator component.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile
import json
import time

from godelOS.symbol_grounding.symbol_grounding_associator import (
    SymbolGroundingAssociator,
    GroundingLink,
    ExperienceTrace,
    PrototypeModel,
    ActionEffectModel
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode


class TestGroundingModels(unittest.TestCase):
    """Tests for the grounding model classes."""
    
    def test_prototype_model(self):
        """Test the PrototypeModel class."""
        model = PrototypeModel("visual_features")
        
        # Test learning from examples
        examples = [
            {"color": "red", "shape": "cube", "size": 0.5},
            {"color": "red", "shape": "sphere", "size": 0.7},
            {"color": "red", "shape": "cube", "size": 0.3}
        ]
        
        prototype = model.learn("red", examples)
        
        # Check the learned prototype
        self.assertEqual(prototype["color"], "red")
        self.assertEqual(prototype["shape"], "cube")  # Most common value
        self.assertAlmostEqual(prototype["size"], 0.5)  # Average
        
        # Test prediction
        test_input = {"color": "red", "shape": "cube", "size": 0.4}
        confidence = model.predict(prototype, test_input)
        self.assertGreater(confidence, 0.8)  # High confidence for similar input
        
        # Test with different input
        different_input = {"color": "blue", "shape": "pyramid", "size": 1.0}
        confidence = model.predict(prototype, different_input)
        self.assertLess(confidence, 0.5)  # Low confidence for different input
        
        # Test update
        new_example = {"color": "red", "shape": "pyramid", "size": 0.9}
        updated_prototype = model.update(prototype, new_example)
        
        # Check the updated prototype
        self.assertEqual(updated_prototype["color"], "red")
        self.assertEqual(updated_prototype["shape"], "cube")  # Original value preserved
        self.assertAlmostEqual(updated_prototype["size"], 0.7)  # Updated average
    
    def test_action_effect_model(self):
        """Test the ActionEffectModel class."""
        model = ActionEffectModel("action_effect")
        
        # Test learning from examples
        examples = [
            {
                "action_type": "Push",
                "effect": {"position_delta": 1.0, "force": 0.5}
            },
            {
                "action_type": "Push",
                "effect": {"position_delta": 1.2, "force": 0.6}
            }
        ]
        
        effect_model = model.learn("Push", examples)
        
        # Check the learned effect model
        self.assertEqual(effect_model["action_type"], "Push")
        self.assertIn("effect_prototype", effect_model)
        self.assertAlmostEqual(effect_model["effect_prototype"]["position_delta"], 1.1)
        self.assertAlmostEqual(effect_model["effect_prototype"]["force"], 0.55)
        
        # Test prediction
        test_input = {"position_delta": 1.0, "force": 0.5}
        confidence = model.predict(effect_model, test_input)
        self.assertGreater(confidence, 0.8)  # High confidence for similar input
        
        # Test update
        new_example = {
            "action_type": "Push",
            "effect": {"position_delta": 1.5, "force": 0.7}
        }
        updated_effect_model = model.update(effect_model, new_example["effect"])
        
        # Check the updated effect model
        self.assertIn("effect_prototype", updated_effect_model)
        # The update method in ActionEffectModel uses PrototypeModel.update which averages values
        # So we expect the values to move toward the new example
        self.assertGreater(updated_effect_model["effect_prototype"]["position_delta"], 1.1)
        self.assertGreater(updated_effect_model["effect_prototype"]["force"], 0.55)


class TestSymbolGroundingAssociator(unittest.TestCase):
    """Tests for the SymbolGroundingAssociator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for grounding models
        self.temp_dir = tempfile.TemporaryDirectory()
        self.grounding_model_db_path = os.path.join(self.temp_dir.name, "grounding_models.json")
        
        # Create mock KR interface
        self.kr_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.kr_interface.list_contexts.return_value = []
        
        # Create mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        self.entity_type = MagicMock()
        self.prop_type = MagicMock()
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Object": self.entity_type,
            "Proposition": self.prop_type
        }.get(name)
        
        # Create the symbol grounding associator
        self.sga = SymbolGroundingAssociator(
            kr_system_interface=self.kr_interface,
            type_system=self.type_system,
            grounding_model_db_path=self.grounding_model_db_path
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initialization."""
        # Check that the grounding context was created
        self.kr_interface.create_context.assert_called_once_with(
            "GROUNDING_CONTEXT", None, "grounding"
        )
        
        # Check that grounding models were initialized
        self.assertIn("visual_features", self.sga.grounding_models)
        self.assertIn("proprioceptive_force", self.sga.grounding_models)
        self.assertIn("action_effect", self.sga.grounding_models)
        
        # Check that experience buffer is empty
        self.assertEqual(len(self.sga.experience_buffer), 0)
    
    def test_record_experience(self):
        """Test recording experiences."""
        # Create a test experience
        experience = ExperienceTrace(
            active_symbols_in_kb={
                ConstantNode("red", self.entity_type),
                ApplicationNode(
                    operator=ConstantNode("HasColor", self.prop_type),
                    arguments=[
                        ConstantNode("obj1", self.entity_type),
                        ConstantNode("red", self.entity_type)
                    ],
                    type_ref=self.prop_type
                )
            },
            extracted_features_by_object={
                "obj1": {"color": "red", "shape": "cube", "size": 0.5}
            }
        )
        
        # Record the experience
        self.sga.record_experience(experience)
        
        # Check that the experience was recorded
        self.assertEqual(len(self.sga.experience_buffer), 1)
        
        # Record more experiences to test buffer size limiting
        for i in range(self.sga.experience_buffer_size + 10):
            self.sga.record_experience(ExperienceTrace())
        
        # Check that the buffer size is limited
        self.assertEqual(len(self.sga.experience_buffer), self.sga.experience_buffer_size)
    
    def test_learn_groundings_from_buffer(self):
        """Test learning groundings from the experience buffer."""
        # Create test experiences
        red_obj1 = ExperienceTrace(
            active_symbols_in_kb={
                ApplicationNode(
                    operator=ConstantNode("HasColor", self.prop_type),
                    arguments=[
                        ConstantNode("obj1", self.entity_type),
                        ConstantNode("red", self.entity_type)
                    ],
                    type_ref=self.prop_type
                )
            },
            extracted_features_by_object={
                "obj1": {"color": "red", "shape": "cube", "size": 0.5}
            }
        )
        
        red_obj2 = ExperienceTrace(
            active_symbols_in_kb={
                ApplicationNode(
                    operator=ConstantNode("HasColor", self.prop_type),
                    arguments=[
                        ConstantNode("obj2", self.entity_type),
                        ConstantNode("red", self.entity_type)
                    ],
                    type_ref=self.prop_type
                )
            },
            extracted_features_by_object={
                "obj2": {"color": "red", "shape": "sphere", "size": 0.7}
            }
        )
        
        # Record the experiences
        self.sga.record_experience(red_obj1)
        self.sga.record_experience(red_obj2)
        
        # Learn groundings
        self.sga.learn_groundings_from_buffer(learning_focus_symbols=["red"])
        
        # Check that a grounding was created for "red"
        self.assertIn("red", self.sga.grounding_links)
        
        # Check that the grounding has the correct modality
        red_links = self.sga.grounding_links["red"]
        self.assertEqual(len(red_links), 1)
        self.assertEqual(red_links[0].modality, "visual_features")
        
        # Check that the grounding was saved to disk
        self.assertTrue(os.path.exists(self.grounding_model_db_path))
        
        # Load the saved groundings and check
        with open(self.grounding_model_db_path, 'r') as f:
            data = json.load(f)
            self.assertIn("red", data)
    
    def test_get_grounding_for_symbol(self):
        """Test getting groundings for a symbol."""
        # Create a test grounding link
        link = GroundingLink(
            symbol_ast_id="red",
            sub_symbolic_representation={"color": "red"},
            modality="visual_features",
            confidence=0.8
        )
        
        # Add the link to the associator
        self.sga.grounding_links["red"] = [link]
        
        # Get groundings for "red"
        links = self.sga.get_grounding_for_symbol("red")
        
        # Check the returned links
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].symbol_ast_id, "red")
        self.assertEqual(links[0].modality, "visual_features")
        
        # Test with modality filter
        links = self.sga.get_grounding_for_symbol("red", modality_filter="visual_features")
        self.assertEqual(len(links), 1)
        
        links = self.sga.get_grounding_for_symbol("red", modality_filter="action_effect")
        self.assertEqual(len(links), 0)
        
        # Test with nonexistent symbol
        links = self.sga.get_grounding_for_symbol("nonexistent")
        self.assertEqual(len(links), 0)
    
    def test_get_symbols_for_features(self):
        """Test getting symbols for a feature vector."""
        # Create test grounding links
        red_link = GroundingLink(
            symbol_ast_id="red",
            sub_symbolic_representation={"color": "red", "hue": 0},
            modality="visual_features",
            confidence=0.9
        )
        
        blue_link = GroundingLink(
            symbol_ast_id="blue",
            sub_symbolic_representation={"color": "blue", "hue": 240},
            modality="visual_features",
            confidence=0.9
        )
        
        # Add the links to the associator
        self.sga.grounding_links["red"] = [red_link]
        self.sga.grounding_links["blue"] = [blue_link]
        
        # Get symbols for a red object
        red_features = {"color": "red", "hue": 10}
        symbols = self.sga.get_symbols_for_features(red_features, "visual_features")
        
        # Check the returned symbols
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0][0], "red")
        self.assertGreater(symbols[0][1], symbols[1][1])  # red should have higher confidence
        
        # Get symbols for a blue object
        blue_features = {"color": "blue", "hue": 230}
        symbols = self.sga.get_symbols_for_features(blue_features, "visual_features")
        
        # Check the returned symbols
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0][0], "blue")
        self.assertGreater(symbols[0][1], symbols[1][1])  # blue should have higher confidence
        
        # Test with top_k
        symbols = self.sga.get_symbols_for_features(red_features, "visual_features", top_k=1)
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0][0], "red")
    
    def test_learn_action_effect_grounding(self):
        """Test learning action effect groundings."""
        # Create a test action experience
        push_experience = ExperienceTrace(
            active_symbols_in_kb={
                ConstantNode("Push", self.prop_type)
            },
            executed_action_ast=ApplicationNode(
                operator=ConstantNode("Push", self.prop_type),
                arguments=[
                    ConstantNode("agent1", self.entity_type),
                    ConstantNode("obj1", self.entity_type)
                ],
                type_ref=self.prop_type
            ),
            observed_effect_symbols={
                ApplicationNode(
                    operator=ConstantNode("HasMoved", self.prop_type),
                    arguments=[
                        ConstantNode("obj1", self.entity_type),
                        ConstantNode("1,0,0", self.entity_type)
                    ],
                    type_ref=self.prop_type
                )
            },
            observed_effect_raw_sensors={
                "force_sensor": 0.5,
                "position_delta": 1.0
            }
        )
        
        # Record the experience
        self.sga.record_experience(push_experience)
        
        # Learn groundings
        self.sga.learn_groundings_from_buffer(learning_focus_symbols=["Push"])
        
        # Check that a grounding was created for "Push"
        self.assertIn("Push", self.sga.grounding_links)
        
        # Check that the grounding has the correct modality
        push_links = self.sga.grounding_links["Push"]
        self.assertEqual(len(push_links), 1)
        self.assertEqual(push_links[0].modality, "action_effect")
        
        # Check the content of the grounding
        representation = push_links[0].sub_symbolic_representation
        self.assertEqual(representation["action_type"], "Push")
        self.assertIn("effect_prototype", representation)
        self.assertIn("sensor_force_sensor", representation["effect_prototype"])
        self.assertIn("sensor_position_delta", representation["effect_prototype"])


if __name__ == '__main__':
    unittest.main()