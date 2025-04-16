from gdm.distribution.components import DistributionBus, DistributionTransformer
from gdm.distribution.enums import Phase

from ditto.readers.cim_iec_61968_13.equipment.distribution_transformer_equipment import (
    DistributionTransformerEquipmentMapper,
)
from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper


class DistributionTransformerMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row):
        return DistributionTransformer(
            name=self.map_name(row),
            buses=self.map_bus(row),
            equipment=self.map_equipment(row),
            winding_phases=self.map_winding_phases(row),
        )

    def map_name(self, row):
        return row["xfmr"]

    def map_winding_phases(self, row):
        return [[Phase.A, Phase.B, Phase.C], [Phase.A, Phase.B, Phase.C]]

    def map_bus(self, row):
        bus_1_name = row["bus_1"]
        bus_2_name = row["bus_2"]
        bus_1 = self.system.get_component(DistributionBus, bus_1_name)
        bus_2 = self.system.get_component(DistributionBus, bus_2_name)
        return [bus_1, bus_2]

    def map_equipment(self, row):
        xfmr_equip_mapper = DistributionTransformerEquipmentMapper(self.system)
        xfmr_equip = xfmr_equip_mapper.parse(row)
        return xfmr_equip
