"""
Template Evolution Module (TEM) for GödelOS.

This module implements the TemplateEvolutionModule component (Module 3.3) of the Learning System,
which is responsible for refining and evolving existing LogicTemplates to improve their utility,
generality, or efficiency using evolutionary algorithms.
"""

import random
import logging
import copy
from typing import List, Dict, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager

logger = logging.getLogger(__name__)


@dataclass
class EvolutionConfig:
    """
    Configuration for the template evolution process.
    
    This class defines parameters for the evolutionary algorithm, including
    crossover and mutation rates, population size, and selection strategy.
    """
    population_size: int = 50
    generations: int = 20
    crossover_rate: float = 0.7
    mutation_rate: float = 0.3
    tournament_size: int = 3  # For tournament selection
    elitism_count: int = 2    # Number of best individuals to preserve unchanged
    max_template_premises: int = 5  # Maximum number of premises allowed in a template


@dataclass
class TemplatePerformanceMetrics:
    """
    Performance metrics for a LogicTemplate.
    
    These metrics are retrieved from the MetaKnowledgeBase and used to calculate
    the fitness of a template during evolution.
    """
    template_id: str
    success_rate: float = 0.0  # Ratio of successful applications to total attempts
    utility_score: float = 0.0  # Usefulness in solving problems
    computational_cost: float = 1.0  # Average computational resources used (lower is better)
    times_used: int = 0  # Number of times the template has been used
    
    def calculate_fitness(self, weights: Dict[str, float] = None) -> float:
        """
        Calculate the fitness score for this template based on its performance metrics.
        
        Args:
            weights: Optional dictionary of weights for each metric
                    (default: equal weights)
        
        Returns:
            A fitness score where higher is better
        """
        if weights is None:
            weights = {
                'success_rate': 0.4,
                'utility_score': 0.4,
                'computational_cost': 0.2
            }
        
        # Invert computational cost so lower cost means higher fitness
        inverted_cost = 1.0 / max(self.computational_cost, 0.001)
        
        # Calculate weighted sum
        fitness = (
            weights['success_rate'] * self.success_rate +
            weights['utility_score'] * self.utility_score +
            weights['computational_cost'] * inverted_cost
        )
        
        # Apply a usage factor - templates that have been used more have more reliable metrics
        usage_factor = min(1.0, self.times_used / 10.0)  # Caps at 1.0 after 10 uses
        
        return fitness * usage_factor


