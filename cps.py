from typing import *



TVar = TypeVar('TVar')
TVal = TypeVar('TVal')

class CpsConstraint(Generic[TVal]):
    _predicates : List[Callable[[TVal, TVal], bool]]
    
    def __init__(self, predicate: Callable[[TVal, TVal], bool] = None):
        self._predicates = []
        
        if predicate is not None:
            self._predicates.append(predicate)
    
    def append(self, predicate: Callable[[TVal, TVal], bool]) -> None:
        self._predicates.append(predicate)
        
    def is_conflicting(self, a: TVal, b: TVal) -> bool:
        """
        Check if the two values a and b would conflict with any constraint
        """
        
        for p in self._predicates:
            if not p(a, b):
                return True
        return False
    
        

class CpsConfiguration(Generic[TVar, TVal]):
    _variables : List[TVar]
    _values : List[TVal]
    _constraints: Dict[TVar, Dict[TVar, CpsConstraint[TVal]]]
    
    
    def __init__(self, variables : List[str], values : List[str]):
        self._variables = variables
        self._values = values
        self._constraints = {}

    def variables(self) -> List[TVar]:
        return self._variables.copy()
    
    def values(self) -> List[TVal]:
        return self._values.copy()
    
    def _ensure_exists(self, source : TVar, target : TVar) -> None:
        if source not in self._constraints:
            self._constraints[source] = {}
        
        s = self._constraints[source]
        
        if target not in s:
            s[target] = CpsConstraint()
            
    
    def addConstraint(self, source : TVar, target : TVar, predicate : Callable[[TVal, TVal], bool]) -> None:
        """
        Add a new, one directional constraint
        """
        
        self._ensure_exists(source, target)
        
        self._constraints[source][target].append(predicate)
    
        
    def addConstraintRev(self, source : TVar, target : TVar, predicate : Callable[[TVal, TVal], bool]) -> None:
        """
        Add a new, two directional constraint.
        For the target -> source direction the parameters for the predicate are swapped, so the predicate is still called with (source, target)
        """
        
        self._ensure_exists(source, target)
        self._constraints[source][target].append(predicate)
        
        self._ensure_exists(target, source)
        self._constraints[target][source].append(lambda a, b: predicate(b, a))
    
    
    def addUnaryConstraint(self, source : TVar, predicate : Callable[[TVal], bool]) -> None:
        """
        Add a new unary constraint. 
        This is a constraint that does not have a target (eg. var must be val)
        """
        self._ensure_exists(source, None)
        
        self._constraints[source][None].append(lambda a, b: predicate(a))    
        
        
    def allNotEqual(self, variables : List[TVar]) -> None:
        """
        Constraint all variables against each other. (ie. all must have different values)
        """        
        for source in variables:
            for target in variables:
                if source == target:
                    continue
                
                self.addConstraint(source, target, lambda a, b: a != b)

                
    def notEqual(self, source : TVar, target : TVar) -> None:
        self.addConstraintRev(source, target, lambda a, b: a != b)

        
    def equal(self, source : TVar, target : TVar) -> None:
        self.addConstraintRev(source, target, lambda a, b: a == b)


    def mustBe(self, source : TVar, value : TVal) -> None:
        self.addUnaryConstraint(source, lambda a: a == value)
        

    def get_constraints(self, variable : TVar) -> Dict[TVar, CpsConstraint[TVal] ]:
        return self._constraints[variable]
    
    def __str__(self):
        s = 'CPS-Config {\n'
        s += ' Values: [\n'
        for v in self._values:
            s += f'  {v}\n'    
        s += ' ]\n'
        s += ' Variables: [\n'
        for v in self._variables:
            s += f'  {v}\n'    
        s += ' ]'
        s += '}'
        return s
    
    def __repr__(self):
        return self.__str__()




