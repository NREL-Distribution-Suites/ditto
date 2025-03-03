from ditto.readers.cyme.cyme_mapper import CymeMapper
from ditto.readers.cyme.equipment.capacitor_equipment import CapacitorEquipmentMapper
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_capacitor import DistributionCapacitor
from gdm import Phase
from loguru import logger

class DistributionCapacitorMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'SHUNT CAPACITOR'

    def parse(self, row, section_id_sections):
        name = self.map_name(row)
        bus = self.map_bus(row, section_id_sections)
        phases = self.map_phases(row)
        controllers = self.map_controllers(row)
        equipment = self.map_equipment(row)
        return DistributionCapacitor(name=name,
                                      bus=bus,
                                      phases=phases,
                                      controllers=controllers,
                                      equipment=equipment)

    def map_name(self, row):
        return row["DeviceNumber"]

    def map_phases(self, row):
        phases = []
        if row["FixedKVARA"]:
            phases.append(Phase.A)
        if row["FixedKVARB"]:
            phases.append(Phase.B)
        if row["FixedKVARC"]:
            phases.append(Phase.C)
        return phases

    def map_bus(self, row, section_id_sections):
        section_id = row["SectionID"]
        section = section_id_sections[section_id]
        from_bus_name = section["FromNodeId"]
        to_bus_name = section["ToNodeId"]
        to_bus = None
        from_bus = None
        try:
            from_bus = self.system.get_component(component_type=DistributionBus,name=from_bus_name)
        except Exception as e:    
            pass

        try:
            to_bus = self.system.get_component(component_type=DistributionBus,name=to_bus_name)
        except:
            pass

        if from_bus is None:
            return to_bus
        if from_bus is None:
            logger.warning(f"Load {section_id} has no bus")
        return from_bus


    def map_controllers(self, row):
        return []

    def map_equipment(self, row):
        mapper = CapacitorEquipmentMapper(self.system)
        equipment = mapper.parse(row)
        return equipment
