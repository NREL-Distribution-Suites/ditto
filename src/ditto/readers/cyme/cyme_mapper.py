from abc import ABC, property

class CymeMapper(ABC):


    def __init__(self, system):
        self.system = system