class CpsState(Generic[TVar, TVal]):
    
    _parent = None
    _variable : TVar = None
    _value : TVal = None
    _config : CpsConfiguration[TVar, TVal]    
    _assigned_cache = None
    _unassigned_cache = None
    
    
    def __init__(self, config : CpsConfiguration[TVar, TVal], parent = None, variable : TVar = None, value : TVal = None):
        self._config = config
        self._parent = parent
        self._variable = variable
        self._value = value
    
    
    def assign(self, variable, value) -> 'CpsState[TVar, TVal]':
        """
        Returns a new state with the given assignment. (A state is immutable)
        """
        if variable not in self._config.variables():
            raise Exception("Invalid variable assigned: " + str(variable), ", allowed: ", self._config.variables())
        
        if value not in self._config.values():
            raise Exception("Invalid value assigned: " + str(value), ", allowed: ", self._config.values())
        
        return CpsState(self._config, self, variable, value)
    
    
    def get_assignments(self) -> Dict[TVar, TVal]:
        """
        Get all assignments
        """
        
        if self._assigned_cache is not None:
            return self._assigned_cache.copy() # return a copy so children can add to it
        
        if self._parent is None:
            return {}
        
        if self._variable is None:
            return self._parent.get_assignments()
        
        t = self._variable, self._value
        
        t2 = self._parent.get_assignments()
        t2[self._variable] = self._value
        self._assigned_cache = t2
        return t2
    
    
    def get_assignment(self, variable: TVar):
        
        assignments = self.get_assignments()
        for var in assignments:
            val = assignments[var]
            
            if var == variable:
                return val
        return None
    
    
    def get_unassigned(self) -> List[TVar]:
        """
        Get all variables that currently have no assignment
        """
        if self._unassigned_cache is not None:
            return self._unassigned_cache.copy()
        
        vars = self._config.variables()
        for a in self.get_assignments():
            if a in vars:
                vars.remove(a)
            
        self._unassigned_cache = vars
        return vars
    
    
    def get_variables(self) -> List[TVar]:
        return self._config.variables().copy()
    
    def get_values(self) -> List[TVal]:
        return self._config.values().copy()
    
    def get_constraints_for(self, variable: TVar) -> Dict[TVar, CpsConstraint[TVal]]:
        return self._config.get_constraints(variable)
    
    def is_complete(self) -> bool:
        """
        check if the CPS has assigned a value to all variables
        """
        return len(self.get_unassigned()) == 0
    
    
    def get_variables_with(self, value : TVal) -> List[TVar]:
        """
        Get all variable the value was assigned to
        """
        return [name for name, val in self.get_assignments().items() if val == value]
    
    
    def is_consistent(self) -> bool:
        
        for var in self.get_variables():
            
            # Assumes an inconsistent value was never assigned
            if self.get_assignment(var) is not None:
                continue
            
            any_consistent = False
            for val in self.get_values():
                if self.will_be_consistent(var, val):
                    any_consistent = True
            
            if not any_consistent:
                return False
        
        return True
                
    
    def will_be_consistent(self, variable: TVar, value: TVal):
        """
        Check if a variable assignment would be consistent
        """
        
        constraints = self._config.get_constraints(variable)
        
        for var in constraints:
            constraint = constraints[var] 
            
            if var is None:
                if constraint.is_conflicting(value, None):
                    return False
            else:
                otherValue = self.get_assignment(var)
                
                if otherValue is not None and constraint.is_conflicting(value, otherValue):
                    return False
                
        return True
    
    
    def get_available_values(self, variable : TVar) -> List[TVal]:
        """
        Get all values that can be assigned to variable
        """
            
        constraints = self._config.get_constraints(variable)
                   
        values = []
        
        for value in self._config.values():
        
            conflict = False
                
            for var in constraints:
                constraint = constraints[var]
                
                # if c is None it is an unary constraint
                if var is None:
                    if constraint.is_conflicting(value, None):
                        conflict = True    
                    continue
                
                otherValue = self.get_assignment(var)
                if otherValue is None: # other is not yet assigned. No check necessary
                    continue
                
                if constraint.is_conflicting(value, otherValue):
                    conflict = True
                    break
                
            if not conflict:
                values.append(value)
                
        return values
            
            
            
        
        
        
    
