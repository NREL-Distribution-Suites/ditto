from enum import Enum


class OpenDSSTestModels(str, Enum):
    FOUR_WIRE = "4wire-Delta-3"
    IEEE13 = "ieee13"
    P4U = "P4U"
