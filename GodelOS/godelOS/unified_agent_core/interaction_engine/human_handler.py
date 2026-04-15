"""
Human Interaction Handler Implementation for GodelOS

This module implements the HumanHandler class, which is responsible for
handling interactions with human users, including natural language understanding,
intent recognition, and response generation.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import re

from godelOS.unified_agent_core.interaction_engine.interfaces import (
    Interaction, Response, InteractionType, InteractionStatus,
    HumanHandlerInterface
)

logger = logging.getLogger(__name__)


class HumanHandler(HumanHandlerInterface):
    """
    HumanHandler implementation for GodelOS.
    
    The HumanHandler is responsible for handling interactions with human users,
    including natural language understanding, intent recognition, and response
    generation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the human handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize conversation context
        self.conversation_contexts: Dict[str, Dict[str, Any]] = {}
        
        # Initialize personality settings
        self.personality = self.config.get("personality", {
            "tone": "professional",
            "verbosity": "moderate",
            "formality": "moderate"
        })
        
        # Initialize intent recognition patterns
        self.intent_patterns = {
            "query": re.compile(r"^(what|how|why|when|where|who|can you|could you tell me|do you know|explain)", re.IGNORECASE),
            "command": re.compile(r"^(do|create|make|build|generate|find|search|execute|run|stop|start)", re.IGNORECASE),
            "clarification": re.compile(r"^(clarify|explain more about|tell me more about|elaborate on|what do you mean by)", re.IGNORECASE),
            "greeting": re.compile(r"^(hello|hi|hey|greetings|good morning|good afternoon|good evening)", re.IGNORECASE),
            "farewell": re.compile(r"^(goodbye|bye|see you|farewell|exit|quit)", re.IGNORECASE)
        }
        
        # Initialize NLU components
        self.knowledge_store = None
        self.cognitive_engine = None
    
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
        Handle a human interaction.
        
        Args:
            interaction: The interaction to handle
            
        Returns:
            The response to the interaction
        """
        logger.info(f"Handling human interaction: {interaction.id}")
        
        try:
            # Get conversation ID from metadata or create new one
            conversation_id = interaction.metadata.get("conversation_id", interaction.id)
            
            # Get or create conversation context
            context = self._get_or_create_context(conversation_id)
            
            # Update context with current interaction
            context["last_interaction"] = interaction
            context["interaction_count"] += 1
            context["last_interaction_time"] = time.time()
            
            # Extract text from interaction content
            text = interaction.content.get("text", "")
            
            # Recognize intent
            intent, confidence = self._recognize_intent(text)
            context["current_intent"] = intent
            context["intent_confidence"] = confidence
            
            # Store intent in interaction metadata
            interaction.metadata["recognized_intent"] = intent
            interaction.metadata["intent_confidence"] = confidence
            
            # Generate response based on intent
            response_content = await self._generate_response(text, intent, context)
            
            # Create response object
            response = Response(
                interaction_id=interaction.id,
                content={
                    "text": response_content["text"],
                    "intent": intent,
                    "explanations": response_content.get("explanations", [])
                },
                metadata={
                    "conversation_id": conversation_id,
                    "processing_time": time.time() - interaction.created_at,
                    "personality": self.personality
                }
            )
            
            # Update context with response
            context["last_response"] = response
            context["last_response_time"] = time.time()
            
            return response
        except Exception as e:
            logger.error(f"Error handling human interaction {interaction.id}: {e}")
            
            # Create error response
            return Response(
                interaction_id=interaction.id,
                content={
                    "text": f"I'm sorry, but I encountered an error while processing your request: {str(e)}",
                    "error": str(e)
                },
                metadata={
                    "error": True,
                    "error_message": str(e)
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
        # Check if interaction type is HUMAN
        if interaction.type != InteractionType.HUMAN:
            return False
        
        # Check if interaction content has text
        if "text" not in interaction.content:
            return False
        
        return True
    
    async def validate(self, interaction: Interaction) -> bool:
        """
        Validate a human interaction before handling.
        
        Args:
            interaction: The interaction to validate
            
        Returns:
            True if the interaction is valid, False otherwise
        """
        # Check if interaction type is HUMAN
        if interaction.type != InteractionType.HUMAN:
            return False
        
        # Check if interaction content has text
        if "text" not in interaction.content:
            return False
        
        # Check if text is empty
        text = interaction.content.get("text", "")
        if not text.strip():
            return False
        
        return True
    
    async def format_response_for_human(self, response: Response) -> str:
        """
        Format a response for human consumption.
        
        Args:
            response: The response to format
            
        Returns:
            The formatted response as a string
        """
        # Get text from response content
        text = response.content.get("text", "")
        
        # Get explanations if available
        explanations = response.content.get("explanations", [])
        
        # Format response based on personality
        formatted_text = self._apply_personality_to_text(text)
        
        # Add explanations if available
        if explanations and self.personality.get("verbosity", "moderate") != "minimal":
            formatted_text += "\n\n"
            formatted_text += "Additional information:\n"
            for i, explanation in enumerate(explanations, 1):
                formatted_text += f"{i}. {explanation}\n"
        
        return formatted_text
    
    async def parse_human_input(self, input_str: str) -> Interaction:
        """
        Parse human input into an interaction.
        
        Args:
            input_str: The human input string
            
        Returns:
            The parsed interaction
        """
        # Create interaction object
        interaction = Interaction(
            type=InteractionType.HUMAN,
            content={
                "text": input_str
            },
            metadata={
                "source": "human_input",
                "parsed_at": time.time()
            }
        )
        
        return interaction
    
    def _get_or_create_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get or create a conversation context.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            The conversation context
        """
        if conversation_id not in self.conversation_contexts:
            # Create new context
            self.conversation_contexts[conversation_id] = {
                "conversation_id": conversation_id,
                "created_at": time.time(),
                "interaction_count": 0,
                "last_interaction": None,
                "last_response": None,
                "last_interaction_time": None,
                "last_response_time": None,
                "current_intent": None,
                "intent_confidence": 0.0,
                "topics": [],
                "entities": [],
                "sentiment": "neutral"
            }
        
        return self.conversation_contexts[conversation_id]
    
    def _recognize_intent(self, text: str) -> Tuple[str, float]:
        """
        Recognize the intent of a text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (intent, confidence)
        """
        # Check against intent patterns
        for intent, pattern in self.intent_patterns.items():
            if pattern.search(text):
                return intent, 0.8
        
        # Default to query with low confidence
        return "query", 0.3
    
    async def _generate_response(self, text: str, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response based on text, intent, and context.
        
        Args:
            text: The input text
            intent: The recognized intent
            context: The conversation context
            
        Returns:
            Response content dictionary
        """
        # If cognitive engine is available, use it to generate response
        if self.cognitive_engine:
            try:
                # Create thought request
                thought_request = {
                    "type": "human_interaction",
                    "content": {
                        "text": text,
                        "intent": intent,
                        "context": context
                    }
                }
                
                # Process thought
                thought_result = await self.cognitive_engine.process_thought(thought_request)
                
                # Extract response from thought result
                return {
                    "text": thought_result.get("response", "I'm processing your request."),
                    "explanations": thought_result.get("explanations", [])
                }
            except Exception as e:
                logger.error(f"Error using cognitive engine: {e}")
        
        # Fallback response generation
        if intent == "greeting":
            return {"text": "Hello! How can I assist you today?"}
        elif intent == "farewell":
            return {"text": "Goodbye! Feel free to interact again if you need assistance."}
        elif intent == "query":
            return {"text": "I understand you're asking a question. Let me find the information for you."}
        elif intent == "command":
            return {"text": "I'll process your request right away."}
        elif intent == "clarification":
            return {"text": "Let me provide more information about that."}
        else:
            return {"text": "I'm here to help. Could you provide more details about what you need?"}
    
    def _apply_personality_to_text(self, text: str) -> str:
        """
        Apply personality settings to text.
        
        Args:
            text: The text to modify
            
        Returns:
            The modified text
        """
        tone = self.personality.get("tone", "professional")
        verbosity = self.personality.get("verbosity", "moderate")
        formality = self.personality.get("formality", "moderate")
        
        # Apply tone
        if tone == "friendly":
            text = text.replace("I will", "I'll")
            text = text.replace("I am", "I'm")
        elif tone == "professional":
            text = text.replace("yeah", "yes")
            text = text.replace("nope", "no")
        
        # Apply verbosity
        if verbosity == "minimal" and len(text) > 100:
            sentences = text.split(". ")
            if len(sentences) > 2:
                text = ". ".join(sentences[:2]) + "."
        
        # Apply formality
        if formality == "formal":
            text = text.replace("don't", "do not")
            text = text.replace("can't", "cannot")
        
        return text
    
    async def generate_explanation(self, action: str, decision: Dict[str, Any]) -> str:
        """
        Generate an explanation for a system action or decision.
        
        Args:
            action: The action to explain
            decision: The decision details
            
        Returns:
            The explanation text
        """
        explanation_templates = {
            "query_processing": "I processed your query by {method} and found {result_count} relevant results.",
            "command_execution": "I executed your command using {tool} with parameters {parameters}.",
            "classification": "I classified your input as {category} with {confidence}% confidence.",
            "inference": "Based on {evidence}, I inferred that {conclusion}."
        }
        
        if action in explanation_templates:
            template = explanation_templates[action]
            try:
                return template.format(**decision)
            except KeyError:
                return f"I performed {action} based on your input."
        
        return f"I performed {action} to process your request."