"""
Meta-Knowledge Base (MKB) for GödelOS.

This module implements the MetaKnowledgeBase component (Module 7.2) of the Metacognition & 
Self-Improvement System, which is responsible for storing and managing meta-knowledge
about the system's own operation.

The MetaKnowledgeBase:
1. Stores and manages meta-knowledge about the system's own operation
2. Maintains models of component performance characteristics
3. Stores historical performance data
4. Implements methods for querying and updating meta-knowledge
5. Integrates with the KR System for knowledge representation
"""

import logging
import time
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import pickle
import statistics
import json

# Custom JSON encoder to handle MetaKnowledgeType enum
class MetaKnowledgeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MetaKnowledgeType(Enum):
    """Enum representing types of meta-knowledge."""
    COMPONENT_PERFORMANCE = "component_performance"
    REASONING_STRATEGY = "reasoning_strategy"
    RESOURCE_USAGE = "resource_usage"
    LEARNING_EFFECTIVENESS = "learning_effectiveness"
    FAILURE_PATTERN = "failure_pattern"
    SYSTEM_CAPABILITY = "system_capability"
    OPTIMIZATION_HINT = "optimization_hint"


# Common fields for all meta-knowledge entries
@dataclass
class MetaKnowledgeEntry:
    """Base class for meta-knowledge entries."""
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    confidence: float = 1.0  # 0.0 to 1.0
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


# Create a factory function to help create entries with common fields
def create_meta_knowledge_entry(entry_type: MetaKnowledgeType, entry_id: str = None, **kwargs) -> Dict[str, Any]:
    """Create a dictionary with common meta-knowledge entry fields."""
    if entry_id is None:
        entry_id = f"{entry_type.value}_{int(time.time())}"
    
    return {
        "entry_id": entry_id,
        "entry_type": entry_type,
        "creation_time": kwargs.get("creation_time", time.time()),
        "last_updated": kwargs.get("last_updated", time.time()),
        "confidence": kwargs.get("confidence", 1.0),
        "source": kwargs.get("source", "system"),
        "metadata": kwargs.get("metadata", {})
    }


@dataclass
class ComponentPerformanceModel:
    """Model of a component's performance characteristics."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Component-specific fields
    component_id: str
    average_response_time_ms: float
    throughput_per_second: float
    failure_rate: float
    resource_usage: Dict[str, float]
    performance_factors: Dict[str, float] = field(default_factory=dict)
    historical_data: Dict[str, List[float]] = field(default_factory=dict)
    
    @classmethod
    def create(cls, component_id: str, average_response_time_ms: float,
               throughput_per_second: float, failure_rate: float,
               resource_usage: Dict[str, float], **kwargs) -> 'ComponentPerformanceModel':
        """Factory method to create a ComponentPerformanceModel with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.COMPONENT_PERFORMANCE,
            entry_id=kwargs.get("entry_id", f"component_performance_{component_id}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            component_id=component_id,
            average_response_time_ms=average_response_time_ms,
            throughput_per_second=throughput_per_second,
            failure_rate=failure_rate,
            resource_usage=resource_usage,
            performance_factors=kwargs.get("performance_factors", {}),
            historical_data=kwargs.get("historical_data", {})
        )


@dataclass
class ReasoningStrategyModel:
    """Model of a reasoning strategy's effectiveness."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Strategy-specific fields
    strategy_name: str
    success_rate: float
    average_duration_ms: float
    applicable_problem_types: List[str]
    preconditions: List[str]
    resource_requirements: Dict[str, float]
    effectiveness_by_domain: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def create(cls, strategy_name: str, success_rate: float, average_duration_ms: float,
               applicable_problem_types: List[str], preconditions: List[str],
               resource_requirements: Dict[str, float], **kwargs) -> 'ReasoningStrategyModel':
        """Factory method to create a ReasoningStrategyModel with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.REASONING_STRATEGY,
            entry_id=kwargs.get("entry_id", f"reasoning_strategy_{strategy_name}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            strategy_name=strategy_name,
            success_rate=success_rate,
            average_duration_ms=average_duration_ms,
            applicable_problem_types=applicable_problem_types,
            preconditions=preconditions,
            resource_requirements=resource_requirements,
            effectiveness_by_domain=kwargs.get("effectiveness_by_domain", {})
        )


