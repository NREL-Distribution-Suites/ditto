from loguru import logger
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.distribution.equipment.distribution_transformer_equipment import DistributionTransformerEquipment
from gdm.quantities import ActivePower, ReactivePower
from gdm.distribution.enums import ConnectionType, Phase

class DistributionTransformerMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'TRANSFORMER SETTING'

    def parse(self, row, section_id_sections, transformer_map):
        equipment_row = transformer_map.get(row['EqID'], None)
        name = self.map_name(row)
        buses = self.map_buses(row, section_id_sections)
        winding_phases = self.map_winding_phases(row, section_id_sections, equipment_row)
        equipment = self.map_equipment(row)
        try:
            return DistributionTransformer(name=name,
                                                buses=buses,
                                                winding_phases=winding_phases,
                                                equipment=equipment)
        except Exception as e:
            print(f"Error creating DistributionTransformer {name}: {e}")
            print(buses)
            return None

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

    def map_winding_phases(self, row, section_id_sections, equipment_row):
        section_id = str(row['SectionID'])
        section = section_id_sections[section_id]
        phase = section['Phase']
        if equipment_row is None:
            print(f"Equipment row not found for transformer {row['EqID']}. Assuming 2 windings. {section}")
            equipment_row = {'Type': 2}
        windings_list = []
        if equipment_row['Type'] == 4:
            num_windings = 3
        else:
            num_windings = 2

        for i in range(num_windings):
            winding_phases = []
            if 'A' in phase:
                winding_phases.append(Phase.A)
            if 'B' in phase:
                winding_phases.append(Phase.B)
            if 'C' in phase:
                winding_phases.append(Phase.C)
            windings_list.append(winding_phases)
        return windings_list

    def map_equipment(self, row):
        transformer_id = row['EqID']
        equipment = self.system.get_component(component_type=DistributionTransformerEquipment, name=transformer_id)
        return equipment
