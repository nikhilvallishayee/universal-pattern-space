"""
Structured error models for cognitive systems.

Provides simple, serializable error shapes that can be propagated through
responses and emitted as WebSocket events without leaking internals.
"""

from dataclasses import dataclass, asdict, field
from typing import Any, Dict, Optional
import time


@dataclass
class CognitiveError:
    code: str
    message: str
    recoverable: bool = False
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExternalServiceError(CognitiveError):
    service: str = "external"
    operation: str = ""


@dataclass
class ValidationError(CognitiveError):
    field: Optional[str] = None


def from_exception(exc: Exception, *, code: str = "exception", recoverable: bool = False, **details) -> Dict[str, Any]:
    err = CognitiveError(code=code, message=str(exc), recoverable=recoverable, details=details)
    return err.to_dict()

