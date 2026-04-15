#!/usr/bin/env python3
"""
Adaptive Coordination Policy Learning System

This module implements machine learning approaches for automatically improving
coordination policies based on historical outcomes and performance patterns.
"""

import asyncio
import logging
import json
import numpy as np
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import math

logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Types of features for policy learning."""
    CONFIDENCE = "confidence"
    COMPONENT_HEALTH = "component_health"
    QUERY_COMPLEXITY = "query_complexity"
    HISTORICAL_SUCCESS = "historical_success"
    TIME_OF_DAY = "time_of_day"
    COMPONENT_LOAD = "component_load"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"


@dataclass
class PolicyFeatures:
    """Features extracted from context for policy learning."""
    confidence: float = 0.0
    component_health_avg: float = 1.0
    component_health_min: float = 1.0
    query_complexity: float = 0.0
    historical_success_rate: float = 0.5
    time_of_day_normalized: float = 0.0
    component_load_avg: float = 0.0
    component_load_max: float = 0.0
    error_rate: float = 0.0
    response_time_avg: float = 0.0
    
    def to_vector(self) -> List[float]:
        """Convert features to numerical vector."""
        return [
            self.confidence,
            self.component_health_avg,
            self.component_health_min,
            self.query_complexity,
            self.historical_success_rate,
            self.time_of_day_normalized,
            self.component_load_avg,
            self.component_load_max,
            self.error_rate,
            self.response_time_avg
        ]
    
    @classmethod
    def feature_names(cls) -> List[str]:
        """Get feature names."""
        return [
            "confidence", "component_health_avg", "component_health_min",
            "query_complexity", "historical_success_rate", "time_of_day_normalized",
            "component_load_avg", "component_load_max", "error_rate", "response_time_avg"
        ]


@dataclass
class PolicyOutcome:
    """Outcome of applying a coordination policy."""
    policy_name: str
    features: PolicyFeatures
    action_taken: str
    success: bool
    improvement: float
    timestamp: float
    execution_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleNeuralNetwork:
    """Simple neural network for policy outcome prediction."""
    
    def __init__(self, input_size: int, hidden_size: int = 16, learning_rate: float = 0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.learning_rate = learning_rate
        
        # Initialize weights randomly
        self.weights1 = np.random.randn(input_size, hidden_size) * 0.1
        self.bias1 = np.zeros((1, hidden_size))
        self.weights2 = np.random.randn(hidden_size, 1) * 0.1
        self.bias2 = np.zeros((1, 1))
        
        self.training_history = []
    
    def sigmoid(self, x):
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def sigmoid_derivative(self, x):
        """Derivative of sigmoid function."""
        return x * (1 - x)
    
    def forward(self, X):
        """Forward propagation."""
        self.z1 = np.dot(X, self.weights1) + self.bias1
        self.a1 = self.sigmoid(self.z1)
        self.z2 = np.dot(self.a1, self.weights2) + self.bias2
        self.a2 = self.sigmoid(self.z2)
        return self.a2
    
    def backward(self, X, y, output):
        """Backward propagation."""
        m = X.shape[0]
        
        # Calculate gradients
        dz2 = output - y
        dw2 = np.dot(self.a1.T, dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m
        
        da1 = np.dot(dz2, self.weights2.T)
        dz1 = da1 * self.sigmoid_derivative(self.a1)
        dw1 = np.dot(X.T, dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m
        
        # Update weights
        self.weights2 -= self.learning_rate * dw2
        self.bias2 -= self.learning_rate * db2
        self.weights1 -= self.learning_rate * dw1
        self.bias1 -= self.learning_rate * db1
    
    def train(self, X, y, epochs: int = 100):
        """Train the neural network."""
        X = np.array(X)
        y = np.array(y).reshape(-1, 1)
        
        for epoch in range(epochs):
            output = self.forward(X)
            loss = np.mean((output - y) ** 2)
            self.backward(X, y, output)
            
            if epoch % 20 == 0:
                self.training_history.append(loss)
        
        return self.training_history[-1] if self.training_history else None
    
    def predict(self, X):
        """Make predictions."""
        X = np.array(X)
        if len(X.shape) == 1:
            X = X.reshape(1, -1)
        return self.forward(X)


class PolicyLearningEngine:
    """Advanced policy learning engine with ML-based adaptation."""
    
    def __init__(self, learning_rate: float = 0.01, min_samples: int = 20):
        self.learning_rate = learning_rate
        self.min_samples = min_samples
        
        # Data storage
        self.policy_outcomes: Dict[str, List[PolicyOutcome]] = defaultdict(list)
        self.feature_stats = {}
        
        # Neural networks for each policy
        self.policy_predictors: Dict[str, SimpleNeuralNetwork] = {}
        
        # Learned thresholds and parameters
        self.learned_thresholds = {}
        self.policy_effectiveness_scores = defaultdict(float)
        
        # Training metrics
        self.training_metrics = {
            "total_outcomes": 0,
            "models_trained": 0,
            "prediction_accuracy": 0.0,
            "last_training": None
        }
        
        logger.info("🧠 Policy learning engine initialized")
    
    def extract_features(self, context) -> PolicyFeatures:
        """Extract features from coordination context."""
        try:
            # Query complexity estimation
            query = context.query if hasattr(context, 'query') else ""
            query_complexity = min(1.0, len(query.split()) / 50.0)
            
            # Component health metrics
            component_states = getattr(context, 'component_states', {})
            if component_states:
                health_values = [s.health for s in component_states.values() if hasattr(s, 'health')]
                load_values = [s.load for s in component_states.values() if hasattr(s, 'load')]
                
                health_avg = sum(health_values) / len(health_values) if health_values else 1.0
                health_min = min(health_values) if health_values else 1.0
                load_avg = sum(load_values) / len(load_values) if load_values else 0.0
                load_max = max(load_values) if load_values else 0.0
            else:
                health_avg = health_min = 1.0
                load_avg = load_max = 0.0
            
            # Time of day (normalized to 0-1)
            hour = datetime.now().hour
            time_normalized = hour / 24.0
            
            # Historical success rate (placeholder - would need actual history)
            historical_success = 0.7  # Default assumption
            
            features = PolicyFeatures(
                confidence=getattr(context, 'confidence', 0.5),
                component_health_avg=health_avg,
                component_health_min=health_min,
                query_complexity=query_complexity,
                historical_success_rate=historical_success,
                time_of_day_normalized=time_normalized,
                component_load_avg=load_avg,
                component_load_max=load_max,
                error_rate=0.0,  # Would need actual error tracking
                response_time_avg=0.0  # Would need actual timing data
            )
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error extracting features: {e}")
            return PolicyFeatures()
    
    def record_outcome(self, policy_name: str, context, action: str, 
                      success: bool, improvement: float = 0.0, 
                      execution_time: float = 0.0, error_message: str = None):
        """Record policy outcome for learning."""
        try:
            features = self.extract_features(context)
            
            outcome = PolicyOutcome(
                policy_name=policy_name,
                features=features,
                action_taken=action,
                success=success,
                improvement=improvement,
                timestamp=datetime.now().timestamp(),
                execution_time=execution_time,
                error_message=error_message
            )
            
            self.policy_outcomes[policy_name].append(outcome)
            self.training_metrics["total_outcomes"] += 1
            
            # Update policy effectiveness score
            outcomes = self.policy_outcomes[policy_name]
            recent_outcomes = outcomes[-10:]  # Last 10 outcomes
            success_rate = sum(1 for o in recent_outcomes if o.success) / len(recent_outcomes)
            avg_improvement = sum(o.improvement for o in recent_outcomes) / len(recent_outcomes)
            
            self.policy_effectiveness_scores[policy_name] = (success_rate * 0.7 + 
                                                           (avg_improvement + 1) / 2 * 0.3)
            
            # Trigger retraining if enough new data
            if len(outcomes) >= self.min_samples and len(outcomes) % 10 == 0:
                asyncio.create_task(self._retrain_policy_model(policy_name))
            
            logger.debug(f"📊 Recorded outcome for policy {policy_name}: success={success}")
            
        except Exception as e:
            logger.error(f"❌ Error recording outcome: {e}")
    
    async def _retrain_policy_model(self, policy_name: str):
        """Retrain the neural network model for a policy."""
        try:
            outcomes = self.policy_outcomes[policy_name]
            if len(outcomes) < self.min_samples:
                return
            
            logger.info(f"🎓 Retraining model for policy: {policy_name}")
            
            # Prepare training data
            X = []
            y = []
            
            for outcome in outcomes:
                features = outcome.features.to_vector()
                # Target is combination of success and improvement
                target = (1.0 if outcome.success else 0.0) * 0.7 + \
                        min(1.0, max(0.0, outcome.improvement + 0.5)) * 0.3
                
                X.append(features)
                y.append(target)
            
            # Create or update neural network
            if policy_name not in self.policy_predictors:
                self.policy_predictors[policy_name] = SimpleNeuralNetwork(
                    input_size=len(PolicyFeatures.feature_names()),
                    hidden_size=16,
                    learning_rate=self.learning_rate
                )
            
            # Train the model
            model = self.policy_predictors[policy_name]
            final_loss = model.train(X, y, epochs=100)
            
            # Update statistics
            self.training_metrics["models_trained"] += 1
            self.training_metrics["last_training"] = datetime.now().isoformat()
            
            # Calculate prediction accuracy on recent data
            if len(X) > 10:
                recent_X = X[-10:]
                recent_y = y[-10:]
                predictions = model.predict(recent_X)
                
                # Calculate accuracy (within 0.2 threshold)
                correct = sum(1 for pred, actual in zip(predictions.flatten(), recent_y) 
                            if abs(pred - actual) < 0.2)
                accuracy = correct / len(recent_y)
                self.training_metrics["prediction_accuracy"] = accuracy
            
            logger.info(f"✅ Model retrained for {policy_name} (loss: {final_loss:.4f})")
            
        except Exception as e:
            logger.error(f"❌ Error retraining model for {policy_name}: {e}")
    
    def predict_policy_outcome(self, policy_name: str, context) -> float:
        """Predict the likely outcome of applying a policy."""
        try:
            if policy_name not in self.policy_predictors:
                # Return baseline prediction based on historical effectiveness
                return self.policy_effectiveness_scores.get(policy_name, 0.5)
            
            features = self.extract_features(context)
            model = self.policy_predictors[policy_name]
            
            prediction = model.predict([features.to_vector()])
            return float(prediction[0][0])
            
        except Exception as e:
            logger.error(f"❌ Error predicting outcome for {policy_name}: {e}")
            return 0.5
    
    def get_optimal_threshold(self, feature_type: str, policy_name: str) -> float:
        """Get learned optimal threshold for a feature."""
        key = f"{policy_name}_{feature_type}"
        
        if key in self.learned_thresholds:
            return self.learned_thresholds[key]
        
        # Learn threshold from outcomes
        outcomes = self.policy_outcomes.get(policy_name, [])
        if len(outcomes) < 10:
            return self._get_default_threshold(feature_type)
        
        # Analyze outcomes to find optimal threshold
        feature_values = []
        success_rates = []
        
        # Get feature values and corresponding success rates
        for outcome in outcomes:
            if feature_type == "confidence":
                feature_values.append(outcome.features.confidence)
            elif feature_type == "component_health":
                feature_values.append(outcome.features.component_health_avg)
            elif feature_type == "query_complexity":
                feature_values.append(outcome.features.query_complexity)
            # Add more feature types as needed
            
            success_rates.append(1.0 if outcome.success else 0.0)
        
        # Find threshold that maximizes discrimination
        best_threshold = self._find_optimal_threshold(feature_values, success_rates)
        self.learned_thresholds[key] = best_threshold
        
        return best_threshold
    
    def _find_optimal_threshold(self, feature_values: List[float], 
                               success_rates: List[float]) -> float:
        """Find threshold that best separates successful from failed outcomes."""
        if not feature_values:
            return 0.5
        
        # Try different threshold values
        sorted_values = sorted(set(feature_values))
        best_threshold = sorted_values[len(sorted_values) // 2]  # Start with median
        best_score = 0.0
        
        for threshold in sorted_values:
            # Calculate discrimination score
            below_threshold = [success_rates[i] for i, v in enumerate(feature_values) if v < threshold]
            above_threshold = [success_rates[i] for i, v in enumerate(feature_values) if v >= threshold]
            
            if not below_threshold or not above_threshold:
                continue
            
            below_avg = sum(below_threshold) / len(below_threshold)
            above_avg = sum(above_threshold) / len(above_threshold)
            
            # Score is the difference in success rates
            score = abs(above_avg - below_avg)
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
        
        return best_threshold
    
    def _get_default_threshold(self, feature_type: str) -> float:
        """Get default threshold for a feature type."""
        defaults = {
            "confidence": 0.6,
            "component_health": 0.7,
            "query_complexity": 0.5,
            "component_load": 0.8,
            "error_rate": 0.1
        }
        return defaults.get(feature_type, 0.5)
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about the learning process."""
        insights = {
            "training_metrics": self.training_metrics.copy(),
            "policy_effectiveness": dict(self.policy_effectiveness_scores),
            "learned_thresholds": self.learned_thresholds.copy(),
            "policies_with_models": list(self.policy_predictors.keys()),
            "total_policies_tracked": len(self.policy_outcomes)
        }
        
        # Add model performance summaries
        model_performance = {}
        for policy_name, model in self.policy_predictors.items():
            outcomes = self.policy_outcomes[policy_name]
            model_performance[policy_name] = {
                "training_samples": len(outcomes),
                "training_history_length": len(model.training_history),
                "last_training_loss": model.training_history[-1] if model.training_history else None
            }
        
        insights["model_performance"] = model_performance
        
        return insights


# Global learning engine instance
adaptive_learning_engine = PolicyLearningEngine()
