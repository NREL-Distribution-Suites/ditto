from gdm.distribution.components import DistributionBus, DistributionCapacitor

from ditto.readers.cim_iec_61968_13.equipment.capacitor_equipment import CapacitorEquipmentMapper
from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper
from ditto.readers.cim_iec_61968_13.common import phase_mapper


class DistributionCapacitorMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row):
        return DistributionCapacitor(
            name=self.map_name(row),
            bus=self.map_bus(row),
            phases=self.map_phases(row),
            controllers=self.map_controllers(row),
            equipment=self.map_equipment(row),
        )

    def map_name(self, row):
        return row["capacitor"]

    def map_bus(self, row):
        bus_name = row["bus"]
        bus = self.system.get_component(component_type=DistributionBus, name=bus_name)
        return bus

    def map_phases(self, row):
        phases = row["phase"]
        if phases is None:
            phases = ["A", "B", "C"]
        else:
            phases = phases.split(",")
        return [phase_mapper[phase] for phase in phases]

    def map_controllers(self, row):
        return []

    def map_equipment(self, row):
        mapper = CapacitorEquipmentMapper(self.system)
        equipment = mapper.parse(row)
        return equipment
