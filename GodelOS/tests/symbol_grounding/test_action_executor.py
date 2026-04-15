"""
Unit tests for the ActionExecutor component.
"""

import unittest
from unittest.mock import MagicMock, patch
import uuid

from godelOS.symbol_grounding.action_executor import (
    ActionExecutor,
    ActionSchema,
    ActionParameter,
    ActionStatus,
    ActionResult
)
from godelOS.symbol_grounding.simulated_environment import (
    SimulatedEnvironment,
    ActionOutcome,
    SimAgent,
    SimObject,
    Pose
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode


class TestActionExecutor(unittest.TestCase):
    """Tests for the ActionExecutor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock SimulatedEnvironment with proper structure
        self.simenv = MagicMock(spec=SimulatedEnvironment)
        self.world_state = MagicMock()
        self.simenv.world_state = self.world_state
        
        # Create mock KR interface
        self.kr_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.kr_interface.list_contexts.return_value = []
        
        # Create mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        self.entity_type = MagicMock()
        self.prop_type = MagicMock()
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Object": self.entity_type,
            "Proposition": self.prop_type
        }.get(name)
        
        # Create the action executor
        self.action_executor = ActionExecutor(
            simulated_environment=self.simenv,
            kr_interface=self.kr_interface,
            type_system=self.type_system
        )
        
        # Create test agent and object
        self.agent = SimAgent(agent_id="agent1", pose=Pose(0, 0, 0))
        self.obj = SimObject(object_id="obj1", object_type="box", pose=Pose(1, 0, 0))
        
        # Mock the world state methods
        self.world_state.get_agent.return_value = self.agent
        self.world_state.get_object.return_value = self.obj
        
        # Mock the execute_primitive_env_action method
        self.simenv.execute_primitive_env_action.return_value = ActionOutcome(
            success=True,
            message="Action succeeded",
            achieved_state_delta={"position_delta": (1.0, 0.0, 0.0)}
        )
    
    def test_init(self):
        """Test initialization."""
        # Check that the action context was created
        self.kr_interface.create_context.assert_called_once_with(
            "ACTION_CONTEXT", None, "action"
        )
        
        # Check that action schemas were initialized
        self.assertIn("Move", self.action_executor.action_schemas)
        self.assertIn("PickUp", self.action_executor.action_schemas)
        self.assertIn("PutDown", self.action_executor.action_schemas)
    
    def test_parse_symbolic_action(self):
        """Test parsing symbolic action AST."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("Move", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("1,2,3", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Parse the action
        action_name, action_params = self.action_executor._parse_symbolic_action(action_ast)
        
        # Check the parsed action
        self.assertEqual(action_name, "Move")
        self.assertEqual(action_params["agent"], "agent1")
        self.assertEqual(action_params["target_location"], "1,2,3")
    
    def test_request_action_execution_move(self):
        """Test requesting a Move action execution."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("Move", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("1,2,3", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Check that the action was executed
        self.assertIn(action_id, self.action_executor.ongoing_actions)
        self.assertEqual(
            self.action_executor.ongoing_actions[action_id]["status"],
            ActionStatus.SUCCEEDED
        )
        
        # Check that the primitive command was executed
        self.simenv.execute_primitive_env_action.assert_called_once()
        
        # Check that the result was reported to the KR system
        self.kr_interface.add_statement.assert_called()
    
    def test_request_action_execution_pickup(self):
        """Test requesting a PickUp action execution."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("PickUp", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("obj1", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Check that the action was executed
        self.assertIn(action_id, self.action_executor.ongoing_actions)
        self.assertEqual(
            self.action_executor.ongoing_actions[action_id]["status"],
            ActionStatus.SUCCEEDED
        )
        
        # Check that the primitive commands were executed
        # The PickUp action should decompose into move and grip commands
        self.assertEqual(self.simenv.execute_primitive_env_action.call_count, 2)
        
        # Check that the result was reported to the KR system
        self.kr_interface.add_statement.assert_called()
    
    def test_request_action_execution_putdown(self):
        """Test requesting a PutDown action execution."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("PutDown", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("obj1", self.entity_type),
                ConstantNode("2,3,4", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Check that the action was executed
        self.assertIn(action_id, self.action_executor.ongoing_actions)
        self.assertEqual(
            self.action_executor.ongoing_actions[action_id]["status"],
            ActionStatus.SUCCEEDED
        )
        
        # Check that the primitive commands were executed
        # The PutDown action should decompose into move and release commands
        self.assertEqual(self.simenv.execute_primitive_env_action.call_count, 2)
        
        # Check that the result was reported to the KR system
        self.kr_interface.add_statement.assert_called()
    
    def test_request_action_execution_unknown_action(self):
        """Test requesting an unknown action execution."""
        # Create a test action AST for an unknown action
        action_ast = ApplicationNode(
            operator=ConstantNode("UnknownAction", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Mock uuid.uuid4 to return a predictable value
        with patch('uuid.uuid4', return_value=uuid.UUID('bfa1e21a-b89c-40e7-a1a9-e354360d0477')):
            # Request action execution
            action_id = self.action_executor.request_action_execution("agent1", action_ast)
            
            # For unknown actions, we report failure but don't add to ongoing_actions
            # Check that the action_id is correct and that the KR system was updated
            self.assertEqual(action_id, "action_bfa1e21a-b89c-40e7-a1a9-e354360d0477")
            self.kr_interface.add_statement.assert_called_once()
        
        # Check that no primitive commands were executed
        self.simenv.execute_primitive_env_action.assert_not_called()
        
        # Check that the failure was reported to the KR system
        self.kr_interface.add_statement.assert_called_once()
    
    def test_request_action_execution_failed_primitive(self):
        """Test action execution when a primitive command fails."""
        # Mock the execute_primitive_env_action method to return failure
        self.simenv.execute_primitive_env_action.return_value = ActionOutcome(
            success=False,
            message="Action failed",
            achieved_state_delta={}
        )
        
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("Move", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("1,2,3", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Check that the action failed
        self.assertIn(action_id, self.action_executor.ongoing_actions)
        self.assertEqual(
            self.action_executor.ongoing_actions[action_id]["status"],
            ActionStatus.FAILED
        )
        
        # Check that the primitive command was executed
        self.simenv.execute_primitive_env_action.assert_called_once()
        
        # Check that the failure was reported to the KR system
        self.kr_interface.add_statement.assert_called()
    
    def test_get_action_status(self):
        """Test getting action status."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("Move", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("1,2,3", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Get the action status
        status = self.action_executor.get_action_status(action_id)
        
        # Check the status
        self.assertEqual(status, ActionStatus.SUCCEEDED)
        
        # Check status for nonexistent action
        status = self.action_executor.get_action_status("nonexistent")
        self.assertEqual(status, ActionStatus.FAILED)
    
    def test_get_action_result(self):
        """Test getting action result."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("Move", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("1,2,3", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Get the action result
        result = self.action_executor.get_action_result(action_id)
        
        # Check the result
        self.assertIsNotNone(result)
        self.assertEqual(result.status, ActionStatus.SUCCEEDED)
        
        # Check result for nonexistent action
        result = self.action_executor.get_action_result("nonexistent")
        self.assertIsNone(result)
    
    def test_determine_effects(self):
        """Test determining action effects."""
        # Create a test action AST
        action_ast = ApplicationNode(
            operator=ConstantNode("Move", self.prop_type),
            arguments=[
                ConstantNode("agent1", self.entity_type),
                ConstantNode("1,2,3", self.entity_type)
            ],
            type_ref=self.prop_type
        )
        
        # Request action execution
        action_id = self.action_executor.request_action_execution("agent1", action_ast)
        
        # Get the effects
        effects = self.action_executor.ongoing_actions[action_id]["effects"]
        
        # Check that effects were determined
        self.assertGreaterEqual(len(effects), 1)
        
        # Check that at least one effect is a HasMoved predicate
        has_moved = False
        for effect in effects:
            if isinstance(effect, ApplicationNode) and isinstance(effect.operator, ConstantNode):
                if effect.operator.name == "HasMoved":
                    has_moved = True
                    break
        
        self.assertTrue(has_moved)


class TestActionSchema(unittest.TestCase):
    """Tests for the ActionSchema class."""
    
    def test_action_schema_creation(self):
        """Test creating an action schema."""
        # Create a simple decomposition function
        def decompose_test(params, context):
            return [{"action_name": "test", "parameters": {}}]
        
        # Create an action schema
        schema = ActionSchema(
            name="TestAction",
            parameters=[
                ActionParameter("agent", "Agent", "The agent performing the action"),
                ActionParameter("target", "Object", "The target of the action")
            ],
            preconditions=[],
            effects=[],
            decomposition=decompose_test,
            description="A test action"
        )
        
        # Check the schema
        self.assertEqual(schema.name, "TestAction")
        self.assertEqual(len(schema.parameters), 2)
        self.assertEqual(schema.parameters[0].name, "agent")
        self.assertEqual(schema.parameters[1].name, "target")
        self.assertEqual(schema.description, "A test action")
        
        # Test the decomposition function
        commands = schema.decomposition({}, {})
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["action_name"], "test")


class TestActionResult(unittest.TestCase):
    """Tests for the ActionResult class."""
    
    def test_action_result_creation(self):
        """Test creating an action result."""
        # Create an action result
        result = ActionResult(
            status=ActionStatus.SUCCEEDED,
            message="Action succeeded",
            effects=[],
            precondition_failures=[],
            execution_trace=[]
        )
        
        # Check the result
        self.assertEqual(result.status, ActionStatus.SUCCEEDED)
        self.assertEqual(result.message, "Action succeeded")
        self.assertEqual(result.effects, [])
        self.assertEqual(result.precondition_failures, [])
        self.assertEqual(result.execution_trace, [])


if __name__ == '__main__':
    unittest.main()