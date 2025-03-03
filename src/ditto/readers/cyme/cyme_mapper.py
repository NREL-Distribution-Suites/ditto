from abc import ABC, abstractproperty

class CymeMapper(ABC):


    def __init__(self, system):
        self.system = system

