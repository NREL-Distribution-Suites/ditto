from ditto.readers.cyme.cyme_mapper import CymeMapper
from ditto.readers.cyme.equipment.phase_voltagesource_equipment import PhaseVoltageSourceEquipmentMapper
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_vsource import DistributionVoltageSource
from gdm.distribution.equipment.voltagesource_equipment import VoltageSourceEquipment



class DistributionVoltageSourceMapper(CymeMapper):
    def __init__(self, cyme_model):
        super().__init__(cyme_model)

    cyme_file = 'Network'
    cyme_section = 'HEADNODES'

    def parse(self, row, feeder_voltage_map):
        name = self.map_name(row)
        bus = self.map_bus(row)
        feeder = bus.feeder
        if feeder is None:
            return None
        feeder_id = feeder.name

        feeder_voltage = feeder_voltage_map.get(feeder_id)

        if feeder_voltage is None or feeder_voltage == '':
            return None

        phases = bus.phases
        equipment = self.map_equipment(bus, feeder_id, feeder_voltage)

        return DistributionVoltageSource.model_construct(name=name,
                                                        feeder=feeder,
                                                        bus=bus,
                                                        phases=phases,
                                                        equipment=equipment)

    def map_name(self, row):
        name = row['NodeID']
        return name
    
    def map_feeder(self, row):
        feeder = row['NetworkID']
        return feeder
    
    def map_bus(self, row):
        bus_name = row['NodeID']
        bus = self.system.get_component(DistributionBus, bus_name)
        return bus

    def map_equipment(self, bus, feeder, feeder_voltage):
        mapper = PhaseVoltageSourceEquipmentMapper(self.system)
        sources = mapper.parse(bus, feeder_voltage)
        return VoltageSourceEquipment.model_construct(
            name=feeder+bus.name+"-source",
            sources=sources
        )
    