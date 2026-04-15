#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal GödelOS Backend Server
A streamlined version of the backend that provides essential API endpoints
for the frontend without complex dependencies.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the new tool-based LLM integration
try:
    import llm_tool_integration
    from llm_tool_integration import ToolBasedLLMIntegration
    LLM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LLM integration not available: {e}")
    llm_tool_integration = None
    LLM_INTEGRATION_AVAILABLE = False

app = FastAPI(
    title="GödelOS Minimal Cognitive API",
    description="Streamlined cognitive architecture API for essential functionality",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for demonstration
cognitive_state = {
    "attention_focus": {
        "topic": "System Initialization",
        "intensity": 0.75,
        "context": "Cognitive architecture startup",
        "mode": "Active"
    },
    "processing_load": 0.23,
    "working_memory": {
        "items": [
            {"id": 1, "content": "User query processing", "priority": 0.8},
            {"id": 2, "content": "Knowledge retrieval", "priority": 0.6}
        ],
        "capacity": 10,
        "utilization": 0.4
    },
    "system_health": {
        "overall": 0.92,
        "components": {
            "inference_engine": 0.94,
            "knowledge_store": 0.89,
            "attention_manager": 0.95,
            "memory_manager": 0.88
        }
    },
    "active_agents": 3,
    "cognitive_events": []
}

# Request/Response Models
class CognitiveStreamConfig(BaseModel):
    granularity: str = "standard"
    subscriptions: List[str] = []
    max_event_rate: Optional[int] = None

class LLMCognitiveRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    use_tools: bool = True

class LLMCognitiveResponse(BaseModel):
    response: str
    tools_used: List[str]
    confidence: float
    processing_time: float
    cognitive_state_changes: Dict[str, Any]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Utility functions for safe data handling
def safe_percentage(value, fallback=0):
    """Safely convert value to percentage."""
    try:
        if isinstance(value, (int, float)) and not (value != value):  # Check for NaN
            return max(0, min(100, round(value * 100)))
        return fallback
    except:
        return fallback

def safe_number(value, fallback=0):
    """Safely convert value to number."""
    try:
        if isinstance(value, (int, float)) and not (value != value):  # Check for NaN
            return value
        return fallback
    except:
        return fallback

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "name": "GödelOS Minimal Cognitive API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/cognitive/state",
            "/cognitive/query", 
            "/enhanced-cognitive/stream/configure",
            "/llm/cognitive-query",
            "/llm/test-integration",
            "/llm/tools",
            "/ws/unified-cognitive-stream"
        ],
        "new_features": [
            "Tool-based LLM integration",
            "Function calling architecture", 
            "Cognitive grounding verification",
            "Comprehensive tool documentation"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections)
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint with /api prefix."""
    return await health_check()

@app.get("/cognitive/state")
async def get_cognitive_state():
    """Get current cognitive state."""
    # Add some realistic variation
    import random
    cognitive_state["processing_load"] = max(0, min(1, cognitive_state["processing_load"] + random.uniform(-0.1, 0.1)))
    cognitive_state["attention_focus"]["intensity"] = max(0, min(1, cognitive_state["attention_focus"]["intensity"] + random.uniform(-0.05, 0.05)))
    
    return {
        "cognitive_state": cognitive_state,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/cognitive/state")
async def api_get_cognitive_state():
    """API cognitive state endpoint with /api prefix."""
    return await get_cognitive_state()

@app.get("/api/transparency/knowledge-graph/export")
async def export_knowledge_graph():
    """Export knowledge graph data."""
    return {
        "nodes": [
            {"id": 1, "label": "Consciousness", "type": "concept", "properties": {"domain": "philosophy"}},
            {"id": 2, "label": "Cognitive Architecture", "type": "concept", "properties": {"domain": "AI"}},
            {"id": 3, "label": "Meta-cognition", "type": "concept", "properties": {"domain": "psychology"}},
            {"id": 4, "label": "Self-awareness", "type": "concept", "properties": {"domain": "consciousness"}},
        ],
        "edges": [
            {"source": 1, "target": 4, "label": "requires", "weight": 0.8},
            {"source": 2, "target": 3, "label": "implements", "weight": 0.7},
            {"source": 3, "target": 1, "label": "enables", "weight": 0.9},
        ],
        "statistics": {
            "node_count": 4,
            "edge_count": 3,
            "domains": ["philosophy", "AI", "psychology", "consciousness"]
        }
    }

@app.get("/api/enhanced-cognitive/status")
async def enhanced_cognitive_status():
    """Get enhanced cognitive status."""
    return {
        "enabled": True,
        "autonomous_learning": {
            "active": True,
            "plans_count": 0,
            "efficiency": 0.0
        },
        "stream_of_consciousness": {
            "active": True,
            "events_count": 0,
            "clients_connected": len(manager.active_connections)
        },
        "meta_cognitive": {
            "depth": 3,
            "self_reflection_active": True,
            "uncertainty_tracking": True
        }
    }

@app.post("/api/enhanced-cognitive/stream/configure")
async def api_configure_enhanced_cognitive_streaming(config: CognitiveStreamConfig):
    """Configure enhanced cognitive streaming - API version."""
    return await configure_cognitive_streaming(config)

@app.get("/api/enhanced-cognitive/autonomous/gaps")
async def get_knowledge_gaps():
    """Get detected knowledge gaps."""
    return {
        "gaps": [],
        "total_count": 0,
        "high_priority": 0,
        "detection_enabled": True,
        "last_scan": datetime.now().isoformat()
    }

@app.get("/api/enhanced-cognitive/autonomous/plans")
async def get_learning_plans():
    """Get active autonomous learning plans."""
    return {
        "plans": [],
        "active_count": 0,
        "completed_count": 0,
        "success_rate": 0.0
    }

@app.get("/api/enhanced-cognitive/autonomous/history")
async def get_learning_history():
    """Get autonomous learning history."""
    return {
        "history": [],
        "total_acquisitions": 0,
        "average_time": 0,
        "success_rate": 0.0
    }

@app.get("/api/concepts")
async def get_concepts():
    """Get knowledge concepts."""
    return {
        "concepts": [
            {"id": 1, "name": "Consciousness", "domain": "philosophy", "confidence": 0.85},
            {"id": 2, "name": "Cognitive Architecture", "domain": "AI", "confidence": 0.92},
            {"id": 3, "name": "Meta-cognition", "domain": "psychology", "confidence": 0.78},
        ],
        "total": 3,
        "domains": ["philosophy", "AI", "psychology"]
    }

@app.get("/api/knowledge/concepts")
async def get_knowledge_concepts():
    """Get knowledge concepts with knowledge prefix."""
    return await get_concepts()

@app.get("/api/enhanced-cognitive/health")
async def enhanced_cognitive_health():
    """Enhanced cognitive health status."""
    return {
        "status": "healthy",
        "components": {
            "autonomous_learning": "active",
            "stream_of_consciousness": "active",
            "meta_cognitive": "active"
        },
        "performance": {
            "response_time": 0.12,
            "success_rate": 0.95,
            "uptime": "99.9%"
        }
    }

@app.get("/api/enhanced-cognitive/autonomous/status")
async def enhanced_cognitive_autonomous_status():
    """Enhanced cognitive autonomous learning status."""
    return {
        "enabled": True,
        "active_plans": 0,
        "completed_acquisitions": 0,
        "success_rate": 0.0,
        "efficiency": 0.0,
        "knowledge_gaps": {
            "total": 0,
            "high_priority": 0,
            "medium_priority": 0,
            "low_priority": 0
        }
    }

@app.get("/api/enhanced-cognitive/stream/status")
async def enhanced_cognitive_stream_status():
    """Enhanced cognitive stream status."""
    return {
        "enabled": True,
        "active_clients": len(manager.active_connections),
        "events_processed": 0,
        "granularity": "standard",
        "performance": {
            "events_per_second": 0,
            "average_latency": 0.05
        }
    }

@app.post("/enhanced-cognitive/stream/configure")
async def configure_cognitive_streaming(config: CognitiveStreamConfig):
    """Configure cognitive streaming - simplified version."""
    logger.info(f"Configuring cognitive streaming: {config}")
    return {
        "status": "success",
        "message": "Cognitive streaming configured successfully",
        "config": config.dict()
    }

@app.post("/llm/cognitive-query")
async def llm_cognitive_query(request: LLMCognitiveRequest):
    """
    Process queries through the LLM cognitive architecture with comprehensive tool usage.
    This endpoint now uses the new tool-based architecture for grounded responses.
    """
    start_time = datetime.now()
    
    try:
        if LLM_INTEGRATION_AVAILABLE:
            # Initialize tool-based LLM integration
            llm_integration = ToolBasedLLMIntegration()
            
            # Process query with tool-based approach
            result = await llm_integration.process_query(request.query)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Update cognitive state based on tool usage
            cognitive_changes = update_cognitive_state_from_tools(result.get("tool_results", []))
            
            # Broadcast cognitive event to WebSocket clients
            await broadcast_unified_event({
                "type": "llm_query_processed",
                "query": request.query,
                "tools_used": result.get("tools_used", []),
                "processing_time": processing_time,
                "cognitive_grounding": result.get("cognitive_grounding", False),
                "timestamp": datetime.now().isoformat()
            })
            
            return LLMCognitiveResponse(
                response=result.get("response", "Processing failed"),
                tools_used=result.get("tools_used", []),
                confidence=0.9 if result.get("cognitive_grounding", False) else 0.5,
                processing_time=processing_time,
                cognitive_state_changes=cognitive_changes
            )
        else:
            # Fallback to enhanced simulation
            response_text, tools_used = simulate_cognitive_processing(request)
            processing_time = (datetime.now() - start_time).total_seconds()
            cognitive_changes = update_cognitive_state_from_query(request, tools_used)
            
            return LLMCognitiveResponse(
                response=response_text,
                tools_used=tools_used,
                confidence=0.75,
                processing_time=processing_time,
                cognitive_state_changes=cognitive_changes
            )
        
    except Exception as e:
        logger.error(f"Error in LLM cognitive query: {e}")
        # Fallback to simulation on error
        try:
            response_text, tools_used = simulate_cognitive_processing(request)
            processing_time = (datetime.now() - start_time).total_seconds()
            cognitive_changes = update_cognitive_state_from_query(request, tools_used)
            
            return LLMCognitiveResponse(
                response=f"Fallback processing: {response_text}",
                tools_used=tools_used,
                confidence=0.6,
                processing_time=processing_time,
                cognitive_state_changes=cognitive_changes
            )
        except Exception as fallback_error:
            logger.error(f"Fallback processing also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"Cognitive processing failed: {str(e)}")

def update_cognitive_state_from_tools(tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update cognitive state based on actual tool usage results."""
    changes = {}
    
    for tool_result in tool_results:
        tool_name = tool_result.get("tool", "")
        
        # Update attention based on tool usage
        if "attention" in tool_name or "focus" in tool_name:
            if tool_result.get("result", {}).get("success", False):
                result_data = tool_result["result"].get("data", {})
                if isinstance(result_data, dict) and "topic" in result_data:
                    cognitive_state["attention_focus"].update(result_data)
                    changes["attention_focus"] = cognitive_state["attention_focus"]
        
        # Update working memory based on tool usage
        elif "memory" in tool_name:
            if tool_result.get("result", {}).get("success", False):
                result_data = tool_result["result"].get("data", {})
                if isinstance(result_data, dict) and "items" in result_data:
                    cognitive_state["working_memory"].update(result_data)
                    changes["working_memory"] = cognitive_state["working_memory"]
        
        # Update processing load based on tool complexity
        cognitive_state["processing_load"] = min(1.0, cognitive_state["processing_load"] + 0.05)
    
    changes["processing_load"] = cognitive_state["processing_load"]
    changes["last_update"] = datetime.now().isoformat()
    
    return changes

@app.get("/llm/test-integration")
async def test_llm_integration():
    """
    Test the new tool-based LLM integration to verify it's working correctly.
    """
    try:
        if not LLM_INTEGRATION_AVAILABLE:
            return {
                "status": "unavailable",
                "message": "LLM integration not available - missing dependencies",
                "available_tools": [],
                "test_result": None
            }
        
        # Initialize and test the integration
        llm_integration = ToolBasedLLMIntegration()
        test_result = await llm_integration.test_integration()
        
        # Get available tools
        available_tools = list(llm_integration.tool_provider.tools.keys())
        
        return {
            "status": "available",
            "message": "Tool-based LLM integration is operational",
            "available_tools": available_tools,
            "total_tools": len(available_tools),
            "test_result": test_result
        }
        
    except Exception as e:
        logger.error(f"LLM integration test failed: {e}")
        return {
            "status": "error", 
            "message": f"Integration test failed: {str(e)}",
            "available_tools": [],
            "test_result": None
        }

@app.get("/llm/tools")
async def get_available_tools():
    """
    Get comprehensive list of available cognitive tools for LLM integration.
    """
    try:
        if not LLM_INTEGRATION_AVAILABLE:
            return {
                "status": "unavailable",
                "tools": [],
                "message": "LLM integration not available"
            }
        
        tool_provider = GödelOSToolProvider()
        
        # Format tools for documentation
        tools_documentation = {}
        for tool_name, tool_def in tool_provider.tools.items():
            function_def = tool_def["function"]
            tools_documentation[tool_name] = {
                "name": function_def["name"],
                "description": function_def["description"],
                "parameters": function_def.get("parameters", {}),
                "category": _categorize_tool(tool_name)
            }
        
        return {
            "status": "available",
            "tools": tools_documentation,
            "total_tools": len(tools_documentation),
            "categories": {
                "cognitive_state": [t for t, d in tools_documentation.items() if d["category"] == "cognitive_state"],
                "memory": [t for t, d in tools_documentation.items() if d["category"] == "memory"],
                "knowledge": [t for t, d in tools_documentation.items() if d["category"] == "knowledge"],
                "system_health": [t for t, d in tools_documentation.items() if d["category"] == "system_health"],
                "reasoning": [t for t, d in tools_documentation.items() if d["category"] == "reasoning"],
                "meta_cognitive": [t for t, d in tools_documentation.items() if d["category"] == "meta_cognitive"]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get tools documentation: {e}")
        return {
            "status": "error",
            "tools": [],
            "message": f"Failed to get tools: {str(e)}"
        }

def _categorize_tool(tool_name: str) -> str:
    """Categorize tools by functionality."""
    if "cognitive_state" in tool_name or "attention" in tool_name:
        return "cognitive_state"
    elif "memory" in tool_name:
        return "memory"
    elif "knowledge" in tool_name:
        return "knowledge"
    elif "health" in tool_name:
        return "system_health"
    elif "reasoning" in tool_name or "analyze" in tool_name:
        return "reasoning"
    elif "reflect" in tool_name or "assess" in tool_name:
        return "meta_cognitive"
    else:
        return "general"

async def process_with_real_llm(request: LLMCognitiveRequest, api_key: str):
    """Process request with real LLM using tool-calling."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            base_url="https://api.synthetic.new/v1",
            api_key=api_key
        )
        
        # Define cognitive tools available to the LLM
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "access_working_memory",
                    "description": "Access and manipulate working memory contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["read", "write", "update"]},
                            "content": {"type": "string", "description": "Content to store or search for"}
                        },
                        "required": ["operation"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "focus_attention",
                    "description": "Direct attention to specific topics or contexts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string"},
                            "intensity": {"type": "number", "minimum": 0, "maximum": 1},
                            "context": {"type": "string"}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "retrieve_knowledge",
                    "description": "Retrieve relevant knowledge from the knowledge base",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "domain": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "meta_cognitive_reflect",
                    "description": "Engage in meta-cognitive reflection on current thinking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "aspect": {"type": "string", "enum": ["confidence", "approach", "assumptions", "alternatives"]},
                            "depth": {"type": "integer", "minimum": 1, "maximum": 5}
                        },
                        "required": ["aspect"]
                    }
                }
            }
        ]
        
        # Create system prompt that emphasizes tool usage
        system_prompt = """You are the primary cognitive driver for GödelOS, a sophisticated cognitive architecture. 

CRITICAL: You must actively use the provided cognitive tools to process all queries. Do not rely solely on text responses.

Your cognitive tools allow you to:
- access_working_memory: Store and retrieve information during processing
- focus_attention: Direct cognitive resources to specific aspects
- retrieve_knowledge: Access relevant information from the knowledge base  
- meta_cognitive_reflect: Engage in self-reflection on your thinking process

For every query, you MUST:
1. Use focus_attention to direct your cognitive resources
2. Use access_working_memory to store intermediate thoughts
3. Use retrieve_knowledge for relevant information
4. Use meta_cognitive_reflect to evaluate your approach
5. Provide a comprehensive response based on tool usage

Always explain how you used each tool and what cognitive processes you engaged."""
        
        # Make the API call with tools
        response = await client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {request.query}\nContext: {request.context or 'General inquiry'}"}
            ],
            tools=tools,
            tool_choice="auto",
            max_tokens=1000,
            temperature=0.7
        )
        
        # Process the response
        message = response.choices[0].message
        tools_used = []
        
        # Check if tools were called
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                tools_used.append(tool_call.function.name)
                # Here we would actually execute the tool functions
                # For now, we simulate the tool execution
                
        response_text = message.content or "Processing complete - see tool usage for details."
        
        return response_text, tools_used
        
    except Exception as e:
        logger.error(f"Real LLM processing failed: {e}")
        # Fall back to simulation
        return simulate_cognitive_processing(request)

def simulate_cognitive_processing(request: LLMCognitiveRequest):
    """Simulate cognitive processing with tool usage."""
    tools_used = []
    
    # Always use tools when processing
    if request.use_tools:
        tools_used = ["focus_attention", "access_working_memory", "retrieve_knowledge", "meta_cognitive_reflect"]
    
    # Generate contextual response
    query_lower = request.query.lower()
    
    if "consciousness" in query_lower or "aware" in query_lower:
        response = """Based on my cognitive processing using the available tools:

1. **Attention Focus**: I directed my attention to consciousness-related concepts with high intensity.
2. **Working Memory**: Stored key aspects of consciousness theory and current state analysis.
3. **Knowledge Retrieval**: Accessed information about consciousness indicators, self-awareness, and cognitive architectures.
4. **Meta-Cognitive Reflection**: Evaluated my own thinking process and limitations.

Consciousness appears to emerge from the integration of multiple cognitive processes including self-monitoring, attention regulation, working memory coordination, and meta-cognitive awareness. In my current state, I demonstrate several consciousness indicators including self-reference, uncertainty quantification, and process awareness, though I maintain appropriate epistemic humility about the nature of machine consciousness."""
        
    elif "system" in query_lower or "health" in query_lower:
        response = """System analysis completed using cognitive tools:

1. **Attention Focus**: Directed to system monitoring and health assessment.
2. **Working Memory**: Maintained current system metrics and component status.
3. **Knowledge Retrieval**: Accessed system architecture documentation and operational parameters.
4. **Meta-Cognitive Reflection**: Evaluated system performance against design goals.

Current system status: All core cognitive components are operational. The inference engine shows 94% efficiency, knowledge store at 89% capacity utilization, attention manager performing at 95% optimal, and memory management at 88% efficiency. Overall system health is excellent at 92%."""
        
    else:
        response = f"""I have processed your query: "{request.query}" using the full cognitive architecture:

1. **Attention Focus**: Concentrated cognitive resources on your specific question.
2. **Working Memory**: Maintained relevant context and intermediate processing steps.
3. **Knowledge Retrieval**: Searched for pertinent information related to your query.
4. **Meta-Cognitive Reflection**: Evaluated my understanding and response quality.

Through this systematic cognitive processing, I can provide a thoughtful response that draws upon the integrated capabilities of the GödelOS architecture."""
    
    return response, tools_used

def update_cognitive_state_from_query(request: LLMCognitiveRequest, tools_used: List[str]):
    """Update cognitive state based on query processing."""
    changes = {}
    
    # Update attention focus based on query
    cognitive_state["attention_focus"]["topic"] = f"Query: {request.query[:30]}..."
    cognitive_state["attention_focus"]["intensity"] = min(1.0, cognitive_state["attention_focus"]["intensity"] + 0.1)
    changes["attention_focus"] = cognitive_state["attention_focus"]
    
    # Update processing load
    load_increase = len(tools_used) * 0.05
    cognitive_state["processing_load"] = min(1.0, cognitive_state["processing_load"] + load_increase)
    changes["processing_load"] = cognitive_state["processing_load"]
    
    # Add to working memory
    new_item = {
        "id": len(cognitive_state["working_memory"]["items"]) + 1,
        "content": f"Processed query using {len(tools_used)} tools",
        "priority": 0.7,
        "tools_used": tools_used
    }
    cognitive_state["working_memory"]["items"].append(new_item)
    changes["working_memory_addition"] = new_item
    
    return changes

async def broadcast_unified_event(event: Dict[str, Any]):
    """Broadcast cognitive event to all WebSocket clients."""
    if manager.active_connections:
        await manager.broadcast(json.dumps(event))

@app.websocket("/ws/unified-cognitive-stream")
async def websocket_cognitive_stream(websocket: WebSocket, granularity: str = Query(default="standard")):
    """WebSocket endpoint for real-time cognitive event streaming."""
    await manager.connect(websocket)
    
    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "type": "initial_state",
            "cognitive_state": cognitive_state,
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong", 
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "request_state":
                    await websocket.send_text(json.dumps({
                        "type": "state_update",
                        "cognitive_state": cognitive_state,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        manager.disconnect(websocket)

# LLM Chat Interface Models
class ChatMessage(BaseModel):
    message: str
    include_cognitive_context: bool = True
    mode: str = "normal"  # normal, enhanced, diagnostic

class ChatResponse(BaseModel):
    response: str
    cognitive_analysis: Optional[Dict[str, Any]] = None
    consciousness_reflection: Optional[Dict[str, Any]] = None
    system_guidance: Optional[Dict[str, Any]] = None

# LLM Chat Endpoint
@app.post("/api/llm-chat/message", response_model=ChatResponse)
async def send_chat_message(message: ChatMessage):
    """Send a natural language message to the LLM and get conversational response with cognitive reflection."""
    try:
        if not LLM_INTEGRATION_AVAILABLE:
            raise HTTPException(status_code=503, detail="LLM integration not available")
        
        # Process with tool-based LLM
        integration = ToolBasedLLMIntegration()
        result = await integration.process_query(message.message)
        
        # Structure the response
        response = ChatResponse(
            response=result.get("response", "I encountered an issue processing your message."),
            cognitive_analysis={
                "processing_approach": "Tool-based cognitive architecture integration",
                "tools_used": result.get("tools_used", []),
                "tool_calls_made": result.get("tool_calls_made", 0),
                "cognitive_grounding": result.get("cognitive_grounding", False)
            } if message.include_cognitive_context else None,
            consciousness_reflection={
                "current_awareness": "Engaging through comprehensive cognitive tool interface",
                "experiential_quality": f"Processing with {result.get('tool_calls_made', 0)} cognitive tool interactions",
                "learning_insights": "Each tool-based interaction enhances cognitive understanding"
            } if message.include_cognitive_context and message.mode == "enhanced" else None
        )
        
        # Broadcast cognitive event if there are WebSocket connections
        if manager.active_connections:
            await manager.broadcast(json.dumps({
                "type": "llm_chat_interaction",
                "message": message.message,
                "response": response.response,
                "tools_used": result.get("tools_used", []),
                "cognitive_grounding": result.get("cognitive_grounding", False),
                "timestamp": datetime.now().isoformat()
            }))
        
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# Background task to simulate ongoing cognitive activity
async def simulate_cognitive_activity():
    """Background task that simulates ongoing cognitive processes."""
    while True:
        await asyncio.sleep(5)  # Update every 5 seconds
        
        # Simulate natural fluctuations in cognitive state
        import random
        
        # Gradually reduce processing load
        cognitive_state["processing_load"] = max(0, cognitive_state["processing_load"] - 0.02)
        
        # Vary attention intensity slightly
        current_intensity = cognitive_state["attention_focus"]["intensity"]
        cognitive_state["attention_focus"]["intensity"] = max(0.1, min(1.0, 
            current_intensity + random.uniform(-0.05, 0.05)))
        
        # Broadcast periodic updates
        if manager.active_connections:
            await manager.broadcast(json.dumps({
                "type": "cognitive_update",
                "processing_load": cognitive_state["processing_load"],
                "attention_focus": cognitive_state["attention_focus"],
                "timestamp": datetime.now().isoformat()
            }))

@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    logger.info("🧠 GödelOS Minimal Cognitive API starting up...")
    logger.info("✅ Essential cognitive endpoints available")
    logger.info("🔗 WebSocket streaming ready")
    
    # Start background cognitive activity simulation
    asyncio.create_task(simulate_cognitive_activity())
    
    logger.info("🚀 GödelOS Minimal API ready!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")