"""
Tests for GroundingPredictionError, PrototypeModel.compute_prediction_error,
and SymbolGroundingAssociator.measure_prediction_error_at_activation.
"""

import unittest
from unittest.mock import MagicMock
import os
import tempfile

from godelOS.symbol_grounding.symbol_grounding_associator import (
    SymbolGroundingAssociator,
    GroundingLink,
    GroundingPredictionError,
    ExperienceTrace,
    PrototypeModel,
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import ConstantNode, ApplicationNode


class TestComputePredictionError(unittest.TestCase):
    """Tests for PrototypeModel.compute_prediction_error."""

    def test_identical_features_zero_error(self):
        predicted = {"a": 1.0, "b": 2.0}
        observed = {"a": 1.0, "b": 2.0}
        errors, norm = PrototypeModel.compute_prediction_error(predicted, observed)
        self.assertEqual(norm, 0.0)
        self.assertEqual(errors, {"a": 0.0, "b": 0.0})

    def test_no_shared_keys(self):
        errors, norm = PrototypeModel.compute_prediction_error(
            {"x": 1.0}, {"y": 2.0}
        )
        self.assertEqual(errors, {})
        self.assertEqual(norm, 0.0)

    def test_non_numeric_keys_ignored(self):
        errors, norm = PrototypeModel.compute_prediction_error(
            {"color": "red", "size": 0.5},
            {"color": "blue", "size": 0.8},
        )
        self.assertIn("size", errors)
        self.assertNotIn("color", errors)
        self.assertAlmostEqual(errors["size"], 0.3, places=5)

    def test_rmse_correctness(self):
        # errors: a=1.0, b=2.0 → RMSE = sqrt((1+4)/2) = sqrt(2.5)
        errors, norm = PrototypeModel.compute_prediction_error(
            {"a": 0.0, "b": 0.0}, {"a": 1.0, "b": 2.0}
        )
        self.assertAlmostEqual(norm, (2.5) ** 0.5, places=5)


class TestMeasurePredictionErrorAtActivation(unittest.TestCase):
    """Tests for SymbolGroundingAssociator.measure_prediction_error_at_activation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.kr_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.kr_interface.list_contexts.return_value = []
        self.type_system = MagicMock(spec=TypeSystemManager)
        entity_type = MagicMock()
        prop_type = MagicMock()
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": entity_type, "Object": entity_type, "Proposition": prop_type
        }.get(name)
        self.sga = SymbolGroundingAssociator(
            kr_system_interface=self.kr_interface,
            type_system=self.type_system,
            grounding_model_db_path=os.path.join(self.temp_dir.name, "g.json"),
        )
        self._entity = entity_type
        self._prop = prop_type

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cold_start_returns_none(self):
        """No grounding link → None."""
        result = self.sga.measure_prediction_error_at_activation(
            "unknown_symbol", {"size": 0.5}, "visual_features"
        )
        self.assertIsNone(result)

    def test_after_learning_novel_observation(self):
        """After prototype is built, novel observation gives non-zero error."""
        # Manually inject a grounding link with a known prototype
        self.sga.grounding_links["ball"] = [
            GroundingLink(
                symbol_ast_id="ball",
                sub_symbolic_representation={"size": 0.5, "roundness": 0.9},
                modality="visual_features",
                confidence=0.8,
            )
        ]
        result = self.sga.measure_prediction_error_at_activation(
            "ball", {"size": 0.8, "roundness": 0.5}, "visual_features"
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, GroundingPredictionError)
        self.assertGreater(result.error_norm, 0.0)
        self.assertIn("size", result.feature_errors)
        self.assertIn("roundness", result.feature_errors)
        self.assertEqual(result.symbol_ast_id, "ball")

    def test_identical_observation_zero_error(self):
        """Observation matching prototype exactly → error_norm == 0."""
        self.sga.grounding_links["ball"] = [
            GroundingLink(
                symbol_ast_id="ball",
                sub_symbolic_representation={"size": 0.5, "roundness": 0.9},
                modality="visual_features",
                confidence=0.8,
            )
        ]
        result = self.sga.measure_prediction_error_at_activation(
            "ball", {"size": 0.5, "roundness": 0.9}, "visual_features"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.error_norm, 0.0)


if __name__ == "__main__":
    unittest.main()
