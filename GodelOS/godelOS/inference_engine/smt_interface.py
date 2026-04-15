"""
SMT Interface for the Inference Engine Architecture.

This module implements the SMTInterface class, which interfaces with external
SMT (Satisfiability Modulo Theories) solvers like Z3, CVC5, Yices. It translates
GödelOS expressions into the SMT-LIB 2 standard format, invokes the external solver,
and parses the results back into a GödelOS-understandable format.
"""

import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Set, Tuple, Any
import time
import logging

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode, QuantifierNode
from godelOS.core_kr.type_system.types import Type, AtomicType, FunctionType, InstantiatedParametricType
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

# Set up logging
logger = logging.getLogger(__name__)


class SMTSolverConfiguration:
    """
    Configuration for an external SMT solver.
    
    This class encapsulates the configuration for an external SMT solver,
    including the path to the executable and command-line options.
    """
    
    def __init__(self, solver_name: str, solver_path: str, solver_options: List[str] = None):
        """
        Initialize an SMT solver configuration.
        
        Args:
            solver_name: The name of the solver (e.g., "Z3", "CVC5")
            solver_path: The path to the solver executable
            solver_options: Optional command-line options for the solver
        """
        self.solver_name = solver_name
        self.solver_path = solver_path
        self.solver_options = solver_options or []
    
    def get_command(self, input_file: str) -> List[str]:
        """
        Get the command to run the solver on an input file.
        
        Args:
            input_file: The path to the input file containing the SMT-LIB script
            
        Returns:
            The command as a list of strings
        """
        return [self.solver_path] + self.solver_options + [input_file]


class SMTResult:
    """
    Result of an SMT solver invocation.
    
    This class encapsulates the result of an SMT solver invocation,
    including the status, model, and unsat core.
    """
    
    def __init__(self, status: str, model: Optional[Dict[VariableNode, ConstantNode]] = None,
                unsat_core_identifiers: Optional[List[str]] = None):
        """
        Initialize an SMT result.
        
        Args:
            status: The status of the result ("sat", "unsat", or "unknown")
            model: Optional model (variable assignments) if status is "sat"
            unsat_core_identifiers: Optional unsat core identifiers if status is "unsat"
        """
        self.status = status
        self.model = model
        self.unsat_core_identifiers = unsat_core_identifiers


