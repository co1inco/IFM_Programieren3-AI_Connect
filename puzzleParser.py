import pandas as pd
import re
from typing import *


##### Variables

class PzVariable:
    name : str
    clues_ident : List[str]

    def __init__(self, name : str, clue_ident : List[str]):
        self.name = name
        self.clues_ident = clue_ident

    def is_for_clue_value(self, clue_ident : str):
        for c in self.clues_ident:
            if c == clue_ident:
                return True
        return False
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()
        


class PzVariableGroup:
    name : str
    variables : List[PzVariable]
    
    def __init__(self, name : str, variables: List[PzVariable]):
        self.name = name
        self.variables = variables
        
    def __str__(self):
        t = list(map(lambda i: str(i), self.variables))
    
        return f'[{", ".join(t)}] "{self.name}"'
        # return f'[{", ".join(self.variables)}] {self.name}'
    
    def __repr__(self):
        return self.__str__()


def parse_puzzle_variable(text : str, house_count : int) -> List[PzVariableGroup]:
    
    # build variables matcher
    x = []
    for i in range(0, house_count):
        x.append('`(.*?)`')
    var_parser = ", ".join(x)
    
    
    raw_variables = re.findall(r' - (.*?): ' + var_parser, text)
    
    variables = []
    for group in raw_variables:
        group_name = group[0]
        
        # clean-up / transform the variables that they match with their usage in clues
        group_variables = []
        for v in group[1:]:
            if ("child" in group_name):
                group_variables.append(PzVariable("c." + v, [f'child is named {v}', f'mother of {v}']))
                
            elif "month" in group_name:
                if v == "jan": 
                    group_variables.append(PzVariable(v, ["january"]))
                else:
                    group_variables.append(PzVariable(v, [v]))
            
            elif "favorite color" in group_name:
                group_variables.append(PzVariable("f." + v, ["favorite color is " + v, "loves " + v]))
                
            elif "hair colors" in group_name:
                group_variables.append(PzVariable("h." + v, [v + " hair"]))
            
            # elif "keep unique animals" in group_name:
            #     l.append(f'{v} kepper')
                
            elif "hip hop" == v:
                group_variables.append(PzVariable(v, ["hip-hop"]))
                
            elif "swede" == v:
                group_variables.append(PzVariable(v, ["swedish"]))
            
            elif "ford f150" == v:
                group_variables.append(PzVariable(v, ["Ford F-150"]))
            
            elif "cat" == v: 
                group_variables.append(PzVariable(v, [" cat"])) # prevent match with vacation
                        
            else:
                v_mod = v
                if v_mod.endswith('ing'):
                    v_mod = v_mod[:-3]
                elif v_mod.endswith('s'):
                    v_mod = v_mod[:-1]
                group_variables.append(PzVariable(v, [v_mod]))
        
        variables.append(PzVariableGroup(group_name, group_variables))

    return variables


#### Clues

class PzClue:
    clue : str
    variables : List[str]
    function : str | None
    
    def __init__(self, clue : str, vars : List[str], func : str | None):
        self.clue = clue
        self.variables = vars
        self.function = func

    def is_valid(self):
        return self.function is not None
    
    def __str__(self):
        return f'{self.variables} -> {self.function}; {self.clue}'
    
    def __repr__(self):
        return self.__str__()
    

def check_for_clue(var1, var2, regex, text):
    
    sa = regex.replace("%1", var1).replace("%2", var2)
    if re.search(sa, text, re.IGNORECASE):
        return True
    
    sb = regex.replace("%1", var2).replace("%2", var1)
    if re.search(sb, text, re.IGNORECASE):
        return True
    
    return False

def check_for_single_clue(var1, regex, text):
    
    sa = regex.replace("%1", var1)
    if re.search(sa, text, re.IGNORECASE):
        return True
    
    return False

