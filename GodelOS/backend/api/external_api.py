"""
External API Router for GodelOS

Provides a clean, documented, and authenticated REST + WebSocket surface
for external consumers (including the frontend dashboard).

Endpoints
---------
- POST /query        Submit a natural-language query, receive a structured response.
- POST /knowledge    Ingest a knowledge item.
- GET  /status       System health and active subsystem status.
- GET  /context      Current active context snapshot.
- WS   /events       Stream cognitive events in real time.

Authentication
--------------
All endpoints are guarded by Bearer-token authentication.  Set the
``GODELOS_API_TOKEN`` environment variable to enable; when the variable is
unset or empty, authentication is **disabled** (convenient for local dev).
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Shared version constant (keep in sync with unified_server.py ``app`` version)
API_VERSION = "2.0.0"

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)

_EXPECTED_TOKEN: Optional[str] = os.environ.get("GODELOS_API_TOKEN", "").strip() or None


def _verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[str]:
    """Validate the Bearer token when ``GODELOS_API_TOKEN`` is configured.

    Returns the token string on success.  Raises 401 if the env var is set
    but the caller did not supply a matching token.
    """
    if _EXPECTED_TOKEN is None:
        # Auth disabled – allow all requests.
        return None
    if credentials is None or credentials.credentials != _EXPECTED_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ExternalQueryRequest(BaseModel):
    """Payload for ``POST /query``."""
    query: str = Field(..., description="Natural-language query to process")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional context dict forwarded to the cognitive engine"
    )
    include_reasoning: bool = Field(
        default=False, description="When true, include step-by-step reasoning trace"
    )


class ExternalQueryResponse(BaseModel):
    """Response from ``POST /query``."""
    response: str = Field(..., description="Natural-language answer")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    reasoning_trace: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    inference_time_ms: Optional[float] = None
    knowledge_used: Optional[List[str]] = None


class ExternalKnowledgeRequest(BaseModel):
    """Payload for ``POST /knowledge``."""
    content: str = Field(..., description="The knowledge content to ingest")
    knowledge_type: str = Field(
        default="fact", description="Type of knowledge (fact, rule, concept, …)"
    )
    context_id: Optional[str] = Field(
        default=None, description="Target knowledge context / namespace"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class ExternalKnowledgeResponse(BaseModel):
    """Response from ``POST /knowledge``."""
    status: str
    message: str
    knowledge_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Module-level references (wired at import time by unified_server)
# ---------------------------------------------------------------------------

_godelos_integration: Any = None
_websocket_manager: Any = None
_cognitive_state: Any = None
_startup_time: Optional[float] = None
_tool_based_llm: Any = None


def configure(
    *,
    godelos_integration: Any = None,
    websocket_manager: Any = None,
    cognitive_state: Any = None,
    startup_time: Optional[float] = None,
    tool_based_llm: Any = None,
) -> None:
    """Inject runtime dependencies from the unified server."""
    global _godelos_integration, _websocket_manager, _cognitive_state
    global _startup_time, _tool_based_llm
    _godelos_integration = godelos_integration
    _websocket_manager = websocket_manager
    _cognitive_state = cognitive_state
    _startup_time = startup_time
    _tool_based_llm = tool_based_llm


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/v1/external", tags=["External API"])

# ---- POST /query ----------------------------------------------------------

@router.post(
    "/query",
    response_model=ExternalQueryResponse,
    summary="Submit a natural-language query",
)
async def submit_query(
    request: ExternalQueryRequest,
    _token: Optional[str] = Depends(_verify_token),
) -> ExternalQueryResponse:
    start = time.time()

    if _godelos_integration is not None:
        try:
            result = await _godelos_integration.process_query(
                request.query, context=request.context
            )
            elapsed_ms = (time.time() - start) * 1000.0
            return ExternalQueryResponse(
                response=result.get("response", ""),
                confidence=result.get("confidence"),
                reasoning_trace=result.get("reasoning_trace") if request.include_reasoning else None,
                sources=result.get("sources"),
                inference_time_ms=elapsed_ms,
                knowledge_used=result.get("knowledge_used") or result.get("sources"),
            )
        except Exception as exc:
            logger.error("Error processing external query: %s", exc)

    # Fallback when the integration layer is not available.
    elapsed_ms = (time.time() - start) * 1000.0
    return ExternalQueryResponse(
        response=f"Received query: '{request.query}'. System is running in fallback mode.",
        confidence=0.5,
        inference_time_ms=elapsed_ms,
        knowledge_used=[],
    )


# ---- POST /knowledge ------------------------------------------------------

@router.post(
    "/knowledge",
    response_model=ExternalKnowledgeResponse,
    summary="Ingest a knowledge item",
)
async def ingest_knowledge(
    request: ExternalKnowledgeRequest,
    _token: Optional[str] = Depends(_verify_token),
) -> ExternalKnowledgeResponse:
    knowledge_id = f"k_{int(time.time() * 1000)}"
    try:
        # Forward to the GödelOS integration if available.
        if _godelos_integration is not None and hasattr(_godelos_integration, "add_knowledge"):
            await _godelos_integration.add_knowledge(
                content=request.content,
                knowledge_type=request.knowledge_type,
                context_id=request.context_id,
                metadata=request.metadata,
            )

        # Broadcast event via WebSocket manager (best-effort).
        if _websocket_manager is not None and _websocket_manager.has_connections():
            try:
                await _websocket_manager.broadcast({
                    "type": "knowledge_added",
                    "timestamp": time.time(),
                    "data": {
                        "knowledge_id": knowledge_id,
                        "knowledge_type": request.knowledge_type,
                        "context_id": request.context_id,
                    },
                })
            except Exception:
                pass

        return ExternalKnowledgeResponse(
            status="success",
            message="Knowledge ingested successfully",
            knowledge_id=knowledge_id,
        )
    except Exception as exc:
        logger.error("Error ingesting knowledge: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ---- GET /status -----------------------------------------------------------

@router.get("/status", summary="System health and active subsystem status")
async def system_status(
    _token: Optional[str] = Depends(_verify_token),
) -> Dict[str, Any]:
    uptime = (time.time() - _startup_time) if _startup_time else 0.0
    return {
        "system": "GodelOS",
        "status": "operational",
        "version": API_VERSION,
        "uptime_seconds": round(uptime, 2),
        "components": {
            "cognitive_engine": "active" if _godelos_integration is not None else "inactive",
            "knowledge_base": "active" if _godelos_integration is not None else "inactive",
            "websocket_streaming": "active" if _websocket_manager is not None else "inactive",
            "llm_integration": "active" if _tool_based_llm is not None else "inactive",
        },
        "timestamp": datetime.now().isoformat(),
    }


# ---- GET /context ----------------------------------------------------------

@router.get("/context", summary="Current active context snapshot")
async def active_context(
    _token: Optional[str] = Depends(_verify_token),
) -> Dict[str, Any]:
    # Prefer live data from the integration layer.
    if _godelos_integration is not None:
        try:
            state = await _godelos_integration.get_cognitive_state()
            return {
                "active_context": state,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            logger.error("Error fetching cognitive state: %s", exc)

    # Return the in-process fallback state.
    return {
        "active_context": _cognitive_state if _cognitive_state is not None else {},
        "timestamp": datetime.now().isoformat(),
    }


# ---- WS /events -----------------------------------------------------------

@router.websocket("/events")
async def cognitive_events_stream(websocket: WebSocket) -> None:
    """Stream cognitive events to the client.

    The client may send JSON messages to control the subscription:
    * ``{"type": "subscribe", "event_types": [...]}``
    * ``{"type": "ping"}`` → receives ``{"type": "pong", ...}``
    """
    # --- Token check for WebSocket (via query param ``token``) ---
    ws_token = websocket.query_params.get("token")
    if _EXPECTED_TOKEN is not None and ws_token != _EXPECTED_TOKEN:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()

    # Register with the shared manager so broadcasts reach this client.
    if _websocket_manager is not None:
        _websocket_manager.active_connections.append(websocket)

    try:
        # Send an initial state snapshot.
        await websocket.send_text(json.dumps({
            "type": "initial_state",
            "data": {"status": "connected", "endpoint": "external/events"},
            "timestamp": datetime.now().isoformat(),
        }))

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                }))
                continue

            msg_type = msg.get("type")
            if msg_type == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                }))
            elif msg_type == "subscribe":
                event_types = msg.get("event_types", [])
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "event_types": event_types,
                }))
            elif msg_type == "request_state":
                ctx = {}
                if _godelos_integration is not None:
                    try:
                        ctx = await _godelos_integration.get_cognitive_state()
                    except Exception:
                        pass
                await websocket.send_text(json.dumps({
                    "type": "state_update",
                    "data": ctx or (_cognitive_state if _cognitive_state is not None else {}),
                    "timestamp": datetime.now().isoformat(),
                }))
            else:
                await websocket.send_text(json.dumps({"type": "ack"}))

    except WebSocketDisconnect:
        logger.info("External events WebSocket disconnected by client")
    except Exception as exc:
        logger.error("External events WebSocket error: %s", exc)
    finally:
        if _websocket_manager is not None and websocket in _websocket_manager.active_connections:
            _websocket_manager.active_connections.remove(websocket)
