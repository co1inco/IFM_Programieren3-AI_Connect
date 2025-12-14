import pandas as pd
import re
from typing import *


##### Variables

class PzVariableGroup:
    name : str
    variables : List[str]
    
    def __init__(self, name : str, variables: List[str]):
        self.name = name
        self.variables = variables
        
    def __str__(self):
        return f'[{", ".join(self.variables)}] {self.name}'
    
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
        cleaned_variables = []
        for v in group[1:]:
            if ("child" in group_name):
                cleaned_variables.append(f'child is named {v}')
                cleaned_variables.append(f'mother of {v}')
                
            elif "month" in group_name:
                if v == "jan": 
                    cleaned_variables.append("january")
                else:
                    cleaned_variables.append(v)
            
            # elif "keep unique animals" in group_name:
            #     l.append(f'{v} kepper')
                
            elif "hip hop" == v:
                cleaned_variables.append("hip-hop")
                
            elif "swede" == v:
                cleaned_variables.append("swedish")
            
            elif "ford f150" == v:
                cleaned_variables.append("Ford F-150")
            
            elif "cat" == v: 
                cleaned_variables.append(" cat") # prevent match with vacation
                
            else:
                if v.endswith('ing'):
                    v = v[:-3]
                elif v.endswith('s'):
                    v = v[:-1]
                cleaned_variables.append(v)
        
        variables.append(PzVariableGroup(group_name, cleaned_variables))

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


def analyze_clues(variables: List[PzVariableGroup], raw_clues : List[str]) -> List[PzClue]:

    # sometimes a variable contains another variables value (eg: 'child of alice' and 'alice')
    # all variables are sorted by length, each match is the removed from the clue text.
    # This ensures that none of the shorter variables can match a part from a longer variable
    all_variables = []
    for var_group in variables:
        for var in var_group.variables:
            all_variables.append(var)
    all_variables = sorted(all_variables, key=len, reverse=True)
    
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
        
        lower_clue = c.lower()    
        vars = sorted(vars, key=lambda s: lower_clue.find(s.lower()))
                
        # find the function the clue implies
        func = analyze_clue(vars, c)
        
        clues.append( PzClue(c, vars, func) )

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