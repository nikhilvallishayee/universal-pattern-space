#!/usr/bin/env python3
"""
Agentic Daemon Management API Endpoints

Provides comprehensive RESTful API for managing the agentic daemon system,
including daemon lifecycle, inter-agent communication, and protocol management.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

from backend.core.agentic_daemon_system import (
    AgenticDaemonSystem, get_agentic_daemon_system, DaemonTask
)
from godelOS.unified_agent_core.interaction_engine.interfaces import (
    Protocol, Interaction, InteractionType, Response
)
from godelOS.unified_agent_core.interaction_engine.agent_handler import AgentHandler
from godelOS.unified_agent_core.interaction_engine.protocol_manager import ProtocolManager

logger = logging.getLogger(__name__)

# ===== API MODELS =====

class DaemonTaskRequest(BaseModel):
    """Request to create a daemon task."""
    type: str = Field(..., description="Type of task")
    description: str = Field(..., description="Task description")
    priority: int = Field(default=5, ge=1, le=10, description="Task priority (1-10)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    scheduled_at: Optional[datetime] = Field(default=None, description="When to schedule the task")

class DaemonConfigRequest(BaseModel):
    """Request to configure a daemon."""
    max_concurrent_tasks: Optional[int] = Field(default=None, ge=1, le=10)
    task_timeout: Optional[int] = Field(default=None, ge=30, le=3600)
    sleep_interval: Optional[int] = Field(default=None, ge=5, le=600)
    enabled: Optional[bool] = Field(default=None)

class AgentRegistrationRequest(BaseModel):
    """Request to register a new agent."""
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    protocols: List[str] = Field(default_factory=list, description="Supported protocols")
    verification_method: str = Field(default="api_key", description="Identity verification method")
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Authentication credentials")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class AgentCommunicationRequest(BaseModel):
    """Request for agent-to-agent communication."""
    target_agent_id: str = Field(..., description="Target agent ID")
    message: str = Field(..., description="Message content")
    message_type: str = Field(default="standard", description="Message type")
    protocol_name: Optional[str] = Field(default=None, description="Preferred protocol")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data")
    timeout: int = Field(default=30, ge=5, le=300, description="Response timeout in seconds")

class ProtocolRegistrationRequest(BaseModel):
    """Request to register a communication protocol."""
    name: str = Field(..., description="Protocol name")
    version: str = Field(..., description="Protocol version")
    interaction_type: str = Field(..., description="Interaction type (AGENT, HUMAN, LOGIC)")
    schema: Dict[str, Any] = Field(..., description="Protocol schema")
    description: Optional[str] = Field(default=None, description="Protocol description")

# ===== DEPENDENCY INJECTION =====

async def get_daemon_system() -> AgenticDaemonSystem:
    """Get the agentic daemon system."""
    return await get_agentic_daemon_system()

def get_agent_handler() -> AgentHandler:
    """Get the agent handler."""
    return AgentHandler()

def get_protocol_manager() -> ProtocolManager:
    """Get the protocol manager."""
    return ProtocolManager()

# ===== API ROUTER =====

router = APIRouter(prefix="/api/v1/agentic", tags=["Agentic Daemon System"])

# ===== DAEMON LIFECYCLE ENDPOINTS =====

@router.get("/daemons/status")
async def get_daemon_system_status(
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Get comprehensive status of the agentic daemon system."""
    try:
        status = await daemon_system.get_system_status()
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting daemon system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daemons/{daemon_name}/status")
async def get_daemon_status(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Get status of a specific daemon."""
    try:
        if daemon_name not in daemon_system.daemons:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        daemon = daemon_system.daemons[daemon_name]
        status = await daemon.get_status()
        
        return {
            "success": True,
            "daemon_name": daemon_name,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daemon status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daemons/{daemon_name}/start")
async def start_daemon(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Start a specific daemon."""
    try:
        if daemon_name not in daemon_system.daemons:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        daemon = daemon_system.daemons[daemon_name]
        success = await daemon.start()
        
        return {
            "success": success,
            "daemon_name": daemon_name,
            "status": "started" if success else "failed",
            "message": f"Daemon {daemon_name} {'started successfully' if success else 'failed to start'}",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting daemon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daemons/{daemon_name}/stop")
async def stop_daemon(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Stop a specific daemon."""
    try:
        if daemon_name not in daemon_system.daemons:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        daemon = daemon_system.daemons[daemon_name]
        success = await daemon.stop()
        
        return {
            "success": success,
            "daemon_name": daemon_name,
            "status": "stopped" if success else "failed",
            "message": f"Daemon {daemon_name} {'stopped successfully' if success else 'failed to stop'}",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping daemon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daemons/{daemon_name}/enable")
async def enable_daemon(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Enable a specific daemon."""
    try:
        success = daemon_system.enable_daemon(daemon_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        return {
            "success": True,
            "daemon_name": daemon_name,
            "status": "enabled",
            "message": f"Daemon {daemon_name} enabled successfully",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling daemon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daemons/{daemon_name}/disable")
async def disable_daemon(
    daemon_name: str,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Disable a specific daemon."""
    try:
        success = daemon_system.disable_daemon(daemon_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        return {
            "success": True,
            "daemon_name": daemon_name,
            "status": "disabled",
            "message": f"Daemon {daemon_name} disabled successfully",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling daemon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daemons/{daemon_name}/configure")
async def configure_daemon(
    daemon_name: str,
    config: DaemonConfigRequest,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Configure a specific daemon."""
    try:
        if daemon_name not in daemon_system.daemons:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        daemon = daemon_system.daemons[daemon_name]
        
        # Apply configuration changes
        if config.max_concurrent_tasks is not None:
            daemon.max_concurrent_tasks = config.max_concurrent_tasks
        if config.task_timeout is not None:
            daemon.task_timeout = config.task_timeout
        if config.sleep_interval is not None:
            daemon.sleep_interval = config.sleep_interval
        if config.enabled is not None:
            daemon.enabled = config.enabled
        
        return {
            "success": True,
            "daemon_name": daemon_name,
            "configuration": {
                "max_concurrent_tasks": daemon.max_concurrent_tasks,
                "task_timeout": daemon.task_timeout,
                "sleep_interval": daemon.sleep_interval,
                "enabled": daemon.enabled
            },
            "message": f"Daemon {daemon_name} configured successfully",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring daemon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== TASK MANAGEMENT ENDPOINTS =====

@router.post("/daemons/{daemon_name}/tasks/add")
async def add_daemon_task(
    daemon_name: str,
    task_request: DaemonTaskRequest,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Add a task to a specific daemon."""
    try:
        if daemon_name not in daemon_system.daemons:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        daemon = daemon_system.daemons[daemon_name]
        
        # Create task
        task = DaemonTask(
            type=task_request.type,
            description=task_request.description,
            priority=task_request.priority,
            parameters=task_request.parameters,
            scheduled_at=task_request.scheduled_at
        )
        
        success = await daemon.add_task(task)
        
        return {
            "success": success,
            "daemon_name": daemon_name,
            "task_id": task.id,
            "task": {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "priority": task.priority,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None
            },
            "message": f"Task added to daemon {daemon_name}",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding daemon task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daemons/{daemon_name}/tasks")
async def get_daemon_tasks(
    daemon_name: str,
    status: Optional[str] = None,
    limit: int = 20,
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Get tasks for a specific daemon."""
    try:
        if daemon_name not in daemon_system.daemons:
            raise HTTPException(status_code=404, detail=f"Daemon not found: {daemon_name}")
        
        daemon = daemon_system.daemons[daemon_name]
        
        # Get completed tasks
        tasks = []
        for task_id, task in daemon.completed_tasks.items():
            if status is None or task.status == status:
                tasks.append({
                    "id": task.id,
                    "type": task.type,
                    "description": task.description,
                    "priority": task.priority,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "error": task.error
                })
        
        # Add current task if it matches filter
        if daemon.current_task:
            task = daemon.current_task
            if status is None or task.status == status:
                tasks.append({
                    "id": task.id,
                    "type": task.type,
                    "description": task.description,
                    "priority": task.priority,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "error": task.error
                })
        
        # Sort by created_at and limit
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        tasks = tasks[:limit]
        
        return {
            "success": True,
            "daemon_name": daemon_name,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "filter": {"status": status} if status else None,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daemon tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/daemons/trigger/{process_type}")
async def trigger_daemon_process(
    process_type: str,
    parameters: Dict[str, Any] = Body(default={}),
    priority: int = Body(default=5, ge=1, le=10),
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Trigger a specific daemon process type."""
    try:
        # Map process types to daemon names
        daemon_map = {
            "knowledge_gap_analysis": "knowledge_gap_detector",
            "autonomous_research": "autonomous_researcher",
            "system_optimization": "system_optimizer",
            "pattern_recognition": "pattern_recognizer",
            "continuous_learning": "continuous_learner",
            "metacognitive_monitoring": "metacognitive_monitor"
        }
        
        daemon_name = daemon_map.get(process_type)
        if not daemon_name:
            raise HTTPException(status_code=400, detail=f"Unknown process type: {process_type}")
        
        success = await daemon_system.trigger_daemon(
            daemon_name=daemon_name,
            task_type=process_type,
            parameters=parameters
        )
        
        return {
            "success": success,
            "process_type": process_type,
            "daemon_name": daemon_name,
            "parameters": parameters,
            "priority": priority,
            "status": "triggered" if success else "failed",
            "message": f"Process {process_type} {'triggered successfully' if success else 'failed to trigger'}",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering daemon process: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== AGENT MANAGEMENT ENDPOINTS =====

@router.post("/agents/register")
async def register_agent(
    request: AgentRegistrationRequest,
    agent_handler: AgentHandler = Depends(get_agent_handler)
):
    """Register a new agent in the system."""
    try:
        # Register agent in the agent handler
        agent_handler.agent_registry[request.agent_id] = {
            "name": request.name,
            "capabilities": request.capabilities,
            "protocols": request.protocols,
            "verification_method": request.verification_method,
            **request.credentials,
            "metadata": request.metadata,
            "registered_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "agent_id": request.agent_id,
            "name": request.name,
            "capabilities": request.capabilities,
            "protocols": request.protocols,
            "message": f"Agent {request.agent_id} registered successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_agents(
    agent_handler: AgentHandler = Depends(get_agent_handler)
):
    """List all registered agents."""
    try:
        agents = []
        for agent_id, agent_info in agent_handler.agent_registry.items():
            agents.append({
                "agent_id": agent_id,
                "name": agent_info.get("name", "Unknown"),
                "capabilities": agent_info.get("capabilities", []),
                "protocols": agent_info.get("protocols", []),
                "registered_at": agent_info.get("registered_at")
            })
        
        return {
            "success": True,
            "agents": agents,
            "total_agents": len(agents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/agents/{agent_id}")
async def unregister_agent(
    agent_id: str,
    agent_handler: AgentHandler = Depends(get_agent_handler)
):
    """Unregister an agent from the system."""
    try:
        if agent_id not in agent_handler.agent_registry:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        del agent_handler.agent_registry[agent_id]
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent_id} unregistered successfully",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== INTER-AGENT COMMUNICATION ENDPOINTS =====

@router.post("/agents/{agent_id}/communicate")
async def agent_communicate(
    agent_id: str,
    request: AgentCommunicationRequest,
    agent_handler: AgentHandler = Depends(get_agent_handler)
):
    """Send a message from one agent to another."""
    try:
        # Verify source agent exists
        if agent_id not in agent_handler.agent_registry:
            raise HTTPException(status_code=404, detail=f"Source agent not found: {agent_id}")
        
        # Verify target agent exists
        if request.target_agent_id not in agent_handler.agent_registry:
            raise HTTPException(status_code=404, detail=f"Target agent not found: {request.target_agent_id}")
        
        # Create interaction
        interaction = Interaction(
            type=InteractionType.AGENT,
            content={
                "agent_id": agent_id,
                "target_agent_id": request.target_agent_id,
                "message": request.message,
                "message_type": request.message_type,
                "protocol_name": request.protocol_name,
                "data": request.data
            }
        )
        
        # Process interaction
        response = await asyncio.wait_for(
            agent_handler.handle(interaction),
            timeout=request.timeout
        )
        
        return {
            "success": True,
            "source_agent_id": agent_id,
            "target_agent_id": request.target_agent_id,
            "interaction_id": interaction.id,
            "response": {
                "content": response.content,
                "status": response.status.value if response.status else "unknown",
                "timestamp": response.timestamp.isoformat() if response.timestamp else None
            },
            "message": "Communication completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail=f"Communication timeout after {request.timeout} seconds")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent communication: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agents/{agent_id}/negotiate-protocol")
async def negotiate_protocol(
    agent_id: str,
    target_agent_id: str = Body(...),
    protocol_candidates: List[str] = Body(...),
    agent_handler: AgentHandler = Depends(get_agent_handler)
):
    """Negotiate a communication protocol between two agents."""
    try:
        # Verify both agents exist
        if agent_id not in agent_handler.agent_registry:
            raise HTTPException(status_code=404, detail=f"Source agent not found: {agent_id}")
        if target_agent_id not in agent_handler.agent_registry:
            raise HTTPException(status_code=404, detail=f"Target agent not found: {target_agent_id}")
        
        # Negotiate protocol
        protocol = await agent_handler.negotiate_protocol(target_agent_id, protocol_candidates)
        
        if not protocol:
            return {
                "success": False,
                "source_agent_id": agent_id,
                "target_agent_id": target_agent_id,
                "protocol_candidates": protocol_candidates,
                "message": "Failed to negotiate protocol",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "source_agent_id": agent_id,
            "target_agent_id": target_agent_id,
            "negotiated_protocol": {
                "name": protocol.name,
                "version": protocol.version,
                "interaction_type": protocol.interaction_type.value
            },
            "message": "Protocol negotiated successfully",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error negotiating protocol: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== PROTOCOL MANAGEMENT ENDPOINTS =====

@router.post("/protocols/register")
async def register_protocol(
    request: ProtocolRegistrationRequest,
    protocol_manager: ProtocolManager = Depends(get_protocol_manager)
):
    """Register a new communication protocol."""
    try:
        # Create protocol object
        protocol = Protocol(
            name=request.name,
            version=request.version,
            interaction_type=InteractionType(request.interaction_type),
            schema=request.schema,
            description=request.description
        )
        
        # Register protocol
        success = await protocol_manager.register_protocol(protocol)
        
        return {
            "success": success,
            "protocol": {
                "name": protocol.name,
                "version": protocol.version,
                "interaction_type": protocol.interaction_type.value,
                "description": protocol.description
            },
            "message": f"Protocol {request.name} v{request.version} {'registered successfully' if success else 'failed to register'}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error registering protocol: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocols")
async def list_protocols(
    protocol_manager: ProtocolManager = Depends(get_protocol_manager)
):
    """List all registered protocols."""
    try:
        protocols = await protocol_manager.list_protocols()
        
        return {
            "success": True,
            "protocols": protocols,
            "total_protocols": len(protocols),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing protocols: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocols/{protocol_name}/schema")
async def get_protocol_schema(
    protocol_name: str,
    version: Optional[str] = None,
    protocol_manager: ProtocolManager = Depends(get_protocol_manager)
):
    """Get the schema for a specific protocol."""
    try:
        schema = await protocol_manager.get_protocol_schema(protocol_name, version)
        
        if not schema:
            raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_name}")
        
        return {
            "success": True,
            "protocol_name": protocol_name,
            "version": version,
            "schema": schema,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting protocol schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/protocols/{protocol_name}/compatibility")
async def check_protocol_compatibility(
    protocol_name: str,
    version1: str = Body(...),
    version2: str = Body(...),
    protocol_manager: ProtocolManager = Depends(get_protocol_manager)
):
    """Check compatibility between two protocol versions."""
    try:
        compatibility = await protocol_manager.check_protocol_compatibility(
            protocol_name, version1, version2
        )
        
        return {
            "success": True,
            "protocol_name": protocol_name,
            "version1": version1,
            "version2": version2,
            "compatibility": compatibility,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking protocol compatibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== SYSTEM MANAGEMENT ENDPOINTS =====

@router.post("/system/start")
async def start_daemon_system(
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Start the entire agentic daemon system."""
    try:
        results = await daemon_system.start_all()
        
        successful_starts = sum(1 for success in results.values() if success)
        total_daemons = len(results)
        
        return {
            "success": successful_starts == total_daemons,
            "results": results,
            "successful_starts": successful_starts,
            "total_daemons": total_daemons,
            "message": f"Started {successful_starts}/{total_daemons} daemons successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting daemon system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/stop")
async def stop_daemon_system(
    daemon_system: AgenticDaemonSystem = Depends(get_daemon_system)
):
    """Stop the entire agentic daemon system."""
    try:
        results = await daemon_system.stop_all()
        
        successful_stops = sum(1 for success in results.values() if success)
        total_daemons = len(results)
        
        return {
            "success": successful_stops == total_daemons,
            "results": results,
            "successful_stops": successful_stops,
            "total_daemons": total_daemons,
            "message": f"Stopped {successful_stops}/{total_daemons} daemons successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping daemon system: {e}")
        raise HTTPException(status_code=500, detail=str(e))
