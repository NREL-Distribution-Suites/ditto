from ditto.readers.cyme.utils import read_cyme_data
from ditto.readers.cyme.cyme_mapper import CymeMapper
from ditto.readers.cyme.equipment.load_equipment import LoadEquipmentMapper
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm.distribution.enums import Phase
from loguru import logger

class DistributionLoadMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Load'  
    cyme_section = 'CUSTOMER LOADS'


    def parse(self, row, section_id_sections, load_file):
        name = self.map_name(row)
        bus = self.map_bus(row, section_id_sections)
        phases = self.map_phases(row)
        equipment = self.map_equipment(row, load_file)
        if len(phases) == 0:
            logger.warning(f"Load {name} has no kW values. Skipping...")
            return None
        return DistributionLoad(name=name,
                                bus=bus,
                                phases=phases,
                                equipment=equipment)
        
    def map_name(self, row):
        load_phase = row["LoadPhase"]
        return row["DeviceNumber"]+"_"+str(load_phase)

    def map_bus(self, row, section_id_sections):
        section_id = row['SectionID']
        section = section_id_sections[section_id]
        from_bus_name = section["FromNodeID"]
        to_bus_name = section["ToNodeID"]
        to_bus = None
        from_bus = None
        try:
            from_bus = self.system.get_component(component_type=DistributionBus,name=from_bus_name)
        except Exception as e:    
            pass

        try:
            to_bus = self.system.get_component(component_type=DistributionBus,name=to_bus_name)
        except Exception as e:
            pass

        if from_bus is None:
            return to_bus
        if from_bus is None:
            logger.warning(f"Load {section_id} has no bus")
        return from_bus

        bus_name = row["NodeID"]
        bus = None
        try:
            bus = self.system.get_component(component_type=DistributionBus, name=bus_name)
        except Exception as e:    
            pass

        if bus is None:
            logger.warning(f"Load {row['NodeID']} has no bus")
        return bus

    def map_phases(self, row):
        phases = []
        if row['LoadPhase'] is not None:
            phase = row['LoadPhase']
            if phase == 'A':
                phases.append(Phase.A)
            elif phase == 'B':
                phases.append(Phase.B)
            elif phase == 'C':
                phases.append(Phase.C)
        return phases

    def map_equipment(self, row, load_file):
        mapper = LoadEquipmentMapper(self.system)
        equipment_data = read_cyme_data(load_file, mapper.cyme_section)
        for idx, equipment_row in equipment_data.iterrows():
            if equipment_row['DeviceNumber'] == row['DeviceNumber']:
                equipment = mapper.parse(equipment_row, row)
                return equipment
        return None
