"""
Unit tests for the SimulatedEnvironment component.
"""

import unittest
import math
from unittest.mock import MagicMock, patch
import tempfile
import json
import os

from godelOS.symbol_grounding.simulated_environment import (
    Pose,
    RawSensorData,
    ActionOutcome,
    SensorModel,
    SensorInstance,
    ActuatorModel,
    ActuatorInstance,
    SimObject,
    SimAgent,
    WorldState,
    PhysicsEngine,
    VisionSensor,
    TouchSensor,
    LocomotionActuator,
    GripperActuator,
    SimulatedEnvironment
)


class TestPose(unittest.TestCase):
    """Tests for the Pose class."""
    
    def test_distance_to(self):
        """Test the distance_to method."""
        pose1 = Pose(1, 2, 3)
        pose2 = Pose(4, 6, 3)
        
        # Calculate expected distance
        expected_distance = math.sqrt((4-1)**2 + (6-2)**2 + (3-3)**2)
        
        self.assertAlmostEqual(pose1.distance_to(pose2), expected_distance)
    
    def test_is_quaternion(self):
        """Test the is_quaternion method."""
        # Default orientation is a quaternion
        pose = Pose()
        self.assertTrue(pose.is_quaternion())
        
        # Euler angles orientation is not a quaternion
        pose.orientation = (0.1, 0.2, 0.3)
        self.assertFalse(pose.is_quaternion())
    
    def test_to_quaternion(self):
        """Test the to_quaternion method."""
        # Test with existing quaternion
        pose = Pose()
        quat = pose.to_quaternion()
        self.assertEqual(quat, (1.0, 0.0, 0.0, 0.0))
        
        # Test with Euler angles
        pose.orientation = (0.0, 0.0, 0.0)  # Zero rotation
        quat = pose.to_quaternion()
        self.assertAlmostEqual(quat[0], 1.0)  # w component should be 1 for zero rotation
        self.assertAlmostEqual(quat[1], 0.0)  # x component
        self.assertAlmostEqual(quat[2], 0.0)  # y component
        self.assertAlmostEqual(quat[3], 0.0)  # z component


