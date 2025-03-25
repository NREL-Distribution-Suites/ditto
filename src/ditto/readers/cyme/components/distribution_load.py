from ditto.readers.cyme.cyme_mapper import CymeMapper
from ditto.readers.cyme.equipment.load_equipment import LoadEquipmentMapper
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm import Phase
from loguru import logger

class DistributionLoadMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'  
    cyme_section = "LOAD EQUIVALENT"


    def parse(self, row):
        name = self.map_name(row)
        bus = self.map_bus(row)
        phases = self.map_phases(row)
        equipment = self.map_equipment(row)
        if len(phases) == 0:
            logger.warning(f"Load {name} has no kW values. Skipping...")
            return None
        return DistributionLoad(name=name,
                                bus=bus,
                                phases=phases,
                                equipment=equipment)
        
    def map_name(self, row):
        return row["LoadModelName"]

    def map_bus(self, row):
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
        if row['Value1A'] is not None:
            phases.append(Phase.A)
        if row['Value1B'] is not None:
            phases.append(Phase.B)
        if row['Value1C'] is not None:
            phases.append(Phase.C)
        return phases

    def map_equipment(self, row):
        mapper = LoadEquipmentMapper(self.system)
        equipment = mapper.parse(row)
        return equipment
