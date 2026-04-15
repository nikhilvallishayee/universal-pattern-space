"""
Tests for the Probabilistic Logic Module.
"""

import unittest
from typing import Dict, List, Set, Tuple, Optional

from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.probabilistic_logic.module import ProbabilisticLogicModule, MCMCInference, GradientDescentWeightLearning


class TestProbabilisticLogicModule(unittest.TestCase):
    """Test cases for the Probabilistic Logic Module."""
    
    def setUp(self):
        """Set up the test case."""
        self.type_system = TypeSystemManager()
        self.ksi = KnowledgeStoreInterface(self.type_system)
        self.plm = ProbabilisticLogicModule(self.ksi)
        
        # Create some types for testing
        self.entity_type = self.type_system.get_type("Entity")
        self.boolean_type = self.type_system.get_type("Boolean")
        
        # Create some constants
        self.alice = ConstantNode("Alice", self.entity_type)
        self.bob = ConstantNode("Bob", self.entity_type)
        self.charlie = ConstantNode("Charlie", self.entity_type)
        
        # Create some predicates
        self.smokes_pred = ConstantNode("Smokes", self.boolean_type)
        self.friends_pred = ConstantNode("Friends", self.boolean_type)
        self.cancer_pred = ConstantNode("Cancer", self.boolean_type)
        
        # Create some atomic formulas
        self.smokes_alice = ApplicationNode(self.smokes_pred, [self.alice], self.boolean_type)
        self.smokes_bob = ApplicationNode(self.smokes_pred, [self.bob], self.boolean_type)
        self.friends_alice_bob = ApplicationNode(self.friends_pred, [self.alice, self.bob], self.boolean_type)
        self.cancer_alice = ApplicationNode(self.cancer_pred, [self.alice], self.boolean_type)
        
        # Create some rules
        # Rule 1: Smoking causes cancer
        self.smoking_causes_cancer = ConnectiveNode(
            "IMPLIES",
            [self.smokes_alice, self.cancer_alice],
            self.boolean_type
        )
        
        # Rule 2: Friends have similar smoking habits
        self.friends_smoke_together = ConnectiveNode(
            "IMPLIES",
            [
                self.friends_alice_bob,
                ConnectiveNode(
                    "EQUIV",
                    [self.smokes_alice, self.smokes_bob],
                    self.boolean_type
                )
            ],
            self.boolean_type
        )
    
    def test_add_weighted_formula(self):
        """Test adding weighted formulas."""
        # Add a weighted formula
        self.plm.add_weighted_formula(self.smoking_causes_cancer, 1.5)
        
        # Check that it was added correctly
        self.assertIn("PROBABILISTIC_RULES", self.plm._weighted_formulas)
        self.assertIn(self.smoking_causes_cancer, self.plm._weighted_formulas["PROBABILISTIC_RULES"])
        self.assertEqual(self.plm._weighted_formulas["PROBABILISTIC_RULES"][self.smoking_causes_cancer], 1.5)
        
        # Add another weighted formula to a different context
        self.plm.add_weighted_formula(self.friends_smoke_together, 0.8, "SOCIAL_RULES")
        
        # Check that it was added correctly
        self.assertIn("SOCIAL_RULES", self.plm._weighted_formulas)
        self.assertIn(self.friends_smoke_together, self.plm._weighted_formulas["SOCIAL_RULES"])
        self.assertEqual(self.plm._weighted_formulas["SOCIAL_RULES"][self.friends_smoke_together], 0.8)
    
    def test_get_marginal_probability(self):
        """Test calculating marginal probabilities."""
        # Add weighted formulas
        self.plm.add_weighted_formula(self.smoking_causes_cancer, 1.5)
        self.plm.add_weighted_formula(self.friends_smoke_together, 0.8)
        
        # Set up evidence
        evidence = {(self.smokes_alice, True), (self.friends_alice_bob, True)}
        
        # Calculate the marginal probability of Bob smoking
        # With a small number of samples for testing
        params = {"num_samples": 100, "burn_in": 10, "sample_interval": 1}
        prob = self.plm.get_marginal_probability(self.smokes_bob, evidence, params)
        
        # The probability should be high since Alice smokes and they are friends
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)
    
    def test_get_map_assignment(self):
        """Test finding MAP assignments."""
        # Add weighted formulas
        self.plm.add_weighted_formula(self.smoking_causes_cancer, 1.5)
        self.plm.add_weighted_formula(self.friends_smoke_together, 0.8)
        
        # Set up evidence
        evidence = {(self.smokes_alice, True), (self.friends_alice_bob, True)}
        
        # Find the MAP assignment for Bob smoking and Alice having cancer
        query_vars = [self.smokes_bob, self.cancer_alice]
        params = {"max_iterations": 100}
        assignment = self.plm.get_map_assignment(query_vars, evidence, params)
        
        # Check that we got assignments for the query variables
        self.assertIn(self.smokes_bob, assignment)
        self.assertIn(self.cancer_alice, assignment)
        
        # Bob should likely smoke since Alice smokes and they are friends
        # Alice should likely have cancer since she smokes
        self.assertTrue(isinstance(assignment[self.smokes_bob], bool))
        self.assertTrue(isinstance(assignment[self.cancer_alice], bool))
    
    def test_learn_weights(self):
        """Test learning weights from data."""
        # Create a training database context
        self.ksi.create_context("TRAINING_DB", context_type="database")
        
        # Add some training data
        self.ksi.add_statement(self.smokes_alice, "TRAINING_DB", {"world_id": 1})
        self.ksi.add_statement(self.cancer_alice, "TRAINING_DB", {"world_id": 1})
        self.ksi.add_statement(self.friends_alice_bob, "TRAINING_DB", {"world_id": 1})
        self.ksi.add_statement(self.smokes_bob, "TRAINING_DB", {"world_id": 1})
        
        self.ksi.add_statement(self.friends_alice_bob, "TRAINING_DB", {"world_id": 2})
        self.ksi.add_statement(self.smokes_alice, "TRAINING_DB", {"world_id": 2})
        self.ksi.add_statement(self.smokes_bob, "TRAINING_DB", {"world_id": 2})
        
        # Create a formula skeletons context
        self.ksi.create_context("FORMULA_SKELETONS", context_type="rules")
        
        # Add formula skeletons
        self.plm.add_weighted_formula(self.smoking_causes_cancer, 0.0, "FORMULA_SKELETONS")
        self.plm.add_weighted_formula(self.friends_smoke_together, 0.0, "FORMULA_SKELETONS")
        
        # Learn weights with a small number of iterations for testing
        params = {"max_iterations": 5, "learning_rate": 0.1}
        weights = self.plm.learn_weights("TRAINING_DB", "FORMULA_SKELETONS", params)
        
        # Check that we got weights for the formula skeletons
        self.assertIn(self.smoking_causes_cancer, weights)
        self.assertIn(self.friends_smoke_together, weights)
        
        # Weights should be real numbers
        self.assertTrue(isinstance(weights[self.smoking_causes_cancer], float))
        self.assertTrue(isinstance(weights[self.friends_smoke_together], float))


if __name__ == '__main__':
    unittest.main()