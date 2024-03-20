from enum import IntEnum

from gdm import Phase

PHASE_MAPPER = {
    "0": Phase.N,
    "1": Phase.A, 
    "2": Phase.B, 
    "3": Phase.C, 
    "4": Phase.N,
    }

UNIT_MAPPER = {
    0: "m", 
    1: "mi", 
    2: "kft", 
    3: "km", 
    4: "m", 
    5: "ft", 
    6: "in", 
    7: "cm"
    }

class LoadTypes(IntEnum):
    CONST_POWER = 1
    CONST_IMPEDANCE = 2
    CONST_P__QUARDRATIC_Q = 3
    LINEAR_P__QUARDRATIC_Q = 4
    CONST_CURRENT = 5
    ZIP = 8