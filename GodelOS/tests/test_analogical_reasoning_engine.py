"""
Unit tests for the Analogical Reasoning Engine.

This module contains unit tests for the AnalogicalReasoningEngine class, which identifies
structural analogies between a "source" domain and a "target" domain, produces
mappings of correspondences, and supports analogical inference.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Set

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode
)
from godelOS.core_kr.type_system.types import AtomicType, FunctionType
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import ResourceLimits
from godelOS.inference_engine.analogical_reasoning_engine import (
    AnalogicalReasoningEngine, AnalogicalMapping, ObjectMapping,
    PredicateFunctionMapping, RelationInstanceMapping
)


class TestAnalogicalReasoningEngine(unittest.TestCase):
    """Tests for the AnalogicalReasoningEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock KnowledgeStoreInterface
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a mock TypeSystemManager
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Create a mock UnificationEngine
        self.unification_engine = MagicMock(spec=UnificationEngine)
        
        # Create an AnalogicalReasoningEngine with the mocks
        self.are = AnalogicalReasoningEngine(
            self.kr_system_interface,
            ontology_manager=None,
            lexicon_linker=None
        )
        
        # Create types for testing
        self.bool_type = AtomicType("Boolean")
        self.int_type = AtomicType("Integer")
        self.person_type = AtomicType("Person")
        self.planet_type = AtomicType("Planet")
        
        # Create constants for source domain (solar system)
        self.sun = ConstantNode("sun", self.planet_type)
        self.earth = ConstantNode("earth", self.planet_type)
        self.mars = ConstantNode("mars", self.planet_type)
        self.venus = ConstantNode("venus", self.planet_type)
        
        # Create constants for target domain (atom)
        self.nucleus = ConstantNode("nucleus", self.planet_type)
        self.electron = ConstantNode("electron", self.planet_type)
        self.proton = ConstantNode("proton", self.planet_type)
        self.neutron = ConstantNode("neutron", self.planet_type)
        
        # Create predicates/functions
        self.revolves_around = ConstantNode("revolves_around", FunctionType([self.planet_type, self.planet_type], self.bool_type))
        self.orbits = ConstantNode("orbits", FunctionType([self.planet_type, self.planet_type], self.bool_type))
        self.larger_than = ConstantNode("larger_than", FunctionType([self.planet_type, self.planet_type], self.bool_type))
        self.attracts = ConstantNode("attracts", FunctionType([self.planet_type, self.planet_type], self.bool_type))
        
        # Create source domain relations
        self.earth_revolves_sun = ApplicationNode(self.revolves_around, [self.earth, self.sun], self.bool_type)
        self.mars_revolves_sun = ApplicationNode(self.revolves_around, [self.mars, self.sun], self.bool_type)
        self.venus_revolves_sun = ApplicationNode(self.revolves_around, [self.venus, self.sun], self.bool_type)
        self.sun_larger_earth = ApplicationNode(self.larger_than, [self.sun, self.earth], self.bool_type)
        self.sun_attracts_earth = ApplicationNode(self.attracts, [self.sun, self.earth], self.bool_type)
        
        # Create target domain relations
        self.electron_orbits_nucleus = ApplicationNode(self.orbits, [self.electron, self.nucleus], self.bool_type)
        self.proton_in_nucleus = ApplicationNode(self.orbits, [self.proton, self.nucleus], self.bool_type)
        self.nucleus_larger_electron = ApplicationNode(self.larger_than, [self.nucleus, self.electron], self.bool_type)
        self.nucleus_attracts_electron = ApplicationNode(self.attracts, [self.nucleus, self.electron], self.bool_type)
        
        # Create source and target domains
        self.source_domain = {
            self.earth_revolves_sun,
            self.mars_revolves_sun,
            self.venus_revolves_sun,
            self.sun_larger_earth,
            self.sun_attracts_earth
        }
        
        self.target_domain = {
            self.electron_orbits_nucleus,
            self.proton_in_nucleus,
            self.nucleus_larger_electron,
            self.nucleus_attracts_electron
        }
    
    def test_capabilities(self):
        """Test the capabilities of the AnalogicalReasoningEngine."""
        capabilities = self.are.capabilities
        
        self.assertTrue(capabilities["analogical_reasoning"])
        self.assertTrue(capabilities["first_order_logic"])
        self.assertFalse(capabilities["modal_logic"])
        self.assertFalse(capabilities["higher_order_logic"])
    
    def test_can_handle(self):
        """Test the can_handle method."""
        # Create a goal that the engine can handle
        find_analogy = ApplicationNode(
            ConstantNode("FindAnalogy", None),
            [ConstantNode("source", None), ConstantNode("target", None)],
            None
        )
        
        # Create a goal that the engine cannot handle
        cannot_handle = ApplicationNode(
            ConstantNode("SolveEquation", None),
            [ConstantNode("x^2 + 2x + 1 = 0", None)],
            None
        )
        
        # Test can_handle
        self.assertTrue(self.are.can_handle(find_analogy, set()))
        self.assertFalse(self.are.can_handle(cannot_handle, set()))
    
    def test_extract_domain_elements(self):
        """Test the _extract_domain_elements method."""
        # Extract elements from the source domain
        objects, predicates, relations = self.are._extract_domain_elements(self.source_domain)
        
        # Check objects
        self.assertIn(self.sun, objects)
        self.assertIn(self.earth, objects)
        self.assertIn(self.mars, objects)
        self.assertIn(self.venus, objects)
        
        # Check predicates
        self.assertIn(self.revolves_around, predicates)
        self.assertIn(self.larger_than, predicates)
        self.assertIn(self.attracts, predicates)
        
        # Check relations
        self.assertIn(self.earth_revolves_sun, relations)
        self.assertIn(self.sun_larger_earth, relations)
        self.assertIn(self.sun_attracts_earth, relations)
    
    def test_calculate_object_similarity(self):
        """Test the _calculate_object_similarity method."""
        # Test identical objects
        self.assertAlmostEqual(
            self.are._calculate_object_similarity(self.sun, self.sun),
            1.0
        )
        
        # Test objects with same type
        self.assertGreater(
            self.are._calculate_object_similarity(self.sun, self.nucleus),
            0.0
        )
        
        # Test objects with different types
        person = ConstantNode("person", self.person_type)
        self.assertLess(
            self.are._calculate_object_similarity(self.sun, person),
            self.are._calculate_object_similarity(self.sun, self.nucleus)
        )
    
    def test_calculate_predicate_similarity(self):
        """Test the _calculate_predicate_similarity method."""
        # Test identical predicates
        self.assertAlmostEqual(
            self.are._calculate_predicate_similarity(self.revolves_around, self.revolves_around),
            1.0
        )
        
        # Test similar predicates
        self.assertGreater(
            self.are._calculate_predicate_similarity(self.revolves_around, self.orbits),
            0.0
        )
    
    def test_generate_initial_mappings(self):
        """Test the _generate_initial_mappings method."""
        # Extract elements from domains
        source_objects, source_predicates, source_relations = self.are._extract_domain_elements(self.source_domain)
        target_objects, target_predicates, target_relations = self.are._extract_domain_elements(self.target_domain)
        
        # Generate initial mappings
        mappings = self.are._generate_initial_mappings(
            source_objects, target_objects,
            source_predicates, target_predicates,
            source_relations, target_relations
        )
        
        # Check that we got at least one mapping
        self.assertGreaterEqual(len(mappings), 1)
        
        # Check that the mapping has some object and predicate mappings
        mapping = mappings[0]
        self.assertGreater(len(mapping.object_mappings), 0)
        self.assertGreater(len(mapping.predicate_function_mappings), 0)
    
    def test_perform_structural_alignment(self):
        """Test the _perform_structural_alignment method."""
        # Create a simple mapping
        mapping = AnalogicalMapping("source", "target")
        mapping.add_object_mapping(self.sun, self.nucleus, 0.8)
        mapping.add_object_mapping(self.earth, self.electron, 0.7)
        mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        
        # Extract relations from domains
        _, _, source_relations = self.are._extract_domain_elements(self.source_domain)
        _, _, target_relations = self.are._extract_domain_elements(self.target_domain)
        
        # Perform structural alignment
        aligned_mappings = self.are._perform_structural_alignment(
            [mapping], source_relations, target_relations
        )
        
        # Check that we got at least one mapping
        self.assertGreaterEqual(len(aligned_mappings), 1)
        
        # Check that the mapping has some relation mappings
        aligned_mapping = aligned_mappings[0]
        self.assertGreaterEqual(len(aligned_mapping.relation_instance_mappings), 0)
    
    def test_evaluate_structural_consistency(self):
        """Test the _evaluate_structural_consistency method."""
        # Create a mapping with good structural consistency
        good_mapping = AnalogicalMapping("source", "target")
        good_mapping.add_object_mapping(self.sun, self.nucleus, 0.8)
        good_mapping.add_object_mapping(self.earth, self.electron, 0.7)
        good_mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        good_mapping.add_relation_mapping(self.earth_revolves_sun, self.electron_orbits_nucleus)
        
        # Create a mapping with poor structural consistency
        poor_mapping = AnalogicalMapping("source", "target")
        poor_mapping.add_object_mapping(self.sun, self.electron, 0.3)  # Inconsistent mapping
        poor_mapping.add_object_mapping(self.earth, self.nucleus, 0.3)  # Inconsistent mapping
        poor_mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        
        # Extract relations from domains
        _, _, source_relations = self.are._extract_domain_elements(self.source_domain)
        _, _, target_relations = self.are._extract_domain_elements(self.target_domain)
        
        # Evaluate structural consistency
        good_score = self.are._evaluate_structural_consistency(
            good_mapping, source_relations, target_relations
        )
        poor_score = self.are._evaluate_structural_consistency(
            poor_mapping, source_relations, target_relations
        )
        
        # Check that the good mapping has a higher score
        self.assertGreater(good_score, poor_score)
    
    def test_evaluate_semantic_fit(self):
        """Test the _evaluate_semantic_fit method."""
        # Create a mapping with good semantic fit
        good_mapping = AnalogicalMapping("source", "target")
        good_mapping.add_object_mapping(self.sun, self.nucleus, 0.8)
        good_mapping.add_object_mapping(self.earth, self.electron, 0.7)
        good_mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        
        # Create a mapping with poor semantic fit
        poor_mapping = AnalogicalMapping("source", "target")
        poor_mapping.add_object_mapping(self.sun, self.electron, 0.3)
        poor_mapping.add_object_mapping(self.earth, self.nucleus, 0.3)
        poor_mapping.add_predicate_mapping(self.revolves_around, self.larger_than, 0.2)
        
        # Extract objects and predicates from domains
        source_objects, source_predicates, _ = self.are._extract_domain_elements(self.source_domain)
        target_objects, target_predicates, _ = self.are._extract_domain_elements(self.target_domain)
        
        # Evaluate semantic fit
        good_score = self.are._evaluate_semantic_fit(
            good_mapping, source_objects, target_objects, source_predicates, target_predicates
        )
        poor_score = self.are._evaluate_semantic_fit(
            poor_mapping, source_objects, target_objects, source_predicates, target_predicates
        )
        
        # Check that the good mapping has a higher score
        self.assertGreater(good_score, poor_score)
    
    def test_project_expression(self):
        """Test the _project_expression method."""
        # Create a mapping
        mapping = AnalogicalMapping("source", "target")
        mapping.add_object_mapping(self.sun, self.nucleus, 0.8)
        mapping.add_object_mapping(self.earth, self.electron, 0.7)
        mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        mapping.add_predicate_mapping(self.attracts, self.attracts, 1.0)
        
        # Project a simple expression
        source_expr = self.earth_revolves_sun
        projected_expr = self.are._project_expression(source_expr, mapping)
        
        # Check that the projection worked
        self.assertIsNotNone(projected_expr)
        self.assertIsInstance(projected_expr, ApplicationNode)
        self.assertEqual(projected_expr.operator, self.orbits)
        self.assertEqual(projected_expr.arguments[0], self.electron)
        self.assertEqual(projected_expr.arguments[1], self.nucleus)
        
        # Project an expression that can't be fully projected
        source_expr2 = ApplicationNode(self.revolves_around, [self.mars, self.sun], self.bool_type)
        projected_expr2 = self.are._project_expression(source_expr2, mapping)
        
        # Check that the projection failed (mars is not mapped)
        self.assertIsNone(projected_expr2)
    
    def test_compute_analogies(self):
        """Test the compute_analogies method."""
        # Compute analogies between the source and target domains
        mappings = self.are.compute_analogies(self.source_domain, self.target_domain)
        
        # Check that we got at least one mapping
        self.assertGreaterEqual(len(mappings), 1)
        
        # Check that the mapping has some object, predicate, and relation mappings
        mapping = mappings[0]
        self.assertGreater(len(mapping.object_mappings), 0)
        self.assertGreater(len(mapping.predicate_function_mappings), 0)
        
        # Check that the mapping has scores
        self.assertGreaterEqual(mapping.structural_consistency_score, 0.0)
        self.assertGreaterEqual(mapping.semantic_fit_score, 0.0)
        self.assertGreaterEqual(mapping.get_overall_score(), 0.0)
    
    def test_project_inferences(self):
        """Test the project_inferences method."""
        # Create a mapping
        mapping = AnalogicalMapping("source", "target")
        mapping.add_object_mapping(self.sun, self.nucleus, 0.8)
        mapping.add_object_mapping(self.earth, self.electron, 0.7)
        mapping.add_object_mapping(self.mars, self.proton, 0.6)
        mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        mapping.add_predicate_mapping(self.larger_than, self.larger_than, 1.0)
        mapping.add_predicate_mapping(self.attracts, self.attracts, 1.0)
        
        # Create source expressions to project
        source_exprs = {
            self.sun_larger_earth,
            self.sun_attracts_earth
        }
        
        # Project inferences
        inferences = self.are.project_inferences(mapping, source_exprs)
        
        # Check that we got the expected number of inferences
        self.assertEqual(len(inferences), 2)
        
        # Check that the inferences are valid
        for inference in inferences:
            self.assertIsInstance(inference, ApplicationNode)
            
            # Check that the inference uses mapped objects
            for arg in inference.arguments:
                self.assertIn(arg, [self.nucleus, self.electron, self.proton])
    
    def test_analyze_goal(self):
        """Test the _analyze_goal method."""
        # Create a find_analogy goal
        find_analogy = ApplicationNode(
            ConstantNode("FindAnalogy", None),
            [ConstantNode("source", None), ConstantNode("target", None)],
            None
        )
        
        # Create a project_inference goal
        project_inference = ApplicationNode(
            ConstantNode("ProjectInference", None),
            [ConstantNode("mapping", None), ConstantNode("source_expr", None)],
            None
        )
        
        # Analyze the goals
        task_type1, params1 = self.are._analyze_goal(find_analogy)
        task_type2, params2 = self.are._analyze_goal(project_inference)
        
        # Check the task types
        self.assertEqual(task_type1, "find_analogy")
        self.assertEqual(task_type2, "project_inference")
        
        # Check the parameters
        self.assertEqual(params1['source_id'], find_analogy.arguments[0])
        self.assertEqual(params1['target_id'], find_analogy.arguments[1])
        self.assertEqual(params2['mapping_id'], project_inference.arguments[0])
        self.assertEqual(params2['source_expr_id'], project_inference.arguments[1])
    
    def test_create_analogy_proof_steps(self):
        """Test the _create_analogy_proof_steps method."""
        # Create a mapping
        mapping = AnalogicalMapping("source", "target")
        mapping.add_object_mapping(self.sun, self.nucleus, 0.8)
        mapping.add_object_mapping(self.earth, self.electron, 0.7)
        mapping.add_predicate_mapping(self.revolves_around, self.orbits, 0.9)
        mapping.structural_consistency_score = 0.8
        mapping.semantic_fit_score = 0.7
        
        # Create proof steps
        proof_steps = self.are._create_analogy_proof_steps(
            mapping, self.source_domain, self.target_domain
        )
        
        # Check that we got some proof steps
        self.assertGreater(len(proof_steps), 0)
        
        # Check that the proof steps are valid
        for step in proof_steps:
            self.assertIsNotNone(step.formula)
            self.assertIsNotNone(step.rule_name)
            self.assertIsInstance(step.premises, list)
            self.assertIsNotNone(step.explanation)


if __name__ == '__main__':
    unittest.main()