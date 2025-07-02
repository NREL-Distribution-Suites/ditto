from loguru import logger
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.distribution.equipment.distribution_transformer_equipment import DistributionTransformerEquipment
from gdm.quantities import ActivePower, ReactivePower
from gdm.distribution.enums import ConnectionType

class DistributionTransformerMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'TRANSFORMER SETTING'

    def parse(self, network_row, section_id_sections):
        name = self.map_name(row)
        buses = self.map_buses(row, section_id_sections)
        winding_phases = self.map_winding_phases(row)
        equipment = self.map_equipment(row, network_row)
        return DistributionTransformerEquipment(name=name,
                                                buses=buses,
                                                winding_phases=winding_phases,
                                                equipment=equipment)

    def map_name(self, row):
        name = row['SectionID']
        return name

    def map_buses(self, row, section_id_sections):
        section_id = str(row['SectionID'])
        section = section_id_sections[section_id]
        from_bus_name = section['FromNodeID']
        to_bus_name = section['ToNodeID']

        from_bus = self.system.get_component(component_type=DistributionBus, name=from_bus_name)
        to_bus = self.system.get_component(component_type=DistributionBus, name=to_bus_name)
        return [from_bus, to_bus]

    def map_winding_phases(self, row):
        section_id = str(row['SectionID'])
        section = section_id_sections[section_id]
        phase = section['Phase']
        phases = []
        if 'A' in phase:
            phases.append(Phase.A)
        if 'B' in phase:
            phases.append(Phase.B)
        if 'C' in phase:
            phases.append(Phase.C)
        return winding_phases

    def map_equipment(self, row, network_row):
        transformer_id = row['EqID']
        equipment = self.system.get_component(component_type=DistributionTransformerEquipment, name=transformer_id)
        return equipment
