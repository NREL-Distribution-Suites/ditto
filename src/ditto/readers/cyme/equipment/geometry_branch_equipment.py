from gdm.quantities import PositiveCurrent, PositiveDistance, PositiveResistancePULength, Distance
from ditto.readers.cyme.utils import read_cyme_data
from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment


class GeometryBranchEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'LINE'

    def parse(self, row, equipment_file):
        name = self.map_name(row)
        conductors = self.map_conductors(row, equipment_file)
        horizontal_positions = self.map_horizontal_positions(row, equipment_file)
        vertical_positions = self.map_vertical_positions(row, equipment_file)

        return GeometryBranchEquipment(name=name,
                                       conductors=conductors,
                                       horizontal_positions=horizontal_positions,
                                       vertical_positions=vertical_positions)

    def map_name(self, row):
        name = row['ID']
        return name

    def map_vertical_positions(self, row, equipment_file):
        spacing_id = row['SpacingID']
        spacing_ids = read_cyme_data(equipment_file,"SPACING TABLE FOR LINE")
        for idx, row in spacing_ids.iterrows():
            if row['ID'] == spacing_id:
                vertical_positions = []
                spacing = row
                cond1_y = spacing['PosOfCond1_Y']
                cond2_y = spacing['PosOfCond2_Y']
                cond3_y = spacing['PosOfCond3_Y']
                neutral_y = spacing['PosOfNeutralCond_Y']
                if cond1_y != "":
                    y1 = float(cond1_y)
                    vertical_positions.append(y1)
                if cond2_y != "":
                    y2 = float(cond2_y)
                    vertical_positions.append(y2)
                if cond3_y != "":
                    y3 = float(cond3_y)
                    vertical_positions.append(y3)
                if neutral_y != "":
                    y_n = float(neutral_y)
                    vertical_positions.append(y_n)
                return Distance(vertical_positions, 'feet').to('m')
        return None

    def map_horizontal_positions(self, row, equipment_file):
        spacing_id = row['SpacingID']
        spacing_ids = read_cyme_data(equipment_file,"SPACING TABLE FOR LINE")
        for idx, row in spacing_ids.iterrows():
            if row['ID'] == spacing_id:
                spacing = row
                horizontal_positions = []
                cond1_x = spacing['PosOfCond1_X']
                cond2_x = spacing['PosOfCond2_X']
                cond3_x = spacing['PosOfCond3_X']
                neutral_x = spacing['PosOfNeutralCond_X']
                if cond1_x != "":
                    x1 = float(cond1_x)
                    horizontal_positions.append(x1)
                if cond2_x != "":
                    x2 = float(cond2_x)
                    horizontal_positions.append(x2)
                if cond3_x != "":
                    x3 = float(cond3_x)
                    horizontal_positions.append(x3)
                if neutral_x != "":
                    x_n = float(neutral_x)
                    horizontal_positions.append(x_n)
                return Distance(horizontal_positions, 'feet').to('m')
        return None

    def map_conductors(self,row, equipment_file):
        phase_conductor_name = row['PhaseCondID']
        neutral_conductor_name = row['NeutralCondID']
        try:
            phase_conductor = self.system.get_component(component_type=BareConductorEquipment, name=phase_conductor_name)
        except Exception as e:
            phase_conductor = self.system.get_component(component_type=BareConductorEquipment, name="Default")
        try:
            neutral_conductor = self.system.get_component(component_type=BareConductorEquipment, name=neutral_conductor_name)
        except:
            neutral_conductor = self.system.get_component(component_type=BareConductorEquipment, name="Default")

        spacing_id = row['SpacingID']
        spacing_ids = read_cyme_data(equipment_file,"SPACING TABLE FOR LINE")
        for idx, row in spacing_ids.iterrows():
            if row['ID'] == spacing_id:
                spacing = row
                conductors = []
                cond1 = spacing['PosOfCond1_X']
                cond2 = spacing['PosOfCond2_X']
                cond3 = spacing['PosOfCond3_X']
                neutral = spacing['PosOfNeutralCond_X']
                if cond1 != "":
                    conductors.append(phase_conductor)
                if cond2 != "":
                    conductors.append(phase_conductor)
                if cond3 != "":
                    conductors.append(phase_conductor)
                if neutral != "":
                    conductors.append(neutral_conductor)
                return conductors
        return None

class ConcentricCableEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'CABLE'

    def parse(self, row):
        name = self.map_name(row)
        strand_diameter = self.map_strand_diameter(row)
        conductor_diameter = self.map_conductor_diameter(row) 
        cable_diameter = self.map_cable_diameter(row)
        insulation_thickness = self.map_insulation_thickness(row)
        insulation_diameter = self.map_insulation_diameter(row)
        amapcity = self.map_ampacity(row)
        conductor_gmr = self.map_conductor_gmr(row)
        strand_gmr = self.map_strand_gmr(row)
        phase_ac_resistance = self.map_phase_ac_resistance(row)
        strand_ac_resistance = self.map_strand_ac_resistance(row)
        num_neutral_strands = self.map_num_neutral_strands(row)
        rated_voltage = self.map_rated_voltage(row)
        return ConcentricCableEquipment(name=name,
                                        strand_diameter=strand_diameter,
                                        conductor_diameter=conductor_diameter,
                                        cable_diameter=cable_diameter,  
                                        insulation_thickness=insulation_thickness,
                                        insulation_diameter=insulation_diameter,
                                        ampacity=amapcity,
                                        conductor_gmr=conductor_gmr,
                                        strand_gmr=strand_gmr,
                                        phase_ac_resistance=phase_ac_resistance,
                                        strand_ac_resistance=strand_ac_resistance,
                                        num_neutral_strands=num_neutral_strands,
                                        rated_voltage=rated_voltage)    

    def map_name(self, row):
        name = row['ID']
        return name 

    def map_conductor_diameter(self, row):
        cable_name = row['ID']
        conductor_info = read_cyme_data(self.system.equipment_file,"CABLE CONDUCTOR")
        for idx, row in conductor_info.iterrows():
            if row['ID'] == cable_name:
                conductor_diameter = float(row['Diameter'])
                return PositiveDistance(conductor_diameter,'inch').to('mm')
        return None


    def map_strand_diameter(self, row):
        cable_name = row['ID']
        strand_info = read_cyme_data(self.system.equipment_file,"CABLE CONCENTRIC NEUTRAL")
        for idx, row in strand_info.iterrows():
            if row['ID'] == cable_name:
                strand_diameter = float(row['Diameter'])
                return PositiveDistance(strand_diameter,'inch').to('mm')
        return None

    def map_ampacity(self, row):
        ampacity = PositiveCurrent(float(row['Amps']),'amp')
        return ampacity

class BareConductorEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    cyme_file = 'Equipment'
    cyme_section = 'CONDUCTOR'

    def parse(self, row):
        name = self.map_name(row)
        conductor_diameter = self.map_conductor_diameter(row) 
        conductor_gmr = self.map_conductor_gmr(row)
        ampacity = self.map_ampacity(row)
        emergency_ampacity = self.map_emergency_ampacity(row)
        ac_resistance = self.map_ac_resistance(row)
        dc_resistance = self.map_dc_resistance(row)
        return BareConductorEquipment(name=name,
                                     conductor_diameter=conductor_diameter,
                                     conductor_gmr=conductor_gmr,
                                     ampacity=ampacity,
                                     emergency_ampacity=emergency_ampacity,
                                     ac_resistance=ac_resistance,
                                     dc_resistance=dc_resistance)

    def map_name(self, row):
        name = row['ID']
        return name

    def map_conductor_diameter(self, row):
        conductor_diameter = float(row['Diameter'])
        return PositiveDistance(conductor_diameter,'inch').to('mm')

    def map_conductor_gmr(self, row):
        conductor_gmr = PositiveDistance(float(row['GMR']),'inch').to('mm')
        return conductor_gmr

    def map_ampacity(self, row):
        ampacity = PositiveCurrent(float(row['Amps']),'amp')
        return ampacity

    def map_emergency_ampacity(self, row):
        emergency_ampacity = PositiveCurrent(float(row['Amps_4']),'amp')
        return emergency_ampacity

    def map_ac_resistance(self, row):
        ac_resistance = PositiveResistancePULength(float(row['R25']),'ohm/mile').to('ohm/km')
        return ac_resistance

    def map_dc_resistance(self, row):
        dc_resistance = PositiveResistancePULength(float(row['R25']),'ohm/mile').to('ohm/km')
        return dc_resistance

