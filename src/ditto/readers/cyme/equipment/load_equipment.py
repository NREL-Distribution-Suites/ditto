from loguru import logger
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.load_equipment import LoadEquipment
from gdm.distribution.equipment.phase_load_equipment import PhaseLoadEquipment
from gdm.quantities import ActivePower, ReactivePower
from gdm.distribution.distribution_enum import ConnectionType

class LoadEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Load'
    cyme_section = 'LOADS'

    def parse(self, row):
        name = self.map_name(row)
        connection_type = self.map_connection_type(row)
        phase_loads = self.map_phase_loads(row)
        return LoadEquipment(name=name,
                             phase_loads=phase_loads)

    def map_name(self, row):
        return row['LoadModelName']

    def map_connection_type(self, row):
        connection_number = int(row['Connection'])
        connection_map = {
            0: ConnectionType.STAR, #Yg
            1: ConnectionType.STAR, #Y
            2: ConnectionType.DELTA, #Delta
            3: ConnectionType.OPEN_DELTA, #Open Delta
            4: ConnectinType.DELTA, #Closed Delta
            5: ConnectionType.ZIG_ZAG, # Zg
            6: ConnectionType.STAR, # CT
            7: ConnectionType.DELTA, # Dg - Not sure what this is?
        }
        return connection_map[connection_number]

    def map_phase_loads(self, row):
        # Get the PhaseLoadEquipment with the same name as the Load
        name = row['DeviceNumber']
        phase_loads = []
        for phase in ['A', 'B', 'C']:
            phase_load_name = name + '_' + phase
            phase_load = self.system.get_component(component_type=PhaseLoadEquipment, name=phase_load_name)
            if phase_load is not None:
                phase_loads.append(phase_load)
        return phase_loads

class PhaseLoadEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Load'  
    cyme_section = "CUSTOMER LOADS"

    def parse(self, row):
        name = self.map_name(row)
        real_power = map_real_power(row),
        reactive_power = map_reactive_power(row),
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

    def map_name(self, row):
        phase = row['LoadPhase']
        return row['DeviceNumber']+"_"+str(phase)
        
    def compute_powers(self, row):
        v1 = float(row['Value1'])
        v2 = float(row['Value2'])
        kw = None
        kvar = None
        value_type = int(row['ValueType'])
        # kw and kvar
        if value_type == 0:
            kw = v1
            kvar = v2
        # kva and pf
        elif value_type == 1:
            kw = v1 * v2
            kvar = v1 * (1 - v2**2) ** 0.5
        # kw and pf
        elif value_type == 2:
            kw = v1
            kvar = v1 * (1/v2**2 - 1) ** 0.5
        # amp and pf
        else:
            pass
        return ActivePower(kw, 'kilowatt'), ReactivePower(kvar, 'kilovar')


    def map_real_power(self, row):
        kw, kvar = self.compute_powers(row)
        return ActivePower(kw, 'kilowatt')

    def map_reactive_power(self, row):
        kw, kvar = self.compute_powers(row)
        return ReactivePower(kvar, 'kilovar')
    
    # Is this included in CYME 9.* ? It was in customer class in previous cyme versions
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
