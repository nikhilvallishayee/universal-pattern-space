"""
Unit tests for the TemplateEvolutionModule component.

This module contains tests for the Template Evolution Module (TEM) component
of the Learning System.
"""

import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Set, Tuple

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.learning_system.template_evolution_module import (
    TemplateEvolutionModule,
    EvolutionConfig,
    TemplatePerformanceMetrics
)


class TestTemplateEvolutionModule(unittest.TestCase):
    """Test cases for the TemplateEvolutionModule class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.kr_system_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Set up type system mock
        self.type_system.get_type.side_effect = self._mock_get_type
        
        # Create EvolutionConfig with smaller values for testing
        self.evolution_config = EvolutionConfig(
            population_size=10,
            generations=5,
            crossover_rate=0.7,
            mutation_rate=0.3,
            tournament_size=2,
            elitism_count=1,
            max_template_premises=3
        )
        
        # Create TemplateEvolutionModule instance
        self.tem = TemplateEvolutionModule(
            kr_system_interface=self.kr_system_interface,
            type_system=self.type_system,
            mkb_context_id="TEST_META_KNOWLEDGE",
            evolution_config=self.evolution_config
        )
    
    def _mock_get_type(self, type_name):
        """Mock implementation of type_system.get_type."""
        mock_type = MagicMock()
        mock_type.name = type_name
        return mock_type
    
    def _create_ast_node(self, predicate, args):
        """Helper method to create an ApplicationNode."""
        predicate_type = self._mock_get_type("Predicate")
        boolean_type = self._mock_get_type("Boolean")
        
        predicate_node = ConstantNode(predicate, predicate_type)
        arg_nodes = []
        
        for arg in args:
            if isinstance(arg, str) and arg.startswith("?"):
                # It's a variable
                var_id = int(arg[2:]) if len(arg) > 2 else 1  # Extract ID from "?V1", "?V2", etc.
                var_type = self._mock_get_type("Entity")
                arg_nodes.append(VariableNode(arg, var_id, var_type))
            elif isinstance(arg, VariableNode):
                # It's already a VariableNode
                arg_nodes.append(arg)
            else:
                # It's a constant
                const_type = self._mock_get_type("Entity")
                arg_nodes.append(ConstantNode(arg, const_type))
        
        return ApplicationNode(predicate_node, arg_nodes, boolean_type)
    
    def _create_template(self, premise_predicates, conclusion_predicate, premise_args_list, conclusion_args):
        """Helper method to create a template (rule) AST."""
        boolean_type = self._mock_get_type("Boolean")
        
        # Create premises
        premises = []
        for predicate, args in zip(premise_predicates, premise_args_list):
            premises.append(self._create_ast_node(predicate, args))
        
        # Create conclusion
        conclusion = self._create_ast_node(conclusion_predicate, conclusion_args)
        
        # Create body (premises)
        if not premises:
            body = ConstantNode("TRUE", boolean_type)
        elif len(premises) == 1:
            body = premises[0]
        else:
            body = ConnectiveNode(
                connective_type="AND",
                operands=premises,
                type_ref=boolean_type
            )
        
        # Create rule (body -> conclusion)
        return ConnectiveNode(
            connective_type="IMPLIES",
            operands=[body, conclusion],
            type_ref=boolean_type
        )
    
    def test_evolution_config(self):
        """Test the EvolutionConfig class."""
        config = EvolutionConfig(
            population_size=50,
            generations=20,
            crossover_rate=0.8,
            mutation_rate=0.2,
            tournament_size=3,
            elitism_count=2,
            max_template_premises=5
        )
        
        self.assertEqual(config.population_size, 50)
        self.assertEqual(config.generations, 20)
        self.assertEqual(config.crossover_rate, 0.8)
        self.assertEqual(config.mutation_rate, 0.2)
        self.assertEqual(config.tournament_size, 3)
        self.assertEqual(config.elitism_count, 2)
        self.assertEqual(config.max_template_premises, 5)
    
    def test_template_performance_metrics(self):
        """Test the TemplatePerformanceMetrics class."""
        metrics = TemplatePerformanceMetrics(
            template_id="test_template_1",
            success_rate=0.8,
            utility_score=0.7,
            computational_cost=0.5,
            times_used=15
        )
        
        self.assertEqual(metrics.template_id, "test_template_1")
        self.assertEqual(metrics.success_rate, 0.8)
        self.assertEqual(metrics.utility_score, 0.7)
        self.assertEqual(metrics.computational_cost, 0.5)
        self.assertEqual(metrics.times_used, 15)
        
        # Test calculate_fitness with default weights
        fitness = metrics.calculate_fitness()
        self.assertGreater(fitness, 0)
        
        # Test calculate_fitness with custom weights
        custom_weights = {
            'success_rate': 0.5,
            'utility_score': 0.3,
            'computational_cost': 0.2
        }
        fitness_custom = metrics.calculate_fitness(weights=custom_weights)
        self.assertGreater(fitness_custom, 0)
        
        # Test that usage factor affects fitness
        metrics_low_usage = TemplatePerformanceMetrics(
            template_id="test_template_2",
            success_rate=0.8,
            utility_score=0.7,
            computational_cost=0.5,
            times_used=2  # Low usage
        )
        fitness_low_usage = metrics_low_usage.calculate_fitness()
        self.assertLess(fitness_low_usage, fitness)  # Lower usage should result in lower fitness
    
    def test_initialization(self):
        """Test the initialization of the TemplateEvolutionModule."""
        self.assertEqual(self.tem.ksi, self.kr_system_interface)
        self.assertEqual(self.tem.type_system, self.type_system)
        self.assertEqual(self.tem.mkb_context_id, "TEST_META_KNOWLEDGE")
        self.assertEqual(self.tem.config, self.evolution_config)
        
        # Test initialization with default config
        tem_default_config = TemplateEvolutionModule(
            kr_system_interface=self.kr_system_interface,
            type_system=self.type_system
        )
        self.assertIsNotNone(tem_default_config.config)
        self.assertIsInstance(tem_default_config.config, EvolutionConfig)
    
    def test_extract_premises(self):
        """Test the _extract_premises method."""
        # Create a template with multiple premises
        template = self._create_template(
            premise_predicates=["isHuman", "isAdult"],
            conclusion_predicate="canVote",
            premise_args_list=[["?x"], ["?x"]],
            conclusion_args=["?x"]
        )
        
        # Extract premises
        premises = self.tem._extract_premises(template)
        
        # Verify that we got two premises
        self.assertEqual(len(premises), 2)
        
        # Create a template with a single premise
        template_single = self._create_template(
            premise_predicates=["isHuman"],
            conclusion_predicate="isMortal",
            premise_args_list=[["?x"]],
            conclusion_args=["?x"]
        )
        
        # Extract premises
        premises_single = self.tem._extract_premises(template_single)
        
        # Verify that we got one premise
        self.assertEqual(len(premises_single), 1)
        
        # Create a template with no premises
        template_no_premises = self._create_template(
            premise_predicates=[],
            conclusion_predicate="isTrue",
            premise_args_list=[],
            conclusion_args=["statement1"]
        )
        
        # Extract premises
        premises_none = self.tem._extract_premises(template_no_premises)
        
        # Verify that we got one premise (TRUE constant)
        self.assertEqual(len(premises_none), 1)
        
        # Test with a non-template AST
        non_template = self._create_ast_node("test", ["arg1"])
        premises_invalid = self.tem._extract_premises(non_template)
        self.assertEqual(len(premises_invalid), 0)
    
    def test_update_template_premises(self):
        """Test the _update_template_premises method."""
        # Create a template
        template = self._create_template(
            premise_predicates=["isHuman"],
            conclusion_predicate="isMortal",
            premise_args_list=[["?x"]],
            conclusion_args=["?x"]
        )
        
        # Create new premises
        new_premise1 = self._create_ast_node("isRational", ["?x"])
        new_premise2 = self._create_ast_node("hasLifespan", ["?x", "finite"])
        
        # Update template with new premises
        updated_template = self.tem._update_template_premises(template, [new_premise1, new_premise2])
        
        # Verify that the template was updated correctly
        self.assertIsInstance(updated_template, ConnectiveNode)
        self.assertEqual(updated_template.connective_type, "IMPLIES")
        
        # The body should now be a conjunction with two premises
        body = updated_template.operands[0]
        self.assertIsInstance(body, ConnectiveNode)
        self.assertEqual(body.connective_type, "AND")
        self.assertEqual(len(body.operands), 2)
        
        # Test updating with empty premises
        empty_template = self.tem._update_template_premises(template, [])
        
        # Verify that the template was updated with a TRUE premise
        self.assertIsInstance(empty_template, ConnectiveNode)
        self.assertEqual(empty_template.connective_type, "IMPLIES")
        
        # The body should be a TRUE constant
        empty_body = empty_template.operands[0]
        self.assertIsInstance(empty_body, ConstantNode)
        self.assertEqual(empty_body.name, "TRUE")
        
        # Test with a non-template AST
        non_template = self._create_ast_node("test", ["arg1"])
        updated_non_template = self.tem._update_template_premises(non_template, [new_premise1])
        self.assertEqual(updated_non_template, non_template)  # Should return the original AST unchanged
    
    def test_is_valid_template(self):
        """Test the _is_valid_template method."""
        # Create a valid template
        valid_template = self._create_template(
            premise_predicates=["isHuman"],
            conclusion_predicate="isMortal",
            premise_args_list=[["?x"]],
            conclusion_args=["?x"]
        )
        
        # Test valid template
        self.assertTrue(self.tem._is_valid_template(valid_template))
        
        # Create a template with too many premises
        many_premises_template = self._create_template(
            premise_predicates=["p1", "p2", "p3", "p4"],  # 4 premises, max is 3
            conclusion_predicate="conclusion",
            premise_args_list=[["?x"], ["?x"], ["?x"], ["?x"]],
            conclusion_args=["?x"]
        )
        
        # Test template with too many premises
        self.assertFalse(self.tem._is_valid_template(many_premises_template))
        
        # Test with a non-template AST
        non_template = self._create_ast_node("test", ["arg1"])
        self.assertFalse(self.tem._is_valid_template(non_template))
    
    def test_tournament_selection(self):
        """Test the _tournament_selection method."""
        # Create a population of templates
        population = [
            self._create_template(
                premise_predicates=["isHuman"],
                conclusion_predicate="isMortal",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            ),
            self._create_template(
                premise_predicates=["isHuman", "isAdult"],
                conclusion_predicate="canVote",
                premise_args_list=[["?x"], ["?x"]],
                conclusion_args=["?x"]
            ),
            self._create_template(
                premise_predicates=["isBird"],
                conclusion_predicate="canFly",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            )
        ]
        
        # Create fitness scores (higher is better)
        fitness_scores = [0.5, 0.8, 0.3]
        
        # Set a fixed tournament size
        self.tem.config.tournament_size = 2
        
        # Mock random.sample to always select indices 0 and 1
        with patch('random.sample', return_value=[0, 1]):
            # The tournament should select the template with the highest fitness among indices 0 and 1
            selected = self.tem._tournament_selection(population, fitness_scores)
            self.assertEqual(selected, population[1])  # Index 1 has the highest fitness (0.8)
        
        # Mock random.sample to always select indices 1 and 2
        with patch('random.sample', return_value=[1, 2]):
            # The tournament should select the template with the highest fitness among indices 1 and 2
            selected = self.tem._tournament_selection(population, fitness_scores)
            self.assertEqual(selected, population[1])  # Index 1 has the highest fitness (0.8)
        
        # Mock random.sample to always select indices 0 and 2
        with patch('random.sample', return_value=[0, 2]):
            # The tournament should select the template with the highest fitness among indices 0 and 2
            selected = self.tem._tournament_selection(population, fitness_scores)
            self.assertEqual(selected, population[0])  # Index 0 has the higher fitness (0.5 > 0.3)
    
    def test_crossover(self):
        """Test the _crossover method."""
        # Create parent templates
        parent1 = self._create_template(
            premise_predicates=["isHuman"],
            conclusion_predicate="isMortal",
            premise_args_list=[["?x"]],
            conclusion_args=["?x"]
        )
        
        parent2 = self._create_template(
            premise_predicates=["isBird"],
            conclusion_predicate="canFly",
            premise_args_list=[["?x"]],
            conclusion_args=["?x"]
        )
        
        # Test premise_swap crossover
        with patch('random.choice', return_value="premise_swap"):
            child = self.tem._crossover(parent1, parent2)
            
            # The child should be a valid template
            self.assertTrue(self.tem._is_valid_template(child))
            
            # Extract premises from the child
            child_premises = self.tem._extract_premises(child)
            
            # The child should have premises from both parents
            self.assertGreaterEqual(len(child_premises), 1)
        
        # Test conclusion_swap crossover
        with patch('random.choice', return_value="conclusion_swap"):
            child = self.tem._crossover(parent1, parent2)
            
            # The child should be a valid template
            self.assertTrue(self.tem._is_valid_template(child))
            
            # The child should have parent1's premises and parent2's conclusion
            child_premises = self.tem._extract_premises(child)
            parent1_premises = self.tem._extract_premises(parent1)
            
            # Check that the premises are from parent1
            self.assertEqual(len(child_premises), len(parent1_premises))
            
            # Check that the conclusion is from parent2
            self.assertEqual(child.operands[1].operator.name, "canFly")
        
        # Test premise_merge crossover
        with patch('random.choice', return_value="premise_merge"):
            child = self.tem._crossover(parent1, parent2)
            
            # The child should be a valid template
            self.assertTrue(self.tem._is_valid_template(child))
            
            # Extract premises from the child
            child_premises = self.tem._extract_premises(child)
            
            # The child should have premises from both parents
            self.assertGreaterEqual(len(child_premises), 1)
        
        # Test crossover with a non-template parent
        non_template = self._create_ast_node("test", ["arg1"])
        child = self.tem._crossover(non_template, parent2)
        
        # Should return a copy of parent1 if it's not a valid template
        self.assertIsNot(child, non_template)  # Should be a copy, not the same object
        self.assertIsInstance(child, AST_Node)
    
    def test_mutate(self):
        """Test the _mutate method."""
        # Create a template to mutate
        template = self._create_template(
            premise_predicates=["isHuman", "isAdult"],
            conclusion_predicate="canVote",
            premise_args_list=[["?x"], ["?x"]],
            conclusion_args=["?x"]
        )
        
        # Test mutation with remove_premise
        with patch('random.choice', return_value="remove_premise"):
            mutated = self.tem._mutate(template)
            
            # The mutated template should be valid
            self.assertTrue(self.tem._is_valid_template(mutated))
            
            # Extract premises from the original and mutated templates
            original_premises = self.tem._extract_premises(template)
            mutated_premises = self.tem._extract_premises(mutated)
            
            # The mutated template should have fewer premises
            self.assertLessEqual(len(mutated_premises), len(original_premises))
        
        # Test mutation with modify_premise
        with patch('random.choice', return_value="modify_premise"):
            # Mock _is_negated to always return False
            with patch.object(self.tem, '_is_negated', return_value=False):
                mutated = self.tem._mutate(template)
                
                # The mutated template should be valid
                self.assertTrue(self.tem._is_valid_template(mutated))
        
        # Test mutation with a non-template
        non_template = self._create_ast_node("test", ["arg1"])
        mutated_non_template = self.tem._mutate(non_template)
        
        # Should return a copy of the original if it's not a valid template
        self.assertIsNot(mutated_non_template, non_template)  # Should be a copy, not the same object
        self.assertIsInstance(mutated_non_template, AST_Node)
    
    def test_initialize_population(self):
        """Test the _initialize_population method."""
        # Create seed templates
        seed_templates = [
            self._create_template(
                premise_predicates=["isHuman"],
                conclusion_predicate="isMortal",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            ),
            self._create_template(
                premise_predicates=["isBird"],
                conclusion_predicate="canFly",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            )
        ]
        
        # Initialize a population with more templates than seeds
        target_size = 5
        population = self.tem._initialize_population(seed_templates, target_size)
        
        # Verify that the population has the target size
        self.assertEqual(len(population), target_size)
        
        # Verify that all templates in the population are valid
        for template in population:
            self.assertTrue(self.tem._is_valid_template(template))
    
    def test_evaluate_population_fitness(self):
        """Test the _evaluate_population_fitness method."""
        # Create a population of templates
        population = [
            self._create_template(
                premise_predicates=["isHuman"],
                conclusion_predicate="isMortal",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            ),
            self._create_template(
                premise_predicates=["isBird"],
                conclusion_predicate="canFly",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            )
        ]
        
        # Mock _get_template_performance_metrics to return fixed metrics
        mock_metrics1 = TemplatePerformanceMetrics(
            template_id="template_1",
            success_rate=0.8,
            utility_score=0.7,
            computational_cost=0.5,
            times_used=15
        )
        
        mock_metrics2 = TemplatePerformanceMetrics(
            template_id="template_2",
            success_rate=0.6,
            utility_score=0.5,
            computational_cost=1.0,
            times_used=10
        )
        
        with patch.object(self.tem, '_get_template_performance_metrics', side_effect=[mock_metrics1, mock_metrics2]):
            # Evaluate the population fitness
            fitness_scores = self.tem._evaluate_population_fitness(population)
            
            # Verify that we got fitness scores for all templates
            self.assertEqual(len(fitness_scores), len(population))
            
            # Verify that the fitness scores are positive
            for score in fitness_scores:
                self.assertGreater(score, 0)
    
    def test_evolve_population(self):
        """Test the evolve_population method."""
        # Create initial population
        initial_population = [
            self._create_template(
                premise_predicates=["isHuman"],
                conclusion_predicate="isMortal",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            ),
            self._create_template(
                premise_predicates=["isBird"],
                conclusion_predicate="canFly",
                premise_args_list=[["?x"]],
                conclusion_args=["?x"]
            )
        ]
        
        # Mock _evaluate_population_fitness to return fixed fitness scores
        # First generation: [0.7, 0.5]
        # Second generation: [0.8, 0.6, 0.4, 0.3]
        with patch.object(self.tem, '_evaluate_population_fitness', side_effect=[[0.7, 0.5], [0.8, 0.6, 0.4, 0.3]]):
            # Mock _tournament_selection to return a fixed template
            with patch.object(self.tem, '_tournament_selection', return_value=initial_population[0]):
                # Mock _crossover to return a fixed template
                with patch.object(self.tem, '_crossover', return_value=initial_population[0]):
                    # Mock _mutate to return a fixed template
                    with patch.object(self.tem, '_mutate', return_value=initial_population[0]):
                        # Mock _is_valid_template to always return True
                        with patch.object(self.tem, '_is_valid_template', return_value=True):
                            # Evolve the population
                            evolved_population = self.tem.evolve_population(
                                initial_population_templates=initial_population,
                                generations=2,
                                population_size=4,
                                crossover_rate=0.7,
                                mutation_rate=0.3
                            )
                            
                            # Verify that we got the expected number of templates
                            self.assertEqual(len(evolved_population), 4)
                            
                            # Verify that all templates in the evolved population are valid
                            for template in evolved_population:
                                self.assertIsInstance(template, AST_Node)


if __name__ == '__main__':
    unittest.main()