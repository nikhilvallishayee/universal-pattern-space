import unittest
from typing import Dict, Set
import uuid

from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, ConnectiveNode, VariableNode
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.belief_revision.system import (
    BeliefRevisionSystem,
    RevisionStrategy,
    Argument,
    ArgumentationFramework
)


class TestBeliefRevisionSystem(unittest.TestCase):
    """Test cases for the BeliefRevisionSystem."""

    def setUp(self):
        """Set up test environment."""
        # Create a type system
        self.type_system = TypeSystemManager()
        self.type_system.register_base_types()
        
        # Create a knowledge store interface
        self.ksi = KnowledgeStoreInterface(self.type_system)
        
        # Create a belief revision system
        self.brs = BeliefRevisionSystem(self.ksi)
        
        # Create some test AST nodes
        self.bool_type = self.type_system.get_type("Bool")
        
        # Some basic facts
        self.fact1 = ConstantNode("fact1", self.bool_type, True)
        self.fact2 = ConstantNode("fact2", self.bool_type, True)
        self.fact3 = ConstantNode("fact3", self.bool_type, True)
        
        # Negation of fact1
        self.not_fact1 = ConnectiveNode(
            connective_type="NOT",
            operands=[self.fact1],
            type_ref=self.bool_type
        )
        
        # Create a test belief set
        self.belief_set_id = f"test_belief_set_{uuid.uuid4().hex[:8]}"
        self.ksi.create_context(self.belief_set_id, context_type="beliefs")
        
        # Add some initial beliefs
        self.ksi.add_statement(self.fact1, self.belief_set_id)
        self.ksi.add_statement(self.fact2, self.belief_set_id)

    def test_expand_belief_set(self):
        """Test expanding a belief set."""
        # Expand the belief set with fact3
        expanded_belief_set_id = self.brs.expand_belief_set(
            self.belief_set_id, self.fact3, entrenchment_value=0.8
        )
        
        # Check that the expanded belief set contains all the original beliefs
        self.assertTrue(self.ksi.statement_exists(self.fact1, [expanded_belief_set_id]))
        self.assertTrue(self.ksi.statement_exists(self.fact2, [expanded_belief_set_id]))
        
        # Check that the expanded belief set contains the new belief
        self.assertTrue(self.ksi.statement_exists(self.fact3, [expanded_belief_set_id]))
        
        # Check that expanding with an existing belief returns the same belief set
        same_belief_set_id = self.brs.expand_belief_set(
            expanded_belief_set_id, self.fact1
        )
        self.assertEqual(expanded_belief_set_id, same_belief_set_id)

    def test_contract_belief_set_partial_meet(self):
        """Test contracting a belief set using partial meet contraction."""
        # Contract the belief set to remove fact1
        contracted_belief_set_id = self.brs.contract_belief_set(
            self.belief_set_id, self.fact1, strategy=RevisionStrategy.PARTIAL_MEET
        )
        
        # Check that the contracted belief set does not contain fact1
        self.assertFalse(self.ksi.statement_exists(self.fact1, [contracted_belief_set_id]))
        
        # Check that the contracted belief set still contains fact2
        self.assertTrue(self.ksi.statement_exists(self.fact2, [contracted_belief_set_id]))
        
        # Check that contracting a belief that doesn't exist returns the same belief set
        same_belief_set_id = self.brs.contract_belief_set(
            contracted_belief_set_id, self.fact1
        )
        self.assertEqual(contracted_belief_set_id, same_belief_set_id)

    def test_contract_belief_set_kernel(self):
        """Test contracting a belief set using kernel contraction."""
        # Contract the belief set to remove fact1
        contracted_belief_set_id = self.brs.contract_belief_set(
            self.belief_set_id, self.fact1, strategy=RevisionStrategy.KERNEL
        )
        
        # Check that the contracted belief set does not contain fact1
        self.assertFalse(self.ksi.statement_exists(self.fact1, [contracted_belief_set_id]))
        
        # Check that the contracted belief set still contains fact2
        self.assertTrue(self.ksi.statement_exists(self.fact2, [contracted_belief_set_id]))

    def test_revise_belief_set(self):
        """Test revising a belief set."""
        # Revise the belief set with not_fact1 (which contradicts fact1)
        revised_belief_set_id = self.brs.revise_belief_set(
            self.belief_set_id, self.not_fact1
        )
        
        # Check that the revised belief set contains not_fact1
        self.assertTrue(self.ksi.statement_exists(self.not_fact1, [revised_belief_set_id]))
        
        # Check that the revised belief set does not contain fact1 (due to contradiction)
        self.assertFalse(self.ksi.statement_exists(self.fact1, [revised_belief_set_id]))
        
        # Check that the revised belief set still contains fact2
        self.assertTrue(self.ksi.statement_exists(self.fact2, [revised_belief_set_id]))

    def test_get_justified_beliefs_via_argumentation(self):
        """Test getting justified beliefs via argumentation."""
        # Create some knowledge and rules
        knowledge = {self.fact1, self.fact2}
        rules = {self.fact3, self.not_fact1}
        
        # Get justified beliefs using grounded semantics
        justified_beliefs = self.brs.get_justified_beliefs_via_argumentation(
            knowledge, rules, semantics_type="grounded"
        )
        
        # Check that justified beliefs is a set of AST_Node objects
        self.assertIsInstance(justified_beliefs, set)
        for belief in justified_beliefs:
            self.assertIsInstance(belief, AST_Node)

    def test_argumentation_framework(self):
        """Test the ArgumentationFramework class."""
        # Create an argumentation framework
        af = ArgumentationFramework()
        
        # Create some arguments
        arg1 = Argument(
            conclusion=self.fact1,
            premises=set(),
            inference_rule_id="fact",
            arg_type="strict"
        )
        
        arg2 = Argument(
            conclusion=self.not_fact1,
            premises=set(),
            inference_rule_id="default",
            arg_type="defeasible"
        )
        
        # Add arguments to the framework
        af.add_argument(arg1)
        af.add_argument(arg2)
        
        # Add an attack relation
        af.add_attack(arg1.id, arg2.id)
        
        # Check that the framework has the correct number of arguments and attacks
        self.assertEqual(len(af.arguments), 2)
        self.assertEqual(len(af.attacks), 1)
        
        # Check that the attack relation is correct
        self.assertEqual(len(af.get_attackers(arg2.id)), 1)
        self.assertEqual(len(af.get_attacked(arg1.id)), 1)


if __name__ == "__main__":
    unittest.main()