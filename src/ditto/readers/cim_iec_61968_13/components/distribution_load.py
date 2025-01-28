from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.components.distribution_bus import DistributionBus

from ditto.readers.cim_iec_61968_13.equipment.load_equipment import LoadEquipmentMapper
from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper
from ditto.readers.cim_iec_61968_13.common import phase_mapper


class DistributionLoadMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row):
        return DistributionLoad(
            name=self.map_name(row),
            bus=self.map_bus(row),
            phases=self.map_phases(row),
            equipment=self.map_equipment(row),
        )

    def map_name(self, row):
        return row["load"]

    def map_bus(self, row):
        bus_name = row["bus"]
        bus = self.system.get_component(component_type=DistributionBus, name=bus_name)
        return bus

    def map_phases(self, row):
        phases = row["phase"]
        if phases is None:
            phases = ["A", "B", "C"]
        return [phase_mapper[phase] for phase in phases]

    def map_equipment(self, row):
        mapper = LoadEquipmentMapper(self.system)
        equipment = mapper.parse(row)
        return equipment
