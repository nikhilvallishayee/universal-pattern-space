"""
Enhanced Self-Monitoring Module with Autonomous Learning Capabilities.

Extends the existing SelfMonitoringModule with monitoring for:
- Knowledge acquisition processes
- Cognitive streaming performance
- Autonomous learning system health
- Enhanced anomaly detection
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .cognitive_models import (
    AutonomousLearningMetrics, StreamingMetrics, 
    CognitiveEvent, CognitiveEventType, GranularityLevel
)

logger = logging.getLogger(__name__)


@dataclass
class AutonomousLearningHealthMetrics:
    """Health metrics for autonomous learning system."""
    gap_detection_success_rate: float = 0.0
    acquisition_success_rate: float = 0.0
    average_gap_resolution_time: float = 0.0
    active_acquisition_count: int = 0
    failed_acquisitions_24h: int = 0
    knowledge_growth_rate: float = 0.0
    system_confidence_trend: float = 0.0
    
    # Thresholds for health assessment
    healthy_gap_detection_rate: float = 0.8
    healthy_acquisition_rate: float = 0.7
    max_resolution_time: float = 300.0  # 5 minutes
    max_active_acquisitions: int = 10


@dataclass
class CognitiveStreamingHealthMetrics:
    """Health metrics for cognitive streaming system."""
    streaming_uptime: float = 0.0
    average_latency_ms: float = 0.0
    connection_stability: float = 0.0
    event_drop_rate: float = 0.0
    buffer_overflow_rate: float = 0.0
    client_satisfaction_score: float = 0.0
    
    # Thresholds for health assessment
    max_acceptable_latency: float = 100.0  # ms
    max_acceptable_drop_rate: float = 0.05  # 5%
    min_stability_score: float = 0.9


class EnhancedSelfMonitoringModule:
    """
    Enhanced self-monitoring module that extends existing capabilities
    with autonomous learning and cognitive streaming monitoring.
    """
    
    def __init__(
        self,
        base_monitoring_module=None,
        enhanced_metacognition_manager=None,
        monitoring_interval: float = 60.0,
        health_check_interval: float = 300.0
    ):
        """
        Initialize the enhanced self-monitoring module.
        
        Args:
            base_monitoring_module: Existing SelfMonitoringModule instance
            enhanced_metacognition_manager: Enhanced metacognition manager
            monitoring_interval: Interval for regular monitoring (seconds)
            health_check_interval: Interval for comprehensive health checks (seconds)
        """
        self.base_monitoring = base_monitoring_module
        self.metacognition_manager = enhanced_metacognition_manager
        self.monitoring_interval = monitoring_interval
        self.health_check_interval = health_check_interval
        
        # Monitoring state
        self.is_monitoring = False
        self.last_health_check = datetime.now()
        
        # Health metrics
        self.autonomous_learning_health = AutonomousLearningHealthMetrics()
        self.cognitive_streaming_health = CognitiveStreamingHealthMetrics()
        
        # Performance tracking
        self.performance_history: Dict[str, List[float]] = {
            'gap_detection_times': [],
            'acquisition_times': [],
            'streaming_latencies': [],
            'connection_counts': []
        }
        
        # Anomaly detection
        self.anomaly_thresholds = {
            'gap_detection_spike': 10.0,  # seconds
            'acquisition_timeout': 600.0,  # 10 minutes
            'streaming_latency_spike': 1000.0,  # ms
            'connection_drop_threshold': 0.5  # 50% drop
        }
        
        self.detected_anomalies: List[Dict[str, Any]] = []
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        logger.info("EnhancedSelfMonitoringModule initialized")
    
    async def start_monitoring(self) -> bool:
        """
        Start enhanced monitoring capabilities.
        
        Returns:
            True if monitoring started successfully
        """
        if self.is_monitoring:
            logger.warning("Enhanced monitoring already running")
            return True
        
        try:
            # Start base monitoring if available
            if self.base_monitoring:
                if hasattr(self.base_monitoring, 'start'):
                    await self.base_monitoring.start()
                elif hasattr(self.base_monitoring, 'start_monitoring'):
                    await self.base_monitoring.start_monitoring()
            
            self.is_monitoring = True
            
            # Start background monitoring tasks
            monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.background_tasks.add(monitoring_task)
            
            health_check_task = asyncio.create_task(self._health_check_loop())
            self.background_tasks.add(health_check_task)
            
            anomaly_detection_task = asyncio.create_task(self._anomaly_detection_loop())
            self.background_tasks.add(anomaly_detection_task)
            
            logger.info("Enhanced self-monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start enhanced monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> None:
        """Stop enhanced monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Stop base monitoring if available
        if self.base_monitoring:
            if hasattr(self.base_monitoring, 'stop'):
                await self.base_monitoring.stop()
            elif hasattr(self.base_monitoring, 'stop_monitoring'):
                await self.base_monitoring.stop_monitoring()
        
        logger.info("Enhanced self-monitoring stopped")
    
    async def get_autonomous_learning_health(self) -> Dict[str, Any]:
        """
        Get health assessment for autonomous learning system.
        
        Returns:
            Dictionary containing health metrics and assessment
        """
        # Update metrics
        await self._update_autonomous_learning_metrics()
        
        # Calculate overall health score
        health_score = self._calculate_autonomous_learning_health_score()
        
        # Determine health status
        if health_score >= 0.8:
            status = "healthy"
        elif health_score >= 0.6:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "metrics": {
                "gap_detection_success_rate": self.autonomous_learning_health.gap_detection_success_rate,
                "acquisition_success_rate": self.autonomous_learning_health.acquisition_success_rate,
                "average_gap_resolution_time": self.autonomous_learning_health.average_gap_resolution_time,
                "active_acquisition_count": self.autonomous_learning_health.active_acquisition_count,
                "failed_acquisitions_24h": self.autonomous_learning_health.failed_acquisitions_24h,
                "knowledge_growth_rate": self.autonomous_learning_health.knowledge_growth_rate,
                "system_confidence_trend": self.autonomous_learning_health.system_confidence_trend
            },
            "recommendations": self._get_autonomous_learning_recommendations(health_score)
        }
    
    async def get_cognitive_streaming_health(self) -> Dict[str, Any]:
        """
        Get health assessment for cognitive streaming system.
        
        Returns:
            Dictionary containing health metrics and assessment
        """
        # Update metrics
        await self._update_cognitive_streaming_metrics()
        
        # Calculate overall health score
        health_score = self._calculate_cognitive_streaming_health_score()
        
        # Determine health status
        if health_score >= 0.8:
            status = "healthy"
        elif health_score >= 0.6:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "metrics": {
                "streaming_uptime": self.cognitive_streaming_health.streaming_uptime,
                "average_latency_ms": self.cognitive_streaming_health.average_latency_ms,
                "connection_stability": self.cognitive_streaming_health.connection_stability,
                "event_drop_rate": self.cognitive_streaming_health.event_drop_rate,
                "buffer_overflow_rate": self.cognitive_streaming_health.buffer_overflow_rate,
                "client_satisfaction_score": self.cognitive_streaming_health.client_satisfaction_score
            },
            "recommendations": self._get_cognitive_streaming_recommendations(health_score)
        }
    
    async def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for all enhanced systems.
        
        Returns:
            Complete health report
        """
        autonomous_health = await self.get_autonomous_learning_health()
        streaming_health = await self.get_cognitive_streaming_health()
        
        # Get base system health if available
        base_health = {}
        if self.base_monitoring:
            if hasattr(self.base_monitoring, 'get_health_report'):
                base_health = await self.base_monitoring.get_health_report()
            elif hasattr(self.base_monitoring, 'get_system_health'):
                base_health = await self.base_monitoring.get_system_health()
        
        # Calculate overall system health
        health_scores = [
            autonomous_health['health_score'],
            streaming_health['health_score']
        ]
        
        if base_health.get('health_score'):
            health_scores.append(base_health['health_score'])
        
        overall_health_score = sum(health_scores) / len(health_scores)
        
        # Determine overall status
        if overall_health_score >= 0.8:
            overall_status = "healthy"
        elif overall_health_score >= 0.6:
            overall_status = "warning"
        else:
            overall_status = "critical"
        
        return {
            "overall_status": overall_status,
            "overall_health_score": overall_health_score,
            "autonomous_learning": autonomous_health,
            "cognitive_streaming": streaming_health,
            "base_system": base_health,
            "anomalies": self.detected_anomalies[-10:],  # Last 10 anomalies
            "performance_trends": self._get_performance_trends(),
            "last_updated": datetime.now().isoformat()
        }
    
    async def detect_performance_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect performance anomalies in enhanced systems.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check gap detection performance
        if self.performance_history['gap_detection_times']:
            recent_times = self.performance_history['gap_detection_times'][-10:]
            avg_time = sum(recent_times) / len(recent_times)
            
            if avg_time > self.anomaly_thresholds['gap_detection_spike']:
                anomalies.append({
                    "type": "gap_detection_slowdown",
                    "severity": "warning",
                    "description": f"Gap detection taking {avg_time:.2f}s (threshold: {self.anomaly_thresholds['gap_detection_spike']}s)",
                    "detected_at": datetime.now().isoformat(),
                    "metric_value": avg_time,
                    "threshold": self.anomaly_thresholds['gap_detection_spike']
                })
        
        # Check acquisition timeouts
        if self.autonomous_learning_health.average_gap_resolution_time > self.anomaly_thresholds['acquisition_timeout']:
            anomalies.append({
                "type": "acquisition_timeout",
                "severity": "critical",
                "description": f"Knowledge acquisition taking {self.autonomous_learning_health.average_gap_resolution_time:.2f}s",
                "detected_at": datetime.now().isoformat(),
                "metric_value": self.autonomous_learning_health.average_gap_resolution_time,
                "threshold": self.anomaly_thresholds['acquisition_timeout']
            })
        
        # Check streaming latency spikes
        if self.performance_history['streaming_latencies']:
            recent_latencies = self.performance_history['streaming_latencies'][-10:]
            avg_latency = sum(recent_latencies) / len(recent_latencies)
            
            if avg_latency > self.anomaly_thresholds['streaming_latency_spike']:
                anomalies.append({
                    "type": "streaming_latency_spike",
                    "severity": "warning",
                    "description": f"Streaming latency at {avg_latency:.2f}ms (threshold: {self.anomaly_thresholds['streaming_latency_spike']}ms)",
                    "detected_at": datetime.now().isoformat(),
                    "metric_value": avg_latency,
                    "threshold": self.anomaly_thresholds['streaming_latency_spike']
                })
        
        # Check connection drops
        if len(self.performance_history['connection_counts']) >= 2:
            recent_counts = self.performance_history['connection_counts'][-5:]
            if len(recent_counts) >= 2:
                current_count = recent_counts[-1]
                previous_avg = sum(recent_counts[:-1]) / (len(recent_counts) - 1)
                
                if previous_avg > 0:
                    drop_ratio = (previous_avg - current_count) / previous_avg
                    
                    if drop_ratio > self.anomaly_thresholds['connection_drop_threshold']:
                        anomalies.append({
                            "type": "connection_drop",
                            "severity": "warning",
                            "description": f"Connection count dropped by {drop_ratio:.1%}",
                            "detected_at": datetime.now().isoformat(),
                            "metric_value": drop_ratio,
                            "threshold": self.anomaly_thresholds['connection_drop_threshold']
                        })
        
        # Store new anomalies
        self.detected_anomalies.extend(anomalies)
        
        # Keep only recent anomalies (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.detected_anomalies = [
            anomaly for anomaly in self.detected_anomalies
            if datetime.fromisoformat(anomaly['detected_at']) > cutoff_time
        ]
        
        return anomalies
    
    # Private methods
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Update performance metrics
                await self._collect_performance_metrics()
                
                # Update health metrics
                await self._update_autonomous_learning_metrics()
                await self._update_cognitive_streaming_metrics()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _health_check_loop(self) -> None:
        """Comprehensive health check loop."""
        while self.is_monitoring:
            try:
                # Perform comprehensive health check
                await self._perform_comprehensive_health_check()
                
                self.last_health_check = datetime.now()
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _anomaly_detection_loop(self) -> None:
        """Anomaly detection loop."""
        while self.is_monitoring:
            try:
                # Detect anomalies
                anomalies = await self.detect_performance_anomalies()
                
                # Log critical anomalies
                for anomaly in anomalies:
                    if anomaly['severity'] == 'critical':
                        logger.error(f"Critical anomaly detected: {anomaly['description']}")
                    elif anomaly['severity'] == 'warning':
                        logger.warning(f"Performance anomaly detected: {anomaly['description']}")
                
                await asyncio.sleep(60.0)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(60.0)
    
    async def _collect_performance_metrics(self) -> None:
        """Collect performance metrics from various sources."""
        try:
            if not self.metacognition_manager:
                return
            
            # Collect streaming metrics
            if hasattr(self.metacognition_manager, 'stream_coordinator'):
                coordinator = self.metacognition_manager.stream_coordinator
                
                if hasattr(coordinator, 'get_streaming_metrics'):
                    streaming_metrics = await coordinator.get_streaming_metrics()
                    
                    # Extract latency data
                    if 'average_latency_ms' in streaming_metrics:
                        self.performance_history['streaming_latencies'].append(
                            streaming_metrics['average_latency_ms']
                        )
                    
                    # Extract connection count
                    if 'connected_clients' in streaming_metrics:
                        self.performance_history['connection_counts'].append(
                            streaming_metrics['connected_clients']
                        )
            
            # Limit history size
            max_history_size = 1000
            for key in self.performance_history:
                if len(self.performance_history[key]) > max_history_size:
                    self.performance_history[key] = self.performance_history[key][-max_history_size:]
                    
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")
    
    async def _update_autonomous_learning_metrics(self) -> None:
        """Update autonomous learning health metrics."""
        try:
            if not self.metacognition_manager:
                return
            
            # Get autonomous learning statistics
            if hasattr(self.metacognition_manager, 'autonomous_knowledge_acquisition'):
                acquisition_engine = self.metacognition_manager.autonomous_knowledge_acquisition
                
                if hasattr(acquisition_engine, 'get_strategy_statistics'):
                    stats = await acquisition_engine.get_strategy_statistics()
                    
                    # Update success rates
                    self.autonomous_learning_health.acquisition_success_rate = stats.get(
                        'overall_success_rate', 0.0
                    )
            
            # Get gap detection statistics
            if hasattr(self.metacognition_manager, 'knowledge_gap_detector'):
                gap_detector = self.metacognition_manager.knowledge_gap_detector
                
                if hasattr(gap_detector, 'get_gap_statistics'):
                    gap_stats = await gap_detector.get_gap_statistics()
                    
                    # Update gap detection rate
                    self.autonomous_learning_health.gap_detection_success_rate = gap_stats.get(
                        'detection_rate', 0.0
                    )
            
            # Update active acquisition count
            if hasattr(self.metacognition_manager, 'active_acquisitions'):
                self.autonomous_learning_health.active_acquisition_count = len(
                    self.metacognition_manager.active_acquisitions
                )
            
            # Calculate average resolution time from performance history
            if self.performance_history['gap_detection_times']:
                self.autonomous_learning_health.average_gap_resolution_time = (
                    sum(self.performance_history['gap_detection_times'][-10:]) /
                    len(self.performance_history['gap_detection_times'][-10:])
                )
                
        except Exception as e:
            logger.error(f"Error updating autonomous learning metrics: {e}")
    
    async def _update_cognitive_streaming_metrics(self) -> None:
        """Update cognitive streaming health metrics."""
        try:
            if not self.metacognition_manager:
                return
            
            # Get streaming metrics
            if hasattr(self.metacognition_manager, 'stream_coordinator'):
                coordinator = self.metacognition_manager.stream_coordinator
                
                if hasattr(coordinator, 'get_streaming_metrics'):
                    streaming_metrics = await coordinator.get_streaming_metrics()
                    
                    # Update metrics
                    self.cognitive_streaming_health.average_latency_ms = streaming_metrics.get(
                        'average_latency_ms', 0.0
                    )
                    
                    # Calculate drop rate
                    total_events = streaming_metrics.get('total_events_sent', 0)
                    dropped_events = streaming_metrics.get('total_events_dropped', 0)
                    
                    if total_events > 0:
                        self.cognitive_streaming_health.event_drop_rate = (
                            dropped_events / total_events
                        )
                    
                    # Calculate connection stability (simplified)
                    connection_errors = streaming_metrics.get('connection_errors', 0)
                    if total_events > 0:
                        self.cognitive_streaming_health.connection_stability = max(
                            0.0, 1.0 - (connection_errors / total_events)
                        )
                    
        except Exception as e:
            logger.error(f"Error updating cognitive streaming metrics: {e}")
    
    def _calculate_autonomous_learning_health_score(self) -> float:
        """Calculate overall health score for autonomous learning."""
        scores = []
        
        # Gap detection success rate (weight: 0.2)
        if self.autonomous_learning_health.gap_detection_success_rate >= self.autonomous_learning_health.healthy_gap_detection_rate:
            scores.append(1.0 * 0.2)
        else:
            ratio = self.autonomous_learning_health.gap_detection_success_rate / self.autonomous_learning_health.healthy_gap_detection_rate
            scores.append(ratio * 0.2)
        
        # Acquisition success rate (weight: 0.3)
        if self.autonomous_learning_health.acquisition_success_rate >= self.autonomous_learning_health.healthy_acquisition_rate:
            scores.append(1.0 * 0.3)
        else:
            ratio = self.autonomous_learning_health.acquisition_success_rate / self.autonomous_learning_health.healthy_acquisition_rate
            scores.append(ratio * 0.3)
        
        # Resolution time (weight: 0.2)
        if self.autonomous_learning_health.average_gap_resolution_time <= self.autonomous_learning_health.max_resolution_time:
            scores.append(1.0 * 0.2)
        else:
            ratio = self.autonomous_learning_health.max_resolution_time / self.autonomous_learning_health.average_gap_resolution_time
            scores.append(max(0.0, ratio) * 0.2)
        
        # Active acquisition load (weight: 0.1)
        if self.autonomous_learning_health.active_acquisition_count <= self.autonomous_learning_health.max_active_acquisitions:
            scores.append(1.0 * 0.1)
        else:
            ratio = self.autonomous_learning_health.max_active_acquisitions / self.autonomous_learning_health.active_acquisition_count
            scores.append(max(0.0, ratio) * 0.1)
        
        # Knowledge growth rate (weight: 0.2)
        # Simplified: assume positive growth is good
        growth_score = min(1.0, max(0.0, self.autonomous_learning_health.knowledge_growth_rate))
        scores.append(growth_score * 0.2)
        
        return sum(scores)
    
    def _calculate_cognitive_streaming_health_score(self) -> float:
        """Calculate overall health score for cognitive streaming."""
        scores = []
        
        # Latency score (weight: 0.3)
        if self.cognitive_streaming_health.average_latency_ms <= self.cognitive_streaming_health.max_acceptable_latency:
            scores.append(1.0 * 0.3)
        else:
            ratio = self.cognitive_streaming_health.max_acceptable_latency / self.cognitive_streaming_health.average_latency_ms
            scores.append(max(0.0, ratio) * 0.3)
        
        # Drop rate score (weight: 0.3)
        if self.cognitive_streaming_health.event_drop_rate <= self.cognitive_streaming_health.max_acceptable_drop_rate:
            scores.append(1.0 * 0.3)
        else:
            ratio = 1.0 - (self.cognitive_streaming_health.event_drop_rate / (self.cognitive_streaming_health.max_acceptable_drop_rate * 2))
            scores.append(max(0.0, ratio) * 0.3)
        
        # Connection stability score (weight: 0.4)
        scores.append(self.cognitive_streaming_health.connection_stability * 0.4)
        
        return sum(scores)
    
    def _get_autonomous_learning_recommendations(self, health_score: float) -> List[str]:
        """Get recommendations for autonomous learning system."""
        recommendations = []
        
        if health_score < 0.6:
            recommendations.append("Consider reducing autonomous learning aggressiveness")
            recommendations.append("Check knowledge acquisition timeout settings")
        
        if self.autonomous_learning_health.acquisition_success_rate < 0.5:
            recommendations.append("Review and tune acquisition strategies")
            recommendations.append("Consider disabling underperforming strategies")
        
        if self.autonomous_learning_health.active_acquisition_count > self.autonomous_learning_health.max_active_acquisitions:
            recommendations.append("Reduce maximum concurrent acquisitions")
        
        if not recommendations:
            recommendations.append("Autonomous learning system is performing well")
        
        return recommendations
    
    def _get_cognitive_streaming_recommendations(self, health_score: float) -> List[str]:
        """Get recommendations for cognitive streaming system."""
        recommendations = []
        
        if health_score < 0.6:
            recommendations.append("Consider reducing streaming granularity")
            recommendations.append("Check WebSocket connection stability")
        
        if self.cognitive_streaming_health.average_latency_ms > self.cognitive_streaming_health.max_acceptable_latency:
            recommendations.append("Optimize event serialization")
            recommendations.append("Consider reducing event rate limits")
        
        if self.cognitive_streaming_health.event_drop_rate > self.cognitive_streaming_health.max_acceptable_drop_rate:
            recommendations.append("Increase buffer size")
            recommendations.append("Reduce maximum event rate")
        
        if not recommendations:
            recommendations.append("Cognitive streaming system is performing well")
        
        return recommendations
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Get performance trend analysis."""
        trends = {}
        
        for metric_name, history in self.performance_history.items():
            if len(history) >= 10:
                recent = history[-10:]
                older = history[-20:-10] if len(history) >= 20 else []
                
                if older:
                    recent_avg = sum(recent) / len(recent)
                    older_avg = sum(older) / len(older)
                    
                    if older_avg > 0:
                        trend = (recent_avg - older_avg) / older_avg
                        trends[metric_name] = {
                            "trend_percentage": trend * 100,
                            "direction": "improving" if trend < 0 else "declining" if trend > 0 else "stable",
                            "recent_average": recent_avg,
                            "previous_average": older_avg
                        }
        
        return trends
    
    async def _perform_comprehensive_health_check(self) -> None:
        """Perform comprehensive health check of all systems."""
        try:
            # Update all metrics
            await self._update_autonomous_learning_metrics()
            await self._update_cognitive_streaming_metrics()
            
            # Check for anomalies
            anomalies = await self.detect_performance_anomalies()
            
            # Log health status
            autonomous_health = await self.get_autonomous_learning_health()
            streaming_health = await self.get_cognitive_streaming_health()
            
            logger.info(f"Health check complete - Autonomous: {autonomous_health['status']}, "
                       f"Streaming: {streaming_health['status']}, "
                       f"Anomalies: {len(anomalies)}")
            
        except Exception as e:
            logger.error(f"Error in comprehensive health check: {e}")
