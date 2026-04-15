"""
Simulated Environment (SimEnv) for GödelOS.

This module implements the SimulatedEnvironment component (Module 4.1) of the Symbol Grounding System,
which is responsible for maintaining the state of a simulated world, providing sensory data to the agent,
and executing primitive actions received from the agent.

The SimulatedEnvironment serves as the interface between the agent's symbolic representations
and the simulated physical world, handling object properties, interactions, and agent embodiment.
"""

import json
import logging
import math
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class Pose:
    """
    Represents the position and orientation of an object or agent in the simulated environment.
    
    Attributes:
        x: X-coordinate in the world
        y: Y-coordinate in the world
        z: Z-coordinate in the world
        orientation: Orientation as a quaternion (w, x, y, z) or Euler angles (roll, pitch, yaw)
    """
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    orientation: Union[Tuple[float, float, float, float], Tuple[float, float, float]] = field(
        default_factory=lambda: (1.0, 0.0, 0.0, 0.0)  # Default quaternion (w, x, y, z) representing no rotation
    )
    
    def distance_to(self, other: 'Pose') -> float:
        """Calculate the Euclidean distance to another pose."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
    
    def is_quaternion(self) -> bool:
        """Check if the orientation is represented as a quaternion."""
        return len(self.orientation) == 4
    
    def to_quaternion(self) -> Tuple[float, float, float, float]:
        """Convert the orientation to a quaternion if it's not already."""
        if self.is_quaternion():
            return self.orientation
        
        # Convert Euler angles (roll, pitch, yaw) to quaternion
        roll, pitch, yaw = self.orientation
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        
        return (w, x, y, z)


@dataclass
class RawSensorData:
    """
    Represents raw data from a sensor in the simulated environment.
    
    Attributes:
        modality: The sensory modality (e.g., "vision", "touch", "audio", "proprioception")
        data: The actual sensor data, which could be a pixel buffer, feature list, contact list, etc.
    """
    modality: str
    data: Any


@dataclass
class ActionOutcome:
    """
    Represents the outcome of an action executed in the simulated environment.
    
    Attributes:
        success: Whether the action was successful
        message: A message describing the outcome
        achieved_state_delta: Changes in state resulting from the action
    """
    success: bool
    message: str = ""
    achieved_state_delta: Dict[str, Any] = field(default_factory=dict)


class SensorModel(ABC):
    """
    Abstract base class for sensor models in the simulated environment.
    
    Sensor models define how sensors perceive the environment and generate sensory data.
    """
    
    @abstractmethod
    def generate_percept(self, world_state: 'WorldState', sensor_pose: Pose) -> RawSensorData:
        """
        Generate a percept based on the current world state and sensor pose.
        
        Args:
            world_state: The current state of the world
            sensor_pose: The pose of the sensor in the world
            
        Returns:
            Raw sensor data representing the percept
        """
        pass


@dataclass
class SensorInstance:
    """
    Represents a configured instance of a sensor model.
    
    Attributes:
        sensor_id: Unique identifier for the sensor
        sensor_type: Type of the sensor
        model: The sensor model
        relative_pose: Pose of the sensor relative to the agent
        parameters: Additional parameters for the sensor
    """
    sensor_id: str
    sensor_type: str
    model: SensorModel
    relative_pose: Pose = field(default_factory=Pose)
    parameters: Dict[str, Any] = field(default_factory=dict)


class ActuatorModel(ABC):
    """
    Abstract base class for actuator models in the simulated environment.
    
    Actuator models define how actuators affect the environment when actions are executed.
    """
    
    @abstractmethod
    def execute_action(self, world_state: 'WorldState', actuator_pose: Pose, 
                      parameters: Dict[str, Any]) -> ActionOutcome:
        """
        Execute an action using the actuator.
        
        Args:
            world_state: The current state of the world
            actuator_pose: The pose of the actuator in the world
            parameters: Parameters for the action
            
        Returns:
            The outcome of the action
        """
        pass