@dataclass
class ResourceUsagePattern:
    """Pattern of resource usage over time."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Resource-specific fields
    resource_name: str
    average_usage: float
    peak_usage: float
    usage_trend: str  # "increasing", "decreasing", "stable"
    periodic_patterns: Dict[str, Any] = field(default_factory=dict)
    correlations: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def create(cls, resource_name: str, average_usage: float, peak_usage: float,
               usage_trend: str, **kwargs) -> 'ResourceUsagePattern':
        """Factory method to create a ResourceUsagePattern with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.RESOURCE_USAGE,
            entry_id=kwargs.get("entry_id", f"resource_usage_{resource_name}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            resource_name=resource_name,
            average_usage=average_usage,
            peak_usage=peak_usage,
            usage_trend=usage_trend,
            periodic_patterns=kwargs.get("periodic_patterns", {}),
            correlations=kwargs.get("correlations", {})
        )


@dataclass
class LearningEffectivenessModel:
    """Model of learning effectiveness for different approaches."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Learning-specific fields
    learning_approach: str
    knowledge_gain_rate: float
    convergence_speed: float
    generalization_ability: float
    resource_efficiency: float
    applicable_domains: List[str]
    limitations: List[str] = field(default_factory=list)
    
    @classmethod
    def create(cls, learning_approach: str, knowledge_gain_rate: float, convergence_speed: float,
               generalization_ability: float, resource_efficiency: float, applicable_domains: List[str],
               **kwargs) -> 'LearningEffectivenessModel':
        """Factory method to create a LearningEffectivenessModel with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.LEARNING_EFFECTIVENESS,
            entry_id=kwargs.get("entry_id", f"learning_effectiveness_{learning_approach}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            learning_approach=learning_approach,
            knowledge_gain_rate=knowledge_gain_rate,
            convergence_speed=convergence_speed,
            generalization_ability=generalization_ability,
            resource_efficiency=resource_efficiency,
            applicable_domains=applicable_domains,
            limitations=kwargs.get("limitations", [])
        )


@dataclass
class FailurePattern:
    """Pattern of system failures."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Failure-specific fields
    pattern_name: str
    affected_components: List[str]
    symptoms: List[str]
    root_causes: List[str]
    frequency: float  # occurrences per time unit
    severity: float  # 0.0 to 1.0
    mitigation_strategies: List[str] = field(default_factory=list)
    
    @classmethod
    def create(cls, pattern_name: str, affected_components: List[str], symptoms: List[str],
               root_causes: List[str], frequency: float, severity: float, **kwargs) -> 'FailurePattern':
        """Factory method to create a FailurePattern with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.FAILURE_PATTERN,
            entry_id=kwargs.get("entry_id", f"failure_pattern_{pattern_name}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            pattern_name=pattern_name,
            affected_components=affected_components,
            symptoms=symptoms,
            root_causes=root_causes,
            frequency=frequency,
            severity=severity,
            mitigation_strategies=kwargs.get("mitigation_strategies", [])
        )


@dataclass
class SystemCapability:
    """Description of a system capability."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Capability-specific fields
    capability_name: str
    capability_description: str
    performance_level: float  # 0.0 to 1.0
    reliability: float  # 0.0 to 1.0
    resource_requirements: Dict[str, float]
    dependencies: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    
    @classmethod
    def create(cls, capability_name: str, capability_description: str, performance_level: float,
               reliability: float, resource_requirements: Dict[str, float], **kwargs) -> 'SystemCapability':
        """Factory method to create a SystemCapability with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.SYSTEM_CAPABILITY,
            entry_id=kwargs.get("entry_id", f"system_capability_{capability_name}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            capability_name=capability_name,
            capability_description=capability_description,
            performance_level=performance_level,
            reliability=reliability,
            resource_requirements=resource_requirements,
            dependencies=kwargs.get("dependencies", []),
            limitations=kwargs.get("limitations", [])
        )


