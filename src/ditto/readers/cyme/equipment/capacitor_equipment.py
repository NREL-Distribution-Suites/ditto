from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.quantities import PositiveReactivePower, PositiveResistance, PositiveReactance
from gdm.distribution.equipment.phase_capacitor_equipment import PhaseCapacitorEquipment
from gdm.distribution.equipment.capacitor_equipment import CapacitorEquipment
from gdm import ConnectionType
from gdm.quantities import PositiveVoltage

class CapacitorEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'SHUNT CAPACITOR'

    def parse(self, row):
        name = self.map_name(row)
        nominal_voltage = self.map_nominal_voltage(row)
        phase_capacitors = self.map_phase_capacitors(row)
        return CapacitorEquipment(name=name,
                                  phase_capacitors=phase_capacitors,
                                  nominal_voltage=nominal_voltage)

    def map_name(self, row):
        return row["ID"]
    
    def map_nominal_voltage(self, row):
        return PositiveVoltage(row["KV"], "kilovolt")

    def map_phase_capacitors(self, row):
        phase_capacitors = []
        number_of_phases = 3 if row["Type"] > 1 else 1
        
        for phase in range(1, number_of_phases + 1):
            mapper = PhaseCapacitorEquipmentMapper(self.system)
            phase_capacitor = mapper.parse(row, phase)
            phase_capacitor.num_banks_on = number_of_phases
            phase_capacitors.append(phase_capacitor)
        return phase_capacitors


class PhaseCapacitorEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'SHUNT CAPACITOR'

    def parse(self, row, phase):
        name = self.map_name(row, phase)
        rated_capacity = self.map_rated_capacity(row)
        num_banks_on = self.map_num_banks_on(row, phase)
        return PhaseCapacitorEquipment(name = name,
                                       rated_capacity=rated_capacity,
                                       num_banks_on=num_banks_on)

    def map_name(self, row, phase):
        if phase == 1:
            return row["ID"] + "_A"
        if phase == 2:
            return row["ID"] + "_B"
        if phase == 3:
            return row["ID"] + "_C"


    def map_rated_capacity(self, row):
        return PositiveReactivePower(row["KVAR"],'kilovar')
