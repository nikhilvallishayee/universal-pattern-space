"""
Action Executor (AE) for GödelOS.

This module implements the ActionExecutor component (Module 4.3) of the Symbol Grounding System,
which is responsible for translating high-level symbolic action ASTs into sequences of primitive
commands executable by the SimulatedEnvironment (SimEnv), monitoring their execution, and
reporting the symbolic outcome of the action back to the agent's KR system.

The ActionExecutor performs:
1. Translation of high-level symbolic actions into primitive commands
2. Monitoring of execution by observing SimEnv outcomes and perceptual changes
3. Reporting of symbolic outcomes (success, failure, key observed effects) back to the KR system
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import time

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode
from godelOS.symbol_grounding.simulated_environment import SimulatedEnvironment, ActionOutcome

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    """Enum representing the status of an action execution."""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class ActionResult:
    """
    Represents the result of executing an action.
    
    Attributes:
        status: The status of the action execution
        message: A message describing the result
        effects: Observed effects of the action
        precondition_failures: List of preconditions that failed, if any
        execution_trace: List of primitive commands executed and their outcomes
    """
    status: ActionStatus
    message: str = ""
    effects: List[AST_Node] = field(default_factory=list)
    precondition_failures: List[Tuple[AST_Node, str]] = field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ActionParameter:
    """
    Represents a parameter for an action schema.
    
    Attributes:
        name: The name of the parameter
        type_name: The type name of the parameter
        description: Optional description of the parameter
    """
    name: str
    type_name: str
    description: str = ""


@dataclass
class ActionSchema:
    """
    Represents a schema for an action, defining its parameters, preconditions, effects,
    and decomposition into primitive commands.
    
    Attributes:
        name: The name of the action
        parameters: List of parameters for the action
        preconditions: List of AST nodes representing preconditions
        effects: List of AST nodes representing effects
        decomposition: Function that decomposes the action into primitive commands
        description: Optional description of the action
    """
    name: str
    parameters: List[ActionParameter]
    preconditions: List[AST_Node]
    effects: List[AST_Node]
    decomposition: Callable[[Dict[str, Any], Dict[str, Any]], List[Dict[str, Any]]]
    description: str = ""


class ActionExecutor:
    """
    Action Executor (AE) for GödelOS.
    
    The ActionExecutor translates high-level symbolic actions into primitive commands
    executable by the SimulatedEnvironment, monitors their execution, and reports the
    symbolic outcome of the action back to the agent's KR system.
    """
    
    def __init__(self, 
                 simulated_environment: SimulatedEnvironment,
                 kr_interface: KnowledgeStoreInterface,
                 type_system: TypeSystemManager,
                 action_schemas_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the action executor.
        
        Args:
            simulated_environment: The simulated environment to interact with
            kr_interface: Interface to the Knowledge Representation System
            type_system: Type system manager
            action_schemas_config: Optional configuration for action schemas
        """
        self.simenv = simulated_environment
        self.kr_interface = kr_interface
        self.type_system = type_system
        
        # Create action context if it doesn't exist
        if "ACTION_CONTEXT" not in kr_interface.list_contexts():
            kr_interface.create_context("ACTION_CONTEXT", None, "action")
        
        # Initialize action schemas
        self.action_schemas = self._init_action_schemas(action_schemas_config)
        
        # Track ongoing actions
        self.ongoing_actions: Dict[str, Dict[str, Any]] = {}
        
        # Cache for action parameters
        self.param_cache: Dict[str, Dict[str, Any]] = {}
    
    def _init_action_schemas(self, config: Optional[Dict[str, Any]]) -> Dict[str, ActionSchema]:
        """
        Initialize action schemas based on configuration.
        
        Args:
            config: Optional configuration for action schemas
            
        Returns:
            Dictionary mapping action names to action schemas
        """
        # Default action schemas
        schemas = {}
        
        # Add Move action schema
        schemas["Move"] = ActionSchema(
            name="Move",
            parameters=[
                ActionParameter("agent", "Agent", "The agent performing the move"),
                ActionParameter("target_location", "Location", "The target location to move to")
            ],
            preconditions=[
                # Preconditions would be AST nodes checking if the move is possible
                # For simplicity, we'll use empty preconditions for now
            ],
            effects=[
                # Effects would be AST nodes describing the new state after moving
                # For simplicity, we'll use empty effects for now
            ],
            decomposition=self._decompose_move_action,
            description="Move an agent to a target location"
        )
        
        # Add PickUp action schema
        schemas["PickUp"] = ActionSchema(
            name="PickUp",
            parameters=[
                ActionParameter("agent", "Agent", "The agent performing the pickup"),
                ActionParameter("object", "Object", "The object to pick up")
            ],
            preconditions=[
                # Preconditions would be AST nodes checking if the pickup is possible
                # For simplicity, we'll use empty preconditions for now
            ],
            effects=[
                # Effects would be AST nodes describing the new state after picking up
                # For simplicity, we'll use empty effects for now
            ],
            decomposition=self._decompose_pickup_action,
            description="Pick up an object"
        )
        
        # Add PutDown action schema
        schemas["PutDown"] = ActionSchema(
            name="PutDown",
            parameters=[
                ActionParameter("agent", "Agent", "The agent performing the put down"),
                ActionParameter("object", "Object", "The object to put down"),
                ActionParameter("target_location", "Location", "The location to put the object")
            ],
            preconditions=[
                # Preconditions would be AST nodes checking if the put down is possible
                # For simplicity, we'll use empty preconditions for now
            ],
            effects=[
                # Effects would be AST nodes describing the new state after putting down
                # For simplicity, we'll use empty effects for now
            ],
            decomposition=self._decompose_putdown_action,
            description="Put down an object at a target location"
        )
        
        # TODO: Use config to customize schemas if provided
        
        return schemas
    
    def request_action_execution(self, agent_id: str, symbolic_action_ast: AST_Node) -> str:
        """
        Request the execution of a high-level symbolic action.
        
        This is the main entry point for executing actions. It:
        1. Parses the symbolic action AST
        2. Validates preconditions
        3. Decomposes the action into primitive commands
        4. Executes the primitive commands
        5. Monitors the execution
        6. Reports the outcome
        
        Args:
            agent_id: ID of the agent performing the action
            symbolic_action_ast: AST node representing the symbolic action
            
        Returns:
            ID of the action execution request
        """
        # Generate a unique ID for this action execution
        action_id = f"action_{uuid.uuid4()}"
        
        # Parse the symbolic action AST to extract action name and parameters
        action_name, action_params = self._parse_symbolic_action(symbolic_action_ast)
        
        # Check if the action schema exists
        if action_name not in self.action_schemas:
            logger.error(f"Unknown action: {action_name}")
            self._report_action_result(
                action_id=action_id,
                agent_id=agent_id,
                action_name=action_name,
                action_params=action_params,
                result=ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Unknown action: {action_name}"
                )
            )
            return action_id
        
        # Get the action schema
        schema = self.action_schemas[action_name]
        
        # Store the action parameters in the cache
        self.param_cache[action_id] = action_params
        
        # Create an entry for this action in the ongoing actions dictionary
        self.ongoing_actions[action_id] = {
            "agent_id": agent_id,
            "action_name": action_name,
            "action_params": action_params,
            "schema": schema,
            "status": ActionStatus.PENDING,
            "start_time": time.time(),
            "primitive_commands": [],
            "current_command_index": 0,
            "results": []
        }
        
        # Start action execution in a separate thread or process
        # For simplicity, we'll execute it synchronously here
        self._execute_action(action_id)
        
        return action_id
    
    def get_action_status(self, action_id: str) -> ActionStatus:
        """
        Get the status of an action execution.
        
        Args:
            action_id: ID of the action execution
            
        Returns:
            The status of the action execution
        """
        if action_id not in self.ongoing_actions:
            return ActionStatus.FAILED
        
        return self.ongoing_actions[action_id]["status"]
    
    def get_action_result(self, action_id: str) -> Optional[ActionResult]:
        """
        Get the result of an action execution.
        
        Args:
            action_id: ID of the action execution
            
        Returns:
            The result of the action execution, or None if not completed
        """
        if action_id not in self.ongoing_actions:
            return None
        
        action_info = self.ongoing_actions[action_id]
        
        if action_info["status"] in [ActionStatus.SUCCEEDED, ActionStatus.FAILED, ActionStatus.INTERRUPTED]:
            return ActionResult(
                status=action_info["status"],
                message=action_info.get("message", ""),
                effects=action_info.get("effects", []),
                precondition_failures=action_info.get("precondition_failures", []),
                execution_trace=action_info.get("results", [])
            )
        
        return None
    
    def _parse_symbolic_action(self, symbolic_action_ast: AST_Node) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a symbolic action AST to extract the action name and parameters.
        
        Args:
            symbolic_action_ast: AST node representing the symbolic action
            
        Returns:
            Tuple of (action_name, action_parameters)
        """
        if not isinstance(symbolic_action_ast, ApplicationNode):
            raise ValueError("Symbolic action must be an ApplicationNode")
        
        # Extract action name from the operator
        if isinstance(symbolic_action_ast.operator, ConstantNode):
            action_name = symbolic_action_ast.operator.name
        else:
            raise ValueError("Action operator must be a ConstantNode")
        
        # Extract parameters from the arguments
        action_params = {}
        
        # Get the action schema
        if action_name in self.action_schemas:
            schema = self.action_schemas[action_name]
            
            # Match arguments to parameters by position
            for i, param in enumerate(schema.parameters):
                if i < len(symbolic_action_ast.arguments):
                    arg = symbolic_action_ast.arguments[i]
                    if isinstance(arg, ConstantNode):
                        action_params[param.name] = arg.name
                    else:
                        action_params[param.name] = str(arg)
        else:
            # If schema is not found, use argument positions as parameter names
            for i, arg in enumerate(symbolic_action_ast.arguments):
                if isinstance(arg, ConstantNode):
                    action_params[f"param{i}"] = arg.name
                else:
                    action_params[f"param{i}"] = str(arg)
        
        return action_name, action_params
    
    def _validate_preconditions(self, action_id: str) -> List[Tuple[AST_Node, str]]:
        """
        Validate the preconditions of an action.
        
        Args:
            action_id: ID of the action execution
            
        Returns:
            List of failed preconditions with failure messages
        """
        action_info = self.ongoing_actions[action_id]
        schema = action_info["schema"]
        action_params = action_info["action_params"]
        
        failed_preconditions = []
        
        # Check each precondition
        for precondition in schema.preconditions:
            # Substitute parameters into the precondition
            instantiated_precondition = self._instantiate_ast_with_params(
                precondition, action_params)
            
            # Query the KR system to check if the precondition holds
            contexts = ["PERCEPTUAL_CONTEXT", "ACTION_CONTEXT", "TRUTHS"]
            results = self.kr_interface.query_statements_match_pattern(
                instantiated_precondition, contexts)
            
            if not results:
                # Precondition failed
                failed_preconditions.append(
                    (instantiated_precondition, f"Precondition not satisfied: {instantiated_precondition}")
                )
        
        return failed_preconditions
    
    def _instantiate_ast_with_params(self, ast_node: AST_Node, params: Dict[str, Any]) -> AST_Node:
        """
        Instantiate an AST node by substituting parameters.
        
        Args:
            ast_node: The AST node to instantiate
            params: Dictionary of parameter values
            
        Returns:
            The instantiated AST node
        """
        # This is a simplified implementation
        # In a real system, this would involve more sophisticated substitution
        
        # For now, just return the original AST node
        return ast_node
    
    def _execute_action(self, action_id: str) -> None:
        """
        Execute an action by decomposing it into primitive commands and executing them.
        
        Args:
            action_id: ID of the action execution
        """
        action_info = self.ongoing_actions[action_id]
        agent_id = action_info["agent_id"]
        action_name = action_info["action_name"]
        action_params = action_info["action_params"]
        schema = action_info["schema"]
        
        # Update action status
        action_info["status"] = ActionStatus.EXECUTING
        
        # Validate preconditions
        failed_preconditions = self._validate_preconditions(action_id)
        if failed_preconditions:
            action_info["status"] = ActionStatus.FAILED
            action_info["message"] = "Precondition check failed"
            action_info["precondition_failures"] = failed_preconditions
            
            self._report_action_result(
                action_id=action_id,
                agent_id=agent_id,
                action_name=action_name,
                action_params=action_params,
                result=ActionResult(
                    status=ActionStatus.FAILED,
                    message="Precondition check failed",
                    precondition_failures=failed_preconditions
                )
            )
            return
        
        # Decompose the action into primitive commands
        try:
            primitive_commands = schema.decomposition(action_params, {
                "agent_id": agent_id,
                "simenv": self.simenv
            })
            action_info["primitive_commands"] = primitive_commands
        except Exception as e:
            action_info["status"] = ActionStatus.FAILED
            action_info["message"] = f"Action decomposition failed: {str(e)}"
            
            self._report_action_result(
                action_id=action_id,
                agent_id=agent_id,
                action_name=action_name,
                action_params=action_params,
                result=ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Action decomposition failed: {str(e)}"
                )
            )
            return
        
        # Execute each primitive command
        results = []
        success = True
        
        for i, command in enumerate(primitive_commands):
            action_info["current_command_index"] = i
            
            # Execute the primitive command
            try:
                outcome = self.simenv.execute_primitive_env_action(
                    agent_id=agent_id,
                    action_name=command["action_name"],
                    parameters=command.get("parameters", {})
                )
                
                # Store the result
                result = {
                    "command": command,
                    "outcome": outcome
                }
                results.append(result)
                
                # Check if the command succeeded
                if not outcome.success:
                    success = False
                    action_info["message"] = f"Primitive command failed: {outcome.message}"
                    break
                
                # Optionally, we could update the world state in the KR system here
                # based on the outcome.achieved_state_delta
                
            except Exception as e:
                success = False
                action_info["message"] = f"Error executing primitive command: {str(e)}"
                results.append({
                    "command": command,
                    "error": str(e)
                })
                break
        
        # Store the results
        action_info["results"] = results
        
        # Determine action status
        if success:
            action_info["status"] = ActionStatus.SUCCEEDED
            if not action_info.get("message"):
                action_info["message"] = "Action completed successfully"
        else:
            action_info["status"] = ActionStatus.FAILED
            if not action_info.get("message"):
                action_info["message"] = "Action failed during execution"
        
        # Determine effects
        effects = self._determine_effects(action_id)
        action_info["effects"] = effects
        
        # Report the result
        self._report_action_result(
            action_id=action_id,
            agent_id=agent_id,
            action_name=action_name,
            action_params=action_params,
            result=ActionResult(
                status=action_info["status"],
                message=action_info["message"],
                effects=effects,
                execution_trace=results
            )
        )
    
    def _determine_effects(self, action_id: str) -> List[AST_Node]:
        """
        Determine the effects of an action based on the execution results.
        
        Args:
            action_id: ID of the action execution
            
        Returns:
            List of AST nodes representing the effects
        """
        action_info = self.ongoing_actions[action_id]
        schema = action_info["schema"]
        action_params = action_info["action_params"]
        
        # Start with the expected effects from the schema
        effects = []
        
        # Instantiate each effect with the actual parameters
        for effect in schema.effects:
            instantiated_effect = self._instantiate_ast_with_params(effect, action_params)
            effects.append(instantiated_effect)
        
        # Add observed effects from the execution results
        for result in action_info.get("results", []):
            if "outcome" in result and hasattr(result["outcome"], "achieved_state_delta"):
                # Convert achieved_state_delta to AST nodes representing the effects
                # This is a simplified implementation
                state_delta = result["outcome"].achieved_state_delta
                
                # For each key-value pair in state_delta, create an effect AST node
                for key, value in state_delta.items():
                    # Get necessary types from type system
                    entity_type = self.type_system.get_type("Entity") or self.type_system.get_type("Object")
                    prop_type = self.type_system.get_type("Proposition")
                    
                    # Create an effect AST node
                    # This is a simplified example - in a real system, the conversion would be more sophisticated
                    if key == "position_delta":
                        # Create a "HasMoved" predicate
                        effect = ApplicationNode(
                            operator=ConstantNode("HasMoved", prop_type),
                            arguments=[
                                ConstantNode(action_params.get("agent", "unknown_agent"), entity_type),
                                ConstantNode(str(value), entity_type)
                            ],
                            type_ref=prop_type
                        )
                        effects.append(effect)
                    elif key == "gripped_object":
                        # Create a "IsHolding" predicate
                        effect = ApplicationNode(
                            operator=ConstantNode("IsHolding", prop_type),
                            arguments=[
                                ConstantNode(action_params.get("agent", "unknown_agent"), entity_type),
                                ConstantNode(str(value), entity_type)
                            ],
                            type_ref=prop_type
                        )
                        effects.append(effect)
        
        return effects
    
    def _report_action_result(self, action_id: str, agent_id: str, action_name: str, 
                             action_params: Dict[str, Any], result: ActionResult) -> None:
        """
        Report the result of an action execution to the KR system.
        
        Args:
            action_id: ID of the action execution
            agent_id: ID of the agent that performed the action
            action_name: Name of the action
            action_params: Parameters of the action
            result: Result of the action execution
        """
        # Get necessary types from type system
        entity_type = self.type_system.get_type("Entity") or self.type_system.get_type("Object")
        prop_type = self.type_system.get_type("Proposition")
        
        # Create a statement about the action execution
        action_statement = ApplicationNode(
            operator=ConstantNode("ActionExecuted", prop_type),
            arguments=[
                ConstantNode(agent_id, entity_type),
                ConstantNode(action_name, entity_type),
                ConstantNode(str(result.status.value), entity_type)
            ],
            type_ref=prop_type
        )
        
        # Add the statement to the ACTION_CONTEXT
        self.kr_interface.add_statement(action_statement, "ACTION_CONTEXT")
        
        # Add each effect to the ACTION_CONTEXT
        for effect in result.effects:
            self.kr_interface.add_statement(effect, "ACTION_CONTEXT")
        
        # Log the action result
        logger.info(f"Action {action_name} by agent {agent_id} completed with status {result.status.value}: {result.message}")
    
    def _decompose_move_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a Move action into primitive commands.
        
        Args:
            params: Parameters of the Move action
            context: Context for the decomposition
            
        Returns:
            List of primitive commands
        """
        agent_id = context["agent_id"]
        target_location = params.get("target_location", "unknown_location")
        
        # Get the agent's current position
        agent = self.simenv.world_state.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        current_pos = agent.pose
        
        # Get the target position
        # In a real implementation, we would look up the target location in the world model
        # For simplicity, we'll assume the target_location is a string like "x,y,z"
        try:
            target_x, target_y, target_z = map(float, target_location.split(","))
            target_pos = (target_x, target_y, target_z)
        except (ValueError, AttributeError):
            # Default to a position 1 unit in front of the agent
            target_pos = (current_pos.x + 1.0, current_pos.y, current_pos.z)
        
        # Calculate direction vector
        dx = target_pos[0] - current_pos.x
        dy = target_pos[1] - current_pos.y
        dz = target_pos[2] - current_pos.z
        
        # Normalize direction vector
        distance = (dx**2 + dy**2 + dz**2)**0.5
        if distance > 0:
            dx /= distance
            dy /= distance
            dz /= distance
        
        # Create the primitive command
        return [
            {
                "action_name": "move",
                "parameters": {
                    "direction": (dx, dy, dz),
                    "speed": distance  # Move in one step
                }
            }
        ]
    
    def _decompose_pickup_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a PickUp action into primitive commands.
        
        Args:
            params: Parameters of the PickUp action
            context: Context for the decomposition
            
        Returns:
            List of primitive commands
        """
        agent_id = context["agent_id"]
        object_id = params.get("object", "unknown_object")
        
        # Get the agent and object positions
        agent = self.simenv.world_state.get_agent(agent_id)
        obj = self.simenv.world_state.get_object(object_id)
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        if not obj:
            raise ValueError(f"Object {object_id} not found")
        
        # Calculate direction to the object
        dx = obj.pose.x - agent.pose.x
        dy = obj.pose.y - agent.pose.y
        dz = obj.pose.z - agent.pose.z
        
        # Normalize direction vector
        distance = (dx**2 + dy**2 + dz**2)**0.5
        if distance > 0:
            dx /= distance
            dy /= distance
            dz /= distance
        
        # Create the primitive commands
        commands = []
        
        # First, move to the object if not already close enough
        if distance > 0.5:  # Assuming 0.5 units is close enough to grip
            commands.append({
                "action_name": "move",
                "parameters": {
                    "direction": (dx, dy, dz),
                    "speed": max(0, distance - 0.3)  # Stop a bit short of the object
                }
            })
        
        # Then, grip the object
        commands.append({
            "action_name": "grip",
            "parameters": {
                "force": 5.0  # Default grip force
            }
        })
        
        return commands
    
    def _decompose_putdown_action(self, params: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decompose a PutDown action into primitive commands.
        
        Args:
            params: Parameters of the PutDown action
            context: Context for the decomposition
            
        Returns:
            List of primitive commands
        """
        agent_id = context["agent_id"]
        target_location = params.get("target_location", "unknown_location")
        
        # Get the agent's current position
        agent = self.simenv.world_state.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        current_pos = agent.pose
        
        # Get the target position
        # In a real implementation, we would look up the target location in the world model
        # For simplicity, we'll assume the target_location is a string like "x,y,z"
        try:
            target_x, target_y, target_z = map(float, target_location.split(","))
            target_pos = (target_x, target_y, target_z)
        except (ValueError, AttributeError):
            # Default to a position 1 unit in front of the agent
            target_pos = (current_pos.x + 1.0, current_pos.y, current_pos.z)
        
        # Calculate direction vector
        dx = target_pos[0] - current_pos.x
        dy = target_pos[1] - current_pos.y
        dz = target_pos[2] - current_pos.z
        
        # Normalize direction vector
        distance = (dx**2 + dy**2 + dz**2)**0.5
        if distance > 0:
            dx /= distance
            dy /= distance
            dz /= distance
        
        # Create the primitive commands
        commands = []
        
        # First, move to the target location if not already there
        if distance > 0.5:  # Assuming 0.5 units is close enough
            commands.append({
                "action_name": "move",
                "parameters": {
                    "direction": (dx, dy, dz),
                    "speed": distance
                }
            })
        
        # Then, release the object
        commands.append({
            "action_name": "release",
            "parameters": {}
        })
        
        return commands