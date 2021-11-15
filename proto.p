B1 -> B2 : int;
B1 -> S : str;
S -> B1 : int;
S -> B2 : int;
B2 -> S : str;

"""
global:
    B1 -> S : str; 
    S -> (B1, B2) : int; 
    B1 -> B2: int; 
    B2 -> S: str;

local:
B1: 
    S : !str; 
    S : ?int; 
    B2 : !int;
B2:
    S : ?int
    B1 : ?int
    S : !int
S: 
    B1 : ?str;
    B1 : !int;
    B2 : !int;
    B2 : ?str;
"""