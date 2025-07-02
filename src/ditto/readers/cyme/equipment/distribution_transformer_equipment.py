from loguru import logger
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.distribution_transformer_equipment import DistributionTransformerEquipment   
from gdm.distribution.equipment.distribution_transformer_equipment import WindingEquipment
from gdm.quantities import ActivePower, ReactivePower
from gdm.distribution.enums import ConnectionType

class DistributionTransformerEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'TRANSFORMER'

    def parse(self, row, network_row):
        name = self.map_name(row)
        pct_no_load_loss = self.map_pct_no_load_loss(row)
        pct_full_load_loss = self.map_pct_full_load_loss(row)
        windings = self.map_windings(row, network_row)
        winding_reactances = self.map_winding_reactances(row)
        is_center_tapped = self.map_is_center_tapped(row)
        return DistributionTransformerEquipment(name=name,
                                                pct_no_load_loss=pct_no_load_loss,
                                                pct_full_load_loss=pct_full_load_loss,
                                                windings=windings,
                                                winding_reactances=winding_reactances,
                                                is_center_tapped=is_center_tapped)

    def map_name(self, row):
        name = row['ID']
        return name

    def map_pct_no_load_loss(self, row):
        no_load_loss = float(row['NoLoadLosses'])
        kva = float(row['KVA'])
        pct_no_load_loss = no_load_loss/kva*100
        return pct_no_load_loss

    def map_pct_full_load_loss(self, row):
        # Need to compute rated current and rated resistance to compute full load loss
        rated_current_sec = float(row['KVA'])/float(row['KVLLsec'])
        resistance_pu = float(row['Z1'])/float((1+float(row['XR'])**2)**0.5)
        resistance_sec = float(resistance_pu)*float(float(row['KVLLsec'])**2) / float(row['KVA'])
        pct_full_load_loss = rated_current_sec*resistance_sec
        return pct_full_load_loss

    def map_winding_reactances(self, row):
        xr_ratio = row['XR']
        rx_ratio = 1/xr_ratio
        reactance_pu = row['Z1']/((1+rx_ratio**2)**0.5)
        transformer_type = row['Type']
        if transformer_type == '4':
            winding_reactances = [reactance_pu, reactance_pu, reactance_pu]
        else:
            winding_reactances = [rectance_pu]
        return winding_reactances

    def map_is_center_tapped(self, row):
        transformer_type = row['Type']
        if transformer_type == '4':
            return True
        return False

    def map_windings(self, row, network_row):
        windings = []
        is_center_tapped = False
        if row['Type'] == '4':
            is_center_tapped = True

        winding_mapper1 = WindingEquipmentMapper(self.system)
        import pdb;pdb.set_trace()
        winding_1 = winding_mapper1.parse(row, network_row, winding_number=1)
        winding_mapper2 = WindingEquipmentMapper(self.system)
        winding_2 = winding_mapper2.parse(row, network_row, winding_number=2)
        windings.append(winding_1)
        windings.append(winding_2)
        if is_center_tapped:
            winding_mapper3 = WindingEquipmentMapper(self.system)
            winding_3 = winding_mapper3.parse(row, network_row, winding_number=3)
            windings.append(winding_3)
        return windings

def WindingEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'TRANSFORMER'
    connection_map = {
                0: 'Y_Y',
                1: 'D_Y',
                2: 'D_Y',
                3: 'YNG_YNG',
                4: 'D_D',
                5: 'DO_DO',
                6: 'YO_DO',
                7: 'D_YNG',
                8: 'YNG_D',
                9: 'Y_YNG',
                10: 'YNG_Y',
                11: 'Yg_Zg',
                12: 'D_Zg'
        }


    def parse(self, row, winding_number, network_row):
        name = self.map_name(row)
        resistance = self.map_resistance(row, winding_number)
        is_grounded = self.map_is_grounded(row, winding_number)
        rated_voltage = self.map_rated_voltage(row, winding_number)
        voltage_type = self.map_voltage_type(row)
        rated_power = self.map_rated_power(row)
        num_phases = self.map_num_phases(row)
        connection_type = self.map_connection_type(row, winding_number)
        tap_positions = self.map_tap_positions(row, winding_number, network_row)
        total_taps = self.map_total_taps(row)
        min_tap_pu = self.map_min_tap_pu(row)
        max_tap_pu = self.map_max_tap_pu(row)
        return WindingEquipment(name=name,
                                resistance=resistance,
                                is_grounded=is_grounded,
                                rated_voltage=rated_voltage,
                                voltage_type=voltage_type,
                                rated_power=rated_power,
                                num_phases=num_phases,
                                connection_type=connection_type,
                                tap_positions=tap_positions,
                                total_taps=total_taps,
                                min_tap_pu=min_tap_pu,
                                max_tap_pu=max_tap_pu)

    def map_name(self, row):
        name = row['ID']
        return name

    def map_resistance(self, row, winding_number):

        if winding_number == 1:
            resistance = resistance_pu*row['KVLLprim']**2 / row['KVA']
        elif winding_number == 2:
            resistance = resistance_pu*row['KVLLsec']**2 / row['KVA']
        elif winding_number == 3:
            resistance = resistance_pu*row['KVLLsec']**2 / row['KVA']
        return resistance

    def map_is_grounded(self, row, winding_number):
        
        connection_type = row['Conn']
        if winding_number == 1:
            winding = 0
        elif winding_number == 2:
            winding = 1
        elif winding_number == 3:
            winding = 1
        winding_type = self.connection_map[connection_type].split('_')[winding]
        if 'YNG' in winding_type:
            grounded = False
        elif 'D' in winding_type:
            grounded = False
        elif 'YO' in winding_type:
            grounded = False
        else:
            grounded = True
        return is_grounded

    def map_rated_voltage(self, row, winding_number):
        if winding_number == 1:
            voltage = row['KVLLprim']
        elif winding_number == 2:
            voltage = row['KVLLsec']
        elif winding_number == 3:
            voltage = row['KVLLsec']
        
        voltage = PositiveVoltage(float(voltage), "kilovolt")
        return voltage

    def map_voltage_type(self, row):
        return VoltageTypes.LINE_TO_LINE

    def map_rated_power(self, row):
        power = row['KVA']
        power = ActivePower(float(power), "kilowatt")
        return power

    def map_num_phases(self, row):
        phase_type = row['Type']
        if phase_type == 1 or phase_type == 4:
            num_phaes = 1
        else:
            num_phases = 3
        return num_phases

    def map_connection_type(self, row, winding_number):
        if winding_number == 1:
            connection = row['Conn']
        elif winding_number == 2:
            connection = row['Conn']
        elif winding_number == 3:
            connection = row['Conn']

        winding_type = self.connection_map[connection_type].split('_')[winding]
        if winding_type == 'YO':
            connection_type = 'OPEN_STAR'
        elif winding_type == 'DO':
            connection_type = 'OPEN_DELTA'
        elif 'Z' in winding_type:
            connection_type = 'ZIG_ZAG'
        elif 'Y' in winding_type:
            connection_type = 'STAR'
        elif 'D' in winding_type:
            connection_type = 'DELTA'
        else:
            raise ValueError("Unknown winding type: {}".format(winding_type))

        return ConnectionType(connection_type)

    def map_tap_positions(self, row, winding_number, network_row):
        phase_type = row['Type']
        if phase_type == 1 or phase_type == 4:
            num_phaes = 1
        else:
            num_phases = 3

        tap_positions = []
        if winding_number == 1:
            if network_row is None:
                tap = 100.0
            else:
                tap = network_row['PrimTap']
        elif winding_number == 2:
            if network_row is None:
                tap = 100.0
            else:
                tap = network_row['SecondaryTap']
        elif winding_number == 3:
            if network_row is None:
                tap = 100.0
            else:
                tap = network_row['SecondaryTap']
        for phase in range(1, num_phases + 1):
            tap_positions.append(tap)
        return tap_positions

    def map_total_taps(self, row):
        total_taps = row['Tap']
        return total_taps

    def min_tap_pu(self, row):
        min_tap_pu = row['LowerBandwidth']
        return min_tap_pu

    def max_tap_pu(self, row):
        max_tap_pu = row['UpperBandwidth']
        return max_tap_pu
