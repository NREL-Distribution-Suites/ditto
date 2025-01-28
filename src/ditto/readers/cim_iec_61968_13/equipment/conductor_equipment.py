from gdm.distribution.equipment.concentric_cable_equipment import ConcentricCableEquipment
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm import PositiveCurrent, PositiveDistance, PositiveResistancePULength
from ditto.readers.synergi.length_units import length_units

from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper


class ConductorEquipmentMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    synergi_table = "DevConductors"
    synergi_database = "Equipment"
    MAGIC_NUMBER_1 = 2
    MAGIC_NUMBER_2 = 0.2

    def parse(self, row, unit_type, section_id_sections, from_node_sections, to_node_sections):
        name = self.map_name(row)
        strand_diameter = self.map_strand_diameter(row, unit_type)
        conductor_diameter = self.map_conductor_diameter(row, unit_type)
        cable_diameter = self.map_cable_diameter(row, unit_type)
        insulation_thickness = self.map_insulation_thickness(row, unit_type)
        insulation_diameter = self.map_insulation_diameter(row, unit_type)
        ampacity = self.map_ampacity(row)
        emergency_ampacity = self.map_emergency_ampacity(row)
        conductor_gmr = self.map_conductor_gmr(row, unit_type)
        strand_gmr = self.map_strand_gmr(row, unit_type)
        phase_ac_resistance = self.map_phase_ac_resistance(row, unit_type)
        strand_ac_resistance = self.map_strand_ac_resistance(row, unit_type)
        num_neutral_strands = self.map_num_neutral_strands(row)
        rated_voltage = self.map_rated_voltage(row)

        if insulation_thickness == 0:
            return BareConductorEquipment(
                name=name,
                conductor_diameter=conductor_diameter,
                conductor_gmr=conductor_gmr,
                ampacity=ampacity,
                emergency_ampacity=emergency_ampacity,
                ac_resistance=phase_ac_resistance,
                dc_resistance=phase_ac_resistance,
                loading_limit=None,
            )
        else:
            return ConcentricCableEquipment(
                name=name,
                strand_diameter=strand_diameter,
                conductor_diameter=conductor_diameter,
                cable_diameter=cable_diameter,
                insulation_thickness=insulation_thickness,
                insulation_diameter=insulation_diameter,
                ampacity=ampacity,
                emergency_ampacity=emergency_ampacity,
                conductor_gmr=conductor_gmr,
                strand_gmr=strand_gmr,
                phase_ac_resistance=phase_ac_resistance,
                strand_ac_resistance=strand_ac_resistance,
                num_neutral_strands=num_neutral_strands,
                rated_voltage=rated_voltage,
            )

    def map_name(self, row):
        return row["ConductorName"]

    def map_strand_diameter(self, row, unit_type):
        value = row["CableConNeutStrandDiameter_SUL"] * self.MAGIC_NUMBER_2
        unit = length_units[unit_type]["SUL"]
        return PositiveDistance(value, unit).to("mm")

    def map_conductor_diameter(self, row, unit_type):
        value = row["CableDiamConductor_SUL"]
        unit = length_units[unit_type]["SUL"]
        return PositiveDistance(value, unit).to("mm")

    def map_cable_diameter(self, row, unit_type):
        value = row["CableDiamOutside_SUL"] * self.MAGIC_NUMBER_1
        unit = length_units[unit_type]["SUL"]
        return PositiveDistance(value, unit).to("mm")

    def map_insulation_thickness(self, row, unit_type):
        outside = row["CableDiamOutside_SUL"]
        inside = row["CableDiamOverInsul_SUL"]
        thickness = (outside - inside) / 2
        unit = length_units[unit_type]["SUL"]
        return PositiveDistance(thickness, unit).to("mm")

    def map_insulation_diameter(self, row, unit_type):
        value = row["CableDiamOverInsul_SUL"] * self.MAGIC_NUMBER_1
        unit = length_units[unit_type]["SUL"]
        return PositiveDistance(value, unit).to("mm")

    def map_ampacity(self, row):
        value = row["ContinuousCurrentRating"]
        return PositiveCurrent(value, "ampere")

    def map_emergency_ampacity(self, row):
        value = row["InterruptCurrentRating"]
        return PositiveCurrent(value, "ampere")

    def map_conductor_gmr(self, row, unit_type):
        value = row["CableGMR_MUL"]
        unit = length_units[unit_type]["MUL"]
        return PositiveDistance(value, unit).to("mm")

    def map_strand_gmr(self, row, unit_type):
        value = row["CableConNeutStrandDiameter_SUL"]
        value = value / 2 * 0.7788  # OpenDSS estimate is 0.7788 * radius
        unit = length_units[unit_type]["SUL"]
        return PositiveDistance(value, unit).to("mm")

    def map_phase_ac_resistance(self, row, unit_type):
        value = row["CableResistance_PerLUL"]
        unit = length_units[unit_type]["PerLUL"]
        return PositiveResistancePULength(value, unit).to("ohm/km")

    def map_strand_ac_resistance(self, row, unit_type):
        value = row["CableConNeutResistance_PerLUL"]
        unit = length_units[unit_type]["PerLUL"]
        return PositiveResistancePULength(value, unit).to("ohm/km")

    # Need a field for number of phase strands too...
    def map_num_neutral_strands(self, row):
        value = row["CableConNeutStrandCount"]
        return value

    # We should remove this field
    def map_rated_voltage(self, row):
        return 0

    def map_loading_limit(self, row):
        return None