class TestWorldState(unittest.TestCase):
    """Tests for the WorldState class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world_state = WorldState()
        
        # Create test objects
        self.obj1 = SimObject(object_id="obj1", object_type="box", pose=Pose(1, 1, 0))
        self.obj2 = SimObject(object_id="obj2", object_type="sphere", pose=Pose(5, 5, 0))
        
        # Create test agent
        self.agent = SimAgent(agent_id="agent1", pose=Pose(0, 0, 0))
    
    def test_add_and_get_object(self):
        """Test adding and retrieving objects."""
        # Add objects
        self.world_state.add_object(self.obj1)
        self.world_state.add_object(self.obj2)
        
        # Get objects
        retrieved_obj1 = self.world_state.get_object("obj1")
        retrieved_obj2 = self.world_state.get_object("obj2")
        
        # Check objects were retrieved correctly
        self.assertEqual(retrieved_obj1, self.obj1)
        self.assertEqual(retrieved_obj2, self.obj2)
        
        # Check nonexistent object returns None
        self.assertIsNone(self.world_state.get_object("nonexistent"))
    
    def test_add_and_get_agent(self):
        """Test adding and retrieving agents."""
        # Add agent
        self.world_state.add_agent(self.agent)
        
        # Get agent
        retrieved_agent = self.world_state.get_agent("agent1")
        
        # Check agent was retrieved correctly
        self.assertEqual(retrieved_agent, self.agent)
        
        # Check nonexistent agent returns None
        self.assertIsNone(self.world_state.get_agent("nonexistent"))
    
    def test_remove_object(self):
        """Test removing objects."""
        # Add object
        self.world_state.add_object(self.obj1)
        
        # Remove object
        result = self.world_state.remove_object("obj1")
        
        # Check removal was successful
        self.assertTrue(result)
        
        # Check object is no longer in world state
        self.assertIsNone(self.world_state.get_object("obj1"))
        
        # Check removing nonexistent object returns False
        self.assertFalse(self.world_state.remove_object("nonexistent"))
    
    def test_remove_agent(self):
        """Test removing agents."""
        # Add agent
        self.world_state.add_agent(self.agent)
        
        # Remove agent
        result = self.world_state.remove_agent("agent1")
        
        # Check removal was successful
        self.assertTrue(result)
        
        # Check agent is no longer in world state
        self.assertIsNone(self.world_state.get_agent("agent1"))
        
        # Check removing nonexistent agent returns False
        self.assertFalse(self.world_state.remove_agent("nonexistent"))
    
    def test_get_objects_in_radius(self):
        """Test getting objects within a radius."""
        # Add objects
        self.world_state.add_object(self.obj1)
        self.world_state.add_object(self.obj2)
        
        # Get objects within radius 3 of (0, 0, 0)
        objects = self.world_state.get_objects_in_radius(Pose(0, 0, 0), 3)
        
        # Check only obj1 is within radius
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.obj1)
        
        # Get objects within radius 10 of (0, 0, 0)
        objects = self.world_state.get_objects_in_radius(Pose(0, 0, 0), 10)
        
        # Check both objects are within radius
        self.assertEqual(len(objects), 2)
        self.assertIn(self.obj1, objects)
        self.assertIn(self.obj2, objects)


class TestPhysicsEngine(unittest.TestCase):
    """Tests for the PhysicsEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.physics_engine = PhysicsEngine()
        self.world_state = WorldState()
        
        # Create test objects
        self.static_obj = SimObject(
            object_id="static_obj",
            object_type="wall",
            pose=Pose(0, 0, 0),
            physical_properties={"static": True}
        )
        
        self.dynamic_obj = SimObject(
            object_id="dynamic_obj",
            object_type="box",
            pose=Pose(5, 5, 5),
            physical_properties={
                "mass": 1.0,
                "velocity": (1.0, 0.0, 0.0),
                "acceleration": (0.0, 0.0, 0.0),
                "collision_radius": 1.0
            }
        )
        
        # Add objects to world state
        self.world_state.add_object(self.static_obj)
        self.world_state.add_object(self.dynamic_obj)
    
    def test_update_position(self):
        """Test updating object positions."""
        # Update physics for 1 second
        self.physics_engine.update(self.world_state, 1.0)
        
        # Check static object hasn't moved
        static_obj = self.world_state.get_object("static_obj")
        self.assertEqual(static_obj.pose.x, 0.0)
        self.assertEqual(static_obj.pose.y, 0.0)
        self.assertEqual(static_obj.pose.z, 0.0)
        
        # Check dynamic object has moved according to its velocity
        dynamic_obj = self.world_state.get_object("dynamic_obj")
        self.assertEqual(dynamic_obj.pose.x, 6.0)  # 5 + 1*1
        self.assertEqual(dynamic_obj.pose.y, 5.0)
        self.assertEqual(dynamic_obj.pose.z, 5.0 - 9.8)  # Gravity should be applied
    
    def test_collision_detection(self):
        """Test collision detection."""
        # Create two objects that will collide
        obj1 = SimObject(
            object_id="obj1",
            object_type="sphere",
            pose=Pose(0, 0, 0),
            physical_properties={"collision_radius": 1.0}
        )
        
        obj2 = SimObject(
            object_id="obj2",
            object_type="sphere",
            pose=Pose(1.5, 0, 0),
            physical_properties={"collision_radius": 1.0}
        )
        
        # Create a new world state with these objects
        collision_world = WorldState()
        collision_world.add_object(obj1)
        collision_world.add_object(obj2)
        
        # Update physics
        self.physics_engine.update(collision_world, 1.0)
        
        # Check collision was detected
        self.assertIn(("obj1", "obj2"), self.physics_engine.collision_pairs)
        
        # Check objects were separated
        obj1 = collision_world.get_object("obj1")
        obj2 = collision_world.get_object("obj2")
        
        # Objects should be at least 2.0 units apart (sum of their radii)
        distance = obj1.pose.distance_to(obj2.pose)
        self.assertGreaterEqual(distance, 2.0)


