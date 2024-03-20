from abc import ABC, abstractmethod

from infrasys.system import System


class Reader(ABC):
    @abstractmethod
    def get_system(self) -> System:
        ...
