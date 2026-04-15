"""
Query Replay Harness for GödelOS

Provides offline reprocessing and replay capabilities for cognitive queries,
enabling debugging, performance analysis, and system optimization.
"""

import asyncio
import json
import time
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReplayStatus(Enum):
    """Status of a replay operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingStep(Enum):
    """Types of processing steps that can be recorded."""
    QUERY_RECEIVED = "query_received"
    PREPROCESSING = "preprocessing"
    CONTEXT_GATHERING = "context_gathering"
    COGNITIVE_ANALYSIS = "cognitive_analysis"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    REASONING = "reasoning"
    REASONING_PROCESS = "reasoning_process"
    CONSCIOUSNESS_ASSESSMENT = "consciousness_assessment"
    RESPONSE_GENERATION = "response_generation"
    QUALITY_ASSURANCE = "quality_assurance"
    POSTPROCESSING = "postprocessing"
    QUERY_COMPLETED = "query_completed"
    RESPONSE_COMPLETE = "response_complete"


@dataclass
class RecordedStep:
    """A single step in the cognitive processing pipeline."""
    step_type: ProcessingStep
    timestamp: float
    duration_ms: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    correlation_id: Optional[str] = None

    @property
    def data(self) -> Dict[str, Any]:
        """Alias returning input_data for backward-compatible access."""
        return self.input_data


@dataclass
class QueryRecording:
    """Complete recording of a query processing session."""
    recording_id: str
    query: str
    context: Dict[str, Any]
    start_timestamp: float
    end_timestamp: Optional[float]
    total_duration_ms: Optional[float]
    steps: List[RecordedStep]
    final_response: Optional[Dict[str, Any]]
    system_state: Dict[str, Any]
    cognitive_state: Dict[str, Any]
    metadata: Dict[str, Any]
    tags: List[str]

    @property
    def correlation_id(self) -> Optional[str]:
        """Return correlation_id stored in metadata."""
        return self.metadata.get("correlation_id")


@dataclass
class ReplayResult:
    """Result of replaying a recorded query."""
    replay_id: str
    original_recording_id: str
    status: ReplayStatus
    start_timestamp: float
    end_timestamp: Optional[float]
    duration_ms: Optional[float]
    replayed_steps: List[RecordedStep]
    final_response: Optional[Dict[str, Any]]
    comparison: Optional[Dict[str, Any]]
    errors: List[str]
    metadata: Dict[str, Any]


class QueryReplayHarness:
    """Main class for recording and replaying cognitive queries."""
    
    def __init__(self, storage_path: str = "data/query_recordings"):
        """Initialize the replay harness."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Active recordings (by correlation_id)
        self._active_recordings: Dict[str, QueryRecording] = {}
        # Public alias for test compatibility
        self.active_recordings = self._active_recordings
        
        # Replay operations (by replay_id)
        self._active_replays: Dict[str, ReplayResult] = {}
        # Public alias for test compatibility
        self.replay_results = self._active_replays
        
        # Configuration
        self.max_recordings = 1000  # Maximum number of recordings to keep
        self.auto_cleanup_days = 30  # Auto-delete recordings older than this
        self.enable_recording = True  # Global recording toggle
        
        logger.info(f"Query replay harness initialized with storage at {self.storage_path}")
    
    async def start_recording(self, query: str, correlation_id: str = None, context: Dict[str, Any] = None, tags: List[str] = None, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Start recording a new query processing session.
        
        Args:
            query: The query string being recorded.
            correlation_id: Optional external correlation id.
            context: Optional context dict.
            tags: Optional list of tags.
            metadata: Optional metadata dict (merged into recording metadata).
            
        Returns:
            The recording_id, or None if recording is disabled.
        """
        if not self.enable_recording:
            logger.debug("Recording disabled, skipping query recording")
            return None
        
        recording_id = f"rec_{uuid.uuid4().hex[:12]}"
        correlation_id = correlation_id or recording_id
        
        # Capture initial system state
        system_state = self._capture_system_state()
        cognitive_state = self._capture_cognitive_state()
        
        rec_metadata: Dict[str, Any] = {
            "correlation_id": correlation_id,
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        if metadata:
            reserved_keys = {"correlation_id", "created_at", "version"}
            for key, value in metadata.items():
                if key not in reserved_keys:
                    rec_metadata[key] = value
        
        recording = QueryRecording(
            recording_id=recording_id,
            query=query,
            context=(context or {}).copy(),
            start_timestamp=time.time(),
            end_timestamp=None,
            total_duration_ms=None,
            steps=[],
            final_response=None,
            system_state=system_state,
            cognitive_state=cognitive_state,
            metadata=rec_metadata,
            tags=tags or []
        )
        
        # Key by recording_id for external lookup
        self._active_recordings[recording_id] = recording
        # Also allow lookup by correlation_id
        if correlation_id != recording_id:
            self._active_recordings[correlation_id] = recording
        
        logger.info(f"Started recording query session: {recording_id}")
        return recording_id
    
    async def record_step(self, recording_id: str = None, step_type: ProcessingStep = None,
                   data: Dict[str, Any] = None,
                   input_data: Dict[str, Any] = None,
                   output_data: Dict[str, Any] = None,
                   duration_ms: float = 0.0,
                   metadata: Dict[str, Any] = None,
                   error: str = None,
                   # Legacy alias
                   correlation_id: str = None) -> bool:
        """Record a processing step in an active session.

        Accepts either a unified ``data`` dict (test-friendly interface) or
        separate ``input_data`` / ``output_data`` dicts (internal interface).
        The first positional arg can be called ``recording_id`` or ``correlation_id``.
        """
        if step_type is None:
            logger.warning("record_step() called without step_type — ignoring")
            return False

        key = recording_id or correlation_id
        if key not in self._active_recordings:
            logger.debug(f"No active recording for key: {key}")
            return False

        recording = self._active_recordings[key]

        # Normalise: if unified `data` provided, use it for both input and output
        _input  = self._sanitize_data(data if data is not None else (input_data or {}))
        _output = self._sanitize_data(data if data is not None else (output_data or {}))

        # Use the recording's actual correlation_id, not the lookup key
        actual_correlation_id = recording.metadata.get("correlation_id", key)

        step = RecordedStep(
            step_type=step_type,
            timestamp=time.time(),
            duration_ms=duration_ms,
            input_data=_input,
            output_data=_output,
            metadata=metadata or {},
            error=error,
            correlation_id=actual_correlation_id
        )
        
        recording.steps.append(step)
        
        logger.debug(f"Recorded step {step_type.value} for session {recording.recording_id}")
        return True
    
    async def complete_recording(self, recording_id_or_correlation_id: str, final_response: Dict[str, Any] = None) -> Optional[str]:
        """Finish recording a query session and save to disk."""
        key = recording_id_or_correlation_id
        if key not in self._active_recordings:
            logger.debug(f"No active recording for key: {key}")
            return None
        
        recording = self._active_recordings[key]
        
        # Finalize recording
        recording.end_timestamp = time.time()
        recording.total_duration_ms = (recording.end_timestamp - recording.start_timestamp) * 1000
        recording.final_response = self._sanitize_data(final_response)
        
        # Save to disk
        filename = f"{recording.recording_id}_{int(recording.start_timestamp)}.json"
        filepath = self.storage_path / filename
        
        try:
            def _json_serializer(obj):
                """Custom JSON serializer for dataclass fields."""
                if isinstance(obj, ProcessingStep):
                    return obj.value
                return str(obj)
            
            with open(filepath, 'w') as f:
                json.dump(asdict(recording), f, indent=2, default=_json_serializer)
            
            logger.info(f"Saved recording {recording.recording_id} to {filepath}")
            
            # Remove from active recordings (both keys if different)
            rec_id = recording.recording_id
            corr_id = recording.metadata.get("correlation_id")
            self._active_recordings.pop(rec_id, None)
            if corr_id and corr_id != rec_id:
                self._active_recordings.pop(corr_id, None)
            
            # Cleanup old recordings if needed
            # cleanup deferred: asyncio.ensure_future(self._cleanup_old_recordings())
            
            return recording.recording_id
            
        except Exception as e:
            logger.error(f"Error saving recording {recording.recording_id}: {e}")
            return None
    
    def load_recording(self, recording_id: str) -> Optional[QueryRecording]:
        """Load a recording from disk."""
        # Find the recording file
        recording_files = list(self.storage_path.glob(f"{recording_id}_*.json"))
        
        if not recording_files:
            logger.warning(f"Recording not found: {recording_id}")
            return None
        
        filepath = recording_files[0]
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Convert back to dataclass
            recording = self._dict_to_recording(data)
            logger.info(f"Loaded recording {recording_id} from {filepath}")
            return recording
            
        except Exception as e:
            logger.error(f"Error loading recording {recording_id}: {e}")
            return None
    
    async def replay_query(self, recording_id: str, cognitive_manager,
                          compare_results: bool = True, 
                          metadata: Dict[str, Any] = None) -> Optional[ReplayResult]:
        """Replay a recorded query using the current cognitive system."""
        recording = self.load_recording(recording_id)
        if not recording:
            return None
        
        replay_id = f"replay_{uuid.uuid4().hex[:12]}"
        
        replay_result = ReplayResult(
            replay_id=replay_id,
            original_recording_id=recording_id,
            status=ReplayStatus.RUNNING,
            start_timestamp=time.time(),
            end_timestamp=None,
            duration_ms=None,
            replayed_steps=[],
            final_response=None,
            comparison=None,
            errors=[],
            metadata=metadata or {}
        )
        
        self._active_replays[replay_id] = replay_result
        
        try:
            logger.info(f"Starting replay {replay_id} of recording {recording_id}")
            
            # Generate new correlation ID for the replay
            replay_correlation_id = f"replay_{uuid.uuid4().hex[:8]}"
            
            # Start new recording for the replay
            replay_recording_id = await self.start_recording(
                query=recording.query,
                context=recording.context,
                correlation_id=replay_correlation_id,
                tags=[f"replay_of:{recording_id}"]
            )
            
            # Execute the query using current cognitive manager
            start_time = time.time()
            
            try:
                # Process the query
                result = await cognitive_manager.process_query(
                    query=recording.query,
                    context=recording.context
                )
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Finish the replay recording
                await self.complete_recording(replay_correlation_id, result)
                
                replay_result.final_response = result
                replay_result.duration_ms = duration_ms
                replay_result.end_timestamp = end_time
                replay_result.status = ReplayStatus.COMPLETED
                
                # Load the replay recording for comparison
                if replay_recording_id:
                    replay_recording = self.load_recording(replay_recording_id)
                    if replay_recording:
                        replay_result.replayed_steps = replay_recording.steps
                
                # Compare results if requested
                if compare_results:
                    replay_result.comparison = self._compare_results(recording, replay_result)
                
                logger.info(f"Replay {replay_id} completed successfully in {duration_ms:.2f}ms")
                
            except Exception as e:
                replay_result.status = ReplayStatus.FAILED
                replay_result.errors.append(str(e))
                logger.error(f"Replay {replay_id} failed: {e}")
                
        except Exception as e:
            replay_result.status = ReplayStatus.FAILED
            replay_result.errors.append(f"Replay setup failed: {str(e)}")
            logger.error(f"Replay {replay_id} setup failed: {e}")
        
        finally:
            if replay_result.end_timestamp is None:
                replay_result.end_timestamp = time.time()
                replay_result.duration_ms = (replay_result.end_timestamp - replay_result.start_timestamp) * 1000
        
        return replay_result
    
    def list_recordings(self, tags: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List available recordings with optional filtering."""
        recordings = []
        
        for filepath in self.storage_path.glob("rec*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Filter by tags if specified
                if tags:
                    recording_tags = data.get('tags', [])
                    if not any(tag in recording_tags for tag in tags):
                        continue
                
                # Return summary info
                summary = {
                    "recording_id": data.get('recording_id', filepath.stem),
                    "query": (data.get('query', '')[:100] + ("..." if len(data.get('query', '')) > 100 else "")),
                    "timestamp": data.get('start_timestamp', data.get('timestamp', 0)),
                    "duration_ms": data.get('total_duration_ms', data.get('duration_ms')),
                    "steps_count": len(data.get('steps', [])),
                    "tags": data.get('tags', []),
                    "created_at": data.get('metadata', {}).get('created_at')
                }
                
                recordings.append(summary)
                
            except Exception as e:
                logger.warning(f"Error reading recording file {filepath}: {e}")
                continue
        
        # Sort by timestamp (newest first) and limit
        recordings.sort(key=lambda x: x['timestamp'], reverse=True)
        return recordings[:limit]
    
    def get_replay_status(self, replay_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a replay operation."""
        if replay_id not in self._active_replays:
            return None
        
        replay = self._active_replays[replay_id]
        return {
            "replay_id": replay.replay_id,
            "status": replay.status.value,
            "start_timestamp": replay.start_timestamp,
            "end_timestamp": replay.end_timestamp,
            "duration_ms": replay.duration_ms,
            "errors": replay.errors,
            "has_comparison": replay.comparison is not None
        }
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for storage (remove sensitive info, limit size)."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Skip potentially sensitive keys
                if key.lower() in ['password', 'token', 'key', 'secret']:
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = self._sanitize_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data[:100]]  # Limit list size
        elif isinstance(data, str):
            return data[:1000]  # Limit string length
        else:
            return data
    
    def _capture_system_state(self) -> Dict[str, Any]:
        """Capture current system state for recording."""
        import psutil
        import os
        
        try:
            process = psutil.Process(os.getpid())
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "process_memory_mb": process.memory_info().rss / 1024 / 1024,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.warning(f"Error capturing system state: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    def _capture_cognitive_state(self) -> Dict[str, Any]:
        """Capture current cognitive system state."""
        # This would integrate with the cognitive manager to get current state
        # For now, return basic placeholder
        return {
            "timestamp": time.time(),
            "active_processes": 0,
            "memory_usage": "normal"
        }
    
    def _dict_to_recording(self, data: Dict[str, Any]) -> QueryRecording:
        """Convert dictionary back to QueryRecording dataclass."""
        # Convert steps
        steps = []
        for step_data in data.get('steps', []):
            # Handle enum deserialization from various serialization formats
            raw_step_type = step_data['step_type']
            if isinstance(raw_step_type, ProcessingStep):
                step_type = raw_step_type
            elif isinstance(raw_step_type, str):
                # Try direct value first, then name-based lookup
                try:
                    step_type = ProcessingStep(raw_step_type)
                except ValueError:
                    # Handle "ProcessingStep.CONTEXT_GATHERING" format
                    name = raw_step_type.split('.')[-1] if '.' in raw_step_type else raw_step_type
                    step_type = ProcessingStep[name]
            else:
                step_type = ProcessingStep(str(raw_step_type))

            step = RecordedStep(
                step_type=step_type,
                timestamp=step_data['timestamp'],
                duration_ms=step_data['duration_ms'],
                input_data=step_data['input_data'],
                output_data=step_data['output_data'],
                metadata=step_data['metadata'],
                error=step_data.get('error'),
                correlation_id=step_data.get('correlation_id')
            )
            steps.append(step)
        
        return QueryRecording(
            recording_id=data['recording_id'],
            query=data['query'],
            context=data['context'],
            start_timestamp=data['start_timestamp'],
            end_timestamp=data.get('end_timestamp'),
            total_duration_ms=data.get('total_duration_ms'),
            steps=steps,
            final_response=data.get('final_response'),
            system_state=data['system_state'],
            cognitive_state=data['cognitive_state'],
            metadata=data['metadata'],
            tags=data.get('tags', [])
        )
    
    def _compare_results(self, original, replay) -> Dict[str, Any]:
        """Compare original recording/result with replay result.
        
        Accepts either (QueryRecording, ReplayResult) for full replay comparison
        or two plain dicts for lightweight response comparison.
        """
        # Plain-dict comparison (test-friendly / lightweight)
        if isinstance(original, dict) and isinstance(replay, dict):
            comparison: Dict[str, Any] = {
                "response_similarity": None,
                "confidence_diff": None,
                "sources_overlap": None,
                "key_differences": [],
            }
            # Response similarity (basic string comparison)
            orig_resp = original.get("response", "")
            repl_resp = replay.get("response", "")
            if orig_resp == repl_resp:
                comparison["response_similarity"] = 1.0
            else:
                # Simple character overlap ratio
                set_a = set(orig_resp.split())
                set_b = set(repl_resp.split())
                intersection = set_a & set_b
                union = set_a | set_b
                comparison["response_similarity"] = len(intersection) / max(len(union), 1)

            # Confidence diff
            orig_conf = original.get("confidence")
            repl_conf = replay.get("confidence")
            if orig_conf is not None and repl_conf is not None:
                comparison["confidence_diff"] = round(repl_conf - orig_conf, 10)

            # Sources overlap
            orig_sources = set(original.get("sources", []))
            repl_sources = set(replay.get("sources", []))
            if orig_sources or repl_sources:
                intersection = orig_sources & repl_sources
                max_len = max(len(orig_sources), len(repl_sources))
                comparison["sources_overlap"] = len(intersection) / max(max_len, 1)

            # Key differences
            all_keys = set(original.keys()) | set(replay.keys())
            for key in all_keys:
                if original.get(key) != replay.get(key):
                    comparison["key_differences"].append(key)

            return comparison

        # Full QueryRecording / ReplayResult comparison
        comparison = {
            "performance": {
                "original_duration_ms": original.total_duration_ms,
                "replay_duration_ms": replay.duration_ms,
                "duration_diff_ms": None,
                "duration_diff_percent": None
            },
            "response_similarity": None,
            "step_comparison": {
                "original_steps": len(original.steps),
                "replay_steps": len(replay.replayed_steps),
                "step_diff": None
            },
            "differences": []
        }
        
        # Performance comparison
        if original.total_duration_ms and replay.duration_ms:
            diff_ms = replay.duration_ms - original.total_duration_ms
            diff_percent = (diff_ms / original.total_duration_ms) * 100
            comparison["performance"]["duration_diff_ms"] = diff_ms
            comparison["performance"]["duration_diff_percent"] = diff_percent
        
        # Step count comparison
        step_diff = len(replay.replayed_steps) - len(original.steps)
        comparison["step_comparison"]["step_diff"] = step_diff
        
        # Response similarity (basic comparison)
        if original.final_response and replay.final_response:
            original_response = json.dumps(original.final_response, sort_keys=True)
            replay_response = json.dumps(replay.final_response, sort_keys=True)
            
            if original_response == replay_response:
                comparison["response_similarity"] = 1.0
            else:
                # Simple similarity metric
                original_hash = hashlib.md5(original_response.encode()).hexdigest()
                replay_hash = hashlib.md5(replay_response.encode()).hexdigest()
                comparison["response_similarity"] = 0.0 if original_hash != replay_hash else 1.0
        
        return comparison
    
    def cleanup_old_recordings(self, max_age_days: int = None):
        """Public method for cleaning up old recordings."""
        import asyncio
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._cleanup_old_recordings())
        loop.close()

    async def _cleanup_old_recordings(self):
        """Clean up old recordings to prevent storage overflow."""
        try:
            current_time = time.time()
            cutoff_time = current_time - (self.auto_cleanup_days * 24 * 3600)
            
            deleted_count = 0
            for filepath in self.storage_path.glob("rec*.json"):
                # Extract timestamp from filename
                try:
                    timestamp_str = filepath.stem.split('_')[-1]
                    file_timestamp = float(timestamp_str)
                    
                    if file_timestamp < cutoff_time:
                        filepath.unlink()
                        deleted_count += 1
                        
                except (ValueError, IndexError):
                    # Skip files with invalid naming
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old recordings")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global instance
replay_harness = QueryReplayHarness()
