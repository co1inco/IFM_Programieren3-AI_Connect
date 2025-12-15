from typing import *
from abc import abstractmethod
from cps import *
from cps import CpsState

TVar = TypeVar('TVar')
TVal = TypeVar('TVal')

class BtSearchTools(Generic[TVar, TVal]):
    
    @abstractmethod
    def get_next_variable(self, state : CpsState[TVar, TVal]):
        """
        Get the next variable that should be assigned
        """
        raise NotImplementedError()
    
    @abstractmethod
    def get_values(self, state : CpsState[TVar, TVal], variable : TVar) -> List[TVal]:
        """
        """
        raise NotImplementedError()
    
    @abstractmethod
    def inference(self, state : CpsState[TVar, TVal], variable : TVar, value : TVal) -> bool:
        """
        """
        raise NotImplementedError()


class BtSearch(Generic[TVar, TVal]):
    """
    Base container for Backtracking search.
    The detailed behavior is specified by the BtSearchTools passed in
    """
    
    _tool : BtSearchTools
    
    count : int
    result : CpsState[TVar, TVal] | None
    
    dead_ends : List[CpsState[TVar, TVal]]
    trace : List[CpsState[TVar, TVal]]
    
    def __init__(self, tool: BtSearchTools):
        self._tool = tool
        self.count = 0
        self.dead_ends = []
        self.trace = []
        
    
    @staticmethod
    def search(tool: BtSearchTools, initialState : CpsState[TVar, TVal]) -> 'BtSearch[TVar, TVal]':
        instance = BtSearch(tool)
        instance.result = instance._search(initialState)
        return instance
        
    def _search(self, state : CpsState[TVar, TVal]) -> CpsState[TVar, TVal] | None:
        
        self.trace.append(state)
        
        if state.is_complete():
            return state
        
        if not state.is_consistent():
            return None
        
        self.count = self.count + 1
        
        variable = self._tool.get_next_variable(state)
        if variable is None:
            return None
        
        recursed = False
        for value in self._tool.get_values(state, variable):
            
            if state.will_be_consistent(variable, value):
                new_state = state.assign(variable, value)
                
                if self._tool.inference(new_state, variable, value):
                    recursed = True
                    result = self._search(new_state)
                    
                    if result is not None:
                        return result
        
        if not recursed:
            self.dead_ends.append(state)
        
        return None
    

def get_bt_result(bt_search : BtSearch[TVar, TVal]) -> Dict[TVal, List[TVar]]:
    
    print("Step count: ", bt_search.count)
    if bt_search.result is None:
        print("No result found")
        return {}
    
    
    d = {}
    
    assignments = bt_search.result.get_assignments()
    
    for val in bt_search.result.get_values():
        
        d[val] = bt_search.result.get_variables_with(val)
        # l = []
        
        # for var in assignments:
        #     if assignments[var] == val:
        #         l.append(var)
                
        # d[val] = l
        
    return d
    
    

class SimpleBtSearch(Generic[TVar, TVal], BtSearchTools[TVar, TVal]):
    """
    Simple backtracking / recursive decent search. No optimizations
    """
    
    def __init__(self):
        pass
    
    
    def get_next_variable(self, state : CpsState[TVar, TVal]):
        """
        Get the next variable that should be assigned
        """
        
        unassigned = state.get_unassigned()
        if len(unassigned) == 0:
            return None
        return unassigned[0]
        
    
    def get_values(self, state : CpsState[TVar, TVal], variable : TVar) -> List[TVal]:
        """
        """
        return state.get_values()
        
    
    def inference(self, state : CpsState[TVar, TVal], variable : TVar, value : TVal) -> bool:
        return True


class MrvBtSearch(Generic[TVar, TVal], BtSearchTools[TVar, TVal]):
    """Backtracking search using MRV and Gradheuristik

    Args:
        Generic (_type_): 
        BtSearchTools (_type_): 
    """
    
    def __init__(self):
        pass
    
    
    def get_next_variable(self, state : CpsState[TVar, TVal]):
        """
        Get the next variable that should be assigned
        """
        
        # MRV
        open_values = 10000
        variables = []
        
        for var in state.get_unassigned():
            consistent_values = 0
            
            for val in state.get_values():
                if state.will_be_consistent(var, val):
                    consistent_values = consistent_values + 1
            
            if consistent_values == 0:
                raise Exception("No consistent value found")
            
            if consistent_values > 0 and consistent_values < open_values:
                variables = [var]
                open_values = consistent_values
            
            elif consistent_values == open_values:
                variables.append(var)
                
        if len(variables) == 0:
            # something is wrong
            raise Exception("MRV selected no value")
            # return None
        
        if len(variables) == 1:
            return variables[0]
        
        
        # Gradheuristik
        variable = None
        variable_constraints = -1
        
        
        for var in variables:
            constraints = state.get_constraints_for(var)
            
            # count the number of constraints that point to unassigned variables
            c = 0
            for to in constraints:
                if to is not None and state.get_assignment(to) is None:
                    c = c + 1
            
            # if c == 0:
            #     raise Exception(f"Variable without constraint: {var}")
            
            if c > variable_constraints:
                variable = var
                variable_constraints = c
        
        if variable is None:
            raise Exception(f"Gradheuristik selected no value. Variables: {variables}")
        
        return variable
        
        
    
    def get_values(self, state : CpsState[TVar, TVal], variable : TVar) -> List[TVal]:
        """
        """
        return state.get_values()
        
    
    def inference(self, state : CpsState[TVar, TVal], variable : TVar, value : TVal) -> bool:
        return True
    