class TestSensors(unittest.TestCase):
    """Tests for sensor models."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world_state = WorldState()
        
        # Create test objects
        self.obj1 = SimObject(
            object_id="obj1",
            object_type="box",
            pose=Pose(2, 0, 0),
            visual_features={"color": "red", "shape": "cube"}
        )
        
        self.obj2 = SimObject(
            object_id="obj2",
            object_type="sphere",
            pose=Pose(0, 2, 0),
            visual_features={"color": "blue", "shape": "sphere"}
        )
        
        # Add objects to world state
        self.world_state.add_object(self.obj1)
        self.world_state.add_object(self.obj2)
    
    def test_vision_sensor(self):
        """Test the vision sensor."""
        # Create vision sensor
        vision_sensor = VisionSensor(fov_degrees=90.0, max_range=5.0, output_type="feature_list")
        
        # Generate percept
        percept = vision_sensor.generate_percept(self.world_state, Pose(0, 0, 0))
        
        # Check percept modality
        self.assertEqual(percept.modality, "vision")
        
        # Check both objects are detected
        self.assertEqual(len(percept.data), 2)
        
        # Check object features are included
        obj1_detected = False
        obj2_detected = False
        
        for feature in percept.data:
            if feature["object_id"] == "obj1":
                obj1_detected = True
                self.assertEqual(feature["object_type"], "box")
                self.assertEqual(feature["visual_features"]["color"], "red")
            elif feature["object_id"] == "obj2":
                obj2_detected = True
                self.assertEqual(feature["object_type"], "sphere")
                self.assertEqual(feature["visual_features"]["color"], "blue")
        
        self.assertTrue(obj1_detected)
        self.assertTrue(obj2_detected)
    
    def test_touch_sensor(self):
        """Test the touch sensor."""
        # Create touch sensor
        touch_sensor = TouchSensor(detection_radius=0.5)
        
        # Generate percept from a position where no objects are in range
        percept = touch_sensor.generate_percept(self.world_state, Pose(0, 0, 0))
        
        # Check no objects are detected
        self.assertEqual(len(percept.data), 0)
        
        # Generate percept from a position where obj1 is in range
        percept = touch_sensor.generate_percept(self.world_state, Pose(1.8, 0, 0))
        
        # Check obj1 is detected
        self.assertEqual(len(percept.data), 1)
        self.assertEqual(percept.data[0]["object_id"], "obj1")


class TestActuators(unittest.TestCase):
    """Tests for actuator models."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world_state = WorldState()
        
        # Create test object
        self.obj = SimObject(
            object_id="obj1",
            object_type="box",
            pose=Pose(0.1, 0, 0)
        )
        
        # Create test agent
        self.locomotion_actuator = LocomotionActuator()
        self.gripper_actuator = GripperActuator()
        
        self.agent = SimAgent(
            agent_id="agent1",
            pose=Pose(0, 0, 0),
            actuators=[
                ActuatorInstance(
                    actuator_id="locomotion1",
                    actuator_type="locomotion",
                    model=self.locomotion_actuator
                ),
                ActuatorInstance(
                    actuator_id="gripper1",
                    actuator_type="gripper",
                    model=self.gripper_actuator
                )
            ]
        )
        
        # Add agent and object to world state
        self.world_state.add_agent(self.agent)
        self.world_state.add_object(self.obj)
    
    def test_locomotion_actuator(self):
        """Test the locomotion actuator."""
        # Execute a move action
        outcome = self.locomotion_actuator.execute_action(
            self.world_state,
            self.agent.actuators[0].relative_pose,
            {"action_type": "move", "direction": (1.0, 0.0, 0.0), "speed": 2.0}
        )
        
        # Check action was successful
        self.assertTrue(outcome.success)
        
        # Check agent position was updated
        agent = self.world_state.get_agent("agent1")
        self.assertEqual(agent.pose.x, 2.0)
        self.assertEqual(agent.pose.y, 0.0)
        self.assertEqual(agent.pose.z, 0.0)
    
    def test_gripper_actuator(self):
        """Test the gripper actuator."""
        # Execute a grip action
        outcome = self.gripper_actuator.execute_action(
            self.world_state,
            self.agent.actuators[1].relative_pose,
            {"action_type": "grip", "force": 5.0}
        )
        
        # Check action was successful
        self.assertTrue(outcome.success)
        
        # Check object was gripped
        self.assertEqual(self.gripper_actuator.gripped_object_id, "obj1")
        
        # Execute a release action
        outcome = self.gripper_actuator.execute_action(
            self.world_state,
            self.agent.actuators[1].relative_pose,
            {"action_type": "release"}
        )
        
        # Check action was successful
        self.assertTrue(outcome.success)
        
        # Check object was released
        self.assertIsNone(self.gripper_actuator.gripped_object_id)


