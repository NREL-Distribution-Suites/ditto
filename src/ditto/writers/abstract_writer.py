from abc import ABC, abstractmethod

from gdm import DistributionSystem


class AbstractWriter(ABC):
    def __init__(self, system: DistributionSystem):
        self.system = system

    @abstractmethod
    def write(self) -> None:
        ...
