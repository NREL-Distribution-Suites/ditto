from abc import ABC, abstractmethod

from infrasys.system import System


class AbstractWriter(ABC):

    def __init__(self, system: System):
        self.system = system

    @abstractmethod
    def write(self) -> None:
        ...
