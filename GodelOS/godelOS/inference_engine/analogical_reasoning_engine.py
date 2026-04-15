"""
Analogical Reasoning Engine for the Inference Engine Architecture.

This module implements the AnalogicalReasoningEngine class, which identifies
structural analogies between a "source" domain and a "target" domain, produces
mappings of correspondences, and supports analogical inference.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, DefaultDict, FrozenSet
import time
import logging
from dataclasses import dataclass, field
from collections import defaultdict
import heapq

from godelOS.core_kr.ast.nodes import (
    AST_Node, VariableNode, ConstantNode, ApplicationNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ObjectMapping:
    """
    A mapping between objects in the source and target domains.
    
    This class represents a mapping between an object in the source domain
    and an object in the target domain, with a similarity score.
    """
    
    source_object: ConstantNode
    """The object in the source domain."""
    
    target_object: ConstantNode
    """The object in the target domain."""
    
    similarity_score: float
    """The similarity score between the objects."""


@dataclass
class PredicateFunctionMapping:
    """
    A mapping between predicates or functions in the source and target domains.
    
    This class represents a mapping between a predicate or function in the source domain
    and a predicate or function in the target domain, with a similarity score.
    """
    
    source_symbol: AST_Node
    """The predicate or function in the source domain."""
    
    target_symbol: AST_Node
    """The predicate or function in the target domain."""
    
    similarity_score: float
    """The similarity score between the predicates or functions."""


@dataclass
class RelationInstanceMapping:
    """
    A mapping between relation instances in the source and target domains.
    
    This class represents a mapping between a specific ground fact in the source domain
    and a specific ground fact in the target domain.
    """
    
    source_fact: ApplicationNode
    """The ground fact in the source domain."""
    
    target_fact: ApplicationNode
    """The ground fact in the target domain."""


@dataclass
class AnalogicalMapping:
    """
    A mapping of correspondences between a source domain and a target domain.
    
    This class encapsulates the mappings between objects, predicates/functions,
    and relation instances in the source and target domains, along with scores
    for the quality of the mapping.
    """
    
    source_domain_id: str
    """The ID of the source domain."""
    
    target_domain_id: str
    """The ID of the target domain."""
    
    object_mappings: List[ObjectMapping] = field(default_factory=list)
    """Mappings between objects in the source and target domains."""
    
    predicate_function_mappings: List[PredicateFunctionMapping] = field(default_factory=list)
    """Mappings between predicates or functions in the source and target domains."""
    
    relation_instance_mappings: List[RelationInstanceMapping] = field(default_factory=list)
    """Mappings between relation instances in the source and target domains."""
    
    structural_consistency_score: float = 0.0
    """Score for the structural consistency of the mapping."""
    
    semantic_fit_score: float = 0.0
    """Score for the semantic fit of the mapping."""
    
    def get_overall_score(self) -> float:
        """
        Get the overall score for this mapping.
        
        Returns:
            The overall score, which is a weighted combination of the structural
            consistency score and the semantic fit score
        """
        # Simple weighted average, could be more sophisticated
        return 0.7 * self.structural_consistency_score + 0.3 * self.semantic_fit_score

    def get_object_mapping(self, source_object: ConstantNode) -> Optional[ConstantNode]:
        """
        Get the target object mapped to a source object.
        
        Args:
            source_object: The source object to find the mapping for
            
        Returns:
            The target object mapped to the source object, or None if no mapping exists
        """
        for mapping in self.object_mappings:
            if mapping.source_object == source_object:
                return mapping.target_object
        return None

    def get_predicate_mapping(self, source_symbol: AST_Node) -> Optional[AST_Node]:
        """
        Get the target predicate/function mapped to a source predicate/function.
        
        Args:
            source_symbol: The source predicate/function to find the mapping for
            
        Returns:
            The target predicate/function mapped to the source predicate/function,
            or None if no mapping exists
        """
        for mapping in self.predicate_function_mappings:
            if mapping.source_symbol == source_symbol:
                return mapping.target_symbol
        return None

    def add_object_mapping(self, source_obj: ConstantNode, target_obj: ConstantNode, score: float) -> None:
        """
        Add an object mapping to this analogical mapping.
        
        Args:
            source_obj: The source object
            target_obj: The target object
            score: The similarity score
        """
        # Check if mapping already exists
        for mapping in self.object_mappings:
            if mapping.source_object == source_obj:
                # Update existing mapping
                mapping.target_object = target_obj
                mapping.similarity_score = score
                return
                
        # Add new mapping
        self.object_mappings.append(ObjectMapping(source_obj, target_obj, score))

    def add_predicate_mapping(self, source_pred: AST_Node, target_pred: AST_Node, score: float) -> None:
        """
        Add a predicate/function mapping to this analogical mapping.
        
        Args:
            source_pred: The source predicate/function
            target_pred: The target predicate/function
            score: The similarity score
        """
        # Check if mapping already exists
        for mapping in self.predicate_function_mappings:
            if mapping.source_symbol == source_pred:
                # Update existing mapping
                mapping.target_symbol = target_pred
                mapping.similarity_score = score
                return
                
        # Add new mapping
        self.predicate_function_mappings.append(
            PredicateFunctionMapping(source_pred, target_pred, score)
        )

    def add_relation_mapping(self, source_fact: ApplicationNode, target_fact: ApplicationNode) -> None:
        """
        Add a relation instance mapping to this analogical mapping.
        
        Args:
            source_fact: The source relation instance
            target_fact: The target relation instance
        """
        # Check if mapping already exists
        for mapping in self.relation_instance_mappings:
            if mapping.source_fact == source_fact:
                # Update existing mapping
                mapping.target_fact = target_fact
                return
                
        # Add new mapping
        self.relation_instance_mappings.append(RelationInstanceMapping(source_fact, target_fact))

class AnalogicalReasoningEngine(BaseProver):
    """
    Engine for analogical reasoning.
    
    This class identifies structural analogies between a "source" domain and a
    "target" domain, produces mappings of correspondences, and supports analogical
    inference.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface, 
                ontology_manager: Any = None, lexicon_linker: Any = None):
        """
        Initialize the analogical reasoning engine.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            ontology_manager: Optional manager for ontological information
            lexicon_linker: Optional linker for lexical information
        """
        self.kr_system_interface = kr_system_interface
        self.ontology_manager = ontology_manager
        self.lexicon_linker = lexicon_linker
    
    @property
    def name(self) -> str:
        """Get the name of this prover."""
        return "AnalogicalReasoningEngine"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get the capabilities of this prover."""
        capabilities = super().capabilities.copy()
        capabilities.update({
            "analogical_reasoning": True,
            "first_order_logic": True  # For representing domains
        })
        return capabilities
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """
        Determine if this prover can handle the given goal and context.
        
        The analogical reasoning engine can handle goals that involve finding
        analogies or making analogical inferences.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            
        Returns:
            True if this prover can handle the given goal and context, False otherwise
        """
        # Check if the goal is an application with a predicate that suggests analogical reasoning
        if isinstance(goal_ast, ApplicationNode):
            op = goal_ast.operator
            if hasattr(op, 'name') and isinstance(op.name, str):
                # Check for predicates indicating analogical reasoning tasks
                analogical_predicates = {
                    'FindAnalogy', 'AnalogicalInference', 'StructuralMapping',
                    'FindMapping', 'ProjectAnalogy', 'TransferKnowledge'
                }
                
                if op.name in analogical_predicates or 'analog' in op.name.lower():
                    return True
                
                # Check for specific forms like "FindAnalogicalMapping(source, target)"
                if op.name == 'FindAnalogicalMapping' and len(goal_ast.arguments) == 2:
                    return True
                
                # Check for specific forms like "ProjectInference(mapping, source_expr)"
                if op.name == 'ProjectInference' and len(goal_ast.arguments) >= 2:
                    return True
        
        return False
    
    def compute_analogies(self, source_domain_asts: Set[AST_Node], target_domain_asts: Set[AST_Node],
                        config_params: Optional[Dict[str, Any]] = None) -> List[AnalogicalMapping]:
        """
        Compute analogies between source and target domains.
        
        This method implements the full analogical mapping algorithm, including:
        1. Identifying potential pairings of individual items
        2. Performing systematicity and structural alignment
        3. Evaluating and selecting the best mappings
        
        Args:
            source_domain_asts: The ASTs constituting the source domain
            target_domain_asts: The ASTs constituting the target domain
            config_params: Optional configuration parameters
            
        Returns:
            A list of analogical mappings, ordered by quality
        """
        logger.info(f"Computing analogies between source domain ({len(source_domain_asts)} ASTs) "
                   f"and target domain ({len(target_domain_asts)} ASTs)")
        
        # Default configuration parameters
        if config_params is None:
            config_params = {}
        
        max_mappings = config_params.get('max_mappings', 5)
        structural_weight = config_params.get('structural_weight', 0.7)
        semantic_weight = config_params.get('semantic_weight', 0.3)
        
        # Extract objects, predicates, and relations from domains
        source_objects, source_predicates, source_relations = self._extract_domain_elements(source_domain_asts)
        target_objects, target_predicates, target_relations = self._extract_domain_elements(target_domain_asts)
        
        logger.debug(f"Source domain: {len(source_objects)} objects, {len(source_predicates)} predicates, "
                    f"{len(source_relations)} relations")
        logger.debug(f"Target domain: {len(target_objects)} objects, {len(target_predicates)} predicates, "
                    f"{len(target_relations)} relations")
        
        # Generate initial candidate mappings
        candidate_mappings = self._generate_initial_mappings(
            source_objects, target_objects,
            source_predicates, target_predicates,
            source_relations, target_relations
        )
        
        # Perform structural alignment
        aligned_mappings = self._perform_structural_alignment(
            candidate_mappings,
            source_relations,
            target_relations
        )
        
        # Evaluate mappings
        evaluated_mappings = []
        for mapping in aligned_mappings:
            # Calculate structural consistency score
            structural_score = self._evaluate_structural_consistency(
                mapping, source_relations, target_relations
            )
            
            # Calculate semantic fit score
            semantic_score = self._evaluate_semantic_fit(
                mapping, source_objects, target_objects,
                source_predicates, target_predicates
            )
            
            # Update scores in the mapping
            mapping.structural_consistency_score = structural_score
            mapping.semantic_fit_score = semantic_score
            
            evaluated_mappings.append(mapping)
        
        # Sort mappings by overall score
        evaluated_mappings.sort(key=lambda m: m.get_overall_score(), reverse=True)
        
        # Return the top mappings
        return evaluated_mappings[:max_mappings]
    
    def project_inferences(self, mapping: AnalogicalMapping,
                         source_expressions_to_project: Set[AST_Node]) -> List[AST_Node]:
        """
        Project inferences from the source domain to the target domain.
        
        This method takes an analogical mapping and a set of source expressions,
        and generates candidate inferences in the target domain.
        
        Args:
            mapping: The analogical mapping to use
            source_expressions_to_project: The source expressions to project
            
        Returns:
            A list of candidate inferences in the target domain
        """
        logger.info(f"Projecting inferences from {len(source_expressions_to_project)} source expressions")
        
        projected_inferences = []
        
        for source_expr in source_expressions_to_project:
            # Project the expression to the target domain
            projected_expr = self._project_expression(source_expr, mapping)
            
            if projected_expr is not None:
                projected_inferences.append(projected_expr)
                logger.debug(f"Projected: {source_expr} -> {projected_expr}")
            else:
                logger.debug(f"Could not project: {source_expr}")
        
        return projected_inferences
    
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node],
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Attempt to prove a goal using analogical reasoning.
        
        This method analyzes the goal to determine the analogical reasoning task,
        extracts the source and target domains from the context, computes analogies,
        and potentially projects inferences.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            resources: Optional resource limits for the proof attempt
            
        Returns:
            A ProofObject representing the result of the proof attempt
        """
        start_time = time.time()
        
        # Set default resource limits if none provided
        if resources is None:
            resources = ResourceLimits(time_limit_ms=10000, depth_limit=100, nodes_limit=10000)
        
        logger.info(f"AnalogicalReasoningEngine attempting to prove: {goal_ast}")
        logger.info(f"Context size: {len(context_asts)}")
        
        try:
            # Analyze the goal to determine the task
            task_type, task_params = self._analyze_goal(goal_ast)
            
            if task_type == "find_analogy":
                # Extract source and target domains from the context
                source_domain, target_domain = self._extract_domains(context_asts, task_params)
                
                # Compute analogies
                mappings = self.compute_analogies(source_domain, target_domain)
                
                if not mappings:
                    # No analogies found
                    return ProofObject.create_failure(
                        status_message="No analogical mappings found",
                        inference_engine_used=self.name,
                        time_taken_ms=(time.time() - start_time) * 1000,
                        resources_consumed={"analogies_explored": 0}
                    )
                    
                # Using class-level helper methods (deduped)
                
                # Using class-level _extract_domains (deduped)
                
                # Using class-level _extract_mapping_and_expressions (deduped)
                
                # Using class-level _extract_domain_elements (deduped)
                
                # Using class-level _generate_initial_mappings (deduped)
                
                # Using class-level _calculate_predicate_similarity (deduped)
                
                # Using class-level _calculate_object_similarity (deduped)
                
                # Using class-level _perform_structural_alignment (deduped)
                
                # Using class-level _calculate_relation_match_score (deduped)
                
                # Using class-level _map_relation_arguments (deduped)
                
                # Using class-level _evaluate_structural_consistency (deduped)
                
                # Using class-level _evaluate_semantic_fit (deduped)
                
                # Using class-level _project_expression (deduped)
                
                # Using class-level _create_analogy_proof_steps (deduped)
                
                # Using class-level _create_projection_proof_steps (deduped)
                
                # Create proof steps
                proof_steps = self._create_analogy_proof_steps(mappings[0], source_domain, target_domain)
                
                # Create success proof object
                return ProofObject.create_success(
                    conclusion_ast=goal_ast,
                    proof_steps=proof_steps,
                    used_axioms_rules=context_asts,
                    inference_engine_used=self.name,
                    time_taken_ms=(time.time() - start_time) * 1000,
                    resources_consumed={"analogies_explored": len(mappings)}
                )
                
            elif task_type == "project_inference":
                # Extract mapping and source expressions from the context
                mapping, source_exprs = self._extract_mapping_and_expressions(context_asts, task_params)
                
                # Project inferences
                inferences = self.project_inferences(mapping, source_exprs)
                
                if not inferences:
                    # No inferences projected
                    return ProofObject.create_failure(
                        status_message="No inferences could be projected",
                        inference_engine_used=self.name,
                        time_taken_ms=(time.time() - start_time) * 1000,
                        resources_consumed={"expressions_projected": 0}
                    )
                
                # Create proof steps
                proof_steps = self._create_projection_proof_steps(mapping, source_exprs, inferences)
                
                # Create success proof object
                return ProofObject.create_success(
                    conclusion_ast=goal_ast,
                    proof_steps=proof_steps,
                    used_axioms_rules=context_asts,
                    inference_engine_used=self.name,
                    time_taken_ms=(time.time() - start_time) * 1000,
                    resources_consumed={"expressions_projected": len(inferences)}
                )
            
            else:
                # Unknown task type
                return ProofObject.create_failure(
                    status_message=f"Unknown analogical reasoning task: {task_type}",
                    inference_engine_used=self.name,
                    time_taken_ms=(time.time() - start_time) * 1000,
                    resources_consumed={}
                )
                
        except Exception as e:
            # Handle exceptions
            logger.error(f"Error during analogical reasoning: {str(e)}", exc_info=True)
            
            return ProofObject.create_failure(
                status_message=f"Error: {str(e)}",
                inference_engine_used=self.name,
                time_taken_ms=(time.time() - start_time) * 1000,
                resources_consumed={"error": 1}
            )

    # --- Helper methods exposed at class level (moved from nested defs) ---
    def _analyze_goal(self, goal_ast: AST_Node) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze the goal to determine the analogical reasoning task.

        Args:
            goal_ast: The goal to analyze

        Returns:
            A tuple of (task_type, task_parameters)
        """
        if not isinstance(goal_ast, ApplicationNode):
            raise ValueError("Goal must be an application node")

        op = goal_ast.operator
        if not hasattr(op, 'name') or not isinstance(op.name, str):
            raise ValueError("Goal operator must have a name")

        task_params: Dict[str, Any] = {}

        # Determine task type based on predicate name
        if op.name in {'FindAnalogy', 'FindMapping', 'StructuralMapping', 'FindAnalogicalMapping'}:
            task_type = "find_analogy"

            # Extract source and target domain identifiers if provided
            if len(goal_ast.arguments) >= 2:
                task_params['source_id'] = goal_ast.arguments[0]
                task_params['target_id'] = goal_ast.arguments[1]

        elif op.name in {'AnalogicalInference', 'ProjectAnalogy', 'TransferKnowledge', 'ProjectInference'}:
            task_type = "project_inference"

            # Extract mapping and source expression identifiers if provided
            if len(goal_ast.arguments) >= 2:
                task_params['mapping_id'] = goal_ast.arguments[0]
                task_params['source_expr_id'] = goal_ast.arguments[1]

        elif 'analog' in op.name.lower():
            # Default to find_analogy for other analogical predicates
            task_type = "find_analogy"

        else:
            raise ValueError(f"Unknown analogical reasoning task: {op.name}")

        return task_type, task_params

    def _extract_domains(self, context_asts: Set[AST_Node], task_params: Dict[str, Any]) -> Tuple[Set[AST_Node], Set[AST_Node]]:
        """
        Extract source and target domains from the context.

        Args:
            context_asts: The set of context assertions
            task_params: Parameters extracted from the goal

        Returns:
            A tuple of (source_domain, target_domain)
        """
        # This is a simplified implementation that assumes the context is already
        # divided into source and target domains. In a full implementation, this
        # would involve more sophisticated domain extraction based on metadata,
        # domain identifiers, or explicit domain specifications.

        source_domain: Set[AST_Node] = set()
        target_domain: Set[AST_Node] = set()

        # Check if we have domain identifiers in task_params
        source_id = task_params.get('source_id')
        target_id = task_params.get('target_id')

        if source_id and target_id:
            # Extract domains based on identifiers
            for ast in context_asts:
                # Check metadata for domain information
                domain_info = getattr(ast, 'metadata', {}).get('domain') if hasattr(ast, 'metadata') else None
                if domain_info:
                    if domain_info == source_id:
                        source_domain.add(ast)
                    elif domain_info == target_id:
                        target_domain.add(ast)
        else:
            # Simple heuristic: split the context into two equal parts
            # In a real implementation, this would be more sophisticated
            sorted_asts = sorted(context_asts, key=lambda ast: str(ast))
            mid_point = len(sorted_asts) // 2

            source_domain = set(sorted_asts[:mid_point])
            target_domain = set(sorted_asts[mid_point:])

        return source_domain, target_domain

    def _extract_mapping_and_expressions(self, context_asts: Set[AST_Node], task_params: Dict[str, Any]) -> Tuple[AnalogicalMapping, Set[AST_Node]]:
        """
        Extract mapping and source expressions from the context.

        Args:
            context_asts: The set of context assertions
            task_params: Parameters extracted from the goal

        Returns:
            A tuple of (mapping, source_expressions)
        """
        # This is a simplified implementation. In a full implementation, this would
        # involve extracting a previously computed mapping and the source expressions
        # to project from the context.

        # For now, create a dummy mapping and use all context assertions as source expressions
        mapping = AnalogicalMapping("source", "target")
        source_exprs = context_asts

        return mapping, source_exprs

    def _extract_domain_elements(self, domain_asts: Set[AST_Node]) -> Tuple[Set[ConstantNode], Set[AST_Node], Set[ApplicationNode]]:
        """
        Extract objects, predicates, and relations from a domain.

        Args:
            domain_asts: The ASTs constituting the domain

        Returns:
            A tuple of (objects, predicates, relations)
        """
        objects: Set[ConstantNode] = set()
        predicates: Set[AST_Node] = set()
        relations: Set[ApplicationNode] = set()

        for ast in domain_asts:
            if isinstance(ast, ConstantNode):
                objects.add(ast)
            elif isinstance(ast, ApplicationNode):
                relations.add(ast)
                predicates.add(ast.operator)

                # Extract objects from the arguments
                for arg in ast.arguments:
                    if isinstance(arg, ConstantNode):
                        objects.add(arg)

        return objects, predicates, relations

    def _generate_initial_mappings(self,
                                   source_objects: Set[ConstantNode],
                                   target_objects: Set[ConstantNode],
                                   source_predicates: Set[AST_Node],
                                   target_predicates: Set[AST_Node],
                                   source_relations: Set[ApplicationNode],
                                   target_relations: Set[ApplicationNode]) -> List[AnalogicalMapping]:
        """
        Generate initial candidate mappings.

        Args:
            source_objects: Objects in the source domain
            target_objects: Objects in the target domain
            source_predicates: Predicates in the source domain
            target_predicates: Predicates in the target domain
            source_relations: Relations in the source domain
            target_relations: Relations in the target domain

        Returns:
            A list of initial candidate mappings
        """
        # Create a single initial mapping
        mapping = AnalogicalMapping("source", "target")

        # Map predicates based on arity and type
        predicate_pairs: List[Tuple[AST_Node, AST_Node, float]] = []
        for s_pred in source_predicates:
            for t_pred in target_predicates:
                # Calculate a simple similarity score
                similarity = self._calculate_predicate_similarity(s_pred, t_pred)
                if similarity > 0:
                    predicate_pairs.append((s_pred, t_pred, similarity))

        # Sort predicate pairs by similarity
        predicate_pairs.sort(key=lambda x: x[2], reverse=True)

        # Add top predicate mappings
        for s_pred, t_pred, similarity in predicate_pairs[:min(10, len(predicate_pairs))]:
            mapping.add_predicate_mapping(s_pred, t_pred, similarity)

        # Map objects based on their roles in relations
        object_pairs: List[Tuple[ConstantNode, ConstantNode, float]] = []
        for s_obj in source_objects:
            for t_obj in target_objects:
                # Calculate a simple similarity score
                similarity = self._calculate_object_similarity(s_obj, t_obj)
                if similarity > 0:
                    object_pairs.append((s_obj, t_obj, similarity))

        # Sort object pairs by similarity
        object_pairs.sort(key=lambda x: x[2], reverse=True)

        # Add top object mappings
        for s_obj, t_obj, similarity in object_pairs[:min(10, len(object_pairs))]:
            mapping.add_object_mapping(s_obj, t_obj, similarity)

        return [mapping]

    def _calculate_predicate_similarity(self, pred1: AST_Node, pred2: AST_Node) -> float:
        """
        Calculate similarity between two predicates.

        Args:
            pred1: First predicate
            pred2: Second predicate

        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity based on name if available
        if hasattr(pred1, 'name') and hasattr(pred2, 'name'):
            if pred1.name == pred2.name:
                return 1.0

            # Heuristic synonym mapping for common predicate pairs
            if isinstance(pred1.name, str) and isinstance(pred2.name, str):
                name1 = pred1.name.lower()
                name2 = pred2.name.lower()

                synonym_pairs = {
                    ("revolves_around", "orbits"),
                    ("orbits", "revolves_around"),
                }
                if (name1, name2) in synonym_pairs:
                    return 0.8

                # Partial string match
                if name1 in name2 or name2 in name1:
                    return 0.5

        # Check types if available
        if hasattr(pred1, 'type') and hasattr(pred2, 'type'):
            if pred1.type == pred2.type:
                return 0.3

        # Default low similarity
        return 0.1

    def _calculate_object_similarity(self, obj1: ConstantNode, obj2: ConstantNode) -> float:
        """
        Calculate similarity between two objects.

        Args:
            obj1: First object
            obj2: Second object

        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity based on name and type
        similarity = 0.0

        # Check names
        if obj1.name == obj2.name:
            similarity += 0.5
        elif isinstance(obj1.name, str) and isinstance(obj2.name, str):
            # Simple substring check
            name1 = obj1.name.lower()
            name2 = obj2.name.lower()

            if name1 in name2 or name2 in name1:
                similarity += 0.3

        # Check types
        if obj1.type == obj2.type:
            similarity += 0.5

        # Check values if available
        if getattr(obj1, 'value', None) is not None and getattr(obj2, 'value', None) is not None and obj1.value == obj2.value:
            similarity += 0.2

        # Normalize
        return min(similarity, 1.0)

    def _perform_structural_alignment(self,
                                      candidate_mappings: List[AnalogicalMapping],
                                      source_relations: Set[ApplicationNode],
                                      target_relations: Set[ApplicationNode]) -> List[AnalogicalMapping]:
        """
        Perform structural alignment to improve mappings.

        Args:
            candidate_mappings: Initial candidate mappings
            source_relations: Relations in the source domain
            target_relations: Relations in the target domain

        Returns:
            A list of improved mappings
        """
        aligned_mappings: List[AnalogicalMapping] = []

        for mapping in candidate_mappings:
            # Create a copy of the mapping to work with
            aligned_mapping = AnalogicalMapping(
                mapping.source_domain_id,
                mapping.target_domain_id,
                list(mapping.object_mappings),
                list(mapping.predicate_function_mappings),
                list(mapping.relation_instance_mappings)
            )

            # Align relations based on predicate mappings
            for source_rel in source_relations:
                source_pred = source_rel.operator
                target_pred = aligned_mapping.get_predicate_mapping(source_pred)

                if target_pred is None:
                    continue

                # Find target relations with the same predicate
                matching_target_rels = [
                    rel for rel in target_relations
                    if rel.operator == target_pred
                ]

                if not matching_target_rels:
                    continue

                # Find the best matching target relation
                best_match: Optional[ApplicationNode] = None
                best_score = -1.0

                for target_rel in matching_target_rels:
                    # Calculate a match score based on argument mappings
                    score = self._calculate_relation_match_score(
                        source_rel, target_rel, aligned_mapping
                    )

                    if score > best_score:
                        best_score = score
                        best_match = target_rel

                if best_match and best_score > 0.0:
                    # Add relation mapping
                    aligned_mapping.add_relation_mapping(source_rel, best_match)

                    # Add object mappings for arguments that aren't already mapped
                    self._map_relation_arguments(
                        source_rel, best_match, aligned_mapping
                    )

            aligned_mappings.append(aligned_mapping)

        return aligned_mappings

    def _calculate_relation_match_score(self,
                                        source_rel: ApplicationNode,
                                        target_rel: ApplicationNode,
                                        mapping: AnalogicalMapping) -> float:
        """
        Calculate how well a source relation matches a target relation under the mapping.

        Args:
            source_rel: Source relation
            target_rel: Target relation
            mapping: Current analogical mapping

        Returns:
            Match score between 0 and 1
        """
        # Check arity
        if len(source_rel.arguments) != len(target_rel.arguments):
            return 0.0

        # Count mapped arguments
        total_args = len(source_rel.arguments)
        mapped_args = 0

        for i, source_arg in enumerate(source_rel.arguments):
            target_arg = target_rel.arguments[i]

            if not isinstance(source_arg, ConstantNode) or not isinstance(target_arg, ConstantNode):
                continue

            mapped_target = mapping.get_object_mapping(source_arg)
            if mapped_target == target_arg:
                mapped_args += 1

        # Return the proportion of correctly mapped arguments
        return mapped_args / total_args if total_args > 0 else 0.0

    def _map_relation_arguments(self,
                                source_rel: ApplicationNode,
                                target_rel: ApplicationNode,
                                mapping: AnalogicalMapping) -> None:
        """
        Add object mappings for relation arguments that aren't already mapped.

        Args:
            source_rel: Source relation
            target_rel: Target relation
            mapping: Analogical mapping to update
        """
        for i, source_arg in enumerate(source_rel.arguments):
            if i >= len(target_rel.arguments):
                break

            target_arg = target_rel.arguments[i]

            if not isinstance(source_arg, ConstantNode) or not isinstance(target_arg, ConstantNode):
                continue

            # Check if the source object is already mapped
            mapped_target = mapping.get_object_mapping(source_arg)

            if mapped_target is None:
                # Add a new mapping
                mapping.add_object_mapping(source_arg, target_arg, 0.5)

    def _evaluate_structural_consistency(self,
                                       mapping: AnalogicalMapping,
                                       source_relations: Set[ApplicationNode],
                                       target_relations: Set[ApplicationNode]) -> float:
        """
        Evaluate the structural consistency of a mapping.

        Args:
            mapping: The analogical mapping to evaluate
            source_relations: Relations in the source domain
            target_relations: Relations in the target domain

        Returns:
            Structural consistency score between 0 and 1
        """
        # Count the number of consistent relation mappings
        consistent_mappings = 0
        total_relations = len(source_relations)

        for source_rel in source_relations:
            # Check if the relation's predicate is mapped
            source_pred = source_rel.operator
            target_pred = mapping.get_predicate_mapping(source_pred)

            if target_pred is None:
                continue

            # Build the projected target arguments using object mappings
            projected_args: List[ConstantNode] = []
            for source_arg in source_rel.arguments:
                if not isinstance(source_arg, ConstantNode):
                    # Only handle constants in this simplified check
                    projected_args = []
                    break
                mapped_target = mapping.get_object_mapping(source_arg)
                if mapped_target is None:
                    projected_args = []
                    break
                projected_args.append(mapped_target)

            if not projected_args:
                continue

            # Check whether such a relation actually exists in the target domain
            exists_in_target = any(
                (rel.operator == target_pred and list(rel.arguments) == projected_args)
                for rel in target_relations
            )

            if exists_in_target:
                consistent_mappings += 1

        # Return the proportion of consistent mappings
        return consistent_mappings / total_relations if total_relations > 0 else 0.0

    def _evaluate_semantic_fit(self,
                               mapping: AnalogicalMapping,
                               source_objects: Set[ConstantNode],
                               target_objects: Set[ConstantNode],
                               source_predicates: Set[AST_Node],
                               target_predicates: Set[AST_Node]) -> float:
        """
        Evaluate the semantic fit of a mapping.

        Args:
            mapping: The analogical mapping to evaluate
            source_objects: Objects in the source domain
            target_objects: Objects in the target domain
            source_predicates: Predicates in the source domain
            target_predicates: Predicates in the target domain

        Returns:
            Semantic fit score between 0 and 1
        """
        # Calculate the average similarity of object mappings
        object_similarities: List[float] = []

        for obj_mapping in mapping.object_mappings:
            similarity = self._calculate_object_similarity(
                obj_mapping.source_object, obj_mapping.target_object
            )
            object_similarities.append(similarity)

        # Calculate the average similarity of predicate mappings
        predicate_similarities: List[float] = []

        for pred_mapping in mapping.predicate_function_mappings:
            similarity = self._calculate_predicate_similarity(
                pred_mapping.source_symbol, pred_mapping.target_symbol
            )
            predicate_similarities.append(similarity)

        # Calculate the overall semantic fit
        avg_obj_similarity = sum(object_similarities) / len(object_similarities) if object_similarities else 0.0
        avg_pred_similarity = sum(predicate_similarities) / len(predicate_similarities) if predicate_similarities else 0.0

        # Weighted combination of object and predicate similarities
        return 0.5 * avg_obj_similarity + 0.5 * avg_pred_similarity

    def _project_expression(self, source_expr: AST_Node, mapping: AnalogicalMapping) -> Optional[AST_Node]:
        """
        Project a source expression to the target domain using the given mapping.

        Args:
            source_expr: The source expression to project
            mapping: The analogical mapping to use

        Returns:
            The projected expression in the target domain, or None if projection is not possible
        """
        if isinstance(source_expr, ConstantNode):
            # Project a constant node
            target_obj = mapping.get_object_mapping(source_expr)
            return target_obj

        elif isinstance(source_expr, ApplicationNode):
            # Project an application node
            source_pred = source_expr.operator
            target_pred = mapping.get_predicate_mapping(source_pred)

            if target_pred is None:
                return None

            # Project the arguments
            target_args: List[AST_Node] = []

            for source_arg in source_expr.arguments:
                target_arg = self._project_expression(source_arg, mapping)

                if target_arg is None:
                    return None

                target_args.append(target_arg)

            # Create the projected application
            return ApplicationNode(target_pred, target_args, source_expr.type)

        else:
            # Other node types not supported for projection
            return None

    def _create_analogy_proof_steps(self,
                                    mapping: AnalogicalMapping,
                                    source_domain: Set[AST_Node],
                                    target_domain: Set[AST_Node]) -> List[ProofStepNode]:
        """
        Create proof steps for analogical mapping.

        Args:
            mapping: The analogical mapping produced
            source_domain: The source domain ASTs
            target_domain: The target domain ASTs

        Returns:
            A list of proof steps
        """
        proof_steps: List[ProofStepNode] = []

        # Step 1: Identify domains
        step1 = ProofStepNode(
            formula=ApplicationNode(
                ConstantNode("IdentifyDomains", None),
                [
                    ConstantNode(mapping.source_domain_id, None),
                    ConstantNode(mapping.target_domain_id, None)
                ],
                None
            ),
            rule_name="IdentifyDomains",
            premises=[],
            explanation=f"Identified source domain '{mapping.source_domain_id}' and target domain '{mapping.target_domain_id}'"
        )
        proof_steps.append(step1)

        # Step 2: Establish predicate mappings
        for i, pred_mapping in enumerate(mapping.predicate_function_mappings):
            step = ProofStepNode(
                formula=ApplicationNode(
                    ConstantNode("MapPredicate", None),
                    [pred_mapping.source_symbol, pred_mapping.target_symbol],
                    None
                ),
                rule_name="MapPredicate",
                premises=[0],  # Depends on step 1
                explanation=f"Mapped predicate {pred_mapping.source_symbol} to {pred_mapping.target_symbol} (score: {pred_mapping.similarity_score:.2f})"
            )
            proof_steps.append(step)

        # Step 3: Establish object mappings
        for i, obj_mapping in enumerate(mapping.object_mappings):
            step = ProofStepNode(
                formula=ApplicationNode(
                    ConstantNode("MapObject", None),
                    [obj_mapping.source_object, obj_mapping.target_object],
                    None
                ),
                rule_name="MapObject",
                premises=[0],
                explanation=f"Mapped object {obj_mapping.source_object} to {obj_mapping.target_object} (score: {obj_mapping.similarity_score:.2f})"
            )
            proof_steps.append(step)

        # Step 4: Establish relation mappings
        for i, rel_mapping in enumerate(mapping.relation_instance_mappings):
            step = ProofStepNode(
                formula=ApplicationNode(
                    ConstantNode("MapRelation", None),
                    [rel_mapping.source_fact, rel_mapping.target_fact],
                    None
                ),
                rule_name="MapRelation",
                premises=[0],
                explanation=f"Mapped relation {rel_mapping.source_fact} to {rel_mapping.target_fact}"
            )
            proof_steps.append(step)

        # Step 5: Evaluate mapping quality
        step5 = ProofStepNode(
            formula=ApplicationNode(
                ConstantNode("EvaluateMapping", None),
                [
                    ConstantNode(f"structural={mapping.structural_consistency_score:.2f}", None),
                    ConstantNode(f"semantic={mapping.semantic_fit_score:.2f}", None),
                    ConstantNode(f"overall={mapping.get_overall_score():.2f}", None)
                ],
                None
            ),
            rule_name="EvaluateMapping",
            premises=list(range(len(proof_steps))),
            explanation="Evaluated mapping quality (structural, semantic, overall)"
        )
        proof_steps.append(step5)

        return proof_steps

    def _create_projection_proof_steps(self,
                                       mapping: AnalogicalMapping,
                                       source_exprs: Set[AST_Node],
                                       projected_inferences: List[AST_Node]) -> List[ProofStepNode]:
        """
        Create proof steps for analogical inference projection.

        Args:
            mapping: The analogical mapping used
            source_exprs: The source expressions that were projected
            projected_inferences: The projected inferences

        Returns:
            A list of proof steps
        """
        proof_steps: List[ProofStepNode] = []

        # Step 1: Use mapping
        step1 = ProofStepNode(
            formula=ApplicationNode(
                ConstantNode("UseMapping", None),
                [
                    ConstantNode(mapping.source_domain_id, None),
                    ConstantNode(mapping.target_domain_id, None)
                ],
                None
            ),
            rule_name="UseMapping",
            premises=[],
            explanation=f"Using analogical mapping from '{mapping.source_domain_id}' to '{mapping.target_domain_id}'"
        )
        proof_steps.append(step1)

        # Step 2: Project expressions
        for i, (source_expr, projected_expr) in enumerate(zip(source_exprs, projected_inferences)):
            step = ProofStepNode(
                formula=ApplicationNode(
                    ConstantNode("ProjectExpression", None),
                    [source_expr, projected_expr],
                    None
                ),
                rule_name="ProjectExpression",
                premises=[0],  # Depends on step 1
                explanation=f"Projected expression {source_expr} to {projected_expr}"
            )
            proof_steps.append(step)

        return proof_steps
