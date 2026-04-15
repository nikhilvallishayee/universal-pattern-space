"""
Constraint Logic Programming Module for the Inference Engine Architecture.

This module implements the CLPModule class, which provides a declarative framework
for solving problems that combine logical deduction with constraint satisfaction
over specific domains (e.g., finite integer domains, real numbers, Booleans).
"""

from typing import Dict, List, Optional, Set, Tuple, Any
import time
import logging

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ApplicationNode, ConstantNode, ConnectiveNode
from godelOS.core_kr.type_system.types import Type, FunctionType
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

# Set up logging
logger = logging.getLogger(__name__)


class ConstraintVariable:
    """
    A logical variable augmented with a domain.
    
    This class represents a logical variable with an associated domain,
    such as a range of integers or an interval of real numbers.
    """
    
    def __init__(self, variable: VariableNode, domain_type: str, domain_min=None, domain_max=None):
        """
        Initialize a constraint variable.
        
        Args:
            variable: The logical variable
            domain_type: The type of domain (e.g., "FD" for finite domain, "R" for reals)
            domain_min: Optional minimum value of the domain
            domain_max: Optional maximum value of the domain
        """
        self.variable = variable
        self.domain_type = domain_type
        self.domain_min = domain_min
        self.domain_max = domain_max
        self.domain_values = None  # For explicit enumeration of domain values
    
    def set_domain_values(self, values: Set[Any]):
        """
        Set the domain to an explicit set of values.
        
        Args:
            values: The set of values in the domain
        """
        self.domain_values = values
    
    def get_size(self) -> int:
        """
        Get the size of the domain.
        
        Returns:
            The number of values in the domain, or -1 if infinite
        """
        if self.domain_values is not None:
            return len(self.domain_values)
        elif self.domain_min is not None and self.domain_max is not None:
            if isinstance(self.domain_min, int) and isinstance(self.domain_max, int):
                return self.domain_max - self.domain_min + 1
        return -1  # Infinite or unknown size
    
    def is_singleton(self) -> bool:
        """
        Check if the domain has exactly one value.
        
        Returns:
            True if the domain has exactly one value, False otherwise
        """
        if self.domain_values is not None:
            return len(self.domain_values) == 1
        elif self.domain_min is not None and self.domain_max is not None:
            return self.domain_min == self.domain_max
        return False
    
    def get_value(self) -> Optional[Any]:
        """
        Get the value if the domain is a singleton.
        
        Returns:
            The value if the domain is a singleton, None otherwise
        """
        if self.is_singleton():
            if self.domain_values is not None:
                return next(iter(self.domain_values))
            return self.domain_min
        return None
    
    def intersect(self, other: 'ConstraintVariable') -> bool:
        """
        Intersect this domain with another domain.
        
        Args:
            other: The other domain to intersect with
            
        Returns:
            True if the domain changed, False otherwise
        """
        if self.domain_type != other.domain_type:
            raise ValueError(f"Cannot intersect domains of different types: {self.domain_type} and {other.domain_type}")
        
        changed = False
        
        if self.domain_values is not None and other.domain_values is not None:
            old_size = len(self.domain_values)
            self.domain_values = self.domain_values.intersection(other.domain_values)
            changed = old_size != len(self.domain_values)
        elif self.domain_min is not None and self.domain_max is not None and other.domain_min is not None and other.domain_max is not None:
            old_min, old_max = self.domain_min, self.domain_max
            self.domain_min = max(self.domain_min, other.domain_min)
            self.domain_max = min(self.domain_max, other.domain_max)
            changed = old_min != self.domain_min or old_max != self.domain_max
        
        return changed
    
    def __str__(self) -> str:
        if self.domain_values is not None:
            return f"{self.variable.name} :: {self.domain_values}"
        elif self.domain_min is not None and self.domain_max is not None:
            return f"{self.variable.name} :: {self.domain_min}..{self.domain_max}"
        else:
            return f"{self.variable.name} :: {self.domain_type}"


class CLPClause:
    """
    A clause in a CLP program.
    
    This class represents a clause in a CLP program, which consists of a head,
    a body of logical goals, and a set of constraints.
    """
    
    def __init__(self, head: Optional[AST_Node] = None, body: List[AST_Node] = None,
                 constraints: List[AST_Node] = None):
        """
        Initialize a CLP clause.
        
        Args:
            head: The head of the clause (None for queries)
            body: The body of the clause (logical goals)
            constraints: The constraints of the clause
        """
        self.head = head
        self.body = body or []
        self.constraints = constraints or []
    
    def is_fact(self) -> bool:
        """
        Check if this clause is a fact (no body or constraints).
        
        Returns:
            True if this clause is a fact, False otherwise
        """
        return self.head is not None and not self.body and not self.constraints
    
    def is_query(self) -> bool:
        """
        Check if this clause is a query (no head).
        
        Returns:
            True if this clause is a query, False otherwise
        """
        return self.head is None
    
    def __str__(self) -> str:
        head_str = str(self.head) if self.head else "?-"
        body_str = ", ".join(str(goal) for goal in self.body)
        constraints_str = ", ".join(str(constraint) for constraint in self.constraints)
        
        if not self.body and not self.constraints:
            return f"{head_str}."
        elif not self.constraints:
            return f"{head_str} :- {body_str}."
        elif not self.body:
            return f"{head_str} :- {constraints_str}."
        else:
            return f"{head_str} :- {body_str}, {constraints_str}."