def analyze_clue(vars, clue):
    
    if len(vars) == 1:
        if check_for_single_clue(vars[0], "%1(.*?) not in the first house", clue):
            return "not1"
        if check_for_single_clue(vars[0], "%1(.*?) not in the second house", clue):
            return "not2"
        if check_for_single_clue(vars[0], "%1(.*?) not in the third house", clue):
            return "not3"
        if check_for_single_clue(vars[0], "%1(.*?) not in the fourth house", clue):
            return "not4"
        if check_for_single_clue(vars[0], "%1(.*?) not in the fifth house", clue):
            return "not5"
        if check_for_single_clue(vars[0], "%1(.*?) not in the sixth house", clue):
            return "not6"
        if check_for_single_clue(vars[0], "%1(.*?) first house", clue):
            return "is1"
        if check_for_single_clue(vars[0], "%1(.*?) second house", clue):
            return "is2"
        if check_for_single_clue(vars[0], "%1(.*?) third house", clue):
            return "is3"
        if check_for_single_clue(vars[0], "%1(.*?) fourth house", clue):
            return "is4"
        if check_for_single_clue(vars[0], "%1(.*?) fifth house", clue):
            return "is5"
        if check_for_single_clue(vars[0], "%1(.*?) sixth house", clue):
            return "is6"
    
    if len(vars) == 2:
        if check_for_clue(vars[0], vars[1], "one house between(.*?)%1(.*?)%2", clue):
            return "oneBetween"
        if check_for_clue(vars[0], vars[1], "two houses between(.*?)%1(.*?)%2", clue):
            return "twoBetween"
        if check_for_clue(vars[0], vars[1], "%1(.*?)%2(.*?)next to each other", clue):
            return "nextTo"
        if check_for_clue(vars[0], vars[1], "%1(.*?)directly left of(.*?)%2", clue):
            return "dLeftOf"
        if check_for_clue(vars[0], vars[1], "%1(.*?)left of(.*?)%2", clue):
            return "leftOf"
        if check_for_clue(vars[0], vars[1], "%1(.*?)directly right of(.*?)%2", clue):
            return "dRightOf"
        if check_for_clue(vars[0], vars[1], "%1(.*?)right of(.*?)%2", clue):
            return "rightOf"
        # if check_for_clue(vars[0], vars[1], "%1(.*?)is (the |a )?%2", clue):
        if check_for_clue(vars[0], vars[1], "%1(.*?)is(.*?)%2", clue):
            return "equal"

    return None


def resolve_clue_var_name(variables: List[PzVariableGroup], var : str):
    for group in variables:
        for v in group.variables:
            if v.is_for_clue_value(var):
                return v.name
    return None

def analyze_clues(variables: List[PzVariableGroup], raw_clues : List[str]) -> List[PzClue]:

    # sometimes a variable contains another variables value (eg: 'child of alice' and 'alice')
    # all variables are sorted by length, each match is the removed from the clue text.
    # This ensures that none of the shorter variables can match a part from a longer variable
    all_variables = []
    for var_group in variables:
        for var in var_group.variables:
            all_variables.extend(var.clues_ident)
    all_variables = sorted(all_variables, key=len, reverse=True)
    # print(all_variables)
    
    clues = []
    for c in raw_clues:
                           
        # extract all variables used in clue
        vars = []
        test_clue = c
        for var in all_variables:
            if re.search(var, test_clue, re.IGNORECASE):
                vars.append(var)
                # test_clue = test_clue.replace(var, "")
                test_clue = re.sub(re.escape(var), '', test_clue, flags=re.IGNORECASE)
        
        # ensure variables are in the order they appear in the clue
        lower_clue = c.lower()    
        vars = sorted(vars, key=lambda s: lower_clue.find(s.lower()))       
                        
        # find the function the clue implies
        func = analyze_clue(vars, c)
        
        # resolve group name from clue variables
        vars2 = []
        for clue_var in vars:
            og_var = resolve_clue_var_name(variables, clue_var)
            if og_var is None:
                raise Exception(f"Failed to resolve all clue variables: {clue_var} from {variables}")
            vars2.append(og_var)
        
        clues.append( PzClue(c, vars2, func) )

    return clues
    
    
##### Puzzle

class PzPuzzleDefinition:
    house_count : int
    variables : List[PzVariableGroup]
    clues : List[PzClue]
    
    def __init__(self, house_count : int, variables : List[PzVariableGroup], clues):
        self.house_count = house_count
        self.variables = variables
        self.clues = clues

    def is_valid(self):
        for c in self.clues:
            if not c.is_valid():
                return False
        return True
    
    def __repr__(self):
        s = f'Houses: {self.house_count}\n'
        s += 'Vars:\n'
        for v in self.variables:
            s += f' {v}\n'
        
        s += 'Clues:\n'
        for c in self.clues:
            s += f' {c}\n'
        
        return s


def analyze_puzzle_text(text):
    # House count
    result = re.findall(r'There are (\d+) houses, numbered 1 to \d+ from left to right', text)

    if len(result) != 1:
        raise Exception("Invalid house count")

    house_count = int(result[0])
        
    # variables
    variables = parse_puzzle_variable(text, house_count)
    
    # clues
    raw_clues = re.findall(r'\d+. (.*?)\.', text)
    clues = analyze_clues(variables, raw_clues)
    
    return PzPuzzleDefinition(house_count, variables, clues)