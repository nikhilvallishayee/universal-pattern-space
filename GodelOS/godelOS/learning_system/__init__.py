"""
Learning System Module for GödelOS.

This module is responsible for enabling the agent to acquire new knowledge,
refine existing knowledge, and improve its problem-solving strategies over time.
It integrates various machine learning paradigms tailored for symbolic representations.

Components:
    - ILPEngine (Module 3.1): Inductive Logic Programming Engine
    - ExplanationBasedLearner (Module 3.2): Explanation-Based Learning
    - TemplateEvolutionModule (Module 3.3): Template Evolution
    - MetaControlRLModule (Module 3.4): Meta-Control Reinforcement Learning
"""

# Import components as they are implemented
from godelOS.learning_system.ilp_engine import ILPEngine
from godelOS.learning_system.explanation_based_learner import ExplanationBasedLearner, OperationalityConfig
from godelOS.learning_system.template_evolution_module import TemplateEvolutionModule, EvolutionConfig
from godelOS.learning_system.meta_control_rl_module import MetaControlRLModule, MetaAction, RLConfig