class ConstraintStore:
    """
    A store of active constraints.
    
    This class represents a global store of active constraints that have been
    encountered during query execution.
    """
    
    def __init__(self):
        """Initialize an empty constraint store."""
        self.constraints = []
        self.wake_up_queue = []  # Queue of constraints to wake up after domain changes
    
    def add_constraint(self, constraint: AST_Node) -> bool:
        """
        Add a constraint to the store.
        
        Args:
            constraint: The constraint to add
            
        Returns:
            True if the constraint was added, False if it was already in the store
        """
        if constraint not in self.constraints:
            self.constraints.append(constraint)
            self.wake_up_queue.append(constraint)
            return True
        return False
    
    def get_constraints(self) -> List[AST_Node]:
        """
        Get all constraints in the store.
        
        Returns:
            The list of constraints
        """
        return self.constraints.copy()
    
    def get_next_constraint_to_wake_up(self) -> Optional[AST_Node]:
        """
        Get the next constraint to wake up.
        
        Returns:
            The next constraint to wake up, or None if the queue is empty
        """
        if self.wake_up_queue:
            return self.wake_up_queue.pop(0)
        return None
    
    def wake_up_all(self):
        """
        Wake up all constraints.
        
        This method adds all constraints to the wake-up queue.
        """
        self.wake_up_queue = self.constraints.copy()


class DomainStore:
    """
    A store of variable domains.
    
    This class maps each constraint variable to its current (possibly pruned) domain.
    """
    
    def __init__(self):
        """Initialize an empty domain store."""
        self.domains = {}
        self.changed_variables = set()  # Set of variables whose domains have changed
    
    def set_domain(self, variable: VariableNode, domain: ConstraintVariable) -> bool:
        """
        Set the domain of a variable.
        
        Args:
            variable: The variable
            domain: The constraint variable representing the domain
            
        Returns:
            True if the domain changed, False otherwise
        """
        var_id = variable.var_id
        if var_id in self.domains:
            old_domain = self.domains[var_id]
            if str(old_domain) != str(domain):  # Simple comparison
                self.domains[var_id] = domain
                self.changed_variables.add(var_id)
                return True
            return False
        else:
            self.domains[var_id] = domain
            self.changed_variables.add(var_id)
            return True
    
    def get_domain(self, variable: VariableNode) -> Optional[ConstraintVariable]:
        """
        Get the domain of a variable.
        
        Args:
            variable: The variable
            
        Returns:
            The constraint variable representing the domain, or None if not found
        """
        return self.domains.get(variable.var_id)
    
    def update_domain(self, variable: VariableNode, domain_type: str,
                     domain_min=None, domain_max=None, domain_values: Optional[Set[Any]] = None) -> bool:
        """
        Update the domain of a variable.
        
        Args:
            variable: The variable
            domain_type: The type of domain
            domain_min: Optional minimum value of the domain
            domain_max: Optional maximum value of the domain
            domain_values: Optional set of explicit domain values
            
        Returns:
            True if the domain changed, False otherwise
        """
        var_id = variable.var_id
        if var_id in self.domains:
            # Intersect with existing domain
            existing_domain = self.domains[var_id]
            if existing_domain.domain_type != domain_type:
                raise ValueError(f"Cannot update domain of different type: {existing_domain.domain_type} and {domain_type}")
            
            changed = False
            if domain_values is not None:
                if existing_domain.domain_values is not None:
                    old_size = len(existing_domain.domain_values)
                    existing_domain.domain_values = existing_domain.domain_values.intersection(domain_values)
                    changed = old_size != len(existing_domain.domain_values)
                else:
                    existing_domain.domain_values = domain_values
                    changed = True
            elif domain_min is not None or domain_max is not None:
                if domain_min is not None:
                    if existing_domain.domain_min is None or domain_min > existing_domain.domain_min:
                        existing_domain.domain_min = domain_min
                        changed = True
                if domain_max is not None:
                    if existing_domain.domain_max is None or domain_max < existing_domain.domain_max:
                        existing_domain.domain_max = domain_max
                        changed = True
            
            if changed:
                self.changed_variables.add(var_id)
            return changed
        else:
            # Create new domain
            new_domain = ConstraintVariable(variable, domain_type, domain_min, domain_max)
            if domain_values is not None:
                new_domain.set_domain_values(domain_values)
            self.domains[var_id] = new_domain
            self.changed_variables.add(var_id)
            return True
    
    def get_changed_variables(self) -> Set[int]:
        """
        Get the set of variables whose domains have changed.
        
        Returns:
            The set of variable IDs whose domains have changed
        """
        return self.changed_variables.copy()
    
    def clear_changed_variables(self):
        """Clear the set of changed variables."""
        self.changed_variables.clear()
    
    def get_all_variables(self) -> List[VariableNode]:
        """
        Get all variables in the domain store.
        
        Returns:
            A list of all variables in the domain store
        """
        return [domain.variable for domain in self.domains.values()]


