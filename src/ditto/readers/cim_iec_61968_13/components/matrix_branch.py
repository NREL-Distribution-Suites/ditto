from gdm.distribution.components import MatrixImpedanceBranch, DistributionBus
from gdm.distribution.equipment import MatrixImpedanceBranchEquipment
from gdm.quantities import Distance

from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper
from ditto.readers.cim_iec_61968_13.common import phase_mapper


class MatrixImpedanceBranchMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row):
        return MatrixImpedanceBranch(
            name=self.map_name(row),
            buses=self.map_buses(row),
            length=self.map_length(row),
            phases=self.map_phases(row),
            equipment=self.map_equipment(row),
        )

    def map_name(self, row):
        return row["line"]

    def map_buses(self, row):
        bus_1_name = row["bus_1"]
        bus_1 = self.system.get_component(DistributionBus, bus_1_name)
        bus_2_name = row["bus_2"]
        bus_2 = self.system.get_component(DistributionBus, bus_2_name)
        return [bus_1, bus_2]

    def map_length(self, row):
        length = float(row["length"])
        return Distance(length, "m")

    def map_phases(self, row):
        phases = row["phases_1"].split(",")
        return [phase_mapper[phase] for phase in phases]

    def map_equipment(self, row):
        equipment = self.system.get_component(MatrixImpedanceBranchEquipment, row["line_code"])
        return equipment
