"""
Interaction Engine Implementation for GodelOS

This module implements the InteractionEngine class, which is responsible for
processing interactions from various sources (human, agent, logic) and generating
appropriate responses.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Type, Callable
import asyncio

from godelOS.unified_agent_core.interaction_engine.interfaces import (
    Interaction, Response, InteractionType, InteractionStatus,
    InteractionHandlerInterface, HumanHandlerInterface, AgentHandlerInterface,
    LogicHandlerInterface, AbstractInteractionEngine
)
from godelOS.unified_agent_core.interaction_engine.protocol_manager import (
    ProtocolManager, ValidationError
)

logger = logging.getLogger(__name__)


class InteractionEngine(AbstractInteractionEngine):
    """
    InteractionEngine implementation for GodelOS.
    
    The InteractionEngine is responsible for processing interactions from various
    sources (human, agent, logic) and generating appropriate responses.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the interaction engine.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        
        self.config = config or {}
        
        # Initialize protocol manager with config
        self.protocol_manager = ProtocolManager(config.get("protocol_manager", {}))
        
        # Initialize handlers
        self.human_handler = None
        self.agent_handler = None
        self.logic_handler = None
        
        # Initialize interaction history
        self.interaction_history: Dict[str, Interaction] = {}
        self.response_history: Dict[str, Response] = {}
        
        # Initialize interaction contexts
        self.interaction_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Initialize processing queue with priority support
        self.interaction_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Initialize processing task
        self.interaction_processor_task = None
        
        # Initialize handler registry
        self.handler_registry: Dict[InteractionType, List[InteractionHandlerInterface]] = {
            InteractionType.HUMAN: [],
            InteractionType.AGENT: [],
            InteractionType.LOGIC: [],
            InteractionType.SYSTEM: []
        }
        
        # Initialize callback registry
        self.callback_registry: Dict[str, List[Callable[[Response], None]]] = {}
        
        # Initialize cognitive engine reference
        self.cognitive_engine = None
    
    async def initialize(self) -> bool:
        """
        Initialize the interaction engine.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("InteractionEngine is already initialized")
            return True
        
        try:
            logger.info("Initializing InteractionEngine")
            
            # Ensure components are set up
            if not all([
                self.protocol_manager,
                self.state,
                self.knowledge_store,
                self.resource_manager
            ]):
                logger.error("InteractionEngine components not properly set up")
                return False
            
            # Register default protocols
            await self._register_default_protocols()
            
            self.is_initialized = True
            logger.info("InteractionEngine initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing InteractionEngine: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the interaction engine.
        
        Returns:
            True if the engine was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("InteractionEngine is already running")
            return True
        
        try:
            logger.info("Starting InteractionEngine")
            
            # Start background processing task
            self.interaction_processor_task = asyncio.create_task(self._interaction_processor())
            
            self.is_running = True
            logger.info("InteractionEngine started successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error starting InteractionEngine: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the interaction engine.
        
        Returns:
            True if the engine was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("InteractionEngine is not running")
            return True
        
        try:
            logger.info("Stopping InteractionEngine")
            
            # Cancel background processing task
            if self.interaction_processor_task:
                self.interaction_processor_task.cancel()
                try:
                    await self.interaction_processor_task
                except asyncio.CancelledError:
                    pass
                self.interaction_processor_task = None
            
            self.is_running = False
            logger.info("InteractionEngine stopped successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping InteractionEngine: {e}")
            return False
    
    def set_cognitive_engine(self, cognitive_engine: Any) -> None:
        """
        Set the cognitive engine reference.
        
        Args:
            cognitive_engine: The cognitive engine
        """
        self.cognitive_engine = cognitive_engine
        
        # Pass cognitive engine to handlers if they support it
        if hasattr(self.human_handler, "set_cognitive_engine") and callable(getattr(self.human_handler, "set_cognitive_engine")):
            self.human_handler.set_cognitive_engine(cognitive_engine)
        
        if hasattr(self.agent_handler, "set_cognitive_engine") and callable(getattr(self.agent_handler, "set_cognitive_engine")):
            self.agent_handler.set_cognitive_engine(cognitive_engine)
        
        if hasattr(self.logic_handler, "set_cognitive_engine") and callable(getattr(self.logic_handler, "set_cognitive_engine")):
            self.logic_handler.set_cognitive_engine(cognitive_engine)
    
    async def process_interaction(self, interaction_data: Dict[str, Any], resources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an interaction.
        
        Args:
            interaction_data: The interaction data
            resources: The resources allocated for processing
            
        Returns:
            The response to the interaction
        """
        if not self.is_running:
            raise RuntimeError("InteractionEngine is not running")
        
        logger.debug(f"Processing interaction: {interaction_data}")
        
        try:
            # Create interaction object
            interaction = self._create_interaction_from_data(interaction_data)
            
            # Store in history
            self.interaction_history[interaction.id] = interaction
            
            # Create or update interaction context
            context_id = interaction_data.get("context_id", interaction.id)
            self._create_or_update_interaction_context(context_id, interaction)
            
            # Update state
            if self.state:
                self.state.update_interaction_context({
                    "current_interaction_id": interaction.id,
                    "current_context_id": context_id,
                    "interaction_history": list(self.interaction_history.keys())[-100:]  # Keep last 100
                })
            
            # Process the interaction
            try:
                # Validate against protocol
                validated_interaction = await self.protocol_manager.validate(interaction)
                
                # Find appropriate handler
                handler = await self._find_handler(validated_interaction)
                
                if not handler:
                    return {
                        "success": False,
                        "error": f"No handler found for interaction type {interaction.type.value}"
                    }
                
                # Update interaction status
                interaction.status = InteractionStatus.PROCESSING
                
                # Check if we should use cognitive engine for complex interactions
                should_use_cognitive = self._should_use_cognitive_engine(validated_interaction, resources)
                
                if should_use_cognitive and self.cognitive_engine:
                    # Process through cognitive engine first
                    thought_request = {
                        "type": "interaction_processing",
                        "content": {
                            "interaction": {
                                "id": validated_interaction.id,
                                "type": validated_interaction.type.value,
                                "content": validated_interaction.content,
                                "metadata": validated_interaction.metadata
                            },
                            "context": self.interaction_contexts.get(context_id, {}),
                            "resources": resources
                        }
                    }
                    
                    thought_result = await self.cognitive_engine.process_thought(thought_request)
                    
                    # Update interaction with cognitive insights
                    if "enhanced_interaction" in thought_result:
                        enhanced_data = thought_result["enhanced_interaction"]
                        
                        # Update content if provided
                        if "content" in enhanced_data:
                            validated_interaction.content.update(enhanced_data["content"])
                        
                        # Update metadata if provided
                        if "metadata" in enhanced_data:
                            validated_interaction.metadata.update(enhanced_data["metadata"])
                    
                    # Store cognitive insights in context
                    if "insights" in thought_result:
                        self._update_interaction_context(context_id, {
                            "cognitive_insights": thought_result["insights"]
                        })
                
                # Handle the interaction
                response = await handler.handle(validated_interaction)
                
                # Store response in history
                self.response_history[response.id] = response
                
                # Update interaction context with response
                self._update_interaction_context(context_id, {
                    "last_response": {
                        "id": response.id,
                        "content": response.content,
                        "created_at": response.created_at
                    }
                })
                
                # Update interaction status
                interaction.status = InteractionStatus.COMPLETED
                interaction.completed_at = time.time()
                
                # Invoke callbacks for this interaction
                await self._invoke_callbacks(interaction.id, response)
                
                return {
                    "success": True,
                    "interaction_id": interaction.id,
                    "response_id": response.id,
                    "content": response.content,
                    "context_id": context_id,
                    "timestamp": response.created_at
                }
            except ValidationError as e:
                # Update interaction status
                interaction.status = InteractionStatus.REJECTED
                
                # Store validation error in context
                self._update_interaction_context(context_id, {
                    "last_error": {
                        "type": "validation_error",
                        "message": str(e),
                        "timestamp": time.time()
                    }
                })
                
                logger.error(f"Validation error for interaction {interaction.id}: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "details": getattr(e, "details", None)
                }
        except Exception as e:
            logger.error(f"Error processing interaction: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def register_handler(self, interaction_type: InteractionType, handler: InteractionHandlerInterface) -> bool:
        """
        Register an interaction handler.
        
        Args:
            interaction_type: The interaction type to register the handler for
            handler: The handler to register
            
        Returns:
            True if the handler was registered successfully, False otherwise
        """
        if interaction_type not in self.handler_registry:
            logger.error(f"Invalid interaction type: {interaction_type}")
            return False
        
        self.handler_registry[interaction_type].append(handler)
        
        # Set specialized handlers if appropriate
        if interaction_type == InteractionType.HUMAN and isinstance(handler, HumanHandlerInterface):
            self.human_handler = handler
        elif interaction_type == InteractionType.AGENT and isinstance(handler, AgentHandlerInterface):
            self.agent_handler = handler
        elif interaction_type == InteractionType.LOGIC and isinstance(handler, LogicHandlerInterface):
            self.logic_handler = handler
        
        logger.info(f"Registered handler for interaction type {interaction_type.value}")
        return True
    
    async def register_callback(self, interaction_id: str, callback: Callable[[Response], None]) -> bool:
        """
        Register a callback for an interaction response.
        
        Args:
            interaction_id: The ID of the interaction
            callback: The callback function to invoke when a response is generated
            
        Returns:
            True if the callback was registered successfully, False otherwise
        """
        if interaction_id not in self.callback_registry:
            self.callback_registry[interaction_id] = []
        
        self.callback_registry[interaction_id].append(callback)
        return True
    
    async def get_interaction_history(self, max_count: int = 100) -> List[Dict[str, Any]]:
        """
        Get the interaction history.
        
        Args:
            max_count: Maximum number of interactions to return
            
        Returns:
            List of interactions with their responses
        """
        # Get the most recent interactions
        recent_interactions = list(self.interaction_history.values())
        recent_interactions.sort(key=lambda i: i.created_at, reverse=True)
        recent_interactions = recent_interactions[:max_count]
        
        # Build history with responses
        history = []
        for interaction in recent_interactions:
            history_item = {
                "interaction_id": interaction.id,
                "interaction_type": interaction.type.value,
                "interaction_content": interaction.content,
                "interaction_status": interaction.status.value,
                "created_at": interaction.created_at,
                "completed_at": interaction.completed_at,
                "responses": []
            }
            
            # Find responses for this interaction
            for response in self.response_history.values():
                if response.interaction_id == interaction.id:
                    history_item["responses"].append({
                        "response_id": response.id,
                        "response_content": response.content,
                        "created_at": response.created_at
                    })
            
            history.append(history_item)
        
        return history
    
    async def enqueue_interaction(
        self, interaction_data: Dict[str, Any], priority: int = 5
    ) -> asyncio.Future:
        """
        Enqueue an interaction for processing.
        
        Args:
            interaction_data: The interaction data
            priority: Priority level (1-10, lower is higher priority)
            
        Returns:
            Future that will contain the processing result
        """
        # Create future for result
        future = asyncio.Future()
        
        # Create interaction object
        interaction = self._create_interaction_from_data(interaction_data)
        
        # Add to queue with priority
        await self.interaction_queue.put((priority, interaction, future))
        
        return future
    
    async def get_interaction_context(self, context_id: str) -> Dict[str, Any]:
        """
        Get interaction context.
        
        Args:
            context_id: The context ID
            
        Returns:
            The interaction context
        """
        return self.interaction_contexts.get(context_id, {})
    
    async def _interaction_processor(self) -> None:
        """Background task for processing interactions."""
        logger.info("Starting interaction processor task")
        
        try:
            while True:
                # Get next interaction from queue
                priority, interaction, future = await self.interaction_queue.get()
                
                try:
                    # Process the interaction
                    result = await self.process_interaction(
                        {
                            "id": interaction.id,
                            "type": interaction.type.value,
                            "content": interaction.content,
                            "metadata": interaction.metadata
                        },
                        {"priority": priority}
                    )
                    
                    # Set result in future
                    future.set_result(result)
                except Exception as e:
                    logger.error(f"Error in interaction processor: {e}")
                    future.set_exception(e)
                finally:
                    # Mark task as done
                    self.interaction_queue.task_done()
        except asyncio.CancelledError:
            logger.info("Interaction processor task cancelled")
        except Exception as e:
            logger.error(f"Unexpected error in interaction processor: {e}")
    
    async def _find_handler(self, interaction: Interaction) -> Optional[InteractionHandlerInterface]:
        """
        Find an appropriate handler for an interaction.
        
        Args:
            interaction: The interaction to find a handler for
            
        Returns:
            The handler, or None if no appropriate handler is found
        """
        # Get handlers for this interaction type
        handlers = self.handler_registry.get(interaction.type, [])
        
        # Find a handler that can handle this interaction
        for handler in handlers:
            if await handler.can_handle(interaction):
                return handler
        
        # If no specific handler found, use the default for this type
        if interaction.type == InteractionType.HUMAN and self.human_handler:
            return self.human_handler
        elif interaction.type == InteractionType.AGENT and self.agent_handler:
            return self.agent_handler
        elif interaction.type == InteractionType.LOGIC and self.logic_handler:
            return self.logic_handler
        
        return None
    
    async def _invoke_callbacks(self, interaction_id: str, response: Response) -> None:
        """
        Invoke callbacks for an interaction response.
        
        Args:
            interaction_id: The ID of the interaction
            response: The response to the interaction
        """
        callbacks = self.callback_registry.get(interaction_id, [])
        
        for callback in callbacks:
            try:
                callback(response)
            except Exception as e:
                logger.error(f"Error in callback for interaction {interaction_id}: {e}")
        
        # Remove callbacks after invocation
        if interaction_id in self.callback_registry:
            del self.callback_registry[interaction_id]
    
    def _create_interaction_from_data(self, interaction_data: Dict[str, Any]) -> Interaction:
        """
        Create an Interaction object from interaction data.
        
        Args:
            interaction_data: The interaction data
            
        Returns:
            The created Interaction object
        """
        # Get interaction ID or generate a new one
        interaction_id = interaction_data.get("id", str(uuid.uuid4()))
        
        # Get interaction type
        interaction_type_str = interaction_data.get("type", "human")
        try:
            interaction_type = InteractionType(interaction_type_str)
        except ValueError:
            logger.warning(f"Invalid interaction type: {interaction_type_str}, defaulting to HUMAN")
            interaction_type = InteractionType.HUMAN
        
        # Create interaction
        return Interaction(
            id=interaction_id,
            type=interaction_type,
            content=interaction_data.get("content", {}),
            status=InteractionStatus.PENDING,
            metadata=interaction_data.get("metadata", {})
        )
    
    def _create_or_update_interaction_context(self, context_id: str, interaction: Interaction) -> None:
        """
        Create or update an interaction context.
        
        Args:
            context_id: The context ID
            interaction: The current interaction
        """
        if context_id not in self.interaction_contexts:
            # Create new context
            self.interaction_contexts[context_id] = {
                "context_id": context_id,
                "created_at": time.time(),
                "interaction_count": 0,
                "interactions": [],
                "metadata": {}
            }
        
        # Update context
        context = self.interaction_contexts[context_id]
        context["interaction_count"] += 1
        context["last_interaction"] = {
            "id": interaction.id,
            "type": interaction.type.value,
            "content": interaction.content,
            "created_at": interaction.created_at
        }
        
        # Add to interactions list (limited to last 10)
        context["interactions"].append(context["last_interaction"])
        if len(context["interactions"]) > 10:
            context["interactions"] = context["interactions"][-10:]
        
        # Update last activity timestamp
        context["last_activity"] = time.time()
    
    def _update_interaction_context(self, context_id: str, updates: Dict[str, Any]) -> None:
        """
        Update an interaction context with new data.
        
        Args:
            context_id: The context ID
            updates: The updates to apply
        """
        if context_id not in self.interaction_contexts:
            # Create new context if it doesn't exist
            self.interaction_contexts[context_id] = {
                "context_id": context_id,
                "created_at": time.time(),
                "interaction_count": 0,
                "interactions": [],
                "metadata": {}
            }
        
        # Apply updates
        context = self.interaction_contexts[context_id]
        for key, value in updates.items():
            context[key] = value
        
        # Update last activity timestamp
        context["last_activity"] = time.time()
    
    def _should_use_cognitive_engine(self, interaction: Interaction, resources: Dict[str, Any]) -> bool:
        """
        Determine if cognitive engine should be used for this interaction.
        
        Args:
            interaction: The interaction
            resources: Resource information
            
        Returns:
            True if cognitive engine should be used, False otherwise
        """
        # Check if cognitive engine is available
        if not self.cognitive_engine:
            return False
        
        # Check if interaction is marked as complex
        if interaction.metadata.get("complex", False):
            return True
        
        # Check interaction content size
        content_complexity = self._estimate_content_complexity(interaction.content)
        if content_complexity > 0.7:  # Threshold for "complex" content
            return True
        
        # Check if interaction type is LOGIC (always use cognitive engine)
        if interaction.type == InteractionType.LOGIC:
            return True
        
        # Check if sufficient resources are available
        priority = resources.get("priority", 5)
        if priority <= 3:  # High priority interactions get cognitive processing
            return True
        
        return False
    
    def _estimate_content_complexity(self, content: Dict[str, Any]) -> float:
        """
        Estimate the complexity of interaction content.
        
        Args:
            content: The interaction content
            
        Returns:
            Complexity score (0.0-1.0)
        """
        # Simple heuristic for content complexity
        if not content:
            return 0.0
        
        complexity = 0.0
        
        # Check content size
        json_size = len(json.dumps(content))
        if json_size > 1000:
            complexity += 0.3
        elif json_size > 500:
            complexity += 0.2
        elif json_size > 200:
            complexity += 0.1
        
        # Check content depth
        max_depth = self._get_dict_depth(content)
        if max_depth > 3:
            complexity += 0.3
        elif max_depth > 2:
            complexity += 0.2
        elif max_depth > 1:
            complexity += 0.1
        
        # Check number of fields
        num_fields = self._count_dict_fields(content)
        if num_fields > 10:
            complexity += 0.3
        elif num_fields > 5:
            complexity += 0.2
        elif num_fields > 3:
            complexity += 0.1
        
        return min(complexity, 1.0)
    
    def _get_dict_depth(self, d: Dict[str, Any], current_depth: int = 1) -> int:
        """
        Get the maximum depth of a nested dictionary.
        
        Args:
            d: The dictionary
            current_depth: The current depth
            
        Returns:
            The maximum depth
        """
        if not isinstance(d, dict) or not d:
            return current_depth
        
        return max(self._get_dict_depth(v, current_depth + 1) if isinstance(v, dict) else current_depth
                  for k, v in d.items())
    
    def _count_dict_fields(self, d: Dict[str, Any]) -> int:
        """
        Count the total number of fields in a dictionary, including nested fields.
        
        Args:
            d: The dictionary
            
        Returns:
            The total number of fields
        """
        if not isinstance(d, dict):
            return 0
        
        count = len(d)
        for k, v in d.items():
            if isinstance(v, dict):
                count += self._count_dict_fields(v)
        
        return count
    
    async def _register_default_protocols(self) -> None:
        """Register default protocols for different interaction types."""
        # Human interaction protocol
        human_protocol = Protocol(
            name="human_interaction",
            version="1.0",
            interaction_type=InteractionType.HUMAN,
            schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "context": {"type": "object"}
                },
                "required": ["text"]
            }
        )
        
        # Agent interaction protocol
        agent_protocol = Protocol(
            name="agent_interaction",
            version="1.0",
            interaction_type=InteractionType.AGENT,
            schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "agent_id": {"type": "string"},
                    "credentials": {"type": "object"},
                    "metadata": {"type": "object"}
                },
                "required": ["message", "agent_id"]
            }
        )
        
        # Logic interaction protocol
        logic_protocol = Protocol(
            name="logic_interaction",
            version="1.0",
            interaction_type=InteractionType.LOGIC,
            schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {"type": "object"},
                    "parameters": {"type": "object"}
                },
                "required": ["query"]
            }
        )
        
        # Register protocols
        await self.protocol_manager.register_protocol(human_protocol)
        await self.protocol_manager.register_protocol(agent_protocol)
        await self.protocol_manager.register_protocol(logic_protocol)