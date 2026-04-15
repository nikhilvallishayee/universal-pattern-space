#!/usr/bin/env python
# coding: utf-8

"""
GödelOS Consciousness Demo

This script demonstrates how GödelOS manifests "consciousness-like" capabilities
through the integration of its learning and monitoring systems. It showcases:

1. Self-monitoring capabilities
2. Adaptive learning based on monitoring feedback
3. Metacognitive processes
4. System health awareness and self-diagnosis
5. Performance optimization through experience
"""

import sys
import os
import logging
import time
import random
import asyncio
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Core KR and Inference Engine components
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.inference_engine.coordinator import InferenceCoordinator

# Import Learning System components
from godelOS.unified_agent_core.learning.manager import UnifiedLearningManager
from godelOS.unified_agent_core.learning.interfaces import (
    UnifiedExperience, LearningResult, StrategyOptimization
)

# Import Monitoring System components
from godelOS.unified_agent_core.monitoring.system import UnifiedMonitoringSystem
from godelOS.unified_agent_core.monitoring.performance_monitor import PerformanceMonitor
from godelOS.unified_agent_core.monitoring.health_checker import HealthChecker, SystemHealthStatus
from godelOS.unified_agent_core.monitoring.diagnostic_tools import DiagnosticTools, DiagnosticResult
from godelOS.unified_agent_core.monitoring.telemetry_collector import TelemetryCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConsciousnessDemo:
    """A demonstration of GödelOS consciousness-like capabilities."""
    
    def __init__(self):
        """Initialize the Consciousness Demo."""
        self.setup_core_components()
        # We'll initialize learning and monitoring systems in the main function
        self.learning_manager = None
        self.monitoring_system = None
        self.performance_monitor = None
        self.health_checker = None
        self.diagnostic_tools = None
        self.telemetry_collector = None
        
    def setup_core_components(self):
        """Set up the core components (KR system and inference engine)."""
        print("\n=== Setting up Core Components ===")
        
        # Initialize the type system
        self.type_system = TypeSystemManager()
        
        # Initialize the unification engine
        from godelOS.core_kr.unification_engine.engine import UnificationEngine
        self.unification_engine = UnificationEngine(self.type_system)
        
        # Initialize knowledge store
        self.ksi = KnowledgeStoreInterface(self.type_system)
        self.ksi.create_context("FACTS", context_type="facts")
        self.ksi.create_context("RULES", context_type="rules")
        self.ksi.create_context("LEARNED", context_type="learned")
        
        # Initialize inference engine
        self.resolution_prover = ResolutionProver(self.ksi, self.unification_engine)
        provers = {"resolution_prover": self.resolution_prover}
        self.coordinator = InferenceCoordinator(self.ksi, provers)
        
        print("Core components initialized successfully.")
        
    async def setup_learning_system(self):
        """Set up the learning system components."""
        print("\n=== Setting up Learning System ===")
        
        # Configuration for learning components
        learning_config = {
            "interaction_learning_rate": 0.05,
            "cognitive_learning_rate": 0.1,
            "performance_history_size": 100,
            "optimization_interval": 10  # Optimize after every 10 experiences
        }
        
        # Initialize the Unified Learning Manager
        self.learning_manager = UnifiedLearningManager(config=learning_config)
        
        # Initialize the learning system
        await self.learning_manager.initialize()
        
        # Start the learning system
        await self.learning_manager.start()
        
        print("Learning system initialized and started.")
        
    async def setup_monitoring_system(self):
        """Set up the monitoring system components."""
        print("\n=== Setting up Monitoring System ===")
        
        # Configuration for monitoring components
        monitoring_config = {
            "performance_sampling_interval": 1.0,  # seconds
            "health_check_interval": 5.0,  # seconds
            "telemetry_collection_interval": 2.0,  # seconds
            "error_log_dir": "logs",
            "history_size": 100
        }
        
        # Initialize the Performance Monitor
        self.performance_monitor = PerformanceMonitor(config={
            "sampling_interval": monitoring_config["performance_sampling_interval"],
            "history_size": monitoring_config["history_size"]
        })
        
        # Initialize the Health Checker
        self.health_checker = HealthChecker(config={
            "check_interval": monitoring_config["health_check_interval"],
            "history_size": monitoring_config["history_size"]
        })
        
        # Initialize the Diagnostic Tools
        self.diagnostic_tools = DiagnosticTools(config={
            "error_log_dir": monitoring_config["error_log_dir"],
            "max_log_size": 10 * 1024 * 1024,  # 10 MB
            "max_log_files": 5
        })
        
        # Initialize the Telemetry Collector
        self.telemetry_collector = TelemetryCollector(config={
            "collection_interval": monitoring_config["telemetry_collection_interval"],
            "history_size": monitoring_config["history_size"]
        })
        
        # Initialize the Unified Monitoring System with component configs
        monitoring_system_config = {
            "performance_monitor": {
                "sampling_interval": monitoring_config["performance_sampling_interval"],
                "history_size": monitoring_config["history_size"]
            },
            "health_checker": {
                "check_interval": monitoring_config["health_check_interval"],
                "history_size": monitoring_config["history_size"]
            },
            "diagnostic_tools": {
                "error_log_dir": monitoring_config["error_log_dir"],
                "max_log_size": 10 * 1024 * 1024,
                "max_log_files": 5
            },
            "telemetry_collector": {
                "collection_interval": monitoring_config["telemetry_collection_interval"],
                "history_size": monitoring_config["history_size"]
            }
        }
        
        self.monitoring_system = UnifiedMonitoringSystem(config=monitoring_system_config)
        
        # Initialize and start the monitoring system
        await self.monitoring_system.initialize()
        await self.monitoring_system.start()
        
        # Register health checks and diagnostics
        await self.register_monitoring_components()
        
        print("Monitoring system initialized and started.")
        
    async def register_monitoring_components(self):
        """Register health checks, diagnostics, and telemetry collectors."""
        
        # Initialize the diagnostic tools
        await self.diagnostic_tools.initialize()
        
        # Define health check for the learning system
        async def check_learning_system_health():
            return SystemHealthStatus.HEALTHY.value if self.learning_manager.is_running else SystemHealthStatus.DEGRADED.value
        
        # Define diagnostic test for the inference engine
        async def diagnose_inference_engine():
            return DiagnosticResult(
                success=True,
                component="inference_engine",
                test_name="functionality_check",
                message="Inference engine functioning correctly"
            )
        
        # Define telemetry collector for the learning system
        async def collect_learning_telemetry():
            return {
                "experiences_processed": random.randint(5, 50),
                "learning_rate": 0.05,
                "strategy_optimizations": random.randint(0, 5)
            }
        
        # Register the components
        await self.health_checker.register_health_check("learning_system", check_learning_system_health)
        await self.diagnostic_tools.register_diagnostic("inference_engine", "functionality_check", diagnose_inference_engine)
        await self.telemetry_collector.register_collector("learning_system", "metrics", collect_learning_telemetry)
        
    async def demonstrate_consciousness(self):
        """Demonstrate consciousness-like capabilities."""
        print("\n" + "="*60)
        print("GödelOS Consciousness Demo")
        print("="*60)
        
        # Demonstrate self-monitoring
        await self.demonstrate_self_monitoring()
        
        # Demonstrate adaptive learning
        await self.demonstrate_adaptive_learning()
        
        # Demonstrate metacognition
        await self.demonstrate_metacognition()
        
        # Clean up
        await self.cleanup()
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("="*60)
        
    async def demonstrate_self_monitoring(self):
        """Demonstrate self-monitoring capabilities."""
        print("\n=== Demonstrating Self-Monitoring Capabilities ===")
        
        # Get current system health
        health = await self.health_checker.check()
        print(f"Overall system health: {health.status}")
        
        # Get performance metrics
        metrics = await self.performance_monitor.get_metrics()
        print("Performance metrics:", metrics)
        
        # Run diagnostics
        diagnostic_result = await self.diagnostic_tools.run_diagnostic(
            "inference_engine", "functionality_check"
        )
        print(f"Diagnostic result: {diagnostic_result.message}")
        
        # Get telemetry data
        telemetry = await self.telemetry_collector.get_telemetry()
        print("Telemetry data:", telemetry)
        
    async def demonstrate_adaptive_learning(self):
        """Demonstrate adaptive learning based on monitoring feedback."""
        print("\n=== Demonstrating Adaptive Learning ===")
        
        # Create and process experiences
        for i in range(3):
            # Create an interaction experience
            interaction_exp = UnifiedExperience(
                id=f"interaction_{i}",
                type="interaction",
                content={
                    "input": {"query": f"Query {i}"},
                    "output": {"result": f"Result {i}"}
                },
                metadata={
                    "strategy": f"Strategy{i+1}",
                    "response_time": random.uniform(0.5, 2.0),
                    "success": random.random() > 0.3
                }
            )
            
            # Learn from the interaction experience
            await self.learning_manager.learn_from_experience(interaction_exp)
            
            # Create a cognitive experience
            cognitive_exp = UnifiedExperience(
                id=f"process_{i}",
                type="cognitive",
                content={
                    "input_state": {"problem": f"Problem{i}"},
                    "output_state": {"solution": f"Solution{i}"},
                    "reasoning_steps": [{"step": 1, "action": "analyze", "result": "Analysis complete"}]
                },
                metadata={"difficulty": i+1}
            )
            
            # Learn from the cognitive experience
            await self.learning_manager.learn_from_experience(cognitive_exp)
            
            # Update strategy performance
            await self.learning_manager.strategy_optimizer.update_strategy_performance(
                strategy_name=f"Strategy{i+1}",
                metrics={"success_rate": random.uniform(0.5, 1.0), "response_time": random.uniform(0.5, 2.0)}
            )
            
        # Optimize strategies based on experiences
        print("\nOptimizing strategies based on experiences...")
        optimization_result = await self.learning_manager.strategy_optimizer.optimize()
        print(f"Optimization result: {optimization_result}")
        
    async def demonstrate_metacognition(self):
        """Demonstrate metacognitive processes."""
        print("\n=== Demonstrating Metacognitive Processes ===")
        
        # Simulate metacognitive reflection
        print("\nPerforming metacognitive reflection on problem-solving strategies...")
        
        strategies = ["Strategy1", "Strategy2", "Strategy3"]
        for strategy in strategies:
            # Get strategy data from the optimizer
            strategy_data = await self.learning_manager.strategy_optimizer.get_strategy(strategy)
            if strategy_data:
                print(f"\nStrategy: {strategy}")
                print(f"Performance: {strategy_data.get('performance', {})}")
                print(f"Parameters: {strategy_data.get('parameters', {})}")
        
        # Simulate self-diagnosis
        print("\nPerforming system self-diagnosis...")
        
        # Log an error to test error handling
        error = Exception("Test error for self-diagnosis")
        await self.diagnostic_tools.log_error(error)
        
        # Get error logs
        error_logs = await self.diagnostic_tools.get_error_logs()
        print(f"Found {len(error_logs)} error logs")
        
        # Simulate system adaptation
        print("\nAdapting system based on self-knowledge...")
        print("1. Analyzing performance patterns")
        print("2. Identifying improvement opportunities")
        print("3. Adjusting learning parameters")
        print("4. Optimizing resource allocation")
        
    async def cleanup(self):
        """Clean up and shut down systems."""
        print("\n=== Cleaning Up ===")
        
        # Stop the learning system
        await self.learning_manager.stop()
        
        # Stop the monitoring system
        await self.monitoring_system.stop()
        
        print("Learning and monitoring systems stopped.")

async def main():
    """Run the consciousness demo."""
    # Create the demo instance
    demo = ConsciousnessDemo()
    
    # Initialize the learning system
    print("\nInitializing learning system...")
    await demo.setup_learning_system()
    
    # Initialize the monitoring system
    print("\nInitializing monitoring system...")
    await demo.setup_monitoring_system()
    
    # Run the demonstration
    await demo.demonstrate_consciousness()

if __name__ == "__main__":
    asyncio.run(main())