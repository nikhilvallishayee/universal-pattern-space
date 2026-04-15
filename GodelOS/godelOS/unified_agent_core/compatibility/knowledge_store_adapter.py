"""
Knowledge Store Adapter for GodelOS

This module implements the KnowledgeStoreAdapter class, which adapts the existing
KnowledgeStoreInterface to work with the new UnifiedKnowledgeStore in the
UnifiedAgentCore architecture.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union, Set, Tuple

from godelOS.core_kr.knowledge_store.interface import (
    KnowledgeStoreInterface,
    QueryResult as LegacyQueryResult
)
from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.manager import TypeSystemManager

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    UnifiedKnowledgeStoreInterface,
    MemoryType,
    KnowledgeType,
    Knowledge,
    Fact,
    Belief,
    Concept,
    Rule,
    Experience,
    Query,
    QueryResult
)

logger = logging.getLogger(__name__)


class KnowledgeStoreAdapter:
    """
    Adapter for connecting the existing KnowledgeStoreInterface with the new UnifiedKnowledgeStore.
    
    This adapter implements the adapter pattern to allow the existing KnowledgeStoreInterface
    to work with the new UnifiedKnowledgeStore in the UnifiedAgentCore architecture, ensuring
    backward compatibility while enabling the new architecture's capabilities.
    """
    
    def __init__(
        self,
        legacy_knowledge_store: KnowledgeStoreInterface,
        unified_knowledge_store: Optional[UnifiedKnowledgeStoreInterface] = None
    ):
        """
        Initialize the knowledge store adapter.
        
        Args:
            legacy_knowledge_store: The existing knowledge store
            unified_knowledge_store: Optional unified knowledge store to connect to
        """
        self.legacy_knowledge_store = legacy_knowledge_store
        self.unified_knowledge_store = unified_knowledge_store
        
        # Context mapping from legacy contexts to memory types
        self.context_mapping: Dict[str, MemoryType] = {
            "TRUTHS": MemoryType.SEMANTIC,
            "BELIEFS": MemoryType.SEMANTIC,
            "HYPOTHETICAL": MemoryType.WORKING
        }
        
        # Type mapping from legacy types to knowledge types
        self.type_mapping: Dict[str, KnowledgeType] = {
            "Fact": KnowledgeType.FACT,
            "Belief": KnowledgeType.BELIEF,
            "Rule": KnowledgeType.RULE,
            "Concept": KnowledgeType.CONCEPT,
            "Hypothesis": KnowledgeType.HYPOTHESIS,
            "Experience": KnowledgeType.EXPERIENCE,
            "Procedure": KnowledgeType.PROCEDURE
        }
    
    async def add_statement(
        self,
        statement_ast: AST_Node,
        context_id: str = "TRUTHS",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a statement to both knowledge stores.
        
        Args:
            statement_ast: The statement to add
            context_id: The context to add the statement to
            metadata: Optional metadata for the statement
            
        Returns:
            True if the statement was added successfully, False otherwise
        """
        # Add to legacy knowledge store
        legacy_result = self.legacy_knowledge_store.add_statement(
            statement_ast, context_id, metadata
        )
        
        # If unified knowledge store is available, add to it as well
        if self.unified_knowledge_store:
            try:
                # Convert AST node to knowledge item
                knowledge_item = await self._convert_ast_to_knowledge(statement_ast, metadata)
                
                # Determine memory type based on context
                memory_type = self.context_mapping.get(context_id, MemoryType.SEMANTIC)
                
                # Add to unified knowledge store
                unified_result = await self.unified_knowledge_store.store_knowledge(
                    knowledge_item, memory_type
                )
                
                # Return True only if both operations succeeded
                return legacy_result and unified_result
            except Exception as e:
                logger.error(f"Error adding statement to unified knowledge store: {e}")
                # If there's an error with the unified store, still return the legacy result
                return legacy_result
        
        return legacy_result
    
    async def retract_statement(
        self,
        statement_pattern_ast: AST_Node,
        context_id: str = "TRUTHS"
    ) -> bool:
        """
        Retract a statement from both knowledge stores.
        
        Args:
            statement_pattern_ast: The statement pattern to retract
            context_id: The context to retract the statement from
            
        Returns:
            True if the statement was retracted successfully, False otherwise
        """
        # Retract from legacy knowledge store
        legacy_result = self.legacy_knowledge_store.retract_statement(
            statement_pattern_ast, context_id
        )
        
        # If unified knowledge store is available, retract from it as well
        if self.unified_knowledge_store:
            try:
                # First, query to find matching items
                query = await self._create_query_from_ast(statement_pattern_ast, [context_id])
                result = await self.unified_knowledge_store.query_knowledge(query)
                
                # Delete each matching item
                unified_result = True
                for item in result.items:
                    item_result = await self._delete_knowledge_item(item.id)
                    unified_result = unified_result and item_result
                
                # Return True only if both operations succeeded
                return legacy_result and unified_result
            except Exception as e:
                logger.error(f"Error retracting statement from unified knowledge store: {e}")
                # If there's an error with the unified store, still return the legacy result
                return legacy_result
        
        return legacy_result
    
    async def query_statements(
        self,
        query_pattern_ast: AST_Node,
        context_ids: List[str] = ["TRUTHS"],
        variables_to_bind: Optional[List[VariableNode]] = None
    ) -> LegacyQueryResult:
        """
        Query statements from the legacy knowledge store.
        
        Args:
            query_pattern_ast: The query pattern
            context_ids: The contexts to query
            variables_to_bind: Optional list of variables to bind
            
        Returns:
            The query result
        """
        # Query the legacy knowledge store
        bindings = self.legacy_knowledge_store.query_statements_match_pattern(
            query_pattern_ast, context_ids, variables_to_bind
        )
        
        # Create a legacy query result
        return LegacyQueryResult(bool(bindings), bindings)
    
    async def unified_query(
        self,
        query_pattern_ast: AST_Node,
        context_ids: List[str] = ["TRUTHS"],
        variables_to_bind: Optional[List[VariableNode]] = None
    ) -> QueryResult:
        """
        Query from both knowledge stores and merge results.
        
        Args:
            query_pattern_ast: The query pattern
            context_ids: The contexts to query
            variables_to_bind: Optional list of variables to bind
            
        Returns:
            The unified query result
        """
        # Query the legacy knowledge store
        legacy_bindings = self.legacy_knowledge_store.query_statements_match_pattern(
            query_pattern_ast, context_ids, variables_to_bind
        )
        
        # Convert legacy bindings to knowledge items
        legacy_items = []
        for binding in legacy_bindings:
            try:
                # For each binding, create a knowledge item
                for var, ast_node in binding.items():
                    knowledge_item = await self._convert_ast_to_knowledge(
                        ast_node, {"source": "legacy_knowledge_store"}
                    )
                    legacy_items.append(knowledge_item)
            except Exception as e:
                logger.error(f"Error converting legacy binding to knowledge item: {e}")
        
        # If unified knowledge store is available, query it as well
        unified_items = []
        if self.unified_knowledge_store:
            try:
                # Create a query from the AST
                query = await self._create_query_from_ast(query_pattern_ast, context_ids)
                
                # Query the unified knowledge store
                unified_result = await self.unified_knowledge_store.query_knowledge(query)
                unified_items = unified_result.items
            except Exception as e:
                logger.error(f"Error querying unified knowledge store: {e}")
        
        # Merge results, avoiding duplicates
        all_items = legacy_items.copy()
        seen_ids = {item.id for item in all_items}
        
        for item in unified_items:
            if item.id not in seen_ids:
                all_items.append(item)
                seen_ids.add(item.id)
        
        # Create a unified query result
        return QueryResult(
            query_id=str(id(query_pattern_ast)),
            items=all_items,
            total_items=len(all_items),
            execution_time=0.0,  # Not tracked in this adapter
            metadata={
                "legacy_bindings_count": len(legacy_bindings),
                "unified_items_count": len(unified_items),
                "contexts": context_ids
            }
        )
    
    async def statement_exists(
        self,
        statement_ast: AST_Node,
        context_ids: List[str] = ["TRUTHS"]
    ) -> bool:
        """
        Check if a statement exists in either knowledge store.
        
        Args:
            statement_ast: The statement to check
            context_ids: The contexts to check
            
        Returns:
            True if the statement exists, False otherwise
        """
        # Check in legacy knowledge store
        legacy_result = self.legacy_knowledge_store.statement_exists(
            statement_ast, context_ids
        )
        
        # If it exists in the legacy store, return True
        if legacy_result:
            return True
        
        # If unified knowledge store is available, check it as well
        if self.unified_knowledge_store:
            try:
                # Create a query from the AST
                query = await self._create_query_from_ast(statement_ast, context_ids)
                
                # Query the unified knowledge store
                result = await self.unified_knowledge_store.query_knowledge(query)
                
                # Return True if any items were found
                return len(result.items) > 0
            except Exception as e:
                logger.error(f"Error checking statement existence in unified knowledge store: {e}")
                # If there's an error with the unified store, still return the legacy result
                return legacy_result
        
        return legacy_result
    
    async def create_context(
        self,
        context_id: str,
        parent_context_id: Optional[str] = None,
        context_type: str = "generic"
    ) -> bool:
        """
        Create a context in the legacy knowledge store.
        
        Args:
            context_id: The ID of the context
            parent_context_id: Optional parent context ID
            context_type: The type of the context
            
        Returns:
            True if the context was created successfully, False otherwise
        """
        try:
            # Create context in legacy knowledge store
            self.legacy_knowledge_store.create_context(
                context_id, parent_context_id, context_type
            )
            return True
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return False
    
    async def _convert_ast_to_knowledge(
        self,
        ast_node: AST_Node,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Knowledge:
        """
        Convert an AST node to a knowledge item.
        
        Args:
            ast_node: The AST node to convert
            metadata: Optional metadata for the knowledge item
            
        Returns:
            The knowledge item
        """
        # Determine knowledge type based on AST node type
        knowledge_type = KnowledgeType.FACT  # Default
        
        if isinstance(ast_node, ApplicationNode):
            if isinstance(ast_node.operator, ConstantNode):
                # Check if the operator name maps to a knowledge type
                operator_name = ast_node.operator.name
                if operator_name in ["Belief", "believe"]:
                    knowledge_type = KnowledgeType.BELIEF
                elif operator_name in ["Rule", "implies", "if-then"]:
                    knowledge_type = KnowledgeType.RULE
                elif operator_name in ["Concept", "concept"]:
                    knowledge_type = KnowledgeType.CONCEPT
                elif operator_name in ["Hypothesis", "hypothesize"]:
                    knowledge_type = KnowledgeType.HYPOTHESIS
        
        # Convert AST node to a dictionary representation
        content = self._ast_to_dict(ast_node)
        
        # Create appropriate knowledge item based on type
        if knowledge_type == KnowledgeType.FACT:
            return Fact(
                id=str(id(ast_node)),
                type=knowledge_type,
                content=content,
                confidence=1.0,
                metadata=metadata or {}
            )
        elif knowledge_type == KnowledgeType.BELIEF:
            return Belief(
                id=str(id(ast_node)),
                type=knowledge_type,
                content=content,
                confidence=0.8,  # Default confidence for beliefs
                evidence=[],  # No evidence initially
                metadata=metadata or {}
            )
        elif knowledge_type == KnowledgeType.CONCEPT:
            return Concept(
                id=str(id(ast_node)),
                type=knowledge_type,
                content=content,
                confidence=1.0,
                related_concepts=[],  # No related concepts initially
                metadata=metadata or {}
            )
        elif knowledge_type == KnowledgeType.RULE:
            return Rule(
                id=str(id(ast_node)),
                type=knowledge_type,
                content=content,
                confidence=1.0,
                conditions=[],  # Extract conditions in a real implementation
                actions=[],  # Extract actions in a real implementation
                metadata=metadata or {}
            )
        elif knowledge_type == KnowledgeType.HYPOTHESIS:
            return Hypothesis(
                id=str(id(ast_node)),
                type=knowledge_type,
                content=content,
                confidence=0.5,  # Default confidence for hypotheses
                evidence_for=[],
                evidence_against=[],
                metadata=metadata or {}
            )
        else:
            # Default to generic Knowledge
            return Knowledge(
                id=str(id(ast_node)),
                type=knowledge_type,
                content=content,
                confidence=1.0,
                metadata=metadata or {}
            )
    
    def _ast_to_dict(self, ast_node: AST_Node) -> Dict[str, Any]:
        """
        Convert an AST node to a dictionary representation.
        
        Args:
            ast_node: The AST node to convert
            
        Returns:
            Dictionary representation of the AST node
        """
        if isinstance(ast_node, ConstantNode):
            return {
                "type": "constant",
                "name": ast_node.name,
                "node_type": ast_node.type.name if ast_node.type else "Unknown"
            }
        elif isinstance(ast_node, VariableNode):
            return {
                "type": "variable",
                "name": ast_node.name,
                "var_id": ast_node.var_id,
                "node_type": ast_node.type.name if ast_node.type else "Unknown"
            }
        elif isinstance(ast_node, ApplicationNode):
            return {
                "type": "application",
                "operator": self._ast_to_dict(ast_node.operator),
                "arguments": [self._ast_to_dict(arg) for arg in ast_node.arguments],
                "node_type": ast_node.type.name if ast_node.type else "Unknown"
            }
        else:
            # Unknown node type
            return {
                "type": "unknown",
                "string_representation": str(ast_node)
            }
    
    async def _create_query_from_ast(
        self,
        ast_node: AST_Node,
        context_ids: List[str]
    ) -> Query:
        """
        Create a query from an AST node.
        
        Args:
            ast_node: The AST node to convert to a query
            context_ids: The contexts to query
            
        Returns:
            The query
        """
        # Convert AST node to a dictionary representation
        content = self._ast_to_dict(ast_node)
        
        # Map contexts to memory types
        memory_types = []
        for context_id in context_ids:
            if context_id in self.context_mapping:
                memory_types.append(self.context_mapping[context_id])
        
        # If no memory types were mapped, default to all memory types
        if not memory_types:
            memory_types = list(MemoryType)
        
        # Create the query
        return Query(
            id=str(id(ast_node)),
            content=content,
            memory_types=memory_types,
            knowledge_types=list(KnowledgeType),  # Query all knowledge types
            max_results=100,
            metadata={
                "original_contexts": context_ids,
                "ast_type": type(ast_node).__name__
            }
        )
    
    async def _delete_knowledge_item(self, item_id: str) -> bool:
        """
        Delete a knowledge item from the unified knowledge store.
        
        Args:
            item_id: The ID of the item to delete
            
        Returns:
            True if the item was deleted, False otherwise
        """
        if not self.unified_knowledge_store:
            return False
        
        try:
            # Retrieve the item first to determine its memory type
            item = await self.unified_knowledge_store.retrieve_knowledge(
                item_id, memory_types=list(MemoryType)
            )
            
            if not item:
                return False
            
            # Determine the memory type based on the item's type
            memory_type = None
            if hasattr(item, "type"):
                for mem_type in MemoryType:
                    if (
                        (mem_type == MemoryType.SEMANTIC and item.type in [KnowledgeType.FACT, KnowledgeType.BELIEF, KnowledgeType.CONCEPT, KnowledgeType.RULE]) or
                        (mem_type == MemoryType.EPISODIC and item.type == KnowledgeType.EXPERIENCE) or
                        (mem_type == MemoryType.WORKING and item.type == KnowledgeType.HYPOTHESIS)
                    ):
                        memory_type = mem_type
                        break
            
            # If memory type couldn't be determined, try all memory types
            if not memory_type:
                memory_type = MemoryType.SEMANTIC  # Default
            
            # Use a custom method to delete the item
            # This is a simplified implementation; in a real implementation,
            # you would need to implement this method in the UnifiedKnowledgeStore
            if hasattr(self.unified_knowledge_store, "delete_knowledge"):
                return await self.unified_knowledge_store.delete_knowledge(item_id, memory_type)
            else:
                logger.warning("UnifiedKnowledgeStore does not implement delete_knowledge method")
                return False
        except Exception as e:
            logger.error(f"Error deleting knowledge item: {e}")
            return False
    
    async def set_unified_knowledge_store(self, unified_knowledge_store: UnifiedKnowledgeStoreInterface) -> None:
        """
        Set the unified knowledge store reference.
        
        Args:
            unified_knowledge_store: The unified knowledge store
        """
        self.unified_knowledge_store = unified_knowledge_store