@dataclass
class ActuatorInstance:
    """
    Represents a configured instance of an actuator model.
    
    Attributes:
        actuator_id: Unique identifier for the actuator
        actuator_type: Type of the actuator
        model: The actuator model
        relative_pose: Pose of the actuator relative to the agent
        parameters: Additional parameters for the actuator
    """
    actuator_id: str
    actuator_type: str
    model: ActuatorModel
    relative_pose: Pose = field(default_factory=Pose)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimObject:
    """
    Represents an object in the simulated environment.
    
    Attributes:
        object_id: Unique identifier for the object
        object_type: Type of the object
        pose: Pose of the object in the world
        visual_features: Visual features of the object (e.g., color, shape)
        physical_properties: Physical properties of the object (e.g., mass, friction)
        custom_state: Additional custom state for the object
    """
    object_id: str
    object_type: str
    pose: Pose = field(default_factory=Pose)
    visual_features: Dict[str, Any] = field(default_factory=dict)
    physical_properties: Dict[str, Any] = field(default_factory=dict)
    custom_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimAgent:
    """
    Represents an agent in the simulated environment.
    
    Attributes:
        agent_id: Unique identifier for the agent
        pose: Pose of the agent in the world
        sensors: List of sensor instances attached to the agent
        actuators: List of actuator instances attached to the agent
        internal_state: Internal state of the agent
    """
    agent_id: str
    pose: Pose = field(default_factory=Pose)
    sensors: List[SensorInstance] = field(default_factory=list)
