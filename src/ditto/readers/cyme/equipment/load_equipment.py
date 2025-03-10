from loguru import logger
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.load_equipment import LoadEquipment
from gdm.distribution.equipment.phase_load_equipment import PhaseLoadEquipment
from gdm.quantities import ActivePower, ReactivePower

class LoadEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'
    cyme_section = 'LOAD EQUIVALENT'

    def parse(self, row):
        name = self.map_name(row)
        phase_loads = self.map_phase_loads(row)
        return LoadEquipment(name=name,
                             phase_loads=phase_loads)

    def map_name(self, row):
        return row['LoadModelName']

    def map_phase_loads(self,row):
        phase_loads = []
        for phase in range(1,4):
            mapper = PhaseLoadEquipmentMapper(self.system)
            phase_load = mapper.parse(row, phase)
            phase_loads.append(phase_load)
        return phase_loads

class PhaseLoadEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Network'  
    cyme_section = "LOAD EQUIVALENT"

    def parse(self, row, phase):
        name = self.map_name(row, phase)
        real_power, reactive_power = self.map_powers(row, phase)
        z_real = self.map_z_real(row)
        z_imag = self.map_z_imag(row)
        i_real = self.map_i_real(row)
        i_imag = self.map_i_imag(row)
        p_real = self.map_p_real(row)
        p_imag = self.map_p_imag(row)
        return PhaseLoadEquipment(name=name,
                                  real_power=real_power,
                                  reactive_power=reactive_power,
                                  z_real=z_real,
                                  z_imag=z_imag,
                                  i_real=i_real,
                                  i_imag=i_imag,
                                  p_real=p_real,
                                  p_imag=p_imag)

    def map_name(self, row, phase):
        if phase == 1:
            return row['NodeID'] + "_A"
        if phase == 2:
            return row['NodeID'] + "_B"
        if phase == 3:
            return row['NodeID'] + "_C"
        
    def map_real_power(self, row, phase):
        if phase == 1:
            kW = float(row["Value1A"])
        elif phase == 2:
            kW = float(row["Value1B"])
        elif phase == 3:
            kW = float(row["Value1C"])
        return ActivePower(kW, 'kilowatt')
    
    def map_reactive_power(self, row, phase):
        if phase == 1:
            kvar = float(row["Value2A"])
        elif phase == 2:
            kvar = float(row["Value2B"])
        elif phase == 3:
            kvar = float(row["Value2C"])
        return ReactivePower(kvar, 'kilovar')
    
    def map_kva_pf(self, row, phase):
        if phase == 1:
            kw = float(row["Value1A"]) * float(row["Value2A"])
            kvar = float(row["Value1A"]) * (1 - float(row["Value2A"])**2) ** 0.5
        elif phase == 2:
            kw = float(row["Value1B"]) * float(row["Value2B"])
            kvar = float(row["Value1B"]) * (1 - float(row["Value2B"])**2) ** 0.5
        elif phase == 3:
            kw = float(row["Value1C"]) * float(row["Value2C"])
            kvar = float(row["Value1C"]) * (1 - float(row["Value2C"])**2) ** 0.5
        return ActivePower(kw, 'kilowatt'), ReactivePower(kvar, 'kilovar')

    def map_kw_pf(self, row, phase):
        if phase == 1:
            kw = float(row["Value1A"])
            
            if float(row["Value2A"]) <= 0 or float(row["Value2A"]) > 1:
                logger.warning("Power factor must be between 0 and 1 (exclusive of 0). Setting kVAR to 0.")
                kvar = 0
            else:
                kvar = float(row["Value1A"]) * ((1 / float(row["Value2A"])**2) - 1) ** 0.5
        elif phase == 2:
            kw = float(row["Value1B"])
            
            if float(row["Value2B"]) <= 0 or float(row["Value2B"]) > 1:
                logger.warning("Power factor must be between 0 and 1 (exclusive of 0). Setting kVAR to 0.")
                kvar = 0
            else:
                kvar = float(row["Value1B"]) * ((1 / float(row["Value2B"])**2) - 1) ** 0.5
        elif phase == 3:
            kw = float(row["Value1C"])
            
            if float(row["Value2C"]) <= 0 or float(row["Value2C"]) > 1:
                logger.warning("Power factor must be between 0 and 1 (exclusive of 0). Setting kVAR to 0.")
                kvar = 0
            else:
                kvar = float(row["Value1C"]) * ((1 / float(row["Value2C"])**2) - 1) ** 0.5
        return ActivePower(kw, 'kilowatt'), ReactivePower(kvar, 'kilovar')

    def map_powers(self, row, phase):
        if row['Format'] == 'KW_KVAR':
            return self.map_real_power(row, phase), self.map_reactive_power(row, phase)
        elif row['Format'] == 'KVA_PF':
            return self.map_kva_pf(row, phase)
        elif row['Format'] == 'KW_PF':
            return self.map_kw_pf(row, phase)
        elif row['Format'] == 'AMP_PF':
            pass #TODO

    def map_z_real(self, row):
        return 1

    def map_z_imag(self, row):
        return 1

    def map_i_real(self, row):
        return 0

    def map_i_imag(self, row):
        return 0

    def map_p_real(self, row):
        return 0

    def map_p_imag(self, row):
        return 0  
