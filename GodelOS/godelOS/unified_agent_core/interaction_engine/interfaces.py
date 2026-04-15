"""
Interaction Engine Interfaces for GodelOS

This module defines the interfaces for the InteractionEngine component of the
UnifiedAgentCore architecture, including HumanHandler, AgentHandler, LogicHandler,
and ProtocolManager.
"""

import abc
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from dataclasses import dataclass, field
import time
import uuid
from enum import Enum


class InteractionType(Enum):
    """Enum representing different types of interactions."""
    HUMAN = "human"
    AGENT = "agent"
    LOGIC = "logic"
    SYSTEM = "system"


class InteractionStatus(Enum):
    """Enum representing the status of an interaction."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class Interaction:
    """Class representing an interaction in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: InteractionType = InteractionType.HUMAN
    content: Dict[str, Any] = field(default_factory=dict)
    status: InteractionStatus = InteractionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Response:
    """Class representing a response to an interaction."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    interaction_id: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Protocol:
    """Class representing a communication protocol."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0"
    interaction_type: InteractionType = InteractionType.HUMAN
    schema: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InteractionHandlerInterface(abc.ABC):
    """Protocol for interaction handlers."""
    
    @abc.abstractmethod
    async def handle(self, interaction: Interaction) -> Response:
        """
        Handle an interaction.
        
        Args:
            interaction: The interaction to handle
            
        Returns:
            The response to the interaction
        """
        pass
    
    @abc.abstractmethod
    async def can_handle(self, interaction: Interaction) -> bool:
        """
        Determine if this handler can handle the interaction.
        
        Args:
            interaction: The interaction to check
            
        Returns:
            True if this handler can handle the interaction, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def validate(self, interaction: Interaction) -> bool:
        """
        Validate an interaction before handling.
        
        Args:
            interaction: The interaction to validate
            
        Returns:
            True if the interaction is valid, False otherwise
        """
        pass


class HumanHandlerInterface(InteractionHandlerInterface):
    """Protocol for human interaction handlers."""
    
    @abc.abstractmethod
    async def format_response_for_human(self, response: Response) -> str:
        """
        Format a response for human consumption.
        
        Args:
            response: The response to format
            
        Returns:
            The formatted response as a string
        """
        pass
    
    @abc.abstractmethod
    async def parse_human_input(self, input_str: str) -> Interaction:
        """
        Parse human input into an interaction.
        
        Args:
            input_str: The human input string
            
        Returns:
            The parsed interaction
        """
        pass


class AgentHandlerInterface(InteractionHandlerInterface):
    """Protocol for agent interaction handlers."""
    
    @abc.abstractmethod
    async def negotiate_protocol(self, agent_id: str, protocol_candidates: List[str]) -> Optional[Protocol]:
        """
        Negotiate a communication protocol with another agent.
        
        Args:
            agent_id: The ID of the agent to negotiate with
            protocol_candidates: List of candidate protocol names
            
        Returns:
            The negotiated protocol, or None if negotiation failed
        """
        pass
    
    @abc.abstractmethod
    async def verify_agent_identity(self, agent_id: str, credentials: Dict[str, Any]) -> bool:
        """
        Verify the identity of an agent.
        
        Args:
            agent_id: The ID of the agent to verify
            credentials: The agent's credentials
            
        Returns:
            True if the agent's identity is verified, False otherwise
        """
        pass


class LogicHandlerInterface(InteractionHandlerInterface):
    """Protocol for logic interaction handlers."""
    
    @abc.abstractmethod
    async def translate_to_formal_logic(self, interaction: Interaction) -> Dict[str, Any]:
        """
        Translate an interaction to formal logic.
        
        Args:
            interaction: The interaction to translate
            
        Returns:
            The formal logic representation
        """
        pass
    
    @abc.abstractmethod
    async def translate_from_formal_logic(self, logic_result: Dict[str, Any]) -> Response:
        """
        Translate formal logic result to a response.
        
        Args:
            logic_result: The formal logic result
            
        Returns:
            The translated response
        """
        pass


class ProtocolManagerInterface(abc.ABC):
    """Protocol for protocol management operations."""
    
    @abc.abstractmethod
    async def register_protocol(self, protocol: Protocol) -> bool:
        """
        Register a communication protocol.
        
        Args:
            protocol: The protocol to register
            
        Returns:
            True if the protocol was registered successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def get_protocol(self, interaction_type: InteractionType) -> Optional[Protocol]:
        """
        Get a protocol for an interaction type.
        
        Args:
            interaction_type: The interaction type
            
        Returns:
            The protocol, or None if no protocol is registered for the interaction type
        """
        pass
    
    @abc.abstractmethod
    async def validate(self, interaction: Interaction) -> Interaction:
        """
        Validate an interaction against its protocol.
        
        Args:
            interaction: The interaction to validate
            
        Returns:
            The validated interaction
        
        Raises:
            ValidationError: If the interaction is invalid
        """
        pass


class InteractionEngineInterface(abc.ABC):
    """Abstract base class for interaction engine implementations."""
    
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the interaction engine.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def start(self) -> bool:
        """
        Start the interaction engine.
        
        Returns:
            True if the engine was started successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def stop(self) -> bool:
        """
        Stop the interaction engine.
        
        Returns:
            True if the engine was stopped successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def process_interaction(self, interaction_data: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an interaction.
        
        Args:
            interaction_data: The interaction data
            resources: The resources allocated for processing
            
        Returns:
            The response to the interaction
        """
        pass
    
    @abc.abstractmethod
    def set_state(self, state: Any) -> None:
        """
        Set the unified state reference.
        
        Args:
            state: The unified state
        """
        pass
    
    @abc.abstractmethod
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The unified knowledge store
        """
        pass
    
    @abc.abstractmethod
    def set_resource_manager(self, resource_manager: Any) -> None:
        """
        Set the resource manager reference.
        
        Args:
            resource_manager: The unified resource manager
        """
        pass
    
    @abc.abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the interaction engine.
        
        Returns:
            Dictionary with status information
        """
        pass


class AbstractInteractionEngine(InteractionEngineInterface):
    """
    Abstract implementation of the InteractionEngineInterface.
    
    This class provides a base implementation of the InteractionEngineInterface
    with common functionality that concrete implementations can build upon.
    """
    
    def __init__(self):
        """Initialize the abstract interaction engine."""
        self.human_handler = None
        self.agent_handler = None
        self.logic_handler = None
        self.protocol_manager = None
        self.state = None
        self.knowledge_store = None
        self.resource_manager = None
        self.is_initialized = False
        self.is_running = False
    
    def set_state(self, state: Any) -> None:
        """
        Set the unified state reference.
        
        Args:
            state: The unified state
        """
        self.state = state
    
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The unified knowledge store
        """
        self.knowledge_store = knowledge_store
    
    def set_resource_manager(self, resource_manager: Any) -> None:
        """
        Set the resource manager reference.
        
        Args:
            resource_manager: The unified resource manager
        """
        self.resource_manager = resource_manager
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the interaction engine.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": {
                "human_handler": bool(self.human_handler),
                "agent_handler": bool(self.agent_handler),
                "logic_handler": bool(self.logic_handler),
                "protocol_manager": bool(self.protocol_manager)
            }
        }