class TemplateEvolutionModule:
    """
    Module for evolving LogicTemplates using genetic programming techniques.
    
    This module implements evolutionary algorithms to refine and evolve existing
    LogicTemplates to improve their utility, generality, or efficiency.
    """
    
    def __init__(self, 
                 kr_system_interface: KnowledgeStoreInterface,
                 type_system: TypeSystemManager,
                 mkb_context_id: str = "META_KNOWLEDGE",
                 evolution_config: Optional[EvolutionConfig] = None):
        """
        Initialize the Template Evolution Module.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            type_system: The type system manager for type checking
            mkb_context_id: Context ID for the MetaKnowledgeBase
            evolution_config: Configuration for the evolutionary algorithm
        """
        self.ksi = kr_system_interface
        self.type_system = type_system
        self.mkb_context_id = mkb_context_id
        self.config = evolution_config or EvolutionConfig()
        
    def evolve_population(self, 
                          initial_population_templates: List[AST_Node],
                          generations: Optional[int] = None,
                          population_size: Optional[int] = None,
                          crossover_rate: Optional[float] = None,
                          mutation_rate: Optional[float] = None) -> List[AST_Node]:
        """
        Evolve a population of LogicTemplates to improve their fitness.
        
        Args:
            initial_population_templates: The initial set of templates to evolve
            generations: Number of generations to evolve (overrides config)
            population_size: Size of the population (overrides config)
            crossover_rate: Probability of crossover (overrides config)
            mutation_rate: Probability of mutation (overrides config)
            
        Returns:
            A list of evolved templates, sorted by fitness (best first)
        """
        # Override config parameters if provided
        generations = generations or self.config.generations
        population_size = population_size or self.config.population_size
        crossover_rate = crossover_rate or self.config.crossover_rate
        mutation_rate = mutation_rate or self.config.mutation_rate
        
        # Ensure we have enough templates to start with
        if len(initial_population_templates) < population_size:
            logger.info(f"Initial population size {len(initial_population_templates)} is less than desired population size {population_size}. Cloning templates to reach desired size.")
            # Clone templates until we reach the desired population size
            population = self._initialize_population(initial_population_templates, population_size)
        else:
            population = initial_population_templates[:population_size]
        
        # Main evolutionary loop
        for generation in range(generations):
            logger.info(f"Starting generation {generation+1}/{generations}")
            
            # Evaluate fitness of all templates in the population
            fitness_scores = self._evaluate_population_fitness(population)
            
            # Sort population by fitness
            population_with_fitness = list(zip(population, fitness_scores))
            population_with_fitness.sort(key=lambda x: x[1], reverse=True)
            
            # Log best fitness
            best_template, best_fitness = population_with_fitness[0]
            logger.info(f"Generation {generation+1}: Best fitness = {best_fitness}")
            
            # If this is the final generation, return the sorted population
            if generation == generations - 1:
                # Return templates sorted by fitness
                return [template for template, _ in population_with_fitness]
            
            # Create the next generation
            next_population = []
            
            # Elitism: Keep the best templates unchanged
            for i in range(min(self.config.elitism_count, len(population))):
                next_population.append(population_with_fitness[i][0])
            
            # Fill the rest of the population with offspring
            while len(next_population) < population_size:
                # Selection
                if random.random() < crossover_rate:
                    # Crossover
                    parent1 = self._tournament_selection(population, fitness_scores)
                    parent2 = self._tournament_selection(population, fitness_scores)
                    child = self._crossover(parent1, parent2)
                else:
                    # No crossover, just select one parent
                    child = self._tournament_selection(population, fitness_scores)
                
                # Mutation
                if random.random() < mutation_rate:
                    child = self._mutate(child)
                
                # Add to next generation if valid
                if self._is_valid_template(child):
                    next_population.append(child)
            
            # Update population for next generation
            population = next_population
        
        # This should never be reached due to the return in the loop
        return population
    
    def _initialize_population(self, seed_templates: List[AST_Node], target_size: int) -> List[AST_Node]:
        """
        Initialize a population of templates from seed templates.
        
        If there aren't enough seed templates, this method will clone and slightly
        modify existing ones to reach the target population size.
        
        Args:
            seed_templates: The initial set of templates
            target_size: The desired population size
            
        Returns:
            A list of templates with the target size
        """
        population = seed_templates.copy()
        
        # If we don't have enough templates, clone and mutate existing ones
        while len(population) < target_size:
            # Select a random template from the seed templates
            template_to_clone = random.choice(seed_templates)
            
            # Clone and mutate it slightly
            cloned_template = copy.deepcopy(template_to_clone)
            mutated_template = self._mutate(cloned_template, mutation_strength=0.3)
            
            if self._is_valid_template(mutated_template):
                population.append(mutated_template)
        
        return population
    
    def _evaluate_population_fitness(self, population: List[AST_Node]) -> List[float]:
        """
        Evaluate the fitness of all templates in the population.
        
        Args:
            population: List of template ASTs to evaluate
            
        Returns:
            List of fitness scores corresponding to the templates
        """
        fitness_scores = []
        
        for template in population:
            # Get the template ID or generate one if it doesn't exist
            template_id = self._get_template_id(template)
            
            # Get performance metrics from MKB
            metrics = self._get_template_performance_metrics(template_id)
            
            # Calculate fitness
            fitness = metrics.calculate_fitness()
            fitness_scores.append(fitness)
        
        return fitness_scores
    
    def _get_template_id(self, template: AST_Node) -> str:
        """
        Get the ID of a template from its metadata or generate a new one.
        
        Args:
            template: The template AST
            
        Returns:
            The template ID as a string
        """
        # Check if the template has an ID in its metadata
        if hasattr(template, 'metadata') and 'template_id' in template.metadata:
            return template.metadata['template_id']
        
        # Generate a hash-based ID if no ID exists
        return f"template_{hash(str(template)) % 10000000}"
    
    def _get_template_performance_metrics(self, template_id: str) -> TemplatePerformanceMetrics:
        """
        Retrieve performance metrics for a template from the MetaKnowledgeBase.
        
        Args:
            template_id: The ID of the template
            
        Returns:
            A TemplatePerformanceMetrics object with the metrics
        """
        # Query the MKB for metrics about this template
        # In a real implementation, this would query the actual MKB
        # For now, we'll use some default values or random values for testing
        
        # Try to find metrics in the MKB
        query_pattern = self._create_metrics_query_pattern(template_id)
        query_results = self.ksi.query_statements_match_pattern(
            query_pattern_ast=query_pattern,
            context_ids=[self.mkb_context_id]
        )
        
        # If we found metrics, extract them
        if query_results:
            # Extract metrics from the query results
            # This is a simplified version - in a real implementation,
            # we would parse the AST nodes to extract the actual metrics
            return self._extract_metrics_from_query_results(query_results, template_id)
        
        # If no metrics found, return default metrics
        return TemplatePerformanceMetrics(
            template_id=template_id,
            success_rate=random.uniform(0.1, 0.9),  # For testing only
            utility_score=random.uniform(0.1, 0.9),  # For testing only
            computational_cost=random.uniform(0.1, 2.0),  # For testing only
            times_used=random.randint(0, 20)  # For testing only
        )
    
    def _create_metrics_query_pattern(self, template_id: str) -> AST_Node:
        """
        Create a query pattern to retrieve metrics for a template from the MKB.
        
        Args:
            template_id: The ID of the template
            
        Returns:
            An AST_Node representing the query pattern
        """
        # This is a simplified implementation
        # In a real system, we would create a proper AST query pattern
        # that matches the structure of how metrics are stored in the MKB
        
        # For now, return a dummy pattern
        # In a real implementation, this would be a proper AST query
        return None  # Placeholder
    
    def _extract_metrics_from_query_results(self, query_results: List[Dict[VariableNode, AST_Node]], template_id: str) -> TemplatePerformanceMetrics:
        """
        Extract metrics from query results.
        
        Args:
            query_results: The results from querying the MKB
            template_id: The ID of the template
            
        Returns:
            A TemplatePerformanceMetrics object with the extracted metrics
        """
        # This is a simplified implementation
        # In a real system, we would parse the AST nodes to extract the metrics
        
        # For now, return default metrics
        return TemplatePerformanceMetrics(
            template_id=template_id,
            success_rate=0.5,  # Default value
            utility_score=0.5,  # Default value
            computational_cost=1.0,  # Default value
            times_used=5  # Default value
        )
    
    def _tournament_selection(self, population: List[AST_Node], fitness_scores: List[float]) -> AST_Node:
        """
        Select a template from the population using tournament selection.
        
        Args:
            population: The population of templates
            fitness_scores: The fitness scores corresponding to the templates
            
        Returns:
            The selected template
        """
        # Randomly select tournament_size individuals
        tournament_size = min(self.config.tournament_size, len(population))
        tournament_indices = random.sample(range(len(population)), tournament_size)
        
        # Find the one with the highest fitness
        best_index = tournament_indices[0]
        best_fitness = fitness_scores[best_index]
        
        for idx in tournament_indices[1:]:
            if fitness_scores[idx] > best_fitness:
                best_index = idx
                best_fitness = fitness_scores[idx]
        
        return population[best_index]
    
    def _crossover(self, parent1: AST_Node, parent2: AST_Node) -> AST_Node:
        """
        Perform crossover between two parent templates to create a child template.
        
        Args:
            parent1: The first parent template
            parent2: The second parent template
            
        Returns:
            A new template created by crossover
        """
        # Ensure both parents are ConnectiveNode with IMPLIES type (rule templates)
        if (not isinstance(parent1, ConnectiveNode) or parent1.connective_type != "IMPLIES" or
            not isinstance(parent2, ConnectiveNode) or parent2.connective_type != "IMPLIES"):
            # If not a proper rule template, just return a copy of parent1
            return copy.deepcopy(parent1)
        
        # Create a deep copy of parent1 as the base for the child
        child = copy.deepcopy(parent1)
        
        # Determine crossover type (random choice)
        crossover_type = random.choice(["premise_swap", "conclusion_swap", "premise_merge"])
        
        if crossover_type == "premise_swap":
            # Swap a random premise from parent2 into the child
            # Extract premises from both parents
            child_premises = self._extract_premises(child)
            parent2_premises = self._extract_premises(parent2)
            
            if parent2_premises and len(child_premises) < self.config.max_template_premises:
                # Select a random premise from parent2
                premise_to_add = random.choice(parent2_premises)
                
                # Add it to the child's premises if it's not already there
                if not any(self._are_nodes_equivalent(premise_to_add, p) for p in child_premises):
                    child_premises.append(copy.deepcopy(premise_to_add))
                    
                    # Update the child with the new premises
                    child = self._update_template_premises(child, child_premises)
        
        elif crossover_type == "conclusion_swap":
            # Swap the conclusion from parent2 into the child
            parent2_conclusion = parent2.operands[1]  # In IMPLIES, operands[1] is the conclusion
            
            # Create a new ConnectiveNode with the updated conclusion
            # Instead of trying to modify the tuple directly
            body = child.operands[0]  # Keep the original premises
            new_conclusion = copy.deepcopy(parent2_conclusion)
            
            # Create a new ConnectiveNode with the same body but new conclusion
            child = ConnectiveNode(
                connective_type="IMPLIES",
                operands=[body, new_conclusion],
                type_ref=new_conclusion.type
            )
        
        elif crossover_type == "premise_merge":
            # Merge premises from both parents
            child_premises = self._extract_premises(child)
            parent2_premises = self._extract_premises(parent2)
            
            # Add premises from parent2 that aren't already in child
            for premise in parent2_premises:
                if (not any(self._are_nodes_equivalent(premise, p) for p in child_premises) and 
                    len(child_premises) < self.config.max_template_premises):
                    child_premises.append(copy.deepcopy(premise))
            
            # Update the child with the merged premises
            child = self._update_template_premises(child, child_premises)
        
        return child
    
    def _mutate(self, template: AST_Node, mutation_strength: float = 1.0) -> AST_Node:
        """
        Mutate a template by making small random changes.
        
        Args:
            template: The template to mutate
            mutation_strength: A factor controlling the intensity of mutation (0.0-1.0)
            
        Returns:
            The mutated template
        """
        # Create a deep copy to avoid modifying the original
        mutated = copy.deepcopy(template)
        
        # Ensure it's a ConnectiveNode with IMPLIES type (rule template)
        if not isinstance(mutated, ConnectiveNode) or mutated.connective_type != "IMPLIES":
            # If not a proper rule template, just return it unchanged
            return mutated
        
        # Determine mutation type (random choice, weighted by mutation_strength)
        mutation_types = [
            "add_premise",
            "remove_premise",
            "modify_premise",
            "generalize_constant",
            "specialize_variable"
        ]
        
        # Number of mutations to apply
        num_mutations = max(1, int(mutation_strength * 2))
        
        for _ in range(num_mutations):
            mutation_type = random.choice(mutation_types)
            
            if mutation_type == "add_premise":
                # Add a new premise (this would require access to available predicates)
                # For now, we'll skip this or implement a simplified version
                pass
                
            elif mutation_type == "remove_premise":
                # Extract premises
                premises = self._extract_premises(mutated)
                
                # If there are premises to remove
                if premises and len(premises) > 0:
                    # Remove a random premise by index instead of by value
                    # This avoids issues with object equality
                    premise_idx = random.randrange(len(premises))
                    del premises[premise_idx]
                    
                    # Update the template with the new premises
                    mutated = self._update_template_premises(mutated, premises)
                
            elif mutation_type == "modify_premise":
                # Extract premises
                premises = self._extract_premises(mutated)
                
                # If there are premises to modify
                if premises:
                    # Select a random premise
                    premise_idx = random.randrange(len(premises))
                    
                    # Modify it (simplified: just negate it if it's not already negated)
                    if not self._is_negated(premises[premise_idx]):
                        premises[premise_idx] = self._negate_node(premises[premise_idx])
                        
                        # Update the template with the modified premises
                        mutated = self._update_template_premises(mutated, premises)
            
            elif mutation_type == "generalize_constant":
                # Find a constant in the template and replace it with a variable
                # This is a complex operation that would require traversing the AST
                # For now, we'll implement a simplified version or skip
                pass
                
            elif mutation_type == "specialize_variable":
                # Find a variable in the template and replace it with a constant
                # This is a complex operation that would require traversing the AST
                # For now, we'll implement a simplified version or skip
                pass
        
        return mutated
    
    def _extract_premises(self, template: AST_Node) -> List[AST_Node]:
        """
        Extract the premises from a template.
        
        Args:
            template: The template AST
            
        Returns:
            A list of premise ASTs
        """
        if not isinstance(template, ConnectiveNode) or template.connective_type != "IMPLIES":
            return []
        
        # The first operand of IMPLIES is the body (premises)
        body = template.operands[0]
        
        # If the body is a conjunction (AND), extract all operands
        if isinstance(body, ConnectiveNode) and body.connective_type == "AND":
            return list(body.operands)
        
        # If the body is a single premise, return it as a list
        return [body]
    
    def _update_template_premises(self, template: AST_Node, premises: List[AST_Node]) -> AST_Node:
        """
        Update a template with new premises.
        
        Args:
            template: The template AST
            premises: The new premises
            
        Returns:
            The updated template AST
        """
        if not isinstance(template, ConnectiveNode) or template.connective_type != "IMPLIES":
            return template
        
        # Get the conclusion (second operand of IMPLIES)
        conclusion = template.operands[1]
        
        # Create a new body from the premises
        if len(premises) == 0:
            # Empty premises - this is probably not valid, but we'll handle it
            # by creating a template with a "TRUE" premise
            # In a real implementation, we might want to handle this differently
            boolean_type = conclusion.type  # Assuming conclusion has a boolean type
            true_const = ConstantNode("TRUE", boolean_type)
            body = true_const
        elif len(premises) == 1:
            # Single premise
            body = premises[0]
        else:
            # Multiple premises - create a conjunction
            body = ConnectiveNode(
                connective_type="AND",
                operands=premises,
                type_ref=premises[0].type  # Assuming all premises have compatible types
            )
        
        # Create a new template with the updated body
        return ConnectiveNode(
            connective_type="IMPLIES",
            operands=[body, conclusion],
            type_ref=conclusion.type
        )
    
    def _is_negated(self, node: AST_Node) -> bool:
        """
        Check if a node is a negation.
        
        Args:
            node: The AST node to check
            
        Returns:
            True if the node is a negation, False otherwise
        """
        return (isinstance(node, ConnectiveNode) and 
                node.connective_type == "NOT")
    
    def _negate_node(self, node: AST_Node) -> AST_Node:
        """
        Create a negation of a node.
        
        Args:
            node: The AST node to negate
            
        Returns:
            A new AST node representing the negation
        """
        return ConnectiveNode(
            connective_type="NOT",
            operands=[node],
            type_ref=node.type  # Assuming the type is compatible with negation
        )
    
    def _are_nodes_equivalent(self, node1: AST_Node, node2: AST_Node) -> bool:
        """
        Check if two AST nodes are semantically equivalent.
        
        This is a simplified implementation that just compares string representations.
        A more sophisticated implementation would perform a structural comparison.
        
        Args:
            node1: The first AST node
            node2: The second AST node
            
        Returns:
            True if the nodes are equivalent, False otherwise
        """
        # For now, we'll use a simple string comparison
        # In a real implementation, we would perform a more sophisticated
        # structural comparison that accounts for variable renaming, etc.
        return str(node1) == str(node2)
    
    def _is_valid_template(self, template: AST_Node) -> bool:
        """
        Check if a template is valid.
        
        Args:
            template: The template AST to check
            
        Returns:
            True if the template is valid, False otherwise
        """
        # Check if it's a ConnectiveNode with IMPLIES type
        if not isinstance(template, ConnectiveNode) or template.connective_type != "IMPLIES":
            logger.warning("Invalid template: not an implication")
            return False
        
        # Check if it has exactly two operands
        if len(template.operands) != 2:
            logger.warning(f"Invalid template: wrong number of operands ({len(template.operands)})")
            return False
        
        # Check if the premises are valid
        premises = self._extract_premises(template)
        if len(premises) > self.config.max_template_premises:
            logger.warning(f"Invalid template: too many premises ({len(premises)})")
            return False
        
        # Additional checks could be performed here, such as:
        # - Type checking using self.type_system
        # - Checking for variable consistency
        # - Checking for semantic validity
        
        return True