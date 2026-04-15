"""
GodelOS Interaction Engine Package

This package implements the InteractionEngine component of the UnifiedAgentCore
architecture, which is responsible for managing interactions with humans, agents,
and logic systems.

Key components:
- HumanHandler: Manages interactions with humans
- AgentHandler: Manages interactions with other agents
- LogicHandler: Manages interactions with logic systems
- ProtocolManager: Manages communication protocols
"""

from godelOS.unified_agent_core.interaction_engine.interfaces import (
    InteractionEngineInterface,
    InteractionHandlerInterface,
    HumanHandlerInterface,
    AgentHandlerInterface,
    LogicHandlerInterface,
    ProtocolManagerInterface
)