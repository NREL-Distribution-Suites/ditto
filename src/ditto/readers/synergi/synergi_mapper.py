from abc import ABC, abstractproperty

class SynergiMapper(ABC):


    def __init__(self, model):
        self.model = model