class SMTInterface(BaseProver):
    """
    Interface to external SMT solvers.
    
    This class interfaces with external SMT (Satisfiability Modulo Theories) solvers
    like Z3, CVC5, Yices. It translates GödelOS expressions into the SMT-LIB 2 standard
    format, invokes the external solver, and parses the results back into a
    GödelOS-understandable format.
    """
    
    def __init__(self, solver_configs: List[SMTSolverConfiguration], 
                type_system: TypeSystemManager):
        """
        Initialize the SMT interface.
        
        Args:
            solver_configs: List of configurations for available SMT solvers
            type_system: The type system manager for type checking and inference
        """
        self.solver_configs = solver_configs
        self.type_system = type_system
        self.default_solver = solver_configs[0] if solver_configs else None
    
    @property
    def name(self) -> str:
        """Get the name of this prover."""
        return "SMTInterface"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get the capabilities of this prover."""
        capabilities = super().capabilities.copy()
        capabilities.update({
            "arithmetic": True,
            "equality": True,
            "uninterpreted_functions": True,
            "propositional_logic": True,
            "first_order_logic": True  # Limited to quantifier-free or with finite domains
        })
        return capabilities
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """
        Determine if this prover can handle the given goal and context.
        
        The SMT interface can handle goals and contexts that involve arithmetic,
        arrays, bit-vectors, and uninterpreted functions.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            
        Returns:
            True if this prover can handle the given goal and context, False otherwise
        """
        # Check if the goal or any context assertion contains arithmetic
        from godelOS.inference_engine.coordinator import InferenceCoordinator
        coordinator = InferenceCoordinator(None, {})
        
        if coordinator._contains_arithmetic(goal_ast):
            return True
        
        for ast in context_asts:
            if coordinator._contains_arithmetic(ast):
                return True
        
        # A more sophisticated implementation would check for other theories like
        # arrays, bit-vectors, etc.
        
        return False
    
    def check_satisfiability(self, formula_ast: AST_Node, axioms_asts: Optional[Set[AST_Node]] = None,
                           logic_theory: str = "AUFLIRA", request_model: bool = False,
                           request_unsat_core: bool = False,
                           resources: Optional[ResourceLimits] = None) -> SMTResult:
        """
        Check the satisfiability of a formula using an SMT solver.
        
        This method implements the full SMT interface, including:
        1. Translating the formula and axioms to SMT-LIB format
        2. Invoking the external SMT solver
        3. Parsing the results
        
        Args:
            formula_ast: The formula to check
            axioms_asts: Optional set of axioms to include
            logic_theory: The SMT-LIB logic theory to use
            request_model: Whether to request a model if satisfiable
            request_unsat_core: Whether to request an unsat core if unsatisfiable
            resources: Optional resource limits for the solver
            
        Returns:
            An SMTResult object containing the result of the solver invocation
        """
        start_time = time.time()
        
        # Set default resource limits if none provided
        if resources is None:
            resources = ResourceLimits(time_limit_ms=10000, depth_limit=100)
        
        # Ensure we have a solver available
        if not self.solver_configs:
            logger.error("No SMT solvers configured")
            return SMTResult(status="unknown", model=None, unsat_core_identifiers=None)
        
        # Use the default solver or select based on resources
        solver_config = self.solver_configs[0]
        if resources and "solver_name" in resources.additional_limits:
            solver_name = resources.additional_limits["solver_name"]
            for config in self.solver_configs:
                if config.solver_name.lower() == solver_name.lower():
                    solver_config = config
                    break
        
        logger.info(f"SMTInterface checking satisfiability of: {formula_ast}")
        logger.info(f"Using solver: {solver_config.solver_name}")
        logger.info(f"Logic theory: {logic_theory}")
        
        try:
            # Step 1: Translate the formula and axioms to SMT-LIB format
            smt_script = self._generate_smt_script(
                formula_ast,
                axioms_asts or set(),
                logic_theory,
                request_model,
                request_unsat_core
            )
            
            # Step 2: Write the SMT-LIB script to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.smt2', delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(smt_script)
            
            try:
                # Step 3: Invoke the external SMT solver
                command = solver_config.get_command(temp_file_path)
                
                # Apply resource limits
                timeout_seconds = None
                if resources and resources.time_limit_ms is not None:
                    timeout_seconds = resources.time_limit_ms / 1000.0
                
                logger.debug(f"Executing SMT solver command: {' '.join(command)}")
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.warning(f"SMT solver timed out after {timeout_seconds} seconds")
                    return SMTResult(status="timeout")
                
                if process.returncode != 0:
                    logger.error(f"SMT solver failed with exit code {process.returncode}: {stderr}")
                    return SMTResult(status="error")
                
                # Step 4: Parse the results
                result = self._parse_smt_result(stdout, request_model, request_unsat_core)
                
                end_time = time.time()
                logger.info(f"SMT solver returned: {result.status} in {(end_time - start_time) * 1000:.2f}ms")
                
                return result
                
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")
        
        except Exception as e:
            logger.exception(f"Error during SMT solving: {e}")
            return SMTResult(status="error")
    
    def _generate_smt_script(self, formula_ast: AST_Node, axioms_asts: Set[AST_Node],
                            logic_theory: str, request_model: bool,
                            request_unsat_core: bool) -> str:
        """
        Generate an SMT-LIB 2 script for the given formula and axioms.
        
        Args:
            formula_ast: The formula to check
            axioms_asts: Set of axioms to include
            logic_theory: The SMT-LIB logic theory to use
            request_model: Whether to request a model if satisfiable
            request_unsat_core: Whether to request an unsat core if unsatisfiable
            
        Returns:
            An SMT-LIB 2 script as a string
        """
        # Start building the SMT-LIB script
        script_lines = []
        
        # Set the logic
        script_lines.append(f"(set-logic {logic_theory})")
        
        # Collect all variables and function symbols
        all_asts = {formula_ast} | axioms_asts
        symbols = self._collect_symbols(all_asts)
        
        # Declare sorts (types)
        declared_sorts = set()
        for symbol_type in symbols.values():
            self._declare_sorts_for_type(symbol_type, declared_sorts, script_lines)
        
        # Declare symbols (constants, variables, functions)
        for symbol, symbol_type in symbols.items():
            if isinstance(symbol, ConstantNode):
                script_lines.append(self._declare_constant(symbol, symbol_type))
            elif isinstance(symbol, VariableNode):
                script_lines.append(self._declare_variable(symbol, symbol_type))
        
        # Add assertions for axioms
        if axioms_asts:
            for axiom in axioms_asts:
                if request_unsat_core:
                    # Add a name to the assertion for unsat core tracking
                    name = f"axiom_{id(axiom)}"
                    script_lines.append(f"(assert (! {self._translate_ast_to_smtlib(axiom)} :named {name}))")
                else:
                    script_lines.append(f"(assert {self._translate_ast_to_smtlib(axiom)})")
        
        # Add assertion for the formula
        if request_unsat_core:
            script_lines.append(f"(assert (! {self._translate_ast_to_smtlib(formula_ast)} :named formula))")
        else:
            script_lines.append(f"(assert {self._translate_ast_to_smtlib(formula_ast)})")
        
        # Add check-sat command
        script_lines.append("(check-sat)")
        
        # Add get-model command if requested
        if request_model:
            script_lines.append("(get-model)")
        
        # Add get-unsat-core command if requested
        if request_unsat_core:
            script_lines.append("(get-unsat-core)")
        
        # Combine all lines into a single script
        return "\n".join(script_lines)
    
    def _collect_symbols(self, asts: Set[AST_Node]) -> Dict[AST_Node, 'Type']:
        """
        Collect all symbols (constants, variables, functions) from a set of AST nodes.
        
        Args:
            asts: Set of AST nodes to collect symbols from
            
        Returns:
            A dictionary mapping symbols to their types
        """
        symbols = {}
        
        def visit_node(node: AST_Node):
            if isinstance(node, (ConstantNode, VariableNode)):
                symbols[node] = node.type
            
            # Recursively visit child nodes
            if isinstance(node, ApplicationNode):
                visit_node(node.operator)
                for arg in node.arguments:
                    visit_node(arg)
            elif isinstance(node, ConnectiveNode):
                for operand in node.operands:
                    visit_node(operand)
            elif isinstance(node, QuantifierNode):
                for var in node.bound_variables:
                    symbols[var] = var.type
                visit_node(node.scope)
        
        for ast in asts:
            visit_node(ast)
        
        return symbols
    
    def _declare_sorts_for_type(self, type_obj: 'Type', declared_sorts: Set[str],
                              script_lines: List[str]):
        """
        Add declarations for any sorts (types) needed for a given type.
        
        Args:
            type_obj: The type to declare sorts for
            declared_sorts: Set of already declared sort names
            script_lines: List of script lines to append to
        """
        # Types already imported at the top of the file
        
        if isinstance(type_obj, AtomicType):
            sort_name = type_obj.name
            if sort_name not in declared_sorts and sort_name not in ["Bool", "Int", "Real"]:
                script_lines.append(f"(declare-sort {sort_name} 0)")
                declared_sorts.add(sort_name)
        elif isinstance(type_obj, FunctionType):
            # Declare sorts for argument types and return type
            for arg_type in type_obj.arg_types:
                self._declare_sorts_for_type(arg_type, declared_sorts, script_lines)
            self._declare_sorts_for_type(type_obj.return_type, declared_sorts, script_lines)
        elif isinstance(type_obj, InstantiatedParametricType):
            # Declare sorts for type arguments
            for arg_type in type_obj.actual_type_args:
                self._declare_sorts_for_type(arg_type, declared_sorts, script_lines)
    
    def _declare_constant(self, const_node: ConstantNode, type_obj: 'Type') -> str:
        """
        Generate an SMT-LIB declaration for a constant.
        
        Args:
            const_node: The constant node to declare
            type_obj: The type of the constant
            
        Returns:
            An SMT-LIB declaration for the constant
        """
        smt_sort = self._type_to_smt_sort(type_obj)
        return f"(declare-const {const_node.name} {smt_sort})"
    
    def _declare_variable(self, var_node: VariableNode, type_obj: 'Type') -> str:
        """
        Generate an SMT-LIB declaration for a variable.
        
        Args:
            var_node: The variable node to declare
            type_obj: The type of the variable
            
        Returns:
            An SMT-LIB declaration for the variable
        """
        # In SMT-LIB, variables are just constants
        smt_sort = self._type_to_smt_sort(type_obj)
        # Use the name and ID to ensure uniqueness
        var_name = f"{var_node.name}_{var_node.var_id}"
        return f"(declare-const {var_name} {smt_sort})"
    
    def _type_to_smt_sort(self, type_obj: 'Type') -> str:
        """
        Convert a GödelOS type to an SMT-LIB sort.
        
        Args:
            type_obj: The type to convert
            
        Returns:
            The corresponding SMT-LIB sort as a string
        """
        # Types already imported at the top of the file
        
        if isinstance(type_obj, AtomicType):
            # Map common types to SMT-LIB sorts
            type_map = {
                "Boolean": "Bool",
                "Integer": "Int",
                "Real": "Real",
                "String": "String"
            }
            return type_map.get(type_obj.name, type_obj.name)
        
        elif isinstance(type_obj, FunctionType):
            # Function types become function sorts
            arg_sorts = [self._type_to_smt_sort(arg_type) for arg_type in type_obj.arg_types]
            return_sort = self._type_to_smt_sort(type_obj.return_type)
            
            if not arg_sorts:
                # Nullary function (constant)
                return return_sort
            else:
                # Function with arguments
                return f"({' -> '.join(arg_sorts + [return_sort])})"
        
        elif isinstance(type_obj, InstantiatedParametricType):
            # For now, just use the constructor name
            # A more sophisticated implementation would handle parameterized types like arrays
            return type_obj.constructor.name
        
        # Default case
        return "Unknown"
    
    def _translate_ast_to_smtlib(self, node: AST_Node) -> str:
        """
        Translate a GödelOS AST node to SMT-LIB format.
        
        Args:
            node: The AST node to translate
            
        Returns:
            The SMT-LIB representation as a string
        """
        if isinstance(node, ConstantNode):
            # Handle special constants
            logger.debug(f"Translating ConstantNode: {node.name}, type: {type(node.type).__name__}")
            
            # Handle Boolean constants
            if hasattr(node.type, 'name') and node.type.name == "Boolean":
                if node.value is True:
                    return "true"
                elif node.value is False:
                    return "false"
            
            # Handle function type constants - these are typically operators
            elif isinstance(node.type, FunctionType):
                # For function constants, just use the name as is
                logger.debug(f"Handling function constant: {node.name} with type {node.type}")
                return node.name
            
            # Handle other types that may not have a 'name' attribute
            elif not hasattr(node.type, 'name'):
                logger.debug(f"Handling constant with type that has no 'name' attribute: {node.name}, type: {type(node.type).__name__}")
                return node.name
            
            # For other constants, just use the name
            return node.name
        
        elif isinstance(node, VariableNode):
            # Use the name and ID to ensure uniqueness
            return f"{node.name}_{node.var_id}"
        
        elif isinstance(node, ApplicationNode):
            # Function application
            op_str = self._translate_ast_to_smtlib(node.operator)
            args_str = " ".join(self._translate_ast_to_smtlib(arg) for arg in node.arguments)
            return f"({op_str} {args_str})"
        
        elif isinstance(node, ConnectiveNode):
            if node.connective_type == "NOT":
                # Negation
                operand_str = self._translate_ast_to_smtlib(node.operands[0])
                return f"(not {operand_str})"
            
            elif node.connective_type == "AND":
                # Conjunction
                if not node.operands:
                    return "true"
                operands_str = " ".join(self._translate_ast_to_smtlib(op) for op in node.operands)
                return f"(and {operands_str})"
            
            elif node.connective_type == "OR":
                # Disjunction
                if not node.operands:
                    return "false"
                operands_str = " ".join(self._translate_ast_to_smtlib(op) for op in node.operands)
                return f"(or {operands_str})"
            
            elif node.connective_type == "IMPLIES":
                # Implication
                left_str = self._translate_ast_to_smtlib(node.operands[0])
                right_str = self._translate_ast_to_smtlib(node.operands[1])
                return f"(=> {left_str} {right_str})"
            
            elif node.connective_type == "EQUIV":
                # Equivalence
                left_str = self._translate_ast_to_smtlib(node.operands[0])
                right_str = self._translate_ast_to_smtlib(node.operands[1])
                return f"(= {left_str} {right_str})"
            
            else:
                # Unknown connective
                logger.warning(f"Unknown connective type: {node.connective_type}")
                return f"(unknown-connective {node.connective_type})"
        
        elif isinstance(node, QuantifierNode):
            # Quantifiers
            vars_str = " ".join(f"({self._translate_ast_to_smtlib(var)} {self._type_to_smt_sort(var.type)})"
                              for var in node.bound_variables)
            body_str = self._translate_ast_to_smtlib(node.scope)
            
            if node.quantifier_type == "FORALL":
                return f"(forall ({vars_str}) {body_str})"
            elif node.quantifier_type == "EXISTS":
                return f"(exists ({vars_str}) {body_str})"
            else:
                # Unknown quantifier
                logger.warning(f"Unknown quantifier type: {node.quantifier_type}")
                return f"(unknown-quantifier {node.quantifier_type})"
        
        # Default case
        logger.warning(f"Unsupported AST node type: {type(node)}")
        return f"(unsupported-node {type(node).__name__})"
    
    def _parse_smt_result(self, output: str, request_model: bool,
                         request_unsat_core: bool) -> SMTResult:
        """
        Parse the output of an SMT solver.
        
        Args:
            output: The output of the SMT solver
            request_model: Whether a model was requested
            request_unsat_core: Whether an unsat core was requested
            
        Returns:
            An SMTResult object containing the parsed result
        """
        lines = output.strip().split('\n')
        if not lines:
            return SMTResult(status="error")
        
        # First line should be the satisfiability result
        status = lines[0].strip()
        if status not in ["sat", "unsat", "unknown"]:
            logger.error(f"Unexpected SMT solver result: {status}")
            return SMTResult(status="error")
        
        model = None
        unsat_core_identifiers = None
        
        # Parse the model if requested and available
        if status == "sat" and request_model and len(lines) > 1:
            model = self._parse_smt_model("\n".join(lines[1:]))
        
        # Parse the unsat core if requested and available
        if status == "unsat" and request_unsat_core and len(lines) > 1:
            unsat_core_identifiers = self._parse_smt_unsat_core("\n".join(lines[1:]))
        
        return SMTResult(status=status, model=model, unsat_core_identifiers=unsat_core_identifiers)
    
    def _parse_smt_model(self, model_str: str) -> Dict[VariableNode, ConstantNode]:
        """
        Parse an SMT model into a dictionary mapping variables to values.
        
        Args:
            model_str: The model string from the SMT solver
            
        Returns:
            A dictionary mapping variables to their values
        """
        # This is a simplified implementation that would need to be expanded
        # to handle complex models with function definitions, etc.
        model = {}
        
        # For now, just return an empty model
        # A full implementation would parse the S-expression model
        logger.info(f"Model parsing not fully implemented yet. Raw model: {model_str}")
        
        return model
    
    def _parse_smt_unsat_core(self, unsat_core_str: str) -> List[str]:
        """
        Parse an SMT unsat core into a list of assertion identifiers.
        
        Args:
            unsat_core_str: The unsat core string from the SMT solver
            
        Returns:
            A list of assertion identifiers
        """
        # This is a simplified implementation that would need to be expanded
        # to handle complex unsat cores.
        
        # Try to parse as a simple list of identifiers
        identifiers = []
        
        # Remove parentheses and split by whitespace
        cleaned_str = unsat_core_str.replace('(', ' ').replace(')', ' ')
        tokens = cleaned_str.split()
        
        for token in tokens:
            token = token.strip()
            if token and token not in ['', 'get-unsat-core']:
                identifiers.append(token)
        
        return identifiers
    
    def _negate_formula(self, formula: AST_Node) -> AST_Node:
        """
        Negate a formula.
        
        Args:
            formula: The formula to negate
            
        Returns:
            The negated formula
        """
        # If the formula is already a negation, return its operand (double negation elimination)
        if (isinstance(formula, ConnectiveNode) and
            formula.connective_type == "NOT" and
            len(formula.operands) == 1):
            return formula.operands[0]
        
        # Otherwise, create a new negation
        return ConnectiveNode("NOT", [formula], formula.type)
    
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node],
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Attempt to prove a goal using an SMT solver.
        
        This method checks the satisfiability of the negation of the goal
        combined with the context assertions. If the result is unsatisfiable,
        the goal is proven.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            resources: Optional resource limits for the proof attempt
            
        Returns:
            A ProofObject representing the result of the proof attempt
        """
        start_time = time.time()
        
        logger.info(f"SMTInterface attempting to prove: {goal_ast}")
        logger.info(f"Context size: {len(context_asts)}")
        
        try:
            # Step 1: Negate the goal
            negated_goal = self._negate_formula(goal_ast)
            logger.debug(f"Negated goal: {negated_goal}")
            
            # Step 2: Check satisfiability of the negated goal and context
            # If the result is unsatisfiable, the goal is proven
            result = self.check_satisfiability(
                negated_goal,
                context_asts,
                logic_theory=resources.get_limit("logic_theory", "AUFLIRA") if resources else "AUFLIRA",
                request_model=resources.get_limit("request_model", False) if resources else False,
                request_unsat_core=resources.get_limit("request_unsat_core", True) if resources else True,
                resources=resources
            )
            
            end_time = time.time()
            time_taken_ms = (end_time - start_time) * 1000
            
            if result.status == "unsat":
                # The negated goal is unsatisfiable, so the goal is proven
                proof_steps = []
                if result.unsat_core_identifiers:
                    # Create proof steps based on the unsat core
                    for i, identifier in enumerate(result.unsat_core_identifiers):
                        if identifier.startswith("axiom_"):
                            # This is an axiom from the context
                            rule_name = "SMT Axiom"
                        else:
                            # This is the negated goal
                            rule_name = "SMT Contradiction"
                        
                        proof_steps.append(ProofStepNode(
                            formula=goal_ast,  # Simplified; would need to map back to the actual formula
                            rule_name=rule_name,
                            premises=[],
                            explanation=f"Step {i+1}: Used in SMT unsat core: {identifier}"
                        ))
                
                return ProofObject.create_success(
                    conclusion_ast=goal_ast,
                    proof_steps=proof_steps,
                    used_axioms_rules=context_asts,
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={
                        "smt_result": result.status,
                        "unsat_core_size": len(result.unsat_core_identifiers) if result.unsat_core_identifiers else 0
                    }
                )
            elif result.status == "sat":
                # The negated goal is satisfiable, so the goal is not proven
                model_info = ""
                if result.model:
                    model_info = f" with model of size {len(result.model)}"
                
                return ProofObject.create_failure(
                    status_message=f"Goal not proven: negated goal is satisfiable{model_info}",
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={
                        "smt_result": result.status,
                        "model_size": len(result.model) if result.model else 0
                    }
                )
            else:
                # The SMT solver returned "unknown" or an error
                return ProofObject.create_failure(
                    status_message=f"SMT solver returned {result.status}",
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={
                        "smt_result": result.status
                    }
                )
        
        except Exception as e:
            end_time = time.time()
            time_taken_ms = (end_time - start_time) * 1000
            
            logger.exception(f"Error during SMT proof: {e}")
            return ProofObject.create_failure(
                status_message=f"Error during SMT proof: {str(e)}",
                inference_engine_used=self.name,
                time_taken_ms=time_taken_ms,
                resources_consumed={}
            )