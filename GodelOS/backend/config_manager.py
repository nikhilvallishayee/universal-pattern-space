"""
Configuration management for enhanced metacognition features.

This module handles loading and managing configuration for:
- Cognitive streaming
- Autonomous learning
- Knowledge acquisition
- Health monitoring
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CognitiveStreamingConfig:
    """Configuration for cognitive streaming."""
    enabled: bool = True
    default_granularity: str = "standard"
    max_event_rate: int = 100
    buffer_size: int = 1000
    websocket_ping_interval: int = 30
    max_connections: int = 50
    event_types: list = field(default_factory=lambda: [
        "reasoning", "knowledge_gap", "acquisition", "reflection", "learning", "synthesis"
    ])
    granularity_levels: Dict[str, list] = field(default_factory=dict)

@dataclass
class AutonomousLearningConfig:
    """Configuration for autonomous learning."""
    enabled: bool = True
    gap_detection_interval: int = 300
    confidence_threshold: float = 0.7
    auto_approval_threshold: float = 0.8
    max_concurrent_acquisitions: int = 3
    learning_rate: float = 1.0
    gap_detection_sensitivity: str = "medium"
    max_acquisition_time: int = 300
    max_memory_usage: int = 512
    strategies: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class KnowledgeAcquisitionConfig:
    """Configuration for knowledge acquisition."""
    plan_expiry_time: int = 3600
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    confidence_validation: bool = True
    source_verification: bool = True
    consistency_checking: bool = True
    batch_processing: bool = True
    caching_enabled: bool = True
    cache_expiry: int = 86400

@dataclass
class GapDetectionConfig:
    """Configuration for gap detection."""
    query_analysis: Dict[str, Any] = field(default_factory=dict)
    knowledge_graph_analysis: Dict[str, Any] = field(default_factory=dict)
    periodic_analysis: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthMonitoringConfig:
    """Configuration for health monitoring."""
    enabled: bool = True
    check_interval: int = 60
    component_timeouts: Dict[str, int] = field(default_factory=dict)
    response_time_threshold: int = 1000
    error_rate_threshold: float = 0.05
    memory_usage_threshold: float = 0.8
    metrics_retention_period: int = 604800

@dataclass
class SecurityConfig:
    """Configuration for security."""
    require_authentication: bool = False
    api_rate_limiting: Dict[str, Any] = field(default_factory=dict)
    log_sensitive_data: bool = False
    anonymize_user_queries: bool = True
    data_retention_period: int = 2592000

@dataclass
class IntegrationConfig:
    """Configuration for system integration."""
    backward_compatibility: bool = True
    legacy_api_support: bool = True
    graceful_degradation: bool = True
    features: Dict[str, bool] = field(default_factory=dict)

@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    log_cognitive_events: bool = True
    log_acquisition_details: bool = True
    log_performance_metrics: bool = True
    max_log_size: int = 10485760
    backup_count: int = 5
    component_log_levels: Dict[str, str] = field(default_factory=dict)

@dataclass
class DevelopmentConfig:
    """Configuration for development and testing."""
    debug_mode: bool = False
    mock_external_apis: bool = False
    test_data_generation: bool = False
    performance_profiling: bool = False
    test_mode_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

@dataclass
class EnhancedMetacognitionConfig:
    """Main configuration container for enhanced metacognition."""
    cognitive_streaming: CognitiveStreamingConfig = field(default_factory=CognitiveStreamingConfig)
    autonomous_learning: AutonomousLearningConfig = field(default_factory=AutonomousLearningConfig)
    knowledge_acquisition: KnowledgeAcquisitionConfig = field(default_factory=KnowledgeAcquisitionConfig)
    gap_detection: GapDetectionConfig = field(default_factory=GapDetectionConfig)
    health_monitoring: HealthMonitoringConfig = field(default_factory=HealthMonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)

class ConfigurationManager:
    """Manages configuration loading and access for enhanced metacognition."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[EnhancedMetacognitionConfig] = None
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Try environment variable first
        env_path = os.getenv("ENHANCED_METACOGNITION_CONFIG")
        if env_path and os.path.exists(env_path):
            return env_path
        
        # Default to config file in backend/config/
        backend_dir = Path(__file__).parent
        config_file = backend_dir / "config" / "enhanced_metacognition_config.yaml"
        return str(config_file)
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Configuration file not found: {self.config_path}")
                logger.info("Using default configuration")
                self.config = EnhancedMetacognitionConfig()
                return
            
            with open(self.config_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            if not yaml_data:
                logger.warning("Empty configuration file, using defaults")
                self.config = EnhancedMetacognitionConfig()
                return
            
            # Parse configuration sections
            self.config = EnhancedMetacognitionConfig(
                cognitive_streaming=self._parse_cognitive_streaming(yaml_data.get('cognitive_streaming', {})),
                autonomous_learning=self._parse_autonomous_learning(yaml_data.get('autonomous_learning', {})),
                knowledge_acquisition=self._parse_knowledge_acquisition(yaml_data.get('knowledge_acquisition', {})),
                gap_detection=self._parse_gap_detection(yaml_data.get('gap_detection', {})),
                health_monitoring=self._parse_health_monitoring(yaml_data.get('health_monitoring', {})),
                security=self._parse_security(yaml_data.get('security', {})),
                integration=self._parse_integration(yaml_data.get('integration', {})),
                logging=self._parse_logging(yaml_data.get('logging', {})),
                development=self._parse_development(yaml_data.get('development', {}))
            )
            
            logger.info(f"Configuration loaded successfully from: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
            self.config = EnhancedMetacognitionConfig()
    
    def _parse_cognitive_streaming(self, data: Dict[str, Any]) -> CognitiveStreamingConfig:
        """Parse cognitive streaming configuration."""
        return CognitiveStreamingConfig(
            enabled=data.get('enabled', True),
            default_granularity=data.get('default_granularity', 'standard'),
            max_event_rate=data.get('max_event_rate', 100),
            buffer_size=data.get('buffer_size', 1000),
            websocket_ping_interval=data.get('websocket_ping_interval', 30),
            max_connections=data.get('max_connections', 50),
            event_types=data.get('event_types', [
                "reasoning", "knowledge_gap", "acquisition", "reflection", "learning", "synthesis"
            ]),
            granularity_levels=data.get('granularity_levels', {})
        )
    
    def _parse_autonomous_learning(self, data: Dict[str, Any]) -> AutonomousLearningConfig:
        """Parse autonomous learning configuration."""
        return AutonomousLearningConfig(
            enabled=data.get('enabled', True),
            gap_detection_interval=data.get('gap_detection_interval', 300),
            confidence_threshold=data.get('confidence_threshold', 0.7),
            auto_approval_threshold=data.get('auto_approval_threshold', 0.8),
            max_concurrent_acquisitions=data.get('max_concurrent_acquisitions', 3),
            learning_rate=data.get('learning_rate', 1.0),
            gap_detection_sensitivity=data.get('gap_detection_sensitivity', 'medium'),
            max_acquisition_time=data.get('max_acquisition_time', 300),
            max_memory_usage=data.get('max_memory_usage', 512),
            strategies=data.get('strategies', {})
        )
    
    def _parse_knowledge_acquisition(self, data: Dict[str, Any]) -> KnowledgeAcquisitionConfig:
        """Parse knowledge acquisition configuration."""
        return KnowledgeAcquisitionConfig(
            plan_expiry_time=data.get('plan_expiry_time', 3600),
            max_retries=data.get('max_retries', 3),
            backoff_multiplier=data.get('backoff_multiplier', 2.0),
            confidence_validation=data.get('confidence_validation', True),
            source_verification=data.get('source_verification', True),
            consistency_checking=data.get('consistency_checking', True),
            batch_processing=data.get('batch_processing', True),
            caching_enabled=data.get('caching_enabled', True),
            cache_expiry=data.get('cache_expiry', 86400)
        )
    
    def _parse_gap_detection(self, data: Dict[str, Any]) -> GapDetectionConfig:
        """Parse gap detection configuration."""
        return GapDetectionConfig(
            query_analysis=data.get('query_analysis', {}),
            knowledge_graph_analysis=data.get('knowledge_graph_analysis', {}),
            periodic_analysis=data.get('periodic_analysis', {})
        )
    
    def _parse_health_monitoring(self, data: Dict[str, Any]) -> HealthMonitoringConfig:
        """Parse health monitoring configuration."""
        return HealthMonitoringConfig(
            enabled=data.get('enabled', True),
            check_interval=data.get('check_interval', 60),
            component_timeouts=data.get('component_timeouts', {}),
            response_time_threshold=data.get('response_time_threshold', 1000),
            error_rate_threshold=data.get('error_rate_threshold', 0.05),
            memory_usage_threshold=data.get('memory_usage_threshold', 0.8),
            metrics_retention_period=data.get('metrics_retention_period', 604800)
        )
    
    def _parse_security(self, data: Dict[str, Any]) -> SecurityConfig:
        """Parse security configuration."""
        return SecurityConfig(
            require_authentication=data.get('require_authentication', False),
            api_rate_limiting=data.get('api_rate_limiting', {}),
            log_sensitive_data=data.get('log_sensitive_data', False),
            anonymize_user_queries=data.get('anonymize_user_queries', True),
            data_retention_period=data.get('data_retention_period', 2592000)
        )
    
    def _parse_integration(self, data: Dict[str, Any]) -> IntegrationConfig:
        """Parse integration configuration."""
        return IntegrationConfig(
            backward_compatibility=data.get('backward_compatibility', True),
            legacy_api_support=data.get('legacy_api_support', True),
            graceful_degradation=data.get('graceful_degradation', True),
            features=data.get('features', {})
        )
    
    def _parse_logging(self, data: Dict[str, Any]) -> LoggingConfig:
        """Parse logging configuration."""
        return LoggingConfig(
            level=data.get('level', 'INFO'),
            log_cognitive_events=data.get('log_cognitive_events', True),
            log_acquisition_details=data.get('log_acquisition_details', True),
            log_performance_metrics=data.get('log_performance_metrics', True),
            max_log_size=data.get('max_log_size', 10485760),
            backup_count=data.get('backup_count', 5),
            component_log_levels=data.get('component_log_levels', {})
        )
    
    def _parse_development(self, data: Dict[str, Any]) -> DevelopmentConfig:
        """Parse development configuration."""
        return DevelopmentConfig(
            debug_mode=data.get('debug_mode', False),
            mock_external_apis=data.get('mock_external_apis', False),
            test_data_generation=data.get('test_data_generation', False),
            performance_profiling=data.get('performance_profiling', False),
            test_mode_overrides=data.get('test_mode_overrides', {})
        )
    
    def get_config(self) -> EnhancedMetacognitionConfig:
        """Get the current configuration."""
        if self.config is None:
            self._load_config()
        return self.config
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled."""
        if not self.config:
            return False
        return self.config.integration.features.get(feature_name, False)

# Global configuration instance
config_manager = ConfigurationManager()

def get_config() -> EnhancedMetacognitionConfig:
    """Get the global configuration instance."""
    return config_manager.get_config()

def reload_config():
    """Reload the global configuration."""
    config_manager.reload_config()

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled in the global configuration."""
    return config_manager.is_feature_enabled(feature_name)
