"""
Agent Interaction Handler Implementation for GodelOS

This module implements the AgentHandler class, which is responsible for
handling interactions with other agents, including protocol negotiation,
identity verification, and structured message exchange.
"""

import logging
import time
import json
import hashlib
import hmac
import base64
from typing import Dict, List, Optional, Any, Tuple
import asyncio

from godelOS.unified_agent_core.interaction_engine.interfaces import (
    Interaction, Response, InteractionType, InteractionStatus, Protocol,
    AgentHandlerInterface
)

logger = logging.getLogger(__name__)


class AgentIdentityError(Exception):
    """Exception raised when agent identity verification fails."""
    pass


class ProtocolNegotiationError(Exception):
    """Exception raised when protocol negotiation fails."""
    pass


class AgentHandler(AgentHandlerInterface):
    """
    AgentHandler implementation for GodelOS.
    
    The AgentHandler is responsible for handling interactions with other agents,
    including protocol negotiation, identity verification, and structured message
    exchange.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize agent registry
        self.agent_registry: Dict[str, Dict[str, Any]] = {}
        
        # Initialize protocol registry
        self.supported_protocols: Dict[str, Dict[str, Any]] = {}
        
        # Initialize collaboration sessions
        self.collaboration_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize conflict resolution strategies
        self.conflict_resolution_strategies: Dict[str, Dict[str, Any]] = {
            "majority_vote": {
                "description": "Resolve conflicts by majority vote among participating agents",
                "min_agents": 3
            },
            "priority_based": {
                "description": "Resolve conflicts based on agent priority levels",
                "requires_priority": True
            },
            "consensus": {
                "description": "Require consensus among all participating agents",
                "consensus_threshold": 1.0
            },
            "expert_domain": {
                "description": "Defer to the agent with expertise in the relevant domain",
                "requires_expertise": True
            }
        }
        
        # Initialize knowledge store and cognitive engine references
        self.knowledge_store = None
        self.cognitive_engine = None
        
        # Load trusted agents from config
        self._load_trusted_agents()
        
        # Load supported protocols from config
        self._load_supported_protocols()
    
    def set_knowledge_store(self, knowledge_store: Any) -> None:
        """
        Set the knowledge store reference.
        
        Args:
            knowledge_store: The unified knowledge store
        """
        self.knowledge_store = knowledge_store
    
    def set_cognitive_engine(self, cognitive_engine: Any) -> None:
        """
        Set the cognitive engine reference.
        
        Args:
            cognitive_engine: The cognitive engine
        """
        self.cognitive_engine = cognitive_engine
    
    async def handle(self, interaction: Interaction) -> Response:
        """
        Handle an agent interaction.
        
        Args:
            interaction: The interaction to handle
            
        Returns:
            The response to the interaction
        """
        logger.info(f"Handling agent interaction: {interaction.id}")
        
        try:
            # Extract agent ID and message from interaction content
            agent_id = interaction.content.get("agent_id", "")
            message = interaction.content.get("message", "")
            credentials = interaction.content.get("credentials", {})
            
            if not agent_id:
                raise ValueError("Missing agent_id in interaction content")
            
            if not message:
                raise ValueError("Missing message in interaction content")
            
            # Verify agent identity
            if not await self.verify_agent_identity(agent_id, credentials):
                raise AgentIdentityError(f"Failed to verify identity of agent {agent_id}")
            
            # Process message based on its type
            message_type = interaction.content.get("message_type", "standard")
            
            if message_type == "protocol_negotiation":
                # Handle protocol negotiation
                protocol_candidates = interaction.content.get("protocol_candidates", [])
                negotiated_protocol = await self.negotiate_protocol(agent_id, protocol_candidates)
                
                if not negotiated_protocol:
                    raise ProtocolNegotiationError("Failed to negotiate protocol")
                
                response_content = {
                    "message_type": "protocol_negotiation_response",
                    "protocol_name": negotiated_protocol.name,
                    "protocol_version": negotiated_protocol.version,
                    "success": True
                }
            elif message_type == "collaboration_request":
                # Handle collaboration request
                session_id = interaction.content.get("session_id", "")
                task = interaction.content.get("task", {})
                participants = interaction.content.get("participants", [])
                
                # Create or join collaboration session
                session = await self._create_or_join_collaboration_session(
                    session_id, agent_id, task, participants
                )
                
                response_content = {
                    "message_type": "collaboration_response",
                    "session_id": session["session_id"],
                    "status": session["status"],
                    "role": session["participants"].get(agent_id, {}).get("role", "participant")
                }
            elif message_type == "conflict_resolution":
                # Handle conflict resolution
                session_id = interaction.content.get("session_id", "")
                conflict_type = interaction.content.get("conflict_type", "")
                conflict_data = interaction.content.get("conflict_data", {})
                
                # Resolve conflict
                resolution = await self._resolve_conflict(
                    session_id, agent_id, conflict_type, conflict_data
                )
                
                response_content = {
                    "message_type": "conflict_resolution_response",
                    "session_id": session_id,
                    "resolution": resolution,
                    "status": "resolved" if resolution else "unresolved"
                }
            else:
                # Handle standard message
                # Process message with cognitive engine if available
                if self.cognitive_engine:
                    thought_request = {
                        "type": "agent_interaction",
                        "content": {
                            "agent_id": agent_id,
                            "message": message,
                            "message_type": message_type
                        }
                    }
                    
                    thought_result = await self.cognitive_engine.process_thought(thought_request)
                    
                    response_content = {
                        "message": thought_result.get("response", "Message received"),
                        "status": "processed"
                    }
                else:
                    # Default response
                    response_content = {
                        "message": "Message received",
                        "status": "acknowledged"
                    }
            
            # Create response object
            response = Response(
                interaction_id=interaction.id,
                content=response_content,
                metadata={
                    "agent_id": agent_id,
                    "processing_time": time.time() - interaction.created_at
                }
            )
            
            return response
        except AgentIdentityError as e:
            logger.error(f"Agent identity error: {e}")
            
            # Create error response
            return Response(
                interaction_id=interaction.id,
                content={
                    "error": "agent_identity_error",
                    "message": str(e)
                },
                metadata={
                    "error": True,
                    "error_type": "agent_identity_error"
                }
            )
        except ProtocolNegotiationError as e:
            logger.error(f"Protocol negotiation error: {e}")
            
            # Create error response
            return Response(
                interaction_id=interaction.id,
                content={
                    "error": "protocol_negotiation_error",
                    "message": str(e)
                },
                metadata={
                    "error": True,
                    "error_type": "protocol_negotiation_error"
                }
            )
        except Exception as e:
            logger.error(f"Error handling agent interaction {interaction.id}: {e}")
            
            # Create error response
            return Response(
                interaction_id=interaction.id,
                content={
                    "error": "internal_error",
                    "message": str(e)
                },
                metadata={
                    "error": True,
                    "error_type": "internal_error"
                }
            )
    
    async def can_handle(self, interaction: Interaction) -> bool:
        """
        Determine if this handler can handle the interaction.
        
        Args:
            interaction: The interaction to check
            
        Returns:
            True if this handler can handle the interaction, False otherwise
        """
        # Check if interaction type is AGENT
        if interaction.type != InteractionType.AGENT:
            return False
        
        # Check if interaction content has required fields
        if "agent_id" not in interaction.content:
            return False
        
        if "message" not in interaction.content:
            return False
        
        return True
    
    async def validate(self, interaction: Interaction) -> bool:
        """
        Validate an agent interaction before handling.
        
        Args:
            interaction: The interaction to validate
            
        Returns:
            True if the interaction is valid, False otherwise
        """
        # Check if interaction type is AGENT
        if interaction.type != InteractionType.AGENT:
            return False
        
        # Check if interaction content has required fields
        if "agent_id" not in interaction.content:
            return False
        
        if "message" not in interaction.content:
            return False
        
        # Check if agent ID is registered
        agent_id = interaction.content.get("agent_id", "")
        if agent_id not in self.agent_registry:
            # Allow unknown agents if configured to do so
            if not self.config.get("allow_unknown_agents", False):
                return False
        
        return True
    
    async def negotiate_protocol(self, agent_id: str, protocol_candidates: List[str]) -> Optional[Protocol]:
        """
        Negotiate a communication protocol with another agent.
        
        Args:
            agent_id: The ID of the agent to negotiate with
            protocol_candidates: List of candidate protocol names
            
        Returns:
            The negotiated protocol, or None if negotiation failed
        """
        logger.info(f"Negotiating protocol with agent {agent_id}")
        
        # Check if agent is registered
        if agent_id not in self.agent_registry and not self.config.get("allow_unknown_agents", False):
            logger.warning(f"Unknown agent {agent_id} attempted protocol negotiation")
            return None
        
        # Find common protocols
        common_protocols = []
        for protocol_name in protocol_candidates:
            if protocol_name in self.supported_protocols:
                common_protocols.append(protocol_name)
        
        if not common_protocols:
            logger.warning(f"No common protocols found with agent {agent_id}")
            return None
        
        # Select highest priority common protocol
        selected_protocol_name = None
        highest_priority = -1
        
        for protocol_name in common_protocols:
            priority = self.supported_protocols[protocol_name].get("priority", 0)
            if priority > highest_priority:
                highest_priority = priority
                selected_protocol_name = protocol_name
        
        if not selected_protocol_name:
            logger.warning(f"Failed to select protocol with agent {agent_id}")
            return None
        
        # Create protocol object
        protocol_info = self.supported_protocols[selected_protocol_name]
        protocol = Protocol(
            name=selected_protocol_name,
            version=protocol_info.get("version", "1.0"),
            interaction_type=InteractionType.AGENT,
            schema=protocol_info.get("schema", {})
        )
        
        logger.info(f"Negotiated protocol {protocol.name} v{protocol.version} with agent {agent_id}")
        return protocol
    
    async def verify_agent_identity(self, agent_id: str, credentials: Dict[str, Any]) -> bool:
        """
        Verify the identity of an agent.
        
        Args:
            agent_id: The ID of the agent to verify
            credentials: The agent's credentials
            
        Returns:
            True if the agent's identity is verified, False otherwise
        """
        # Check if agent is registered
        if agent_id not in self.agent_registry:
            # Allow unknown agents if configured to do so
            if self.config.get("allow_unknown_agents", False):
                logger.warning(f"Unknown agent {agent_id} allowed due to configuration")
                return True
            else:
                logger.warning(f"Unknown agent {agent_id} attempted to interact")
                return False
        
        # Get agent info
        agent_info = self.agent_registry[agent_id]
        
        # Check verification method
        verification_method = agent_info.get("verification_method", "api_key")
        
        if verification_method == "api_key":
            # Verify API key
            expected_key = agent_info.get("api_key", "")
            provided_key = credentials.get("api_key", "")
            
            if not expected_key or not provided_key:
                logger.warning(f"Missing API key for agent {agent_id}")
                return False
            
            return hmac.compare_digest(expected_key, provided_key)
        
        elif verification_method == "hmac":
            # Verify HMAC signature
            secret_key = agent_info.get("secret_key", "")
            signature = credentials.get("signature", "")
            message = credentials.get("message", "")
            
            if not secret_key or not signature or not message:
                logger.warning(f"Missing HMAC verification data for agent {agent_id}")
                return False
            
            # Compute expected signature
            expected_signature = hmac.new(
                secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        elif verification_method == "certificate":
            # Certificate verification would be implemented here
            # This is a placeholder for future implementation
            logger.warning("Certificate verification not yet implemented")
            return False
        
        else:
            logger.warning(f"Unknown verification method {verification_method} for agent {agent_id}")
            return False
    
    async def _create_or_join_collaboration_session(
        self, session_id: str, agent_id: str, task: Dict[str, Any], participants: List[str]
    ) -> Dict[str, Any]:
        """
        Create or join a collaboration session.
        
        Args:
            session_id: The session ID (empty for new session)
            agent_id: The agent ID
            task: The task details
            participants: List of participant agent IDs
            
        Returns:
            The collaboration session
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{int(time.time())}_{hash(agent_id) % 10000}"
        
        # Check if session exists
        if session_id in self.collaboration_sessions:
            # Join existing session
            session = self.collaboration_sessions[session_id]
            
            # Add agent as participant if not already
            if agent_id not in session["participants"]:
                session["participants"][agent_id] = {
                    "joined_at": time.time(),
                    "role": "participant",
                    "status": "active"
                }
            
            return session
        else:
            # Create new session
            session = {
                "session_id": session_id,
                "created_at": time.time(),
                "status": "active",
                "task": task,
                "participants": {
                    agent_id: {
                        "joined_at": time.time(),
                        "role": "initiator",
                        "status": "active"
                    }
                },
                "messages": [],
                "conflicts": [],
                "results": {}
            }
            
            # Add other participants
            for participant_id in participants:
                if participant_id != agent_id:
                    session["participants"][participant_id] = {
                        "joined_at": time.time(),
                        "role": "participant",
                        "status": "invited"
                    }
            
            # Store session
            self.collaboration_sessions[session_id] = session
            
            return session
    
    async def _resolve_conflict(
        self, session_id: str, agent_id: str, conflict_type: str, conflict_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve a conflict in a collaboration session.
        
        Args:
            session_id: The session ID
            agent_id: The agent ID
            conflict_type: The type of conflict
            conflict_data: The conflict data
            
        Returns:
            The conflict resolution
        """
        # Check if session exists
        if session_id not in self.collaboration_sessions:
            logger.warning(f"Conflict resolution attempted for unknown session {session_id}")
            return {"status": "error", "message": "Unknown session"}
        
        session = self.collaboration_sessions[session_id]
        
        # Check if agent is a participant
        if agent_id not in session["participants"]:
            logger.warning(f"Non-participant agent {agent_id} attempted conflict resolution")
            return {"status": "error", "message": "Not a session participant"}
        
        # Record conflict
        conflict = {
            "id": f"conflict_{len(session['conflicts']) + 1}",
            "type": conflict_type,
            "data": conflict_data,
            "reported_by": agent_id,
            "reported_at": time.time(),
            "status": "pending",
            "resolution": None
        }
        
        session["conflicts"].append(conflict)
        
        # Select resolution strategy
        strategy = conflict_data.get("resolution_strategy", "consensus")
        
        if strategy not in self.conflict_resolution_strategies:
            strategy = "consensus"  # Default to consensus
        
        # Apply resolution strategy
        if strategy == "majority_vote":
            resolution = await self._apply_majority_vote(session, conflict)
        elif strategy == "priority_based":
            resolution = await self._apply_priority_based(session, conflict)
        elif strategy == "expert_domain":
            resolution = await self._apply_expert_domain(session, conflict)
        else:  # consensus
            resolution = await self._apply_consensus(session, conflict)
        
        # Update conflict with resolution
        conflict["status"] = "resolved" if resolution else "unresolved"
        conflict["resolution"] = resolution
        
        return resolution
    
    async def _apply_majority_vote(self, session: Dict[str, Any], conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply majority vote conflict resolution strategy."""
        # This is a placeholder implementation
        # In a real system, this would collect votes from all participants
        return {
            "strategy": "majority_vote",
            "result": conflict["data"].get("options", [])[0] if conflict["data"].get("options") else None,
            "reason": "Selected by majority vote (simulated)"
        }
    
    async def _apply_priority_based(self, session: Dict[str, Any], conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply priority-based conflict resolution strategy."""
        # This is a placeholder implementation
        # In a real system, this would determine the highest priority agent's preference
        return {
            "strategy": "priority_based",
            "result": conflict["data"].get("options", [])[0] if conflict["data"].get("options") else None,
            "reason": "Selected by highest priority agent (simulated)"
        }
    
    async def _apply_expert_domain(self, session: Dict[str, Any], conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply expert domain conflict resolution strategy."""
        # This is a placeholder implementation
        # In a real system, this would identify the domain expert and use their preference
        domain = conflict["data"].get("domain", "general")
        return {
            "strategy": "expert_domain",
            "result": conflict["data"].get("options", [])[0] if conflict["data"].get("options") else None,
            "reason": f"Selected by domain expert for {domain} (simulated)"
        }
    
    async def _apply_consensus(self, session: Dict[str, Any], conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply consensus conflict resolution strategy."""
        # This is a placeholder implementation
        # In a real system, this would require agreement from all participants
        return {
            "strategy": "consensus",
            "result": conflict["data"].get("options", [])[0] if conflict["data"].get("options") else None,
            "reason": "Consensus reached (simulated)"
        }
    
    def _load_trusted_agents(self) -> None:
        """Load trusted agents from configuration."""
        trusted_agents = self.config.get("trusted_agents", [])
        
        for agent in trusted_agents:
            agent_id = agent.get("id")
            if agent_id:
                self.agent_registry[agent_id] = agent
    
    def _load_supported_protocols(self) -> None:
        """Load supported protocols from configuration."""
        protocols = self.config.get("supported_protocols", [])
        
        for protocol in protocols:
            protocol_name = protocol.get("name")
            if protocol_name:
                self.supported_protocols[protocol_name] = protocol
        
        # Add default protocol if none configured
        if not self.supported_protocols:
            self.supported_protocols["standard_agent_protocol"] = {
                "name": "standard_agent_protocol",
                "version": "1.0",
                "priority": 100,
                "schema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "message_type": {"type": "string"},
                        "data": {"type": "object"}
                    },
                    "required": ["message"]
                }
            }