class TestSimulatedEnvironment(unittest.TestCase):
    """Tests for the SimulatedEnvironment class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.env = SimulatedEnvironment()
        
        # Create test agent
        self.vision_sensor = VisionSensor()
        self.locomotion_actuator = LocomotionActuator()
        
        self.agent = SimAgent(
            agent_id="agent1",
            pose=Pose(0, 0, 0),
            sensors=[
                SensorInstance(
                    sensor_id="vision1",
                    sensor_type="vision",
                    model=self.vision_sensor
                )
            ],
            actuators=[
                ActuatorInstance(
                    actuator_id="locomotion1",
                    actuator_type="locomotion",
                    model=self.locomotion_actuator
                )
            ]
        )
        
        # Add agent to environment
        self.env.world_state.add_agent(self.agent)
        
        # Create test object
        self.obj = SimObject(
            object_id="obj1",
            object_type="box",
            pose=Pose(3, 0, 0)
        )
        
        # Add object to environment
        self.env.world_state.add_object(self.obj)
    
    def test_tick(self):
        """Test the tick method."""
        # Initial position
        agent_before = self.env.world_state.get_agent("agent1")
        x_before = agent_before.pose.x
        
        # Execute a primitive action
        self.env.execute_primitive_env_action(
            "agent1",
            "move",
            {"direction": (1.0, 0.0, 0.0), "speed": 1.0}
        )
        
        # Tick the environment
        self.env.tick(1.0)
        
        # Check agent position was updated
        agent_after = self.env.world_state.get_agent("agent1")
        x_after = agent_after.pose.x
        
        self.assertEqual(x_after, x_before + 1.0)
    
    def test_get_agent_percepts(self):
        """Test the get_agent_percepts method."""
        # Get percepts
        percepts = self.env.get_agent_percepts("agent1")
        
        # Check vision percept is included
        self.assertIn("vision1", percepts)
        
        # Check vision percept contains the object
        vision_percept = percepts["vision1"]
        self.assertEqual(vision_percept.modality, "vision")
        
        # At least one object should be detected
        self.assertGreaterEqual(len(vision_percept.data), 1)
    
    def test_execute_primitive_env_action(self):
        """Test the execute_primitive_env_action method."""
        # Execute a primitive action
        outcome = self.env.execute_primitive_env_action(
            "agent1",
            "move",
            {"direction": (1.0, 0.0, 0.0), "speed": 2.0}
        )
        
        # Check action was successful
        self.assertTrue(outcome.success)
        
        # Check agent position was updated
        agent = self.env.world_state.get_agent("agent1")
        self.assertEqual(agent.pose.x, 2.0)
    
    def test_get_object_details(self):
        """Test the get_object_details method."""
        # Get object details
        obj_details = self.env.get_object_details("obj1")
        
        # Check object details
        self.assertEqual(obj_details.object_id, "obj1")
        self.assertEqual(obj_details.object_type, "box")
        self.assertEqual(obj_details.pose.x, 3.0)
    
    def test_add_object(self):
        """Test the add_object method."""
        # Create object config
        object_config = {
            "object_type": "sphere",
            "pose": {"x": 5.0, "y": 5.0, "z": 0.0},
            "visual_features": {"color": "blue"},
            "physical_properties": {"mass": 2.0}
        }
        
        # Add object
        object_id = self.env.add_object(object_config)
        
        # Check object was added
        obj = self.env.world_state.get_object(object_id)
        self.assertIsNotNone(obj)
        self.assertEqual(obj.object_type, "sphere")
        self.assertEqual(obj.pose.x, 5.0)
        self.assertEqual(obj.visual_features["color"], "blue")
        self.assertEqual(obj.physical_properties["mass"], 2.0)
    
    def test_load_world_config(self):
        """Test loading a world configuration from a file."""
        # Create a temporary config file
        config = {
            "objects": [
                {
                    "object_id": "test_obj",
                    "object_type": "test_type",
                    "pose": {"x": 1.0, "y": 2.0, "z": 3.0}
                }
            ],
            "agents": [
                {
                    "agent_id": "test_agent",
                    "pose": {"x": 0.0, "y": 0.0, "z": 0.0}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            # Create a new environment with the config
            with patch('godelOS.symbol_grounding.simulated_environment.SimulatedEnvironment._process_world_config') as mock_process:
                env = SimulatedEnvironment(config_path)
                mock_process.assert_called_once()
        finally:
            # Clean up
            os.unlink(config_path)


if __name__ == '__main__':
    unittest.main()