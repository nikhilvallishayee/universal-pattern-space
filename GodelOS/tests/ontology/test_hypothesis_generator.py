"""
Unit tests for the HypothesisGenerator component.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.ontology.hypothesis_generator import HypothesisGenerator
from godelOS.ontology.ontology_manager import OntologyManager

class TestHypothesisGenerator(unittest.TestCase):
    """Test cases for the HypothesisGenerator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ontology_manager = OntologyManager()
        self.hypothesis_generator = HypothesisGenerator(self.ontology_manager)
        
        # Add some test concepts to the ontology
        self.ontology_manager.add_concept("water", {
            "name": "Water",
            "description": "A transparent, odorless, tasteless liquid that forms the seas, lakes, rivers, and rain.",
            "properties": {
                "state": "liquid",
                "color": "transparent",
                "taste": "none",
                "temperature": 20
            }
        })
        
        self.ontology_manager.add_concept("ice", {
            "name": "Ice",
            "description": "Frozen water, a brittle, transparent crystalline solid.",
            "properties": {
                "state": "solid",
                "color": "transparent",
                "taste": "none",
                "temperature": -10
            }
        })
        
        self.ontology_manager.add_concept("steam", {
            "name": "Steam",
            "description": "The vapor into which water is converted when heated.",
            "properties": {
                "state": "gas",
                "color": "transparent",
                "taste": "none",
                "temperature": 100
            }
        })
        
        # Add some relations
        self.ontology_manager.add_relation("causes", {"type": "causal"})
        self.ontology_manager.add_relation("transforms_into", {"type": "transformation"})
        
        # Add relation instances
        self.ontology_manager.add_relation_instance("causes", "heat", "steam")
        self.ontology_manager.add_relation_instance("causes", "cold", "ice")
        self.ontology_manager.add_relation_instance("transforms_into", "water", "ice")
        self.ontology_manager.add_relation_instance("transforms_into", "water", "steam")
        
        # Test observations
        self.observations = [
            {"type": "observation", "concept_id": "ice", "property": "state", "value": "solid"},
            {"type": "observation", "concept_id": "water", "property": "temperature", "value": 0}
        ]
        
        # Test context
        self.context = {
            "environment": "laboratory",
            "time": "morning",
            "previous_observations": [
                {"type": "observation", "concept_id": "water", "property": "temperature", "value": 20}
            ]
        }
    
    def test_generate_hypotheses_abductive(self):
        """Test generating hypotheses using abductive reasoning."""
        # Generate hypotheses
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "abductive"
        )
        
        # Check that hypotheses were generated
        self.assertIsNotNone(hypotheses)
        self.assertGreater(len(hypotheses), 0)
        
        # Check hypothesis structure
        for hypothesis in hypotheses:
            self.assertIn("id", hypothesis)
            self.assertIn("type", hypothesis)
            self.assertEqual("abductive", hypothesis["type"])
            self.assertIn("explanation", hypothesis)
            self.assertIn("supporting_evidence", hypothesis)
            self.assertIn("contradicting_evidence", hypothesis)
            self.assertIn("predictions", hypothesis)
            self.assertIn("plausibility", hypothesis)
    
    def test_generate_hypotheses_analogical(self):
        """Test generating hypotheses using analogical reasoning."""
        # Generate hypotheses
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "analogical"
        )
        
        # Check that hypotheses were generated
        self.assertIsNotNone(hypotheses)
        
        # Check hypothesis structure for any generated hypotheses
        for hypothesis in hypotheses:
            self.assertIn("id", hypothesis)
            self.assertIn("type", hypothesis)
            self.assertEqual("analogical", hypothesis["type"])
            self.assertIn("explanation", hypothesis)
            self.assertIn("plausibility", hypothesis)
    
    def test_generate_hypotheses_inductive(self):
        """Test generating hypotheses using inductive reasoning."""
        # Generate hypotheses
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "inductive"
        )
        
        # Check that hypotheses were generated
        self.assertIsNotNone(hypotheses)
        
        # Check hypothesis structure for any generated hypotheses
        for hypothesis in hypotheses:
            self.assertIn("id", hypothesis)
            self.assertIn("type", hypothesis)
            self.assertEqual("inductive", hypothesis["type"])
            self.assertIn("explanation", hypothesis)
            self.assertIn("pattern", hypothesis)
            self.assertIn("plausibility", hypothesis)
    
    def test_generate_hypotheses_deductive(self):
        """Test generating hypotheses using deductive reasoning."""
        # Generate hypotheses
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "deductive"
        )
        
        # Check that hypotheses were generated
        self.assertIsNotNone(hypotheses)
        
        # Check hypothesis structure for any generated hypotheses
        for hypothesis in hypotheses:
            self.assertIn("id", hypothesis)
            self.assertIn("type", hypothesis)
            self.assertEqual("deductive", hypothesis["type"])
            self.assertIn("explanation", hypothesis)
            self.assertIn("rule", hypothesis)
            self.assertIn("plausibility", hypothesis)
    
    def test_generate_hypotheses_with_constraints(self):
        """Test generating hypotheses with constraints."""
        # Create constraints
        constraints = {
            "excluded_concepts": ["steam"],
            "allowed_types": ["abductive", "deductive"]
        }
        
        # Generate hypotheses with constraints
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "abductive", constraints
        )
        
        # Check that hypotheses were generated
        self.assertIsNotNone(hypotheses)
        
        # Check that constraints were applied
        for hypothesis in hypotheses:
            if "causal_concept" in hypothesis:
                self.assertNotEqual("steam", hypothesis["causal_concept"])
            
            self.assertIn(hypothesis["type"], ["abductive", "deductive"])
    
    def test_generate_hypotheses_invalid_strategy(self):
        """Test generating hypotheses with an invalid strategy."""
        # Generate hypotheses with invalid strategy
        hypotheses = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "invalid_strategy"
        )
        
        # Check that no hypotheses were generated
        self.assertEqual(0, len(hypotheses))
    
    def test_hypothesis_caching(self):
        """Test that hypotheses are cached."""
        # Generate hypotheses
        hypotheses1 = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "abductive"
        )
        
        # Generate the same hypotheses again
        hypotheses2 = self.hypothesis_generator.generate_hypotheses(
            self.observations, self.context, "abductive"
        )
        
        # Check that the same hypotheses were returned
        self.assertEqual(hypotheses1, hypotheses2)
        
        # Check cache directly
        cache_key = (str(self.observations), str(self.context), "abductive", str(None), 5)
        self.assertIn(cache_key, self.hypothesis_generator._hypothesis_cache)
        self.assertEqual(hypotheses1, self.hypothesis_generator._hypothesis_cache[cache_key])
    
    def test_evaluate_hypothesis(self):
        """Test evaluating a hypothesis."""
        # Create a test hypothesis
        hypothesis = {
            "id": "test-hypothesis",
            "type": "abductive",
            "explanation": "Cold temperatures caused water to freeze into ice",
            "causal_concept": "cold",
            "observed_concept": "ice",
            "relation": "causes",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "predictions": [
                {"type": "property", "concept_id": "ice", "property_id": "temperature", "expected_value": -10}
            ]
        }
        
        # Evaluate the hypothesis
        evaluated_hypothesis = self.hypothesis_generator.evaluate_hypothesis(
            hypothesis, self.observations, self.context
        )
        
        # Check that the hypothesis was evaluated
        self.assertIsNotNone(evaluated_hypothesis)
        self.assertIn("evaluation_scores", evaluated_hypothesis)
        self.assertIn("plausibility", evaluated_hypothesis)
        
        # Check that evaluation scores were calculated
        scores = evaluated_hypothesis["evaluation_scores"]
        self.assertIn("explanatory_power", scores)
        self.assertIn("parsimony", scores)
        self.assertIn("consistency", scores)
        self.assertIn("novelty", scores)
        self.assertIn("testability", scores)
    
    def test_test_hypothesis(self):
        """Test testing a hypothesis against new observations."""
        # Create a test hypothesis
        hypothesis = {
            "id": "test-hypothesis",
            "type": "abductive",
            "explanation": "Cold temperatures caused water to freeze into ice",
            "causal_concept": "cold",
            "observed_concept": "ice",
            "relation": "causes",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "predictions": [
                {"type": "property", "concept_id": "ice", "property_id": "temperature", "expected_value": -10},
                {"type": "property", "concept_id": "ice", "property_id": "state", "expected_value": "solid"}
            ]
        }
        
        # Create new observations
        new_observations = [
            {"type": "observation", "concept_id": "ice", "property": "temperature", "value": -10},
            {"type": "observation", "concept_id": "ice", "property": "state", "value": "solid"}
        ]
        
        # Test the hypothesis
        test_results = self.hypothesis_generator.test_hypothesis(hypothesis, new_observations)
        
        # Check that test results were generated
        self.assertIsNotNone(test_results)
        self.assertIn("success", test_results)
        self.assertIn("confirmation_score", test_results)
        self.assertIn("confirmed_predictions", test_results)
        self.assertIn("disconfirmed_predictions", test_results)
        self.assertIn("inconclusive_predictions", test_results)
    
    def test_test_hypothesis_no_predictions(self):
        """Test testing a hypothesis with no predictions."""
        # Create a test hypothesis with no predictions
        hypothesis = {
            "id": "test-hypothesis",
            "type": "abductive",
            "explanation": "Cold temperatures caused water to freeze into ice",
            "causal_concept": "cold",
            "observed_concept": "ice",
            "relation": "causes",
            "supporting_evidence": [],
            "contradicting_evidence": []
        }
        
        # Create new observations
        new_observations = [
            {"type": "observation", "concept_id": "ice", "property": "temperature", "value": -10}
        ]
        
        # Test the hypothesis
        test_results = self.hypothesis_generator.test_hypothesis(hypothesis, new_observations)
        
        # Check that test results indicate failure due to no predictions
        self.assertIsNotNone(test_results)
        self.assertFalse(test_results["success"])
        self.assertEqual("Hypothesis makes no predictions", test_results["reason"])
    
    def test_helper_methods(self):
        """Test helper methods of the HypothesisGenerator."""
        # Test _extract_concepts_from_observations
        concepts = self.hypothesis_generator._extract_concepts_from_observations(self.observations)
        self.assertIsNotNone(concepts)
        self.assertIn("ice", concepts)
        self.assertIn("water", concepts)
        
        # Test _find_causal_relations
        causal_relations = self.hypothesis_generator._find_causal_relations("steam")
        self.assertIsNotNone(causal_relations)
        
        # Test _generate_predictions (water has outgoing relations)
        predictions = self.hypothesis_generator._generate_predictions("water", self.context)
        self.assertIsNotNone(predictions)
        self.assertGreater(len(predictions), 0)
        
        # Test _is_consistent_with_constraints
        hypothesis = {
            "type": "abductive",
            "causal_concept": "cold",
            "observed_concept": "ice"
        }
        constraints = {
            "excluded_concepts": ["heat"],
            "allowed_types": ["abductive"]
        }
        self.assertTrue(self.hypothesis_generator._is_consistent_with_constraints(hypothesis, constraints))
        
        # Test with excluded concept
        constraints["excluded_concepts"] = ["cold"]
        self.assertFalse(self.hypothesis_generator._is_consistent_with_constraints(hypothesis, constraints))

if __name__ == "__main__":
    unittest.main()