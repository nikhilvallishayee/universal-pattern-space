"""
Query Optimizer (Module 6.2).

This module implements the QueryOptimizer class, which analyzes and optimizes
queries before execution, implements query planning strategies, reorders query
clauses for efficiency, and utilizes statistics about the knowledge base to make
optimization decisions.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, DefaultDict, Callable
import time
import copy
import logging
from collections import defaultdict

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface


class QueryStatistics:
    """
    Class for collecting and managing statistics about the knowledge base.
    
    These statistics are used by the QueryOptimizer to make optimization decisions.
    """
    
    def __init__(self, knowledge_store: KnowledgeStoreInterface, type_system=None):
        """
        Initialize the query statistics.
        
        Args:
            knowledge_store: The knowledge store interface
            type_system: Optional type system manager
        """
        self.knowledge_store = knowledge_store
        self.type_system = type_system
        self.predicate_counts: Dict[str, int] = {}
        self.constant_counts: Dict[str, int] = {}
        self.type_counts: Dict[str, int] = {}
        self.query_times: Dict[str, List[float]] = defaultdict(list)
        self.last_updated = 0
        self.update_interval = 3600  # Update statistics every hour
    
    def update_statistics(self, force: bool = False) -> None:
        """
        Update the statistics about the knowledge base.
        
        Args:
            force: Whether to force an update even if the update interval hasn't elapsed
        """
        current_time = time.time()
        if not force and current_time - self.last_updated < self.update_interval:
            return
        
        self.last_updated = current_time
        
        # Get all contexts
        contexts = self.knowledge_store.list_contexts()
        
        # Clear existing statistics
        self.predicate_counts.clear()
        self.constant_counts.clear()
        self.type_counts.clear()
        
        # Collect statistics for each context
        for context_id in contexts:
            self._collect_context_statistics(context_id)
    
    def _collect_context_statistics(self, context_id: str) -> None:
        """
        Collect statistics for a specific context.
        
        Args:
            context_id: The context ID
        """
        # This is a simplified implementation that would need to be enhanced
        # in a real system to efficiently collect statistics without loading
        # all statements into memory.
        
        # In a real system, we would use more sophisticated techniques such as
        # sampling, incremental updates, or dedicated statistics tables.
        
        # For now, we'll just count predicates, constants, and types
        # based on the statements in the context.
        
        # Get all statements in the context
        # Note: In a real system, we would use a more efficient approach
        all_statements = self._get_all_statements_in_context(context_id)
        
        for statement in all_statements:
            self._update_statement_statistics(statement)
    
    def _get_all_statements_in_context(self, context_id: str) -> List[AST_Node]:
        """
        Get all statements in a context.
        
        Args:
            context_id: The context ID
            
        Returns:
            A list of statements
        """
        # This is a simplified implementation that assumes we can get all
        # statements in a context by querying with a wildcard pattern.
        # In a real system, we would use a more efficient approach.
        
        # Create a wildcard query pattern
        # This is a placeholder and would need to be implemented properly
        # based on the actual AST structure
        if self.type_system:
            entity_type = self.type_system.get_type("Entity")
        else:
            # Fallback to try accessing through knowledge_store if type_system not provided
            try:
                entity_type = self.knowledge_store.type_system.get_type("Entity")
            except AttributeError:
                # If all else fails, use a string as a placeholder
                entity_type = "Entity"
                
        wildcard_var = VariableNode("?x", "x", entity_type)
        query_pattern = wildcard_var
        
        # Query all statements in the context
        results = self.knowledge_store.query_statements_match_pattern(query_pattern, [context_id])
        
        # Extract the statements from the results
        statements = []
        for binding in results:
            for var, node in binding.items():
                statements.append(node)
        
        return statements
    
    def _update_statement_statistics(self, statement: AST_Node) -> None:
        """
        Update statistics based on a statement.
        
        Args:
            statement: The statement to update statistics for
        """
        # Update type count
        type_name = statement.type.name
        self.type_counts[type_name] = self.type_counts.get(type_name, 0) + 1
        
        # Update predicate and constant counts for ApplicationNodes
        if isinstance(statement, ApplicationNode):
            if isinstance(statement.operator, ConstantNode):
                predicate_name = statement.operator.name
                self.predicate_counts[predicate_name] = self.predicate_counts.get(predicate_name, 0) + 1
            
            for arg in statement.arguments:
                if isinstance(arg, ConstantNode):
                    constant_name = arg.name
                    self.constant_counts[constant_name] = self.constant_counts.get(constant_name, 0) + 1
    
    def record_query_time(self, query_hash: str, execution_time: float) -> None:
        """
        Record the execution time for a query.
        
        Args:
            query_hash: A hash of the query
            execution_time: The execution time in seconds
        """
        self.query_times[query_hash].append(execution_time)
        
        # Keep only the last 100 execution times for each query
        if len(self.query_times[query_hash]) > 100:
            self.query_times[query_hash] = self.query_times[query_hash][-100:]
    
    def get_average_query_time(self, query_hash: str) -> Optional[float]:
        """
        Get the average execution time for a query.
        
        Args:
            query_hash: A hash of the query
            
        Returns:
            The average execution time in seconds, or None if no data is available
        """
        times = self.query_times.get(query_hash)
        if not times:
            return None
        
        return sum(times) / len(times)
    
    def get_predicate_selectivity(self, predicate_name: str) -> float:
        """
        Get the selectivity of a predicate.
        
        The selectivity is a value between 0 and 1, where lower values
        indicate more selective predicates (i.e., predicates that match
        fewer statements).
        
        Args:
            predicate_name: The predicate name
            
        Returns:
            The selectivity of the predicate
        """
        total_statements = sum(self.predicate_counts.values())
        if total_statements == 0:
            return 1.0
        
        predicate_count = self.predicate_counts.get(predicate_name, 0)
        return predicate_count / total_statements
    
    def get_constant_selectivity(self, constant_name: str) -> float:
        """
        Get the selectivity of a constant.
        
        Args:
            constant_name: The constant name
            
        Returns:
            The selectivity of the constant
        """
        total_constants = sum(self.constant_counts.values())
        if total_constants == 0:
            return 1.0
        
        constant_count = self.constant_counts.get(constant_name, 0)
        return constant_count / total_constants
    
    def get_type_selectivity(self, type_name: str) -> float:
        """
        Get the selectivity of a type.
        
        Args:
            type_name: The type name
            
        Returns:
            The selectivity of the type
        """
        total_types = sum(self.type_counts.values())
        if total_types == 0:
            return 1.0
        
        type_count = self.type_counts.get(type_name, 0)
        return type_count / total_types


class QueryPlan:
    """
    Class representing a query execution plan.
    
    A query plan specifies the order in which query clauses should be executed
    and any optimizations that should be applied.
    """
    
    def __init__(self, query_pattern: AST_Node, context_ids: List[str], variables_to_bind: Optional[List[VariableNode]] = None):
        """
        Initialize the query plan.
        
        Args:
            query_pattern: The query pattern
            context_ids: The contexts to query
            variables_to_bind: Optional list of variables to bind
        """
        self.original_query_pattern = query_pattern
        self.optimized_query_pattern = copy.deepcopy(query_pattern)
        self.context_ids = context_ids
        self.variables_to_bind = variables_to_bind
        self.estimated_cost = float('inf')
        self.query_hash = str(hash((str(query_pattern), tuple(context_ids), str(variables_to_bind))))
    
    def __str__(self) -> str:
        """
        Get a string representation of the query plan.
        
        Returns:
            A string representation of the query plan
        """
        return f"QueryPlan(pattern={self.optimized_query_pattern}, contexts={self.context_ids}, cost={self.estimated_cost})"


class QueryOptimizer:
    """
    Class for optimizing queries before execution.
    
    The QueryOptimizer analyzes queries and applies various optimization
    strategies to improve query performance.
    """
    
    def __init__(self, knowledge_store: KnowledgeStoreInterface, type_system=None):
        """
        Initialize the query optimizer.
        
        Args:
            knowledge_store: The knowledge store interface
            type_system: Optional type system manager
        """
        self.knowledge_store = knowledge_store
        self.type_system = type_system
        self.statistics = QueryStatistics(knowledge_store, type_system)
        self.optimization_strategies: List[Callable[[QueryPlan, QueryStatistics], QueryPlan]] = [
            self._reorder_conjunctions,
            self._push_constants_to_front,
            self._optimize_variable_binding
        ]
        self.logger = logging.getLogger(__name__)
    
    def optimize_query(self, query_pattern: AST_Node, context_ids: List[str], variables_to_bind: Optional[List[VariableNode]] = None) -> QueryPlan:
        """
        Optimize a query.
        
        Args:
            query_pattern: The query pattern
            context_ids: The contexts to query
            variables_to_bind: Optional list of variables to bind
            
        Returns:
            An optimized query plan
        """
        # Update statistics if needed
        self.statistics.update_statistics()
        
        # Create initial query plan
        plan = QueryPlan(query_pattern, context_ids, variables_to_bind)
        
        # Apply optimization strategies
        for strategy in self.optimization_strategies:
            try:
                plan = strategy(plan, self.statistics)
            except Exception as e:
                self.logger.warning(f"Error applying optimization strategy {strategy.__name__}: {e}")
        
        # Estimate the cost of the optimized plan
        plan.estimated_cost = self._estimate_query_cost(plan)
        
        return plan
    
    def _estimate_query_cost(self, plan: QueryPlan) -> float:
        """
        Estimate the cost of a query plan.
        
        Args:
            plan: The query plan
            
        Returns:
            The estimated cost of the query plan
        """
        # Check if we have historical data for this query
        avg_time = self.statistics.get_average_query_time(plan.query_hash)
        if avg_time is not None:
            return avg_time
        
        # If no historical data, estimate based on query complexity
        # This is a simplified cost model that would need to be enhanced
        # in a real system.
        cost = 1.0
        
        # Add cost based on the number of contexts
        cost *= len(plan.context_ids)
        
        # Add cost based on the complexity of the query pattern
        cost *= self._estimate_pattern_complexity(plan.optimized_query_pattern)
        
        return cost
    
    def _estimate_pattern_complexity(self, pattern: AST_Node) -> float:
        """
        Estimate the complexity of a query pattern.
        
        Args:
            pattern: The query pattern
            
        Returns:
            The estimated complexity of the pattern
        """
        # This is a simplified complexity model that would need to be enhanced
        # in a real system.
        
        if isinstance(pattern, VariableNode):
            # Variables are expensive because they match anything
            return 10.0
        
        if isinstance(pattern, ConstantNode):
            # Constants are cheap because they match specific values
            return 1.0
        
        if isinstance(pattern, ApplicationNode):
            # Application nodes are as expensive as their operator and arguments
            complexity = self._estimate_pattern_complexity(pattern.operator)
            for arg in pattern.arguments:
                complexity += self._estimate_pattern_complexity(arg)
            return complexity
        
        # Default complexity for other node types
        return 5.0
    
    def _reorder_conjunctions(self, plan: QueryPlan, statistics: QueryStatistics) -> QueryPlan:
        """
        Reorder conjunctions in a query to improve performance.
        
        This strategy reorders conjunctions (AND clauses) so that the most
        selective clauses are executed first, which reduces the number of
        intermediate results.
        
        Args:
            plan: The query plan
            statistics: The query statistics
            
        Returns:
            The optimized query plan
        """
        # This is a simplified implementation that assumes conjunctions are
        # represented as nested ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return the original plan
        return plan
    
    def _push_constants_to_front(self, plan: QueryPlan, statistics: QueryStatistics) -> QueryPlan:
        """
        Push constant terms to the front of the query.
        
        This strategy reorders terms in a query so that terms with constants
        are executed first, which reduces the number of intermediate results.
        
        Args:
            plan: The query plan
            statistics: The query statistics
            
        Returns:
            The optimized query plan
        """
        # This is a simplified implementation that assumes terms are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return the original plan
        return plan
    
    def _optimize_variable_binding(self, plan: QueryPlan, statistics: QueryStatistics) -> QueryPlan:
        """
        Optimize variable binding in a query.
        
        This strategy reorders variable bindings so that variables that
        appear in multiple clauses are bound first, which reduces the
        number of intermediate results.
        
        Args:
            plan: The query plan
            statistics: The query statistics
            
        Returns:
            The optimized query plan
        """
        # This is a simplified implementation that assumes variable bindings
        # are represented in a specific way in the AST.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return the original plan
        return plan
    
    def execute_optimized_query(self, plan: QueryPlan) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute an optimized query.
        
        Args:
            plan: The optimized query plan
            
        Returns:
            The query results
        """
        start_time = time.time()
        
        # Execute the query using the optimized pattern
        results = self.knowledge_store.query_statements_match_pattern(
            plan.optimized_query_pattern, plan.context_ids, plan.variables_to_bind)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Record the execution time for future optimization
        self.statistics.record_query_time(plan.query_hash, execution_time)
        
        return results