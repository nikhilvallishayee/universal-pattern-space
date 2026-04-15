"""
Probabilistic Logic Module.

This module manages and reasons with uncertain knowledge where logical formulas
or rules have associated probabilities or weights. It supports multiple probabilistic
reasoning approaches, including Markov Logic Networks (MLNs) and Probabilistic Soft Logic (PSL).
"""

from godelOS.core_kr.probabilistic_logic.module import (
    ProbabilisticLogicModule,
    InferenceAlgorithm,
    MCMCInference,
    WeightLearningAlgorithm,
    GradientDescentWeightLearning
)

__all__ = [
    "ProbabilisticLogicModule",
    "InferenceAlgorithm",
    "MCMCInference",
    "WeightLearningAlgorithm",
    "GradientDescentWeightLearning"
]