class WorldState:
    """
    Represents the state of the simulated world.
    
    This class maintains the list of objects and agents in the world,
    and provides methods for accessing and modifying the world state.
    """
    
    def __init__(self):
        """Initialize an empty world state."""
        self.objects: Dict[str, SimObject] = {}
        self.agents: Dict[str, SimAgent] = {}
        self.global_state: Dict[str, Any] = {}
        self.time: float = 0.0
    
    def add_object(self, obj: SimObject) -> str:
        """
        Add an object to the world.
        
        Args:
            obj: The object to add
            
        Returns:
            The ID of the added object
        """
        self.objects[obj.object_id] = obj
        return obj.object_id
    
    def add_agent(self, agent: SimAgent) -> str:
        """
        Add an agent to the world.
        
        Args:
            agent: The agent to add
            
        Returns:
            The ID of the added agent
        """
        self.agents[agent.agent_id] = agent
        return agent.agent_id
    
    def get_object(self, object_id: str) -> Optional[SimObject]:
        """
        Get an object by ID.
        
        Args:
            object_id: The ID of the object to get
            
        Returns:
            The object, or None if not found
        """
        return self.objects.get(object_id)
    
    def get_agent(self, agent_id: str) -> Optional[SimAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get
            
        Returns:
            The agent, or None if not found
        """
        return self.agents.get(agent_id)
    
    def remove_object(self, object_id: str) -> bool:
        """
        Remove an object from the world.
        
        Args:
            object_id: The ID of the object to remove
            
        Returns:
            True if the object was removed, False if it wasn't found
        """
        if object_id in self.objects:
            del self.objects[object_id]
            return True
        return False
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the world.
        
        Args:
            agent_id: The ID of the agent to remove
            
        Returns:
            True if the agent was removed, False if it wasn't found
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def get_objects_in_radius(self, center: Pose, radius: float) -> List[SimObject]:
        """
        Get all objects within a certain radius of a point.
        
        Args:
            center: The center point
            radius: The radius
            
        Returns:
            A list of objects within the radius
        """
        return [obj for obj in self.objects.values() if obj.pose.distance_to(center) <= radius]
    
    def get_agents_in_radius(self, center: Pose, radius: float) -> List[SimAgent]:
        """
        Get all agents within a certain radius of a point.
        
        Args:
            center: The center point
            radius: The radius
            
        Returns:
            A list of agents within the radius
        """
        return [agent for agent in self.agents.values() if agent.pose.distance_to(center) <= radius]


class PhysicsEngine:
    """
    Handles physics simulation for the simulated environment.
    
    This class is responsible for updating object positions, handling collisions,
    and applying forces and constraints.
    """
    
    def __init__(self, gravity: Tuple[float, float, float] = (0.0, 0.0, -9.8)):
        """
        Initialize the physics engine.
        
        Args:
            gravity: The gravity vector (x, y, z)
        """
        self.gravity = gravity
        self.collision_pairs: Set[Tuple[str, str]] = set()
    
    def update(self, world_state: WorldState, delta_t: float) -> None:
        """
        Update the physics for a time step.
        
        Args:
            world_state: The current world state
            delta_t: The time step
        """
        # Clear previous collision pairs
        self.collision_pairs.clear()
        
        # Apply gravity and update positions
        for obj_id, obj in world_state.objects.items():
            # Skip static objects
            if obj.physical_properties.get("static", False):
                continue
            
            # Get velocity and acceleration
            velocity = obj.physical_properties.get("velocity", (0.0, 0.0, 0.0))
            acceleration = obj.physical_properties.get("acceleration", (0.0, 0.0, 0.0))
            mass = obj.physical_properties.get("mass", 1.0)
            
            # Apply gravity if the object has mass
            if mass > 0:
                ax = acceleration[0] + self.gravity[0]
                ay = acceleration[1] + self.gravity[1]
                az = acceleration[2] + self.gravity[2]
            else:
                ax, ay, az = acceleration
            
            # Update velocity
            vx = velocity[0] + ax * delta_t
            vy = velocity[1] + ay * delta_t
            vz = velocity[2] + az * delta_t
            
            # Update position
            obj.pose.x += vx * delta_t
            obj.pose.y += vy * delta_t
            obj.pose.z += vz * delta_t
            
            # Update object properties
            obj.physical_properties["velocity"] = (vx, vy, vz)
            obj.physical_properties["acceleration"] = (ax, ay, az)
        
        # Handle collisions (simplified)
        self._handle_collisions(world_state)
    
    def _handle_collisions(self, world_state: WorldState) -> None:
        """
        Handle collisions between objects.
        
        This is a simplified collision detection and resolution system.
        In a real implementation, this would use more sophisticated algorithms.
        
        Args:
            world_state: The current world state
        """
        objects = list(world_state.objects.values())
        
        # Check for collisions between all pairs of objects
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                obj1 = objects[i]
                obj2 = objects[j]
                
                # Skip if either object is static
                if (obj1.physical_properties.get("static", False) and 
                    obj2.physical_properties.get("static", False)):
                    continue
                
                # Get collision radius (simplified as spheres)
                radius1 = obj1.physical_properties.get("collision_radius", 1.0)
                radius2 = obj2.physical_properties.get("collision_radius", 1.0)
                
                # Check if objects are colliding
                distance = obj1.pose.distance_to(obj2.pose)
                if distance < radius1 + radius2:
                    # Record collision
                    self.collision_pairs.add((obj1.object_id, obj2.object_id))
                    
                    # Simplified collision response (just separate the objects)
                    if not obj1.physical_properties.get("static", False) and not obj2.physical_properties.get("static", False):
                        # Calculate separation vector
                        dx = obj1.pose.x - obj2.pose.x
                        dy = obj1.pose.y - obj2.pose.y
                        dz = obj1.pose.z - obj2.pose.z
                        
                        # Normalize
                        length = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
                        dx /= length
                        dy /= length
                        dz /= length
                        
                        # Calculate overlap
                        overlap = (radius1 + radius2) - distance
                        
                        # Separate objects
                        obj1.pose.x += dx * overlap * 0.5
                        obj1.pose.y += dy * overlap * 0.5
                        obj1.pose.z += dz * overlap * 0.5
                        
                        obj2.pose.x -= dx * overlap * 0.5
                        obj2.pose.y -= dy * overlap * 0.5
                        obj2.pose.z -= dz * overlap * 0.5
                    elif obj1.physical_properties.get("static", False):
                        # Move only obj2 if obj1 is static
                        obj2.pose.x -= dx * overlap
                        obj2.pose.y -= dy * overlap
                        obj2.pose.z -= dz * overlap
                    elif obj2.physical_properties.get("static", False):
                        # Move only obj1 if obj2 is static
                        obj1.pose.x += dx * overlap
                        obj1.pose.y += dy * overlap
                        obj1.pose.z += dz * overlap


class VisionSensor(SensorModel):
    """
    A vision sensor model for the simulated environment.
    
    This sensor simulates a camera that can detect objects in its field of view.
    """
    
    def __init__(self, fov_degrees: float = 90.0, max_range: float = 100.0, 
                resolution_pixels: Tuple[int, int] = (640, 480),
                output_type: str = "feature_list"):
        """
        Initialize the vision sensor.
        
        Args:
            fov_degrees: Field of view in degrees
            max_range: Maximum detection range
            resolution_pixels: Resolution of the simulated camera
            output_type: Type of output ("raw_pixels" or "feature_list")
        """
        self.fov_degrees = fov_degrees
        self.max_range = max_range
        self.resolution_pixels = resolution_pixels
        self.output_type = output_type
    
    def generate_percept(self, world_state: WorldState, sensor_pose: Pose) -> RawSensorData:
        """
        Generate a vision percept based on the current world state and sensor pose.
        
        Args:
            world_state: The current state of the world
            sensor_pose: The pose of the sensor in the world
            
        Returns:
            Raw sensor data representing the vision percept
        """
        # Get objects within range
        visible_objects = world_state.get_objects_in_radius(sensor_pose, self.max_range)
        
        if self.output_type == "feature_list":
            # Generate a list of features for each visible object
            features = []
            
            for obj in visible_objects:
                # Check if object is in field of view (simplified)
                # In a real implementation, this would involve more sophisticated calculations
                
                # Calculate angle to object (simplified 2D version)
                dx = obj.pose.x - sensor_pose.x
                dy = obj.pose.y - sensor_pose.y
                angle = math.atan2(dy, dx) * 180 / math.pi
                
                # Check if angle is within field of view
                if abs(angle) <= self.fov_degrees / 2:
                    # Object is in field of view
                    distance = sensor_pose.distance_to(obj.pose)
                    
                    # Create feature for the object
                    feature = {
                        "object_id": obj.object_id,
                        "object_type": obj.object_type,
                        "distance": distance,
                        "angle": angle,
                        "visual_features": obj.visual_features.copy()
                    }
                    
                    features.append(feature)
            
            return RawSensorData(modality="vision", data=features)
        else:  # "raw_pixels"
            # In a real implementation, this would render a simulated camera view
            # For simplicity, we'll just return a placeholder
            return RawSensorData(modality="vision", data={
                "resolution": self.resolution_pixels,
                "pixel_data": "Simulated pixel data would go here"
            })


class TouchSensor(SensorModel):
    """
    A touch sensor model for the simulated environment.
    
    This sensor detects contact with objects in the environment.
    """
    
    def __init__(self, detection_radius: float = 0.1):
        """
        Initialize the touch sensor.
        
        Args:
            detection_radius: Radius within which contact is detected
        """
        self.detection_radius = detection_radius
    
    def generate_percept(self, world_state: WorldState, sensor_pose: Pose) -> RawSensorData:
        """
        Generate a touch percept based on the current world state and sensor pose.
        
        Args:
            world_state: The current state of the world
            sensor_pose: The pose of the sensor in the world
            
        Returns:
            Raw sensor data representing the touch percept
        """
        # Get objects in contact range
        contact_objects = world_state.get_objects_in_radius(sensor_pose, self.detection_radius)
        
        # Generate contact data
        contacts = []
        for obj in contact_objects:
            distance = sensor_pose.distance_to(obj.pose)
            force = 1.0 - (distance / self.detection_radius)  # Simplified force calculation
            
            contact = {
                "object_id": obj.object_id,
                "object_type": obj.object_type,
                "distance": distance,
                "force": force,
                "physical_properties": obj.physical_properties.copy()
            }
            
            contacts.append(contact)
        
        return RawSensorData(modality="touch", data=contacts)


class LocomotionActuator(ActuatorModel):
    """
    A locomotion actuator model for the simulated environment.
    
    This actuator allows agents to move around in the environment.
    """
    
    def __init__(self, max_speed: float = 5.0, max_force: float = 10.0):
        """
        Initialize the locomotion actuator.
        
        Args:
            max_speed: Maximum speed
            max_force: Maximum force
        """
        self.max_speed = max_speed
        self.max_force = max_force
    
    def execute_action(self, world_state: WorldState, actuator_pose: Pose, 
                      parameters: Dict[str, Any]) -> ActionOutcome:
        """
        Execute a locomotion action.
        
        Args:
            world_state: The current state of the world
            actuator_pose: The pose of the actuator in the world
            parameters: Parameters for the action
            
        Returns:
            The outcome of the action
        """
        # Get action parameters
        action_type = parameters.get("action_type", "move")
        
        if action_type == "move":
            # Get movement parameters
            direction = parameters.get("direction", (1.0, 0.0, 0.0))
            speed = min(parameters.get("speed", 1.0), self.max_speed)
            
            # Normalize direction
            dx, dy, dz = direction
            length = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
            dx /= length
            dy /= length
            dz /= length
            
            # Calculate movement
            delta_x = dx * speed
            delta_y = dy * speed
            delta_z = dz * speed
            
            # Find the agent this actuator belongs to
            agent = None
            for a in world_state.agents.values():
                for act in a.actuators:
                    if act.relative_pose.distance_to(actuator_pose) < 0.01:
                        agent = a
                        break
                if agent:
                    break
            
            if not agent:
                return ActionOutcome(
                    success=False,
                    message="Could not find agent for this actuator"
                )
            
            # Update agent position
            agent.pose.x += delta_x
            agent.pose.y += delta_y
            agent.pose.z += delta_z
            
            return ActionOutcome(
                success=True,
                message=f"Moved by ({delta_x}, {delta_y}, {delta_z})",
                achieved_state_delta={
                    "position_delta": (delta_x, delta_y, delta_z)
                }
            )
        
        elif action_type == "rotate":
            # Get rotation parameters
            axis = parameters.get("axis", (0.0, 0.0, 1.0))
            angle = parameters.get("angle", 0.0)
            
            # Find the agent this actuator belongs to
            agent = None
            for a in world_state.agents.values():
                for act in a.actuators:
                    if act.relative_pose.distance_to(actuator_pose) < 0.01:
                        agent = a
                        break
                if agent:
                    break
            
            if not agent:
                return ActionOutcome(
                    success=False,
                    message="Could not find agent for this actuator"
                )
            
            # For simplicity, we'll just update the orientation directly
            # In a real implementation, this would involve quaternion operations
            if agent.pose.is_quaternion():
                # Placeholder for quaternion rotation
                return ActionOutcome(
                    success=True,
                    message=f"Rotated by {angle} radians around axis {axis}",
                    achieved_state_delta={
                        "rotation_delta": (axis, angle)
                    }
                )
            else:
                # Euler angles rotation (simplified)
                roll, pitch, yaw = agent.pose.orientation
                
                # Update based on axis
                if axis[0] > 0.5:  # X-axis
                    roll += angle
                elif axis[1] > 0.5:  # Y-axis
                    pitch += angle
                elif axis[2] > 0.5:  # Z-axis
                    yaw += angle
                
                agent.pose.orientation = (roll, pitch, yaw)
                
                return ActionOutcome(
                    success=True,
                    message=f"Rotated by {angle} radians around axis {axis}",
                    achieved_state_delta={
                        "rotation_delta": (axis, angle)
                    }
                )
        
        else:
            return ActionOutcome(
                success=False,
                message=f"Unknown action type: {action_type}"
            )


class GripperActuator(ActuatorModel):
    """
    A gripper actuator model for the simulated environment.
    
    This actuator allows agents to grasp and manipulate objects.
    """
    
    def __init__(self, max_force: float = 10.0, open_angle_range: Tuple[float, float] = (0.0, 1.5)):
        """
        Initialize the gripper actuator.
        
        Args:
            max_force: Maximum gripping force
            open_angle_range: Range of opening angles
        """
        self.max_force = max_force
        self.open_angle_range = open_angle_range
        self.gripped_object_id = None
    
    def execute_action(self, world_state: WorldState, actuator_pose: Pose, 
                      parameters: Dict[str, Any]) -> ActionOutcome:
        """
        Execute a gripper action.
        
        Args:
            world_state: The current state of the world
            actuator_pose: The pose of the actuator in the world
            parameters: Parameters for the action
            
        Returns:
            The outcome of the action
        """
        # Get action parameters
        action_type = parameters.get("action_type", "grip")
        
        if action_type == "grip":
            # Get gripping parameters
            force = min(parameters.get("force", 5.0), self.max_force)
            
            # Find objects within gripping range
            grippable_objects = world_state.get_objects_in_radius(actuator_pose, 0.2)
            
            if not grippable_objects:
                return ActionOutcome(
                    success=False,
                    message="No objects within gripping range"
                )
            
            # Sort by distance and pick the closest
            grippable_objects.sort(key=lambda obj: obj.pose.distance_to(actuator_pose))
            target_object = grippable_objects[0]
            
            # Set the gripped object
            self.gripped_object_id = target_object.object_id
            
            return ActionOutcome(
                success=True,
                message=f"Gripped object {target_object.object_id} with force {force}",
                achieved_state_delta={
                    "gripped_object_id": target_object.object_id,
                    "grip_force": force
                }
            )
        
        elif action_type == "release":
            if not self.gripped_object_id:
                return ActionOutcome(
                    success=False,
                    message="No object currently gripped"
                )
            
            # Release the object
            released_object_id = self.gripped_object_id
            self.gripped_object_id = None
            
            return ActionOutcome(
                success=True,
                message=f"Released object {released_object_id}",
                achieved_state_delta={
                    "released_object_id": released_object_id
                }
            )
        
        else:
            return ActionOutcome(
                success=False,
                message=f"Unknown action type: {action_type}"
            )


class SimulatedEnvironment:
    """
    Simulated Environment (SimEnv) for GödelOS.
    
    This class implements the SimulatedEnvironment component (Module 4.1) of the Symbol Grounding System,
    which is responsible for maintaining the state of a simulated world, providing sensory data to the agent,
    and executing primitive actions received from the agent.
    """
    
    def __init__(self, world_config_filepath: Optional[str] = None):
        """
        Initialize the simulated environment.
        
        Args:
            world_config_filepath: Path to a JSON file containing the world configuration
        """
        self.world_state = WorldState()
        self.physics_engine = PhysicsEngine()
        self.pending_actions = {}  # agent_id -> (action_name, parameters)
        
        # Load world configuration if provided
        if world_config_filepath:
            self.load_world_config(world_config_filepath)
    
    def load_world_config(self, config_filepath: str) -> None:
        """
        Load a world configuration from a file.
        
        Args:
            config_filepath: Path to the configuration file
        """
        try:
            with open(config_filepath, 'r') as f:
                config = json.load(f)
            
            # Process configuration
            self._process_world_config(config)
            
            logger.info(f"Loaded world configuration from {config_filepath}")
        except Exception as e:
            logger.error(f"Error loading world configuration: {e}")
            raise
    
    def _process_world_config(self, config: Dict[str, Any]) -> None:
        """
        Process a world configuration.
        
        Args:
            config: The configuration dictionary
        """
        # Process objects
        for obj_config in config.get("objects", []):
            self.add_object(obj_config)
        
        # Process agents
        for agent_config in config.get("agents", []):
            # Create agent
            agent_id = agent_config.get("agent_id", str(uuid.uuid4()))
            
            # Create pose
            pose_config = agent_config.get("pose", {})
            pose = Pose(
                x=pose_config.get("x", 0.0),
                y=pose_config.get("y", 0.0),
                z=pose_config.get("z", 0.0)
            )
            
            # Create agent
            agent = SimAgent(agent_id=agent_id, pose=pose)
            
            # Add sensors
            for sensor_config in agent_config.get("sensors", []):
                sensor_type = sensor_config.get("sensor_type")
                if sensor_type == "vision":
                    model = VisionSensor(
                        fov_degrees=sensor_config.get("fov_degrees", 90.0),
                        max_range=sensor_config.get("max_range", 100.0),
                        resolution_pixels=sensor_config.get("resolution_pixels", (640, 480)),
                        output_type=sensor_config.get("output_type", "feature_list")
                    )
                elif sensor_type == "touch":
                    model = TouchSensor(
                        detection_radius=sensor_config.get("detection_radius", 0.1)
                    )
                else:
                    logger.warning(f"Unknown sensor type: {sensor_type}")
                    continue
                
                # Create sensor instance
                sensor = SensorInstance(
                    sensor_id=sensor_config.get("sensor_id", f"{sensor_type}_{uuid.uuid4()}"),
                    sensor_type=sensor_type,
                    model=model,
                    relative_pose=Pose(
                        x=sensor_config.get("relative_x", 0.0),
                        y=sensor_config.get("relative_y", 0.0),
                        z=sensor_config.get("relative_z", 0.0)
                    ),
                    parameters=sensor_config.get("parameters", {})
                )
                
                agent.sensors.append(sensor)
            
            # Add actuators
            for actuator_config in agent_config.get("actuators", []):
                actuator_type = actuator_config.get("actuator_type")
                if actuator_type == "locomotion":
                    model = LocomotionActuator(
                        max_speed=actuator_config.get("max_speed", 5.0),
                        max_force=actuator_config.get("max_force", 10.0)
                    )
                elif actuator_type == "gripper":
                    model = GripperActuator(
                        max_force=actuator_config.get("max_force", 10.0),
                        open_angle_range=actuator_config.get("open_angle_range", (0.0, 1.5))
                    )
                else:
                    logger.warning(f"Unknown actuator type: {actuator_type}")
                    continue
                
                # Create actuator instance
                actuator = ActuatorInstance(
                    actuator_id=actuator_config.get("actuator_id", f"{actuator_type}_{uuid.uuid4()}"),
                    actuator_type=actuator_type,
                    model=model,
                    relative_pose=Pose(
                        x=actuator_config.get("relative_x", 0.0),
                        y=actuator_config.get("relative_y", 0.0),
                        z=actuator_config.get("relative_z", 0.0)
                    ),
                    parameters=actuator_config.get("parameters", {})
                )
                
                agent.actuators.append(actuator)
            
            # Add agent to world state
            self.world_state.add_agent(agent)
        
        # Process global state
        self.world_state.global_state.update(config.get("global_state", {}))
    
    def tick(self, delta_t: float) -> None:
        """
        Update the world state for a time step.
        
        Args:
            delta_t: The time step
        """
        # Process pending actions
        for agent_id, (action_name, parameters) in self.pending_actions.items():
            self.execute_primitive_env_action(agent_id, action_name, parameters)
        
        # Clear pending actions
        self.pending_actions.clear()
        
        # Update physics
        self.physics_engine.update(self.world_state, delta_t)
        
        # Update time
        self.world_state.time += delta_t
    
    def get_agent_percepts(self, agent_id: str) -> Dict[str, RawSensorData]:
        """
        Get sensory data for a specific agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            A dictionary mapping sensor IDs to raw sensor data
        """
        agent = self.world_state.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return {}
        
        percepts = {}
        for sensor in agent.sensors:
            # Calculate sensor pose in world coordinates
            sensor_pose = Pose(
                x=agent.pose.x + sensor.relative_pose.x,
                y=agent.pose.y + sensor.relative_pose.y,
                z=agent.pose.z + sensor.relative_pose.z
            )
            
            # Generate percept
            percept = sensor.model.generate_percept(self.world_state, sensor_pose)
            percepts[sensor.sensor_id] = percept
        
        return percepts
    
    def execute_primitive_env_action(self, agent_id: str, action_name: str, 
                                    parameters: Dict[str, Any]) -> ActionOutcome:
        """
        Execute a primitive action for a specific agent.
        
        Args:
            agent_id: The ID of the agent
            action_name: The name of the action
            parameters: Parameters for the action
            
        Returns:
            The outcome of the action
        """
        agent = self.world_state.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return ActionOutcome(
                success=False,
                message=f"Agent {agent_id} not found"
            )
        
        # Find the appropriate actuator
        actuator = None
        for act in agent.actuators:
            if act.actuator_type == action_name or act.actuator_id == action_name:
                actuator = act
                break
        
        if not actuator:
            logger.warning(f"Actuator for action {action_name} not found on agent {agent_id}")
            return ActionOutcome(
                success=False,
                message=f"Actuator for action {action_name} not found on agent {agent_id}"
            )
        
        # Calculate actuator pose in world coordinates
        actuator_pose = Pose(
            x=agent.pose.x + actuator.relative_pose.x,
            y=agent.pose.y + actuator.relative_pose.y,
            z=agent.pose.z + actuator.relative_pose.z
        )
        
        # Execute action
        return actuator.model.execute_action(self.world_state, actuator_pose, parameters)
    
    def get_object_details(self, object_id: str) -> Optional[SimObject]:
        """
        Get details about a specific object.
        
        Args:
            object_id: The ID of the object
            
        Returns:
            The object, or None if not found
        """
        return self.world_state.get_object(object_id)
    
    def add_object(self, object_config: Dict[str, Any]) -> str:
        """
        Add a new object to the environment.
        
        Args:
            object_config: Configuration for the object
            
        Returns:
            The ID of the added object
        """
        # Create object ID
        object_id = object_config.get("object_id", str(uuid.uuid4()))
        
        # Get object type
        object_type = object_config.get("object_type", "generic")
        
        # Create pose
        pose_config = object_config.get("pose", {})
        pose = Pose(
            x=pose_config.get("x", 0.0),
            y=pose_config.get("y", 0.0),
            z=pose_config.get("z", 0.0)
        )
        
        # Create object
        obj = SimObject(
            object_id=object_id,
            object_type=object_type,
            pose=pose,
            visual_features=object_config.get("visual_features", {}),
            physical_properties=object_config.get("physical_properties", {}),
            custom_state=object_config.get("custom_state", {})
        )
        
        # Add object to world state
        return self.world_state.add_object(obj)