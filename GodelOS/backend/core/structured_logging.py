#!/usr/bin/env python3
"""
Enhanced Logging System with Structured JSON and Correlation IDs

This module provides structured logging capabilities with correlation tracking,
trace IDs, and comprehensive context for debugging and monitoring.
"""

import json
import logging
import time
import uuid
import threading
from logging.config import dictConfig
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from contextvars import ContextVar
from contextlib import contextmanager
from enum import Enum

# Context variables for correlation tracking
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class LogLevel(Enum):
    """Enhanced log levels with cognitive context."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    COGNITIVE = "COGNITIVE"  # Special level for cognitive events
    PERFORMANCE = "PERFORMANCE"  # Performance metrics
    SECURITY = "SECURITY"  # Security events


class LogCategory(Enum):
    """Categories for log organization."""
    SYSTEM = "system"
    API = "api"
    COGNITIVE = "cognitive"
    COORDINATION = "coordination"
    KNOWLEDGE = "knowledge"
    WEBSOCKET = "websocket"
    VECTOR_DB = "vector_db"
    LLM = "llm"
    CONSCIOUSNESS = "consciousness"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class LogContext:
    """Enhanced context for structured logging."""
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    category: LogCategory = LogCategory.SYSTEM
    
    # Performance metrics
    start_time: Optional[float] = None
    duration_ms: Optional[float] = None
    
    # Request context
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    
    # Cognitive context
    confidence: Optional[float] = None
    reasoning_depth: Optional[int] = None
    cognitive_load: Optional[float] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        data = asdict(self)
        # Remove None values and convert enums
        cleaned = {}
        for k, v in data.items():
            if v is not None:
                if isinstance(v, Enum):
                    cleaned[k] = v.value
                elif k == 'metadata' and isinstance(v, dict):
                    cleaned[k] = v
                elif v != {} and v != []:
                    cleaned[k] = v
        return cleaned


class StructuredJSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs."""
    
    def __init__(self, include_trace_info: bool = True):
        super().__init__()
        self.include_trace_info = include_trace_info
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "thread": threading.current_thread().name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add correlation context
        if self.include_trace_info:
            if correlation_id.get():
                log_entry["correlation_id"] = correlation_id.get()
            if trace_id.get():
                log_entry["trace_id"] = trace_id.get()
            if session_id.get():
                log_entry["session_id"] = session_id.get()
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add custom context if available
        if hasattr(record, 'context') and record.context:
            if isinstance(record.context, LogContext):
                log_entry.update(record.context.to_dict())
            elif isinstance(record.context, dict):
                log_entry.update(record.context)
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message',
                          'context'}:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class CorrelationTracker:
    """Manages correlation and trace IDs for request tracking."""
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a new correlation ID."""
        return f"corr_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_trace_id() -> str:
        """Generate a new trace ID."""
        return f"trace_{uuid.uuid4().hex[:16]}"
    
    @staticmethod
    def set_correlation_context(corr_id: str = None, tr_id: str = None, sess_id: str = None):
        """Set correlation context for current execution."""
        if corr_id:
            correlation_id.set(corr_id)
        if tr_id:
            trace_id.set(tr_id)
        if sess_id:
            session_id.set(sess_id)
    
    @staticmethod
    def get_correlation_context() -> Dict[str, Optional[str]]:
        """Get current correlation context."""
        return {
            "correlation_id": correlation_id.get(),
            "trace_id": trace_id.get(),
            "session_id": session_id.get()
        }
    
    @staticmethod
    def clear_correlation_context():
        """Clear correlation context."""
        correlation_id.set(None)
        trace_id.set(None)
        session_id.set(None)
    
    @staticmethod
    @contextmanager
    def request_context(corr_id: str = None, tr_id: str = None, sess_id: str = None):
        """Context manager for setting correlation context during request processing."""
        # Store previous context
        prev_corr_id = correlation_id.get()
        prev_trace_id = trace_id.get()
        prev_session_id = session_id.get()
        
        try:
            # Set new context
            CorrelationTracker.set_correlation_context(
                corr_id or CorrelationTracker.generate_correlation_id(),
                tr_id or CorrelationTracker.generate_trace_id(),
                sess_id
            )
            yield
        finally:
            # Restore previous context
            correlation_id.set(prev_corr_id)
            trace_id.set(prev_trace_id)
            session_id.set(prev_session_id)


class EnhancedLogger:
    """Enhanced logger with structured logging and cognitive context."""
    
    def __init__(self, name: str, category: LogCategory = LogCategory.SYSTEM):
        self.logger = logging.getLogger(name)
        self.category = category
        self.performance_tracker = {}
    
    def _log_with_context(self, level: int, message: str, context: LogContext = None, **kwargs):
        """Log with enhanced context."""
        if context is None:
            context = LogContext(category=self.category)
        
        # Merge correlation context
        if not context.correlation_id:
            context.correlation_id = correlation_id.get()
        if not context.trace_id:
            context.trace_id = trace_id.get()
        if not context.session_id:
            context.session_id = session_id.get()
        
        # Add kwargs to metadata
        if kwargs:
            context.metadata.update(kwargs)
        
        # Create log record with context
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        record.context = context
        
        self.logger.handle(record)
    
    def debug(self, message: str, context: LogContext = None, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: LogContext = None, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: LogContext = None, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: LogContext = None, exc_info: bool = True, **kwargs):
        """Log error message."""
        if exc_info:
            # Capture exception info
            import sys
            kwargs['exc_info'] = sys.exc_info()
        self._log_with_context(logging.ERROR, message, context, **kwargs)
    
    def critical(self, message: str, context: LogContext = None, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, context, **kwargs)
    
    def cognitive_event(self, message: str, event_type: str, confidence: float = None, 
                       reasoning_depth: int = None, **kwargs):
        """Log cognitive processing event."""
        context = LogContext(
            category=LogCategory.COGNITIVE,
            operation=event_type,
            confidence=confidence,
            reasoning_depth=reasoning_depth,
            metadata=kwargs
        )
        self._log_with_context(logging.INFO, message, context)
    
    def performance_event(self, operation: str, duration_ms: float, success: bool = True, **kwargs):
        """Log performance metric."""
        context = LogContext(
            category=LogCategory.PERFORMANCE,
            operation=operation,
            duration_ms=duration_ms,
            metadata={"success": success, **kwargs}
        )
        self._log_with_context(logging.INFO, f"Performance: {operation} took {duration_ms:.2f}ms", context)
    
    def security_event(self, message: str, event_type: str, severity: str = "info", **kwargs):
        """Log security event."""
        context = LogContext(
            category=LogCategory.SECURITY,
            operation=event_type,
            metadata={"severity": severity, **kwargs}
        )
        level = logging.WARNING if severity in ["warning", "high"] else logging.INFO
        self._log_with_context(level, message, context)
    
    def start_operation(self, operation: str) -> str:
        """Start tracking an operation."""
        op_id = f"{operation}_{uuid.uuid4().hex[:8]}"
        self.performance_tracker[op_id] = {
            "operation": operation,
            "start_time": time.time(),
            "trace_id": trace_id.get()
        }
        return op_id
    
    def end_operation(self, op_id: str, success: bool = True, **kwargs):
        """End tracking an operation."""
        if op_id not in self.performance_tracker:
            return
        
        op_data = self.performance_tracker.pop(op_id)
        duration_ms = (time.time() - op_data["start_time"]) * 1000
        
        self.performance_event(
            operation=op_data["operation"],
            duration_ms=duration_ms,
            success=success,
            **kwargs
        )


def setup_structured_logging(log_level: str = "INFO", 
                           log_file: Optional[str] = None,
                           enable_json: bool = True,
                           enable_console: bool = True) -> None:
    """Setup structured logging configuration."""
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatters
    if enable_json:
        json_formatter = StructuredJSONFormatter()
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        if enable_json:
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        if enable_json:
            file_handler.setFormatter(json_formatter)
        else:
            file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)



def setup_json_logging():
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json-default": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "timestamp:asctime level:levelname logger:name message:message process:process thread:threadName module:module function:funcName line:lineno",
            },
            "json-access": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "timestamp:asctime level:levelname logger:name client:client_addr request:request_line status:status_code",
            },
        },
        "handlers": {
            "default": {"class": "logging.StreamHandler", "formatter": "json-default", "stream": "ext://sys.stderr"},
            "access": {"class": "logging.StreamHandler", "formatter": "json-access", "stream": "ext://sys.stdout"},
        },
        "loggers": {
            "uvicorn.error": {"level": "INFO", "handlers": ["default"], "propagate": False},
            "uvicorn.access": {"level": "INFO", "handlers": ["access"], "propagate": False},
            "backend":        {"level": "INFO", "handlers": ["default"], "propagate": False},
        },
        "root": {"level": "INFO", "handlers": ["default"]},
    })


# Context managers for correlation tracking
class correlation_context:
    """Context manager for correlation tracking."""
    
    def __init__(self, correlation_id: str = None, trace_id: str = None, session_id: str = None):
        self.correlation_id = correlation_id or CorrelationTracker.generate_correlation_id()
        self.trace_id = trace_id or CorrelationTracker.generate_trace_id()
        self.session_id = session_id
        self.previous_context = None
    
    def __enter__(self):
        self.previous_context = CorrelationTracker.get_correlation_context()
        CorrelationTracker.set_correlation_context(
            self.correlation_id, self.trace_id, self.session_id
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        CorrelationTracker.set_correlation_context(
            self.previous_context["correlation_id"],
            self.previous_context["trace_id"],
            self.previous_context["session_id"]
        )


# Convenience logger instances
cognitive_logger = EnhancedLogger("godelos.cognitive", LogCategory.COGNITIVE)
api_logger = EnhancedLogger("godelos.api", LogCategory.API)
performance_logger = EnhancedLogger("godelos.performance", LogCategory.PERFORMANCE)
security_logger = EnhancedLogger("godelos.security", LogCategory.SECURITY)
websocket_logger = EnhancedLogger("godelos.websocket", LogCategory.WEBSOCKET)


# Decorator for automatic operation tracking
def track_operation(operation_name: str = None, log_performance: bool = True):
    """Decorator to automatically track operation performance."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = EnhancedLogger(func.__module__)
            
            with correlation_context():
                op_id = logger.start_operation(op_name)
                try:
                    result = await func(*args, **kwargs)
                    if log_performance:
                        logger.end_operation(op_id, success=True)
                    return result
                except Exception as e:
                    if log_performance:
                        logger.end_operation(op_id, success=False, error=str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger = EnhancedLogger(func.__module__)
            
            with correlation_context():
                op_id = logger.start_operation(op_name)
                try:
                    result = func(*args, **kwargs)
                    if log_performance:
                        logger.end_operation(op_id, success=True)
                    return result
                except Exception as e:
                    if log_performance:
                        logger.end_operation(op_id, success=False, error=str(e))
                    raise
        
        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
