"""
Inference Engine Architecture for GödelOS.

This module contains the components of the Inference Engine Architecture,
which is responsible for all deductive reasoning in the GödelOS system.
It takes goals and applies logical rules and knowledge from the KR system,
employing multiple reasoning strategies.

Components:
- ProofObject: Data structure representing the outcome of a reasoning process
- BaseProver: Abstract base class for all provers
- InferenceCoordinator: Manages and coordinates the reasoning process
- ResolutionProver: Prover using resolution for FOL and propositional logic
- ModalTableauProver: Prover for modal logics using tableau method
- SMTInterface: Interface to external SMT solvers
- CLPModule: Constraint Logic Programming module
- AnalogicalReasoningEngine: Engine for analogical reasoning
"""

from godelOS.inference_engine.proof_object import ProofObject
from godelOS.inference_engine.base_prover import BaseProver
from godelOS.inference_engine.coordinator import InferenceCoordinator

# Import all implemented provers
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.inference_engine.modal_tableau_prover import ModalTableauProver
from godelOS.inference_engine.smt_interface import SMTInterface
from godelOS.inference_engine.clp_module import CLPModule
from godelOS.inference_engine.analogical_reasoning_engine import AnalogicalReasoningEngine

__all__ = [
    'ProofObject',
    'BaseProver',
    'InferenceCoordinator',
    'ResolutionProver',
    'ModalTableauProver',
    'SMTInterface',
    'CLPModule',
    'AnalogicalReasoningEngine',
]