class ConstraintSolver:
    """
    Base class for constraint solvers.
    
    This class defines the interface for constraint solvers, which are responsible
    for propagating constraints and pruning variable domains.
    """
    
    def __init__(self, domain_type: str):
        """
        Initialize a constraint solver.
        
        Args:
            domain_type: The type of domain this solver handles (e.g., "FD", "R")
        """
        self.domain_type = domain_type
    
    def propagate(self, constraint: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate a constraint and prune variable domains.
        
        Args:
            constraint: The constraint to propagate
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        raise NotImplementedError("Subclasses must implement propagate")
    
    def can_handle_constraint(self, constraint: AST_Node) -> bool:
        """
        Check if this solver can handle a given constraint.
        
        Args:
            constraint: The constraint to check
            
        Returns:
            True if this solver can handle the constraint, False otherwise
        """
        raise NotImplementedError("Subclasses must implement can_handle_constraint")


class FiniteDomainSolver(ConstraintSolver):
    """
    Constraint solver for finite integer domains (CLP(FD)).
    
    This class implements a constraint solver for finite integer domains,
    supporting common constraints like equality, inequality, and arithmetic.
    """
    
    def __init__(self):
        """Initialize a finite domain solver."""
        super().__init__("FD")
    
    def can_handle_constraint(self, constraint: AST_Node) -> bool:
        """
        Check if this solver can handle a given constraint.
        
        Args:
            constraint: The constraint to check
            
        Returns:
            True if this solver can handle the constraint, False otherwise
        """
        # Check if the constraint is an application of a supported constraint predicate
        if isinstance(constraint, ApplicationNode):
            op = constraint.operator
            if isinstance(op, ConstantNode):
                # Supported constraint predicates for finite domains
                fd_constraints = {'=', '!=', '<', '<=', '>', '>=', 'AllDifferent', 'SumEquals'}
                return op.name in fd_constraints
        
        return False
    
    def propagate(self, constraint: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate a constraint and prune variable domains.
        
        Args:
            constraint: The constraint to propagate
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        if not isinstance(constraint, ApplicationNode):
            return True  # Not a constraint we can handle
        
        op = constraint.operator
        if not isinstance(op, ConstantNode):
            return True  # Not a constraint we can handle
        
        # Get the arguments of the constraint
        args = constraint.arguments
        
        # Handle different types of constraints
        if op.name == '=':
            return self._propagate_equality(args[0], args[1], domain_store)
        elif op.name == '!=':
            return self._propagate_inequality(args[0], args[1], domain_store)
        elif op.name == '<':
            return self._propagate_less_than(args[0], args[1], domain_store)
        elif op.name == '<=':
            return self._propagate_less_than_or_equal(args[0], args[1], domain_store)
        elif op.name == '>':
            return self._propagate_greater_than(args[0], args[1], domain_store)
        elif op.name == '>=':
            return self._propagate_greater_than_or_equal(args[0], args[1], domain_store)
        elif op.name == 'AllDifferent':
            return self._propagate_all_different(args, domain_store)
        elif op.name == 'SumEquals':
            return self._propagate_sum_equals(args[:-1], args[-1], domain_store)
        
        return True  # Unknown constraint, assume satisfiable
    
    def _propagate_equality(self, left: AST_Node, right: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate an equality constraint: left = right.
        
        Args:
            left: The left-hand side of the equality
            right: The right-hand side of the equality
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        # Case 1: Both are variables
        if isinstance(left, VariableNode) and isinstance(right, VariableNode):
            left_domain = domain_store.get_domain(left)
            right_domain = domain_store.get_domain(right)
            
            if left_domain is None or right_domain is None:
                return True  # Can't constrain without domains
            
            # Create new domains by intersecting the existing domains
            new_left_domain = ConstraintVariable(left, "FD", left_domain.domain_min, left_domain.domain_max)
            if left_domain.domain_values is not None:
                new_left_domain.set_domain_values(left_domain.domain_values.copy())
            
            new_right_domain = ConstraintVariable(right, "FD", right_domain.domain_min, right_domain.domain_max)
            if right_domain.domain_values is not None:
                new_right_domain.set_domain_values(right_domain.domain_values.copy())
            
            # Intersect the domains
            left_changed = new_left_domain.intersect(right_domain)
            right_changed = new_right_domain.intersect(left_domain)
            
            # Check if the domains are empty
            if ((new_left_domain.domain_values is not None and not new_left_domain.domain_values) or
                (new_left_domain.domain_min is not None and new_left_domain.domain_max is not None and
                 new_left_domain.domain_min > new_left_domain.domain_max)):
                return False  # Unsatisfiable
            
            if ((new_right_domain.domain_values is not None and not new_right_domain.domain_values) or
                (new_right_domain.domain_min is not None and new_right_domain.domain_max is not None and
                 new_right_domain.domain_min > new_right_domain.domain_max)):
                return False  # Unsatisfiable
            
            # Update the domains if they changed
            if left_changed:
                domain_store.set_domain(left, new_left_domain)
            if right_changed:
                domain_store.set_domain(right, new_right_domain)
            
            return True
        
        # Case 2: Left is a variable, right is a constant
        elif isinstance(left, VariableNode) and isinstance(right, ConstantNode):
            left_domain = domain_store.get_domain(left)
            if left_domain is None:
                return True  # Can't constrain without domain
            
            # Check if the constant is in the domain
            if left_domain.domain_values is not None:
                if right.value not in left_domain.domain_values:
                    return False  # Unsatisfiable
                
                # Update the domain to only include the constant
                new_domain = ConstraintVariable(left, "FD")
                new_domain.set_domain_values({right.value})
                domain_store.set_domain(left, new_domain)
            elif left_domain.domain_min is not None and left_domain.domain_max is not None:
                if right.value < left_domain.domain_min or right.value > left_domain.domain_max:
                    return False  # Unsatisfiable
                
                # Update the domain to only include the constant
                new_domain = ConstraintVariable(left, "FD", right.value, right.value)
                domain_store.set_domain(left, new_domain)
            
            return True
        
        # Case 3: Right is a variable, left is a constant
        elif isinstance(right, VariableNode) and isinstance(left, ConstantNode):
            return self._propagate_equality(right, left, domain_store)
        
        # Case 4: Both are constants
        elif isinstance(left, ConstantNode) and isinstance(right, ConstantNode):
            return left.value == right.value
        
        return True  # Unknown case, assume satisfiable
    
    def _propagate_inequality(self, left: AST_Node, right: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate an inequality constraint: left != right.
        
        Args:
            left: The left-hand side of the inequality
            right: The right-hand side of the inequality
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        # Case 1: Both are variables
        if isinstance(left, VariableNode) and isinstance(right, VariableNode):
            left_domain = domain_store.get_domain(left)
            right_domain = domain_store.get_domain(right)
            
            if left_domain is None or right_domain is None:
                return True  # Can't constrain without domains
            
            # If both domains are singletons, check if they're different
            if left_domain.is_singleton() and right_domain.is_singleton():
                left_value = left_domain.get_value()
                right_value = right_domain.get_value()
                return left_value != right_value
            
            return True  # Not singletons, so constraint is satisfiable
        
        # Case 2: Left is a variable, right is a constant
        elif isinstance(left, VariableNode) and isinstance(right, ConstantNode):
            left_domain = domain_store.get_domain(left)
            if left_domain is None:
                return True  # Can't constrain without domain
            
            # If the domain is a singleton equal to the constant, it's unsatisfiable
            if left_domain.is_singleton() and left_domain.get_value() == right.value:
                return False
            
            # If the domain is explicitly enumerated, remove the constant
            if left_domain.domain_values is not None:
                if len(left_domain.domain_values) == 1 and right.value in left_domain.domain_values:
                    return False  # Unsatisfiable
                
                if right.value in left_domain.domain_values:
                    new_values = left_domain.domain_values.copy()
                    new_values.remove(right.value)
                    new_domain = ConstraintVariable(left, "FD")
                    new_domain.set_domain_values(new_values)
                    domain_store.set_domain(left, new_domain)
            
            return True
        
        # Case 3: Right is a variable, left is a constant
        elif isinstance(right, VariableNode) and isinstance(left, ConstantNode):
            return self._propagate_inequality(right, left, domain_store)
        
        # Case 4: Both are constants
        elif isinstance(left, ConstantNode) and isinstance(right, ConstantNode):
            return left.value != right.value
        
        return True  # Unknown case, assume satisfiable
    
    def _propagate_less_than(self, left: AST_Node, right: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate a less-than constraint: left < right.
        
        Args:
            left: The left-hand side of the constraint
            right: The right-hand side of the constraint
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        # Case 1: Both are variables
        if isinstance(left, VariableNode) and isinstance(right, VariableNode):
            left_domain = domain_store.get_domain(left)
            right_domain = domain_store.get_domain(right)
            
            if left_domain is None or right_domain is None:
                return True  # Can't constrain without domains
            
            # Update domains based on the constraint
            changed = False
            
            # Update left domain's max: X < Y ⇒ max(X) ≤ max(Y) - 1
            if right_domain.domain_max is not None:
                new_max = right_domain.domain_max - 1
                if left_domain.domain_max is None or new_max < left_domain.domain_max:
                    if left_domain.domain_min is not None and new_max < left_domain.domain_min:
                        return False  # Unsatisfiable
                    
                    new_domain = ConstraintVariable(left, "FD", left_domain.domain_min, new_max)
                    if left_domain.domain_values is not None:
                        new_values = {v for v in left_domain.domain_values if v <= new_max}
                        if not new_values:
                            return False  # Unsatisfiable
                        new_domain.set_domain_values(new_values)
                    
                    domain_store.set_domain(left, new_domain)
                    changed = True
            
            # Update right domain's min: X < Y ⇒ min(Y) ≥ min(X) + 1
            if left_domain.domain_min is not None:
                new_min = left_domain.domain_min + 1
                if right_domain.domain_min is None or new_min > right_domain.domain_min:
                    if right_domain.domain_max is not None and new_min > right_domain.domain_max:
                        return False  # Unsatisfiable
                    
                    new_domain = ConstraintVariable(right, "FD", new_min, right_domain.domain_max)
                    if right_domain.domain_values is not None:
                        new_values = {v for v in right_domain.domain_values if v >= new_min}
                        if not new_values:
                            return False  # Unsatisfiable
                        new_domain.set_domain_values(new_values)
                    
                    domain_store.set_domain(right, new_domain)
                    changed = True
            
            return True
        
        # Case 2: Left is a variable, right is a constant
        elif isinstance(left, VariableNode) and isinstance(right, ConstantNode):
            left_domain = domain_store.get_domain(left)
            if left_domain is None:
                return True  # Can't constrain without domain
            
            # Update left domain's max
            if left_domain.domain_min is not None and left_domain.domain_min >= right.value:
                return False  # Unsatisfiable
            
            new_domain = ConstraintVariable(left, "FD", left_domain.domain_min, right.value - 1)
            if left_domain.domain_values is not None:
                new_values = {v for v in left_domain.domain_values if v < right.value}
                if not new_values:
                    return False  # Unsatisfiable
                new_domain.set_domain_values(new_values)
            
            domain_store.set_domain(left, new_domain)
            return True
        
        # Case 3: Right is a variable, left is a constant
        elif isinstance(right, VariableNode) and isinstance(left, ConstantNode):
            right_domain = domain_store.get_domain(right)
            if right_domain is None:
                return True  # Can't constrain without domain
            
            # Update right domain's min
            if right_domain.domain_max is not None and right_domain.domain_max <= left.value:
                return False  # Unsatisfiable
            
            new_domain = ConstraintVariable(right, "FD", left.value + 1, right_domain.domain_max)
            if right_domain.domain_values is not None:
                new_values = {v for v in right_domain.domain_values if v > left.value}
                if not new_values:
                    return False  # Unsatisfiable
                new_domain.set_domain_values(new_values)
            
            domain_store.set_domain(right, new_domain)
            return True
        
        # Case 4: Both are constants
        elif isinstance(left, ConstantNode) and isinstance(right, ConstantNode):
            return left.value < right.value
        
        return True  # Unknown case, assume satisfiable
    
    def _propagate_greater_than(self, left: AST_Node, right: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate a greater-than constraint: left > right.
        
        Args:
            left: The left-hand side of the constraint
            right: The right-hand side of the constraint
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        # This is equivalent to right < left
        return self._propagate_less_than(right, left, domain_store)
    
    def _propagate_less_than_or_equal(self, left: AST_Node, right: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate a less-than-or-equal constraint: left <= right.
        
        Args:
            left: The left-hand side of the constraint
            right: The right-hand side of the constraint
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        # Similar to _propagate_less_than, but with <= instead of <
        # Case 1: Both are variables
        if isinstance(left, VariableNode) and isinstance(right, VariableNode):
            left_domain = domain_store.get_domain(left)
            right_domain = domain_store.get_domain(right)
            
            if left_domain is None or right_domain is None:
                return True  # Can't constrain without domains
            
            # Update domains based on the constraint
            changed = False
            
            # Update left domain's max
            if right_domain.domain_max is not None:
                if left_domain.domain_max is None or left_domain.domain_max > right_domain.domain_max:
                    new_max = right_domain.domain_max
                    if left_domain.domain_min is not None and new_max < left_domain.domain_min:
                        return False  # Unsatisfiable
                    
                    new_domain = ConstraintVariable(left, "FD", left_domain.domain_min, new_max)
                    if left_domain.domain_values is not None:
                        new_values = {v for v in left_domain.domain_values if v <= right_domain.domain_max}
                        if not new_values:
                            return False  # Unsatisfiable
                        new_domain.set_domain_values(new_values)
                    
                    domain_store.set_domain(left, new_domain)
                    changed = True
            
            # Update right domain's min
            if left_domain.domain_min is not None:
                if right_domain.domain_min is None or right_domain.domain_min < left_domain.domain_min:
                    new_min = left_domain.domain_min
                    if right_domain.domain_max is not None and new_min > right_domain.domain_max:
                        return False  # Unsatisfiable
                    
                    new_domain = ConstraintVariable(right, "FD", new_min, right_domain.domain_max)
                    if right_domain.domain_values is not None:
                        new_values = {v for v in right_domain.domain_values if v >= left_domain.domain_min}
                        if not new_values:
                            return False  # Unsatisfiable
                        new_domain.set_domain_values(new_values)
                    
                    domain_store.set_domain(right, new_domain)
                    changed = True
            
            return True
        
        # Case 2: Left is a variable, right is a constant
        elif isinstance(left, VariableNode) and isinstance(right, ConstantNode):
            left_domain = domain_store.get_domain(left)
            if left_domain is None:
                return True  # Can't constrain without domain
            
            # Update left domain's max
            if left_domain.domain_min is not None and left_domain.domain_min > right.value:
                return False  # Unsatisfiable
            
            new_domain = ConstraintVariable(left, "FD", left_domain.domain_min, right.value)
            if left_domain.domain_values is not None:
                new_values = {v for v in left_domain.domain_values if v <= right.value}
                if not new_values:
                    return False  # Unsatisfiable
                new_domain.set_domain_values(new_values)
            
            domain_store.set_domain(left, new_domain)
            return True
        
        # Case 3: Right is a variable, left is a constant
        elif isinstance(right, VariableNode) and isinstance(left, ConstantNode):
            right_domain = domain_store.get_domain(right)
            if right_domain is None:
                return True  # Can't constrain without domain
            
            # Update right domain's min
            if right_domain.domain_max is not None and right_domain.domain_max < left.value:
                return False  # Unsatisfiable
            
            new_domain = ConstraintVariable(right, "FD", left.value, right_domain.domain_max)
            if right_domain.domain_values is not None:
                new_values = {v for v in right_domain.domain_values if v >= left.value}
                if not new_values:
                    return False  # Unsatisfiable
                new_domain.set_domain_values(new_values)
            
            domain_store.set_domain(right, new_domain)
            return True
        
        # Case 4: Both are constants
        elif isinstance(left, ConstantNode) and isinstance(right, ConstantNode):
            return left.value <= right.value
        
        return True  # Unknown case, assume satisfiable
    
    def _propagate_greater_than_or_equal(self, left: AST_Node, right: AST_Node, domain_store: DomainStore) -> bool:
        """
        Propagate a greater-than-or-equal constraint: left >= right.
        
        Args:
            left: The left-hand side of the constraint
            right: The right-hand side of the constraint
            domain_store: The store of variable domains
            
        Returns:
            True if the constraint is satisfiable, False otherwise
        """
        # This is equivalent to right <= left
        return self._propagate_less_than_or_equal(right, left, domain_store)


class CLPModule(BaseProver):
    """
    Constraint Logic Programming module.
    
    This class provides a declarative framework for solving problems that combine
    logical deduction with constraint satisfaction over specific domains.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface, 
                unification_engine: UnificationEngine,
                solver_registry: Optional[Dict[str, ConstraintSolver]] = None):
        """
        Initialize the CLP module.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            unification_engine: Engine for unifying logical expressions
            solver_registry: Optional registry of constraint solvers
        """
        self.kr_system_interface = kr_system_interface
        self.unification_engine = unification_engine
        self.solver_registry = solver_registry or {}
    
    @property
    def name(self) -> str:
        """Get the name of this prover."""
        return "CLPModule"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get the capabilities of this prover."""
        capabilities = super().capabilities.copy()
        capabilities.update({
            "constraint_solving": True,
            "first_order_logic": True,
            "arithmetic": True  # Limited to constraints
        })
        return capabilities
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """
        Determine if this prover can handle the given goal and context.
        
        The CLP module can handle goals and contexts that involve constraints.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            
        Returns:
            True if this prover can handle the given goal and context, False otherwise
        """
        # Check if the goal or any context assertion contains constraints
        from godelOS.inference_engine.coordinator import InferenceCoordinator
        coordinator = InferenceCoordinator(self.kr_system_interface, {})
        
        if coordinator._contains_constraints(goal_ast):
            return True
        
        for ast in context_asts:
            if coordinator._contains_constraints(ast):
                return True
        
        return False
    
    def solve_clp_query(self, clp_program_asts: Set[AST_Node], query_ast: AST_Node,
                      max_solutions: int = 1, labeling_strategy: str = "default") -> List[Dict[VariableNode, AST_Node]]:
        """
        Solve a CLP query.
        
        This method implements the full CLP query solving algorithm, including:
        1. Setting up the constraint and domain stores
        2. Executing SLD resolution with constraint handling
        3. Performing constraint propagation
        4. Finding solutions through labeling/enumeration
        
        Args:
            clp_program_asts: The CLP program (facts and rules)
            query_ast: The query to solve
            max_solutions: Maximum number of solutions to find
            labeling_strategy: Strategy for labeling/enumeration
            
        Returns:
            A list of solutions, each as a dictionary mapping variables to values
        """
        logger.info(f"CLPModule solving query: {query_ast}")
        logger.info(f"Max solutions: {max_solutions}")
        logger.info(f"Labeling strategy: {labeling_strategy}")
        
        # 1. Parse the program and query into CLP clauses
        program_clauses = self._parse_program(clp_program_asts)
        query_clause = self._parse_query(query_ast)
        
        # 2. Initialize constraint and domain stores
        constraint_store = ConstraintStore()
        domain_store = DomainStore()
        
        # 3. Initialize the variable domains
        self._initialize_domains(query_clause, domain_store)
        
        # 4. Execute modified SLD resolution with constraint handling
        solutions = self._solve(query_clause, program_clauses, constraint_store, domain_store, max_solutions, labeling_strategy)
        
        return solutions
    
    def _parse_program(self, program_asts: Set[AST_Node]) -> List[CLPClause]:
        """
        Parse a set of AST nodes into CLP clauses.
        
        Args:
            program_asts: The set of AST nodes representing the program
            
        Returns:
            A list of CLP clauses
        """
        clauses = []
        
        for ast in program_asts:
            # Handle implications (rules)
            if isinstance(ast, ConnectiveNode) and ast.connective_type == "IMPLIES":
                head = ast.operands[1]  # The head is the consequent
                body = []
                constraints = []
                
                # The body is the antecedent
                antecedent = ast.operands[0]
                
                # If the antecedent is a conjunction, split it into goals and constraints
                if isinstance(antecedent, ConnectiveNode) and antecedent.connective_type == "AND":
                    for operand in antecedent.operands:
                        if self._is_constraint(operand):
                            constraints.append(operand)
                        else:
                            body.append(operand)
                else:
                    # If the antecedent is not a conjunction, it's a single goal or constraint
                    if self._is_constraint(antecedent):
                        constraints.append(antecedent)
                    else:
                        body.append(antecedent)
                
                clauses.append(CLPClause(head, body, constraints))
            else:
                # Handle facts (no body or constraints)
                clauses.append(CLPClause(ast, [], []))
        
        return clauses
    
    def _parse_query(self, query_ast: AST_Node) -> CLPClause:
        """
        Parse an AST node into a CLP query clause.
        
        Args:
            query_ast: The AST node representing the query
            
        Returns:
            A CLP clause representing the query
        """
        body = []
        constraints = []
        
        # If the query is a conjunction, split it into goals and constraints
        if isinstance(query_ast, ConnectiveNode) and query_ast.connective_type == "AND":
            for operand in query_ast.operands:
                if self._is_constraint(operand):
                    constraints.append(operand)
                else:
                    body.append(operand)
        else:
            # If the query is not a conjunction, it's a single goal or constraint
            if self._is_constraint(query_ast):
                constraints.append(query_ast)
            else:
                body.append(query_ast)
        
        return CLPClause(None, body, constraints)
    
    def _is_constraint(self, ast: AST_Node) -> bool:
        """
        Check if an AST node represents a constraint.
        
        Args:
            ast: The AST node to check
            
        Returns:
            True if the AST node represents a constraint, False otherwise
        """
        # Check if the AST node is an application of a constraint predicate
        if isinstance(ast, ApplicationNode):
            op = ast.operator
            if isinstance(op, ConstantNode):
                # Check if any solver can handle this constraint
                for solver in self.solver_registry.values():
                    if hasattr(solver, 'can_handle_constraint') and solver.can_handle_constraint(ast):
                        return True
        
        return False
    
    def _initialize_domains(self, query_clause: CLPClause, domain_store: DomainStore):
        """
        Initialize the domains of variables in a query.
        
        Args:
            query_clause: The query clause
            domain_store: The domain store to update
        """
        # Collect all variables in the query
        variables = set()
        
        # Helper function to collect variables from an AST node
        def collect_variables(ast: AST_Node):
            if isinstance(ast, VariableNode):
                variables.add(ast)
            elif isinstance(ast, ApplicationNode):
                collect_variables(ast.operator)
                for arg in ast.arguments:
                    collect_variables(arg)
            elif isinstance(ast, ConnectiveNode):
                for operand in ast.operands:
                    collect_variables(operand)
        
        # Collect variables from the query body and constraints
        for goal in query_clause.body:
            collect_variables(goal)
        
        for constraint in query_clause.constraints:
            collect_variables(constraint)
        
        # Initialize domains for all variables
        for var in variables:
            # Default domain for variables is integers from -100 to 100
            # This is a simplification; in a real system, the domain would be inferred
            # from the constraints or specified by the user
            domain = ConstraintVariable(var, "FD", -100, 100)
            domain_store.set_domain(var, domain)
    
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node],
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Attempt to prove a goal using constraint logic programming.
        
        This method treats the goal as a CLP query and the context assertions
        as a CLP program, and attempts to find a solution.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            resources: Optional resource limits for the proof attempt
            
        Returns:
            A ProofObject representing the result of the proof attempt
        """
        start_time = time.time()
        
        logger.info(f"CLPModule attempting to prove: {goal_ast}")
        
        # Set default resource limits if none provided
        if resources is None:
            resources = ResourceLimits(time_limit_ms=10000, depth_limit=100)
        
        # Get the maximum number of solutions to find
        max_solutions = resources.get_limit("max_solutions", 1)
        
        # Get the labeling strategy
        labeling_strategy = resources.get_limit("labeling_strategy", "default")
        
        # Solve the query
        solutions = self.solve_clp_query(context_asts, goal_ast, max_solutions, labeling_strategy)
        
        end_time = time.time()
        time_taken_ms = (end_time - start_time) * 1000
        
        if solutions:
            # Create a successful proof object
            bindings = solutions[0]  # Use the first solution
            
            # Create a proof step for the solution
            proof_steps = []
            for var, value in bindings.items():
                proof_steps.append(ProofStepNode(
                    formula=ApplicationNode(
                        ConstantNode("=", FunctionType([var.type, value.type], self.type_system.get_boolean_type())),
                        [var, value],
                        self.type_system.get_boolean_type()
                    ),
                    rule_name="CLP Solution",
                    premises=[],
                    explanation=f"Variable {var.name} = {value.value}"
                ))
            
            return ProofObject.create_success(
                conclusion_ast=goal_ast,
                bindings=bindings,
                proof_steps=proof_steps,
                used_axioms_rules=context_asts,
                inference_engine_used=self.name,
                time_taken_ms=time_taken_ms,
                resources_consumed={
                    "solutions_found": len(solutions),
                    "labeling_strategy": labeling_strategy
                }
            )
        else:
            # Create a failure proof object
            return ProofObject.create_failure(
                status_message="No solution found",
                inference_engine_used=self.name,
                time_taken_ms=time_taken_ms,
                resources_consumed={
                    "labeling_strategy": labeling_strategy
                }
            )
    
    def _solve(self, query_clause: CLPClause, program_clauses: List[CLPClause],
              constraint_store: ConstraintStore, domain_store: DomainStore,
              max_solutions: int, labeling_strategy: str) -> List[Dict[VariableNode, AST_Node]]:
        """
        Solve a CLP query using modified SLD resolution with constraint handling.
        
        Args:
            query_clause: The query clause
            program_clauses: The program clauses
            constraint_store: The constraint store
            domain_store: The domain store
            max_solutions: Maximum number of solutions to find
            labeling_strategy: Strategy for labeling/enumeration
            
        Returns:
            A list of solutions, each as a dictionary mapping variables to values
        """
        # Add constraints from the query to the constraint store
        for constraint in query_clause.constraints:
            constraint_store.add_constraint(constraint)
        
        # Propagate constraints
        if not self._propagate_constraints(constraint_store, domain_store):
            # Constraints are unsatisfiable
            return []
        
        # If there are no goals left, perform labeling/enumeration
        if not query_clause.body:
            return self._label_variables(domain_store, max_solutions, labeling_strategy)
        
        # Select the first goal to resolve
        selected_goal = query_clause.body[0]
        remaining_goals = query_clause.body[1:]
        
        # Find matching clauses in the program
        solutions = []
        
        for program_clause in program_clauses:
            # Skip clauses that don't match the selected goal
            if not self._can_unify(selected_goal, program_clause.head):
                continue
            
            # Create a copy of the stores for this branch
            branch_constraint_store = ConstraintStore()
            for constraint in constraint_store.get_constraints():
                branch_constraint_store.add_constraint(constraint)
            
            branch_domain_store = DomainStore()
            for var in domain_store.get_all_variables():
                domain = domain_store.get_domain(var)
                if domain:
                    branch_domain_store.set_domain(var, domain)
            
            # Unify the selected goal with the clause head
            bindings, _ = self.unification_engine.unify(selected_goal, program_clause.head)
            
            if bindings is None:
                # Unification failed
                continue
            
            # Apply bindings to the remaining goals
            new_goals = []
            for goal in remaining_goals:
                substitution = {var: bindings[var.var_id] for var in self._get_variables(goal) if var.var_id in bindings}
                new_goals.append(goal.substitute(substitution))
            
            # Add the clause body to the goals
            for goal in program_clause.body:
                substitution = {var: bindings[var.var_id] for var in self._get_variables(goal) if var.var_id in bindings}
                new_goals.append(goal.substitute(substitution))
            
            # Add the clause constraints to the constraint store
            for constraint in program_clause.constraints:
                substitution = {var: bindings[var.var_id] for var in self._get_variables(constraint) if var.var_id in bindings}
                new_constraint = constraint.substitute(substitution)
                branch_constraint_store.add_constraint(new_constraint)
            
            # Propagate constraints
            if not self._propagate_constraints(branch_constraint_store, branch_domain_store):
                # Constraints are unsatisfiable
                continue
            
            # Create a new query clause with the new goals
            new_query_clause = CLPClause(None, new_goals, [])
            
            # Recursively solve the new query
            branch_solutions = self._solve(
                new_query_clause, program_clauses,
                branch_constraint_store, branch_domain_store,
                max_solutions - len(solutions), labeling_strategy
            )
            
            solutions.extend(branch_solutions)
            
            if len(solutions) >= max_solutions:
                break
        
        return solutions
    
    def _can_unify(self, goal: AST_Node, head: AST_Node) -> bool:
        """
        Check if a goal can unify with a clause head.
        
        Args:
            goal: The goal to unify
            head: The clause head
            
        Returns:
            True if the goal can unify with the head, False otherwise
        """
        if head is None:
            return False
        
        # Check if the goal and head have the same structure
        if isinstance(goal, ApplicationNode) and isinstance(head, ApplicationNode):
            # Check if the operators can unify
            if not self._can_unify(goal.operator, head.operator):
                return False
            
            # Check if the number of arguments match
            if len(goal.arguments) != len(head.arguments):
                return False
            
            # We don't need to check if the arguments can unify here,
            # as that will be done during the actual unification
            return True
        
        # For other node types, we just check if they're the same type
        return type(goal) == type(head)
    
    def _get_variables(self, ast: AST_Node) -> Set[VariableNode]:
        """
        Get all variables in an AST node.
        
        Args:
            ast: The AST node
            
        Returns:
            A set of variables
        """
        variables = set()
        
        if isinstance(ast, VariableNode):
            variables.add(ast)
        elif isinstance(ast, ApplicationNode):
            variables.update(self._get_variables(ast.operator))
            for arg in ast.arguments:
                variables.update(self._get_variables(arg))
        elif isinstance(ast, ConnectiveNode):
            for operand in ast.operands:
                variables.update(self._get_variables(operand))
        
        return variables
    
    def _propagate_constraints(self, constraint_store: ConstraintStore, domain_store: DomainStore) -> bool:
        """
        Propagate constraints and prune variable domains.
        
        Args:
            constraint_store: The constraint store
            domain_store: The domain store
            
        Returns:
            True if the constraints are satisfiable, False otherwise
        """
        # Wake up all constraints initially
        constraint_store.wake_up_all()
        # Clear any pre-existing domain change markers so the first pass
        # only reacts to changes actually caused by propagation.
        domain_store.clear_changed_variables()
        
        # Process constraints until no more changes or a constraint is unsatisfiable
        while True:
            constraint = constraint_store.get_next_constraint_to_wake_up()
            if constraint is None:
                break
            
            # Find a solver that can handle this constraint
            solver = None
            for s in self.solver_registry.values():
                if hasattr(s, 'can_handle_constraint') and s.can_handle_constraint(constraint):
                    solver = s
                    break
            
            if solver is None:
                # No solver can handle this constraint
                continue
            
            # Propagate the constraint
            if not solver.propagate(constraint, domain_store):
                # Constraint is unsatisfiable
                return False
            
            # If any domains changed, wake up all constraints again
            if domain_store.get_changed_variables():
                constraint_store.wake_up_all()
                domain_store.clear_changed_variables()
        
        return True
    
    def _label_variables(self, domain_store: DomainStore, max_solutions: int,
                        labeling_strategy: str) -> List[Dict[VariableNode, AST_Node]]:
        """
        Perform labeling/enumeration to find solutions.
        
        Args:
            domain_store: The domain store
            max_solutions: Maximum number of solutions to find
            labeling_strategy: Strategy for labeling/enumeration
            
        Returns:
            A list of solutions, each as a dictionary mapping variables to values
        """
        # Get all variables with non-singleton domains
        variables = []
        for var in domain_store.get_all_variables():
            domain = domain_store.get_domain(var)
            if domain and not domain.is_singleton():
                variables.append(var)
        
        # If all variables have singleton domains, we have a solution
        if not variables:
            solution = {}
            for var in domain_store.get_all_variables():
                domain = domain_store.get_domain(var)
                if domain and domain.is_singleton():
                    value = domain.get_value()
                    solution[var] = ConstantNode(str(value), var.type, value)
            return [solution]
        
        # Select a variable to label based on the strategy
        selected_var = self._select_variable(variables, domain_store, labeling_strategy)
        
        # Get the domain of the selected variable
        domain = domain_store.get_domain(selected_var)
        if domain is None:
            return []
        
        # Get the values to try
        values = self._get_values(domain, labeling_strategy)
        
        # Try each value and collect solutions
        solutions = []
        
        for value in values:
            # Create a copy of the domain store for this branch
            branch_domain_store = DomainStore()
            for var in domain_store.get_all_variables():
                var_domain = domain_store.get_domain(var)
                if var_domain:
                    branch_domain_store.set_domain(var, var_domain)
            
            # Set the domain of the selected variable to the single value
            new_domain = ConstraintVariable(selected_var, domain.domain_type, value, value)
            branch_domain_store.set_domain(selected_var, new_domain)
            
            # Recursively label the remaining variables
            branch_solutions = self._label_variables(
                branch_domain_store,
                max_solutions - len(solutions),
                labeling_strategy
            )
            
            solutions.extend(branch_solutions)
            
            if len(solutions) >= max_solutions:
                break
        
        return solutions
    
    def _select_variable(self, variables: List[VariableNode], domain_store: DomainStore,
                        labeling_strategy: str) -> VariableNode:
        """
        Select a variable to label based on the strategy.
        
        Args:
            variables: The list of variables to select from
            domain_store: The domain store
            labeling_strategy: The labeling strategy
            
        Returns:
            The selected variable
        """
        if labeling_strategy == "first_fail":
            # Select the variable with the smallest domain
            min_size = float('inf')
            selected_var = variables[0]
            
            for var in variables:
                domain = domain_store.get_domain(var)
                if domain:
                    size = domain.get_size()
                    if size < min_size:
                        min_size = size
                        selected_var = var
            
            return selected_var
        else:
            # Default strategy: select the first variable
            return variables[0]
    
    def _get_values(self, domain: ConstraintVariable, labeling_strategy: str) -> List[Any]:
        """
        Get the values to try for a domain based on the strategy.
        
        Args:
            domain: The domain
            labeling_strategy: The labeling strategy
            
        Returns:
            The list of values to try
        """
        if domain.domain_values is not None:
            values = list(domain.domain_values)
        elif domain.domain_min is not None and domain.domain_max is not None:
            values = list(range(domain.domain_min, domain.domain_max + 1))
        else:
            # Default to an empty list if the domain is not well-defined
            return []
        
        if labeling_strategy == "min":
            # Try values from smallest to largest
            values.sort()
        elif labeling_strategy == "max":
            # Try values from largest to smallest
            values.sort(reverse=True)
        elif labeling_strategy == "middle_out":
            # Try values from the middle outwards
            values.sort()
            middle = len(values) // 2
            result = []
            for i in range(len(values)):
                if i % 2 == 0:
                    result.append(values[middle + i // 2])
                else:
                    result.append(values[middle - (i + 1) // 2])
            values = result
        
        return values