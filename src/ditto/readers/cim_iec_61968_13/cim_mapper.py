from abc import ABC

from gdm.distribution import DistributionSystem


class CimMapper(ABC):
    def __init__(self, system: DistributionSystem):
        self.system = system