@dataclass
class OptimizationHint:
    """Hint for system optimization."""
    # Meta-knowledge fields
    entry_id: str
    entry_type: MetaKnowledgeType
    creation_time: float
    last_updated: float
    confidence: float
    source: str
    metadata: Dict[str, Any]
    
    # Optimization-specific fields
    target_component: str
    optimization_type: str  # "performance", "resource", "reliability"
    expected_improvement: float  # 0.0 to 1.0
    implementation_difficulty: float  # 0.0 to 1.0
    preconditions: List[str]
    side_effects: List[str] = field(default_factory=list)
    
    @classmethod
    def create(cls, target_component: str, optimization_type: str, expected_improvement: float,
               implementation_difficulty: float, preconditions: List[str], **kwargs) -> 'OptimizationHint':
        """Factory method to create an OptimizationHint with proper defaults."""
        base_fields = create_meta_knowledge_entry(
            MetaKnowledgeType.OPTIMIZATION_HINT,
            entry_id=kwargs.get("entry_id", f"optimization_hint_{target_component}_{optimization_type}_{int(time.time())}"),
            **kwargs
        )
        
        return cls(
            **base_fields,
            target_component=target_component,
            optimization_type=optimization_type,
            expected_improvement=expected_improvement,
            implementation_difficulty=implementation_difficulty,
            preconditions=preconditions,
            side_effects=kwargs.get("side_effects", [])
        )


class MetaKnowledgeRepository(Generic[T]):
    """Repository for storing and retrieving meta-knowledge entries of a specific type."""
    
    def __init__(self, entry_type: type):
        """Initialize the repository for a specific entry type."""
        self.entry_type = entry_type
        self.entries: Dict[str, T] = {}
    
    def add(self, entry: T) -> None:
        """Add an entry to the repository."""
        if not isinstance(entry, self.entry_type):
            raise TypeError(f"Entry must be of type {self.entry_type.__name__}")
        
        self.entries[entry.entry_id] = entry
    
    def get(self, entry_id: str) -> Optional[T]:
        """Get an entry by ID."""
        return self.entries.get(entry_id)
    
    def update(self, entry: T) -> None:
        """Update an existing entry."""
        if not isinstance(entry, self.entry_type):
            raise TypeError(f"Entry must be of type {self.entry_type.__name__}")
        
        if entry.entry_id not in self.entries:
            raise KeyError(f"Entry with ID {entry.entry_id} does not exist")
        
        # Update last_updated timestamp
        entry.last_updated = time.time()
        self.entries[entry.entry_id] = entry
    
    def remove(self, entry_id: str) -> None:
        """Remove an entry by ID."""
        if entry_id in self.entries:
            del self.entries[entry_id]
    
    def list_all(self) -> List[T]:
        """List all entries."""
        return list(self.entries.values())
    
    def find_by_attribute(self, attribute: str, value: Any) -> List[T]:
        """Find entries by attribute value."""
        return [entry for entry in self.entries.values() 
                if hasattr(entry, attribute) and getattr(entry, attribute) == value]


class MetaKnowledgeBase:
    """
    Meta-Knowledge Base (MKB) for GödelOS.
    
    The MetaKnowledgeBase stores and manages meta-knowledge about the system's own operation,
    including component performance models, reasoning strategy effectiveness, resource usage
    patterns, and more.
    """
    
    def __init__(
        self,
        kr_system_interface: KnowledgeStoreInterface,
        type_system: TypeSystemManager,
        meta_knowledge_context_id: str = "META_KNOWLEDGE_CONTEXT",
        persistence_directory: Optional[str] = None
    ):
        """Initialize the meta-knowledge base."""
        self.kr_interface = kr_system_interface
        self.type_system = type_system
        self.meta_knowledge_context_id = meta_knowledge_context_id
        self.persistence_directory = persistence_directory
        
        # Create meta-knowledge context if it doesn't exist
        if meta_knowledge_context_id not in kr_system_interface.list_contexts():
            kr_system_interface.create_context(meta_knowledge_context_id, None, "meta_knowledge")
        
        # Initialize repositories for different types of meta-knowledge
        self.component_performance_repo = MetaKnowledgeRepository(ComponentPerformanceModel)
        self.reasoning_strategy_repo = MetaKnowledgeRepository(ReasoningStrategyModel)
        self.resource_usage_repo = MetaKnowledgeRepository(ResourceUsagePattern)
        self.learning_effectiveness_repo = MetaKnowledgeRepository(LearningEffectivenessModel)
        self.failure_pattern_repo = MetaKnowledgeRepository(FailurePattern)
        self.system_capability_repo = MetaKnowledgeRepository(SystemCapability)
        self.optimization_hint_repo = MetaKnowledgeRepository(OptimizationHint)
        
        # Map of meta-knowledge types to repositories
        self.repositories = {
            MetaKnowledgeType.COMPONENT_PERFORMANCE: self.component_performance_repo,
            MetaKnowledgeType.REASONING_STRATEGY: self.reasoning_strategy_repo,
            MetaKnowledgeType.RESOURCE_USAGE: self.resource_usage_repo,
            MetaKnowledgeType.LEARNING_EFFECTIVENESS: self.learning_effectiveness_repo,
            MetaKnowledgeType.FAILURE_PATTERN: self.failure_pattern_repo,
            MetaKnowledgeType.SYSTEM_CAPABILITY: self.system_capability_repo,
            MetaKnowledgeType.OPTIMIZATION_HINT: self.optimization_hint_repo,
        }
        
        # Load persisted data if available
        if persistence_directory:
            self._load_persisted_data()
    
    def add_component_performance_model(
        self,
        component_id: str,
        average_response_time_ms: float,
        throughput_per_second: float,
        failure_rate: float,
        resource_usage: Dict[str, float],
        performance_factors: Optional[Dict[str, float]] = None,
        historical_data: Optional[Dict[str, List[float]]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a component performance model to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the model
        model = ComponentPerformanceModel.create(
            component_id=component_id,
            average_response_time_ms=average_response_time_ms,
            throughput_per_second=throughput_per_second,
            failure_rate=failure_rate,
            resource_usage=resource_usage,
            performance_factors=performance_factors,
            historical_data=historical_data,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = model.entry_id
        
        self.component_performance_repo.add(model)
        self._persist_entry(model)
        self._assert_to_kr_system(model)
        
        return entry_id
    
    def add_reasoning_strategy_model(
        self,
        strategy_name: str,
        success_rate: float,
        average_duration_ms: float,
        applicable_problem_types: List[str],
        preconditions: List[str],
        resource_requirements: Dict[str, float],
        effectiveness_by_domain: Optional[Dict[str, float]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a reasoning strategy model to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the model
        model = ReasoningStrategyModel.create(
            strategy_name=strategy_name,
            success_rate=success_rate,
            average_duration_ms=average_duration_ms,
            applicable_problem_types=applicable_problem_types,
            preconditions=preconditions,
            resource_requirements=resource_requirements,
            effectiveness_by_domain=effectiveness_by_domain,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = model.entry_id
        
        self.reasoning_strategy_repo.add(model)
        self._persist_entry(model)
        self._assert_to_kr_system(model)
        
        return entry_id
    
    def add_resource_usage_pattern(
        self,
        resource_name: str,
        average_usage: float,
        peak_usage: float,
        usage_trend: str,
        periodic_patterns: Optional[Dict[str, Any]] = None,
        correlations: Optional[Dict[str, float]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a resource usage pattern to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the pattern
        pattern = ResourceUsagePattern.create(
            resource_name=resource_name,
            average_usage=average_usage,
            peak_usage=peak_usage,
            usage_trend=usage_trend,
            periodic_patterns=periodic_patterns,
            correlations=correlations,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = pattern.entry_id
        
        self.resource_usage_repo.add(pattern)
        self._persist_entry(pattern)
        self._assert_to_kr_system(pattern)
        
        return entry_id
    
    def add_learning_effectiveness_model(
        self,
        learning_approach: str,
        knowledge_gain_rate: float,
        convergence_speed: float,
        generalization_ability: float,
        resource_efficiency: float,
        applicable_domains: List[str],
        limitations: Optional[List[str]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a learning effectiveness model to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the model
        model = LearningEffectivenessModel.create(
            learning_approach=learning_approach,
            knowledge_gain_rate=knowledge_gain_rate,
            convergence_speed=convergence_speed,
            generalization_ability=generalization_ability,
            resource_efficiency=resource_efficiency,
            applicable_domains=applicable_domains,
            limitations=limitations,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = model.entry_id
        
        self.learning_effectiveness_repo.add(model)
        self._persist_entry(model)
        self._assert_to_kr_system(model)
        
        return entry_id
    
    def add_failure_pattern(
        self,
        pattern_name: str,
        affected_components: List[str],
        symptoms: List[str],
        root_causes: List[str],
        frequency: float,
        severity: float,
        mitigation_strategies: Optional[List[str]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a failure pattern to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the pattern
        pattern = FailurePattern.create(
            pattern_name=pattern_name,
            affected_components=affected_components,
            symptoms=symptoms,
            root_causes=root_causes,
            frequency=frequency,
            severity=severity,
            mitigation_strategies=mitigation_strategies,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = pattern.entry_id
        
        self.failure_pattern_repo.add(pattern)
        self._persist_entry(pattern)
        self._assert_to_kr_system(pattern)
        
        return entry_id
    
    def add_system_capability(
        self,
        capability_name: str,
        capability_description: str,
        performance_level: float,
        reliability: float,
        resource_requirements: Dict[str, float],
        dependencies: Optional[List[str]] = None,
        limitations: Optional[List[str]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a system capability to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the capability
        capability = SystemCapability.create(
            capability_name=capability_name,
            capability_description=capability_description,
            performance_level=performance_level,
            reliability=reliability,
            resource_requirements=resource_requirements,
            dependencies=dependencies,
            limitations=limitations,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = capability.entry_id
        
        self.system_capability_repo.add(capability)
        self._persist_entry(capability)
        self._assert_to_kr_system(capability)
        
        return entry_id
    
    def add_optimization_hint(
        self,
        target_component: str,
        optimization_type: str,
        expected_improvement: float,
        implementation_difficulty: float,
        preconditions: List[str],
        side_effects: Optional[List[str]] = None,
        confidence: float = 1.0,
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an optimization hint to the meta-knowledge base.
        
        Returns:
            The ID of the newly created entry
        """
        # Use the factory method to create the hint
        hint = OptimizationHint.create(
            target_component=target_component,
            optimization_type=optimization_type,
            expected_improvement=expected_improvement,
            implementation_difficulty=implementation_difficulty,
            preconditions=preconditions,
            side_effects=side_effects,
            confidence=confidence,
            source=source,
            metadata=metadata
        )
        entry_id = hint.entry_id
        
        self.optimization_hint_repo.add(hint)
        self._persist_entry(hint)
        self._assert_to_kr_system(hint)
        
        return entry_id
    
    def get_entry(self, entry_id: str) -> Optional[MetaKnowledgeEntry]:
        """Get a meta-knowledge entry by ID."""
        for repo in self.repositories.values():
            entry = repo.get(entry_id)
            if entry:
                return entry
        
        return None
    
    def update_entry(self, entry) -> None:
        """Update a meta-knowledge entry."""
        # Check if entry has the required fields
        required_fields = ['entry_id', 'entry_type']
        for field in required_fields:
            if not hasattr(entry, field):
                raise TypeError(f"Entry must have field '{field}'")
        
        repo = self.repositories.get(entry.entry_type)
        if not repo:
            raise ValueError(f"No repository for entry type {entry.entry_type}")
        
        repo.update(entry)
        self._persist_entry(entry)
        self._update_kr_system(entry)
    
    def remove_entry(self, entry_id: str) -> bool:
        """
        Remove a meta-knowledge entry by ID.
        
        Returns:
            True if the entry was found and removed, False otherwise
        """
        for repo in self.repositories.values():
            entry = repo.get(entry_id)
            if entry:
                repo.remove(entry_id)
                self._remove_from_kr_system(entry)
                self._remove_persisted_entry(entry_id)
                return True
        
        return False
    
    def get_entries_by_type(self, entry_type: MetaKnowledgeType) -> List[MetaKnowledgeEntry]:
        """Get all meta-knowledge entries of a specific type."""
        repo = self.repositories.get(entry_type)
        if not repo:
            raise KeyError(f"No repository for entry type {entry_type}")
        
        return repo.list_all()
    
    def get_component_performance_model(self, component_id: str) -> Optional[ComponentPerformanceModel]:
        """Get the most recent performance model for a component."""
        models = self.component_performance_repo.find_by_attribute("component_id", component_id)
        
        if not models:
            return None
        
        # Return the most recently updated model
        return max(models, key=lambda m: m.last_updated)
    
    def get_reasoning_strategy_model(self, strategy_name: str) -> Optional[ReasoningStrategyModel]:
        """Get the most recent model for a reasoning strategy."""
        models = self.reasoning_strategy_repo.find_by_attribute("strategy_name", strategy_name)
        
        if not models:
            return None
        
        # Return the most recently updated model
        return max(models, key=lambda m: m.last_updated)
    
    def get_resource_usage_pattern(self, resource_name: str) -> Optional[ResourceUsagePattern]:
        """Get the most recent usage pattern for a resource."""
        patterns = self.resource_usage_repo.find_by_attribute("resource_name", resource_name)
        
        if not patterns:
            return None
        
        # Return the most recently updated pattern
        return max(patterns, key=lambda p: p.last_updated)
    
    def get_learning_effectiveness_model(self, learning_approach: str) -> Optional[LearningEffectivenessModel]:
        """Get the most recent effectiveness model for a learning approach."""
        models = self.learning_effectiveness_repo.find_by_attribute("learning_approach", learning_approach)
        
        if not models:
            return None
        
        # Return the most recently updated model
        return max(models, key=lambda m: m.last_updated)
    
    def get_failure_patterns_for_component(self, component_id: str) -> List[FailurePattern]:
        """Get all failure patterns affecting a component."""
        all_patterns = self.failure_pattern_repo.list_all()
        
        return [pattern for pattern in all_patterns if component_id in pattern.affected_components]
    
    def get_system_capability(self, capability_name: str) -> Optional[SystemCapability]:
        """Get the most recent model for a system capability."""
        capabilities = self.system_capability_repo.find_by_attribute("capability_name", capability_name)
        
        if not capabilities:
            return None
        
        # Return the most recently updated capability
        return max(capabilities, key=lambda c: c.last_updated)
    
    def get_optimization_hints_for_component(self, component_id: str) -> List[OptimizationHint]:
        """Get all optimization hints for a component."""
        return self.optimization_hint_repo.find_by_attribute("target_component", component_id)
    
    def search_entries(
        self, 
        keywords: List[str], 
        entry_types: Optional[List[MetaKnowledgeType]] = None,
        min_confidence: float = 0.0,
        max_age_days: Optional[float] = None
    ) -> List[MetaKnowledgeEntry]:
        """
        Search for meta-knowledge entries matching keywords.
        
        Args:
            keywords: List of keywords to search for
            entry_types: Optional list of entry types to search in
            min_confidence: Minimum confidence level
            max_age_days: Maximum age in days
            
        Returns:
            List of matching entries
        """
        results = []
        
        repos_to_search = [self.repositories[t] for t in entry_types] if entry_types else self.repositories.values()
        
        for repo in repos_to_search:
            for entry in repo.list_all():
                # Check confidence
                if entry.confidence < min_confidence:
                    continue
                
                # Check age
                if max_age_days is not None:
                    age_days = (time.time() - entry.creation_time) / (24 * 3600)
                    if age_days > max_age_days:
                        continue
                
                # Check keywords
                entry_dict = asdict(entry)
                entry_str = json.dumps(entry_dict, cls=MetaKnowledgeEncoder).lower()
                
                if all(keyword.lower() in entry_str for keyword in keywords):
                    results.append(entry)
        
        return results
    
    def export_to_json(self, file_path: str) -> None:
        """Export all meta-knowledge to a JSON file."""
        all_entries = []
        
        for repo in self.repositories.values():
            for entry in repo.list_all():
                all_entries.append(asdict(entry))
        
        with open(file_path, 'w') as f:
            json.dump(all_entries, f, indent=2, cls=MetaKnowledgeEncoder)
    
    def _persist_entry(self, entry: MetaKnowledgeEntry) -> None:
        """Persist an entry to disk if persistence is enabled."""
        if not self.persistence_directory:
            return
        
        os.makedirs(self.persistence_directory, exist_ok=True)
        
        file_path = os.path.join(self.persistence_directory, f"{entry.entry_id}.pickle")
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)
        except (IOError, OSError) as e:
            # Log the error but don't raise an exception
            logger.error(f"Error persisting entry {entry.entry_id}: {e}")
    
    def _remove_persisted_entry(self, entry_id: str) -> None:
        """Remove a persisted entry from disk."""
        if not self.persistence_directory:
            return
        
        file_path = os.path.join(self.persistence_directory, f"{entry_id}.pickle")
        
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def _load_persisted_data(self) -> None:
        """Load persisted data from disk."""
        if not self.persistence_directory or not os.path.exists(self.persistence_directory):
            return
        
        for file_name in os.listdir(self.persistence_directory):
            if file_name.endswith('.pickle'):
                file_path = os.path.join(self.persistence_directory, file_name)
                
                try:
                    with open(file_path, 'rb') as f:
                        entry = pickle.load(f)
                        
                        if isinstance(entry, MetaKnowledgeEntry):
                            repo = self.repositories.get(entry.entry_type)
                            if repo:
                                repo.add(entry)
                except Exception as e:
                    logger.error(f"Error loading persisted entry {file_name}: {e}")
    
    def _assert_to_kr_system(self, entry: MetaKnowledgeEntry) -> None:
        """Assert a meta-knowledge entry to the KR system."""
        # Convert the entry to AST nodes and assert to the KR system
        # This is a simplified implementation that would need to be expanded
        # based on the actual KR system's capabilities
        
        try:
            # Get necessary types from type system
            entity_type = self.type_system.get_type("Entity") or self.type_system.get_type("Object")
            prop_type = self.type_system.get_type("Proposition")
            float_type = self.type_system.get_type("Float") or self.type_system.get_type("Real")
            string_type = self.type_system.get_type("String")
            
            # Create a simple predicate for the entry
            predicate = ApplicationNode(
                operator=ConstantNode(f"Has{entry.entry_type.value.title().replace('_', '')}", prop_type),
                arguments=[
                    ConstantNode(entry.entry_id, entity_type),
                    ConstantNode(str(entry.confidence), float_type)
                ],
                type_ref=prop_type
            )
            
            # Assert the predicate to the meta-knowledge context
            self.kr_interface.assert_statement(
                context_id=self.meta_knowledge_context_id,
                statement=predicate
            )
        except Exception as e:
            # Log the error but don't raise an exception
            logger.error(f"Error asserting entry {entry.entry_id} to KR system: {e}")
    
    def _update_kr_system(self, entry: MetaKnowledgeEntry) -> None:
        """Update a meta-knowledge entry in the KR system."""
        try:
            # For simplicity, we'll just remove and re-assert
            self._remove_from_kr_system(entry)
            self._assert_to_kr_system(entry)
        except Exception as e:
            # Log the error but don't raise an exception
            logger.error(f"Error updating entry {entry.entry_id} in KR system: {e}")
    
    def _remove_from_kr_system(self, entry: MetaKnowledgeEntry) -> None:
        """Remove a meta-knowledge entry from the KR system."""
        try:
            # This is a simplified implementation that would need to be expanded
            # based on the actual KR system's capabilities
            
            # Get necessary types from type system
            entity_type = self.type_system.get_type("Entity") or self.type_system.get_type("Object")
            prop_type = self.type_system.get_type("Proposition")
            
            # Create a variable for the confidence
            float_type = self.type_system.get_type("Float") or self.type_system.get_type("Real")
            # Generate a unique ID for the variable
            var_id = hash(f"Confidence_{time.time()}")
            confidence_var = VariableNode(name="Confidence", var_id=var_id, type_ref=float_type)
            
            # Create a pattern to match the predicate
            pattern = ApplicationNode(
                operator=ConstantNode(f"Has{entry.entry_type.value.title().replace('_', '')}", prop_type),
                arguments=[
                    ConstantNode(entry.entry_id, entity_type),
                    confidence_var
                ],
                type_ref=prop_type
            )
            
            # Retract matching statements from the meta-knowledge context
            self.kr_interface.retract_matching(
                self.meta_knowledge_context_id,
                pattern
            )
        except Exception as e:
            # Log the error but don't raise an exception
            logger.error(f"Error removing entry {entry.entry_id} from KR system: {e}")