"""
Internal State Monitor (ISM) for GödelOS.

This module implements the InternalStateMonitor component (Module 4.5) of the Symbol Grounding System,
which is responsible for providing symbolic access to aspects of the agent's own internal cognitive
and computational state for introspection and metacognition.

The InternalStateMonitor performs:
1. Monitoring of system metrics (e.g., CPU load, memory usage)
2. Monitoring of module states (e.g., inference engine, learning modules)
3. Abstracting low-level metrics into symbolic predicates
4. Asserting symbolic internal state facts to a dedicated "InternalStateContext" in the KR System
"""

import logging
import time
import threading
import os
import platform
import psutil
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode

logger = logging.getLogger(__name__)


class ResourceStatus(Enum):
    """Enum representing qualitative status of a system resource."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ModuleStatus(Enum):
    """Enum representing the status of a GödelOS module."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class SystemMetric:
    """
    Represents a system metric with its value and metadata.
    
    Attributes:
        name: Name of the metric
        value: Current value of the metric
        unit: Unit of measurement
        status: Qualitative status based on thresholds
        timestamp: Time when the metric was collected
    """
    name: str
    value: float
    unit: str
    status: ResourceStatus
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModuleState:
    """
    Represents the state of a GödelOS module.
    
    Attributes:
        module_id: Identifier of the module
        status: Current status of the module
        metrics: Dictionary of module-specific metrics
        timestamp: Time when the state was collected
    """
    module_id: str
    status: ModuleStatus
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SystemMetricAccessAPI:
    """
    API for accessing system-level metrics like CPU, memory, etc.
    """
    
    @staticmethod
    def get_cpu_load() -> float:
        """
        Get the current CPU load as a percentage.
        
        Returns:
            CPU load as a percentage (0-100)
        """
        return psutil.cpu_percent(interval=0.1)
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """
        Get the current memory usage statistics.
        
        Returns:
            Dictionary with memory usage statistics
        """
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free
        }
    
    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """
        Get the current disk usage statistics.
        
        Returns:
            Dictionary with disk usage statistics
        """
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """
        Get basic system information.
        
        Returns:
            Dictionary with system information
        """
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }


class ModuleIntrospectionAPI:
    """
    API for introspecting GödelOS modules to get their current state.
    
    This is a base class that should be extended by specific module APIs.
    """
    
    def __init__(self, module_id: str):
        """
        Initialize a module introspection API.
        
        Args:
            module_id: Identifier of the module
        """
        self.module_id = module_id
    
    def get_module_state(self) -> ModuleState:
        """
        Get the current state of the module.
        
        Returns:
            ModuleState object representing the current state
        """
        raise NotImplementedError("Subclasses must implement get_module_state()")


class InferenceEngineAPI(ModuleIntrospectionAPI):
    """
    API for introspecting the Inference Engine module.
    """
    
    def __init__(self, inference_engine=None):
        """
        Initialize an Inference Engine introspection API.
        
        Args:
            inference_engine: Optional reference to the inference engine
        """
        super().__init__("InferenceEngine")
        self.inference_engine = inference_engine
    
    def get_module_state(self) -> ModuleState:
        """
        Get the current state of the Inference Engine.
        
        Returns:
            ModuleState object representing the current state
        """
        # If we have a reference to the inference engine, query it directly
        if self.inference_engine:
            # This would be replaced with actual calls to the inference engine's API
            active_tasks = getattr(self.inference_engine, 'get_active_tasks', lambda: [])()
            status = ModuleStatus.ACTIVE if active_tasks else ModuleStatus.IDLE
            
            metrics = {
                "active_tasks": len(active_tasks),
                "inference_steps_per_second": getattr(self.inference_engine, 'get_inference_rate', lambda: 0)(),
                "average_proof_time_ms": getattr(self.inference_engine, 'get_average_proof_time', lambda: 0)()
            }
        else:
            # Mock data for testing or when inference engine is not available
            status = ModuleStatus.IDLE
            metrics = {
                "active_tasks": 0,
                "inference_steps_per_second": 0,
                "average_proof_time_ms": 0
            }
        
        return ModuleState(
            module_id=self.module_id,
            status=status,
            metrics=metrics
        )


class LearningSystemAPI(ModuleIntrospectionAPI):
    """
    API for introspecting the Learning System module.
    """
    
    def __init__(self, learning_system=None):
        """
        Initialize a Learning System introspection API.
        
        Args:
            learning_system: Optional reference to the learning system
        """
        super().__init__("LearningSystem")
        self.learning_system = learning_system
    
    def get_module_state(self) -> ModuleState:
        """
        Get the current state of the Learning System.
        
        Returns:
            ModuleState object representing the current state
        """
        # If we have a reference to the learning system, query it directly
        if self.learning_system:
            # This would be replaced with actual calls to the learning system's API
            active_learning_processes = getattr(self.learning_system, 'get_active_learning_processes', lambda: [])()
            status = ModuleStatus.ACTIVE if active_learning_processes else ModuleStatus.IDLE
            
            metrics = {
                "active_learning_processes": len(active_learning_processes),
                "rules_learned": getattr(self.learning_system, 'get_rules_learned_count', lambda: 0)(),
                "learning_cycles_completed": getattr(self.learning_system, 'get_learning_cycles_completed', lambda: 0)()
            }
        else:
            # Mock data for testing or when learning system is not available
            status = ModuleStatus.IDLE
            metrics = {
                "active_learning_processes": 0,
                "rules_learned": 0,
                "learning_cycles_completed": 0
            }
        
        return ModuleState(
            module_id=self.module_id,
            status=status,
            metrics=metrics
        )


class KRSystemAPI(ModuleIntrospectionAPI):
    """
    API for introspecting the Knowledge Representation System module.
    """
    
    def __init__(self, kr_system_interface=None):
        """
        Initialize a KR System introspection API.
        
        Args:
            kr_system_interface: Optional reference to the KR system interface
        """
        super().__init__("KRSystem")
        self.kr_system_interface = kr_system_interface
    
    def get_module_state(self) -> ModuleState:
        """
        Get the current state of the KR System.
        
        Returns:
            ModuleState object representing the current state
        """
        # If we have a reference to the KR system, query it directly
        if self.kr_system_interface:
            # This would be replaced with actual calls to the KR system's API
            contexts = self.kr_system_interface.list_contexts()
            
            metrics = {
                "context_count": len(contexts),
                "query_rate_per_second": getattr(self.kr_system_interface, 'get_query_rate', lambda: 0)(),
                "statement_count": getattr(self.kr_system_interface, 'get_statement_count', lambda: 0)()
            }
            
            # Determine status based on query rate
            query_rate = metrics["query_rate_per_second"]
            if query_rate > 100:
                status = ModuleStatus.BUSY
            elif query_rate > 0:
                status = ModuleStatus.ACTIVE
            else:
                status = ModuleStatus.IDLE
        else:
            # Mock data for testing or when KR system is not available
            status = ModuleStatus.IDLE
            metrics = {
                "context_count": 0,
                "query_rate_per_second": 0,
                "statement_count": 0
            }
        
        return ModuleState(
            module_id=self.module_id,
            status=status,
            metrics=metrics
        )


class InternalStatePredicateSchema:
    """
    Defines the schema for internal state predicates in the agent's ontology.
    
    This class provides methods to create AST nodes representing internal state predicates.
    """
    
    def __init__(self, type_system: TypeSystemManager):
        """
        Initialize the internal state predicate schema.
        
        Args:
            type_system: Type system manager for creating typed AST nodes
        """
        self.type_system = type_system
        
        # Get necessary types from type system
        self.entity_type = type_system.get_type("Entity") or type_system.get_type("Object")
        self.prop_type = type_system.get_type("Proposition")
        self.float_type = type_system.get_type("Float") or type_system.get_type("Real")
        self.int_type = type_system.get_type("Integer") or type_system.get_type("Int")
        self.string_type = type_system.get_type("String")
    
    def create_system_resource_level_predicate(self, resource_name: str, current_value: float, 
                                               unit: str, status: ResourceStatus) -> AST_Node:
        """
        Create a SystemResourceLevel predicate AST node.
        
        Args:
            resource_name: Name of the resource
            current_value: Current value of the resource
            unit: Unit of measurement
            status: Qualitative status of the resource
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("SystemResourceLevel", self.prop_type),
            arguments=[
                ConstantNode(resource_name, self.entity_type),
                ConstantNode(str(current_value), self.float_type),
                ConstantNode(unit, self.entity_type),
                ConstantNode(status.value, self.entity_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_cognitive_operation_count_predicate(self, operation_type: str, count: int, 
                                                  time_unit: str) -> AST_Node:
        """
        Create a CognitiveOperationCount predicate AST node.
        
        Args:
            operation_type: Type of cognitive operation
            count: Count of operations
            time_unit: Time unit for the count
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("CognitiveOperationCount", self.prop_type),
            arguments=[
                ConstantNode(operation_type, self.entity_type),
                ConstantNode(str(count), self.int_type),
                ConstantNode(time_unit, self.entity_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_current_primary_goal_predicate(self, goal_id: str) -> AST_Node:
        """
        Create a CurrentPrimaryGoal predicate AST node.
        
        Args:
            goal_id: Identifier of the current primary goal
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("CurrentPrimaryGoal", self.prop_type),
            arguments=[
                ConstantNode(goal_id, self.entity_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_goal_queue_length_predicate(self, length: int) -> AST_Node:
        """
        Create a GoalQueueLength predicate AST node.
        
        Args:
            length: Length of the goal queue
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("GoalQueueLength", self.prop_type),
            arguments=[
                ConstantNode(str(length), self.int_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_active_reasoning_strategy_predicate(self, strategy_name: str) -> AST_Node:
        """
        Create an ActiveReasoningStrategy predicate AST node.
        
        Args:
            strategy_name: Name of the active reasoning strategy
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("ActiveReasoningStrategy", self.prop_type),
            arguments=[
                ConstantNode(strategy_name, self.entity_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_learning_module_status_predicate(self, module_id: str, status: ModuleStatus) -> AST_Node:
        """
        Create a LearningModuleStatus predicate AST node.
        
        Args:
            module_id: Identifier of the learning module
            status: Status of the learning module
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("LearningModuleStatus", self.prop_type),
            arguments=[
                ConstantNode(module_id, self.entity_type),
                ConstantNode(status.value, self.entity_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_attention_focus_on_predicate(self, symbol_or_goal_id: str) -> AST_Node:
        """
        Create an AttentionFocusOn predicate AST node.
        
        Args:
            symbol_or_goal_id: Identifier of the symbol or goal in focus
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("AttentionFocusOn", self.prop_type),
            arguments=[
                ConstantNode(symbol_or_goal_id, self.entity_type)
            ],
            type_ref=self.prop_type
        )
    
    def create_module_status_predicate(self, module_id: str, status: ModuleStatus) -> AST_Node:
        """
        Create a ModuleStatus predicate AST node.
        
        Args:
            module_id: Identifier of the module
            status: Status of the module
            
        Returns:
            AST node representing the predicate
        """
        return ApplicationNode(
            operator=ConstantNode("ModuleStatus", self.prop_type),
            arguments=[
                ConstantNode(module_id, self.entity_type),
                ConstantNode(status.value, self.entity_type)
            ],
            type_ref=self.prop_type
        )


class InternalStateMonitor:
    """
    Internal State Monitor (ISM) for GödelOS.
    
    The InternalStateMonitor provides symbolic access to aspects of the agent's own internal
    cognitive and computational state for introspection and metacognition.
    """
    
    def __init__(self, 
                 kr_system_interface: KnowledgeStoreInterface,
                 type_system: TypeSystemManager,
                 internal_state_context_id: str = "INTERNAL_STATE_CONTEXT",
                 system_apis: Optional[Dict[str, Any]] = None,
                 module_apis: Optional[Dict[str, ModuleIntrospectionAPI]] = None,
                 poll_interval_sec: float = 5.0):
        """
        Initialize the internal state monitor.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation System
            type_system: Type system manager
            internal_state_context_id: ID of the context for internal state facts
            system_apis: Optional dictionary of system APIs
            module_apis: Optional dictionary of module introspection APIs
            poll_interval_sec: Interval in seconds for polling system and module states
        """
        self.kr_interface = kr_system_interface
        self.type_system = type_system
        self.internal_state_context_id = internal_state_context_id
        self.poll_interval_sec = poll_interval_sec
        
        # Create internal state context if it doesn't exist
        if internal_state_context_id not in kr_system_interface.list_contexts():
            kr_system_interface.create_context(internal_state_context_id, None, "internal_state")
        
        # Initialize predicate schema
        self.predicate_schema = InternalStatePredicateSchema(type_system)
        
        # Initialize system APIs
        self.system_metric_api = SystemMetricAccessAPI()
        
        # Initialize module APIs
        self.module_apis = module_apis or {
            "InferenceEngine": InferenceEngineAPI(),
            "LearningSystem": LearningSystemAPI(),
            "KRSystem": KRSystemAPI(kr_system_interface)
        }
        
        # Initialize monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # Cache for previous state facts
        self.previous_state_facts = {}
    
    def start_monitoring(self) -> None:
        """
        Start the monitoring thread.
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Started internal state monitoring thread")
    
    def stop_monitoring(self) -> None:
        """
        Stop the monitoring thread.
        """
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is not running")
            return
        
        self.stop_monitoring.set()
        self.monitoring_thread.join(timeout=2.0)
        logger.info("Stopped internal state monitoring thread")
    
    def _monitoring_loop(self) -> None:
        """
        Main monitoring loop that periodically collects and processes system and module states.
        """
        while not self.stop_monitoring.is_set():
            try:
                self.perform_monitoring_cycle()
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
            
            # Sleep until next cycle
            self.stop_monitoring.wait(self.poll_interval_sec)
    
    def perform_monitoring_cycle(self) -> None:
        """
        Perform a single monitoring cycle.
        
        This method:
        1. Collects system metrics and module states
        2. Abstracts the raw data into symbolic representations
        3. Generates AST nodes for the internal state facts
        4. Asserts the facts to the KR system
        """
        # 1. Collect system metrics
        system_metrics = self._collect_system_metrics()
        
        # 2. Collect module states
        module_states = self._collect_module_states()
        
        # 3. Generate AST nodes for internal state facts
        state_facts = []
        
        # 3.1 Generate facts for system metrics
        for metric in system_metrics:
            fact = self.predicate_schema.create_system_resource_level_predicate(
                resource_name=metric.name,
                current_value=metric.value,
                unit=metric.unit,
                status=metric.status
            )
            state_facts.append(fact)
        
        # 3.2 Generate facts for module states
        for module_state in module_states:
            # Basic module status fact
            fact = self.predicate_schema.create_module_status_predicate(
                module_id=module_state.module_id,
                status=module_state.status
            )
            state_facts.append(fact)
            
            # Additional facts for specific modules
            if module_state.module_id == "InferenceEngine":
                if "inference_steps_per_second" in module_state.metrics:
                    fact = self.predicate_schema.create_cognitive_operation_count_predicate(
                        operation_type="InferenceSteps",
                        count=int(module_state.metrics["inference_steps_per_second"]),
                        time_unit="PerSecond"
                    )
                    state_facts.append(fact)
            
            elif module_state.module_id == "LearningSystem":
                if module_state.status != ModuleStatus.IDLE:
                    fact = self.predicate_schema.create_learning_module_status_predicate(
                        module_id=module_state.module_id,
                        status=module_state.status
                    )
                    state_facts.append(fact)
        
        # 4. Assert facts to KR system
        self._assert_state_facts(state_facts)
    
    def _collect_system_metrics(self) -> List[SystemMetric]:
        """
        Collect system metrics using the system metric access API.
        
        Returns:
            List of SystemMetric objects
        """
        metrics = []
        
        # CPU load
        cpu_load = psutil.cpu_percent(interval=0.1)
        cpu_status = ResourceStatus.LOW
        if cpu_load > 90:
            cpu_status = ResourceStatus.CRITICAL
        elif cpu_load > 70:
            cpu_status = ResourceStatus.HIGH
        elif cpu_load > 30:
            cpu_status = ResourceStatus.MODERATE
        
        metrics.append(SystemMetric(
            name="CPU",
            value=cpu_load,
            unit="Percent",
            status=cpu_status
        ))
        
        # Memory usage
        mem = psutil.virtual_memory()
        memory = {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used,
            "free": mem.free
        }
        memory_status = ResourceStatus.LOW
        if memory["percent"] > 90:
            memory_status = ResourceStatus.CRITICAL
        elif memory["percent"] > 70:
            memory_status = ResourceStatus.HIGH
        elif memory["percent"] > 30:
            memory_status = ResourceStatus.MODERATE
        
        metrics.append(SystemMetric(
            name="Memory",
            value=memory["percent"],
            unit="Percent",
            status=memory_status
        ))
        
        # Disk usage
        disk_info = psutil.disk_usage('/')
        disk = {
            "total": disk_info.total,
            "used": disk_info.used,
            "free": disk_info.free,
            "percent": disk_info.percent
        }
        disk_status = ResourceStatus.LOW
        if disk["percent"] > 90:
            disk_status = ResourceStatus.CRITICAL
        elif disk["percent"] > 70:
            disk_status = ResourceStatus.HIGH
        elif disk["percent"] > 30:
            disk_status = ResourceStatus.MODERATE
        
        metrics.append(SystemMetric(
            name="Disk",
            value=disk["percent"],
            unit="Percent",
            status=disk_status
        ))
        
        return metrics
    
    def _collect_module_states(self) -> List[ModuleState]:
        """
        Collect module states using the module introspection APIs.
        
        Returns:
            List of ModuleState objects
        """
        states = []
        
        for module_id, api in self.module_apis.items():
            try:
                state = api.get_module_state()
                states.append(state)
            except Exception as e:
                logger.error(f"Error collecting state for module {module_id}: {e}")
                # Create a fallback state with ERROR status
                states.append(ModuleState(
                    module_id=module_id,
                    status=ModuleStatus.ERROR,
                    metrics={"error": str(e)}
                ))
        
        return states
    
    def _assert_state_facts(self, state_facts: List[AST_Node]) -> None:
        """
        Assert internal state facts to the KR system.
        
        This method also handles retracting old facts that are no longer valid.
        
        Args:
            state_facts: List of AST nodes representing internal state facts
        """
        # Get current timestamp
        timestamp = time.time()
        
        # Assert new facts
        for fact in state_facts:
            fact_str = str(fact)
            self.kr_interface.add_statement(fact, self.internal_state_context_id)
            self.previous_state_facts[fact_str] = timestamp
        
        # Retract old facts that are no longer valid
        # This is a simplified approach; in a real system, we might use more sophisticated
        # temporal reasoning or fact lifecycle management
        facts_to_retract = []
        for fact_str, last_updated in self.previous_state_facts.items():
            if timestamp - last_updated > self.poll_interval_sec * 2:
                # This fact is stale (hasn't been updated in 2 polling cycles)
                facts_to_retract.append(fact_str)
        
        for fact_str in facts_to_retract:
            # In a real system, we would parse the fact string back to an AST node
            # or use a more direct way to reference the fact in the KR system
            # For simplicity, we'll just remove it from our cache
            del self.previous_state_facts[fact_str]
    
    def subscribe_to_event(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to a specific type of internal event.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when the event occurs
        """
        # This is a placeholder for a more sophisticated event subscription system
        # In a real implementation, this would register callbacks with various modules
        # to receive notifications about important state changes
        logger.info(f"Subscribed to event type: {event_type}")
    
    def get_current_state_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current internal state.
        
        Returns:
            Dictionary summarizing the current internal state
        """
        # This is a convenience method for quickly accessing the current state
        # without going through the KR system
        
        system_metrics = self._collect_system_metrics()
        module_states = self._collect_module_states()
        
        return {
            "system_metrics": {m.name: {"value": m.value, "unit": m.unit, "status": m.status.value} 
                              for m in system_metrics},
            "module_states": {s.module_id: {"status": s.status.value, "metrics": s.metrics} 
                             for s in module_states},
            "timestamp": time.time()
        }