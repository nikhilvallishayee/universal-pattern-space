"""
Utility functions for the GödelOS Backend API

Common helper functions and utilities used across the backend.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import psutil
import uuid


logger = logging.getLogger(__name__)


def ensure_logs_directory():
    """Ensure the logs directory exists."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format a timestamp for logging."""
    if timestamp is None:
        timestamp = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def safe_json_serialize(obj: Any) -> str:
    """Safely serialize an object to JSON."""
    try:
        return json.dumps(obj, default=str, indent=2)
    except Exception as e:
        logger.warning(f"JSON serialization failed: {e}")
        return str(obj)


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "disk_usage": dict(psutil.disk_usage('/')._asdict()),
            "network_io": dict(psutil.net_io_counters()._asdict()) if psutil.net_io_counters() else {},
            "process_count": len(psutil.pids()),
            "boot_time": psutil.boot_time()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {}


def validate_query_input(query: str) -> bool:
    """Validate natural language query input."""
    if not query or not isinstance(query, str):
        return False
    
    # Basic validation
    query = query.strip()
    if len(query) < 3 or len(query) > 1000:
        return False
    
    # Check for potentially harmful content (basic)
    harmful_patterns = ['<script', 'javascript:', 'eval(', 'exec(']
    query_lower = query.lower()
    for pattern in harmful_patterns:
        if pattern in query_lower:
            return False
    
    return True


def sanitize_knowledge_content(content: str) -> str:
    """Sanitize knowledge content for safe storage."""
    if not content or not isinstance(content, str):
        return ""
    
    # Remove potentially harmful content
    content = content.strip()
    
    # Basic HTML/script tag removal
    import re
    content = re.sub(r'<[^>]*>', '', content)
    
    # Limit length
    if len(content) > 10000:
        content = content[:10000] + "..."
    
    return content


def format_inference_time(time_ms: float) -> str:
    """Format inference time for display."""
    if time_ms < 1:
        return f"{time_ms:.2f}ms"
    elif time_ms < 1000:
        return f"{time_ms:.0f}ms"
    else:
        return f"{time_ms/1000:.2f}s"


def extract_entities_from_query(query: str) -> List[str]:
    """Extract potential entities from a natural language query."""
    # Simple entity extraction (would be enhanced with NLP)
    import re
    
    # Look for capitalized words (potential proper nouns)
    entities = re.findall(r'\b[A-Z][a-z]+\b', query)
    
    # Look for quoted strings
    quoted = re.findall(r'"([^"]*)"', query)
    entities.extend(quoted)
    
    # Look for common location/person indicators
    location_patterns = [
        r'\b(?:at|in|to|from)\s+([A-Z][a-z]+)\b',
        r'\b([A-Z][a-z]+)(?:\s+(?:Office|Library|Home|Park|Cafe))\b'
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, query)
        entities.extend(matches)
    
    return list(set(entities))  # Remove duplicates


def calculate_confidence_score(
    inference_result: Dict[str, Any],
    query_complexity: int = 1,
    knowledge_coverage: float = 1.0
) -> float:
    """Calculate a confidence score for query results."""
    base_confidence = 1.0 if inference_result.get("goal_achieved", False) else 0.0
    
    # Adjust based on query complexity
    complexity_factor = max(0.5, 1.0 - (query_complexity - 1) * 0.1)
    
    # Adjust based on knowledge coverage
    coverage_factor = max(0.3, knowledge_coverage)
    
    # Combine factors
    confidence = base_confidence * complexity_factor * coverage_factor
    
    return min(1.0, max(0.0, confidence))


def format_reasoning_steps(raw_steps: List[Any]) -> List[Dict[str, Any]]:
    """Format raw reasoning steps into structured format."""
    formatted_steps = []
    
    for i, step in enumerate(raw_steps):
        formatted_step = {
            "step_number": i + 1,
            "operation": getattr(step, 'operation', 'inference'),
            "description": str(step),
            "premises": getattr(step, 'premises', []),
            "conclusion": getattr(step, 'conclusion', str(step)),
            "confidence": getattr(step, 'confidence', 1.0)
        }
        formatted_steps.append(formatted_step)
    
    return formatted_steps


class AsyncTimer:
    """Async context manager for timing operations."""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if a request is allowed for the given client."""
        now = time.time()
        
        # Clean old entries
        self.requests = {
            cid: times for cid, times in self.requests.items()
            if times and max(times) > now - self.window_seconds
        }
        
        # Get client's recent requests
        client_requests = self.requests.get(client_id, [])
        
        # Filter to current window
        recent_requests = [
            req_time for req_time in client_requests
            if req_time > now - self.window_seconds
        ]
        
        # Check limit
        if len(recent_requests) >= self.max_requests:
            return False
        
        # Record this request
        recent_requests.append(now)
        self.requests[client_id] = recent_requests
        
        return True


def create_error_response(
    error_message: str,
    error_type: str = "general_error",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": error_message,
        "error_type": error_type,
        "details": details or {},
        "timestamp": time.time()
    }


def log_api_request(
    endpoint: str,
    method: str,
    client_ip: str,
    user_agent: str = "",
    request_id: str = "",
    execution_time_ms: float = 0.0
):
    """Log API request details."""
    logger.info(
        f"API Request - {method} {endpoint} - "
        f"Client: {client_ip} - "
        f"User-Agent: {user_agent[:100]} - "
        f"Request ID: {request_id} - "
        f"Time: {execution_time_ms:.2f}ms"
    )


# Initialize logs directory when module is imported
ensure_logs_directory()