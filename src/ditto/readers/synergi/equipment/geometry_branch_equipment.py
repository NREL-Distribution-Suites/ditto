from ditto.readers.synergi.synergi_mapper import SynergiMapper
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment
from gdm.quantities import Distance
from gdm import PositiveDistance
from ditto.readers.synergi.length_units import length_units

class GeometryBranchEquipmentMapper(SynergiMapper):
    def __init__(self, system):
        super().__init__(system)

    synergi_table = "DevConfig"
    synergi_database = "Equipment"

    def parse(self, row, unit_type, section_id_sections, from_node_sections, to_node_sections):
        name = self.map_name(row)
        horizontal_positions = self.map_horizontal_positions(row, unit_type)
        vertical_positions = self.map_vertical_positions(row, unit_type)
        return GeometryBranchEquipment(name=name,
                                       horizontal_positions=horizontal_positions,
                                       vertical_positions=vertical_positions)

    def map_name(self, row):    
        return row["ConfigName"]

    def map_horizontal_positions(self, row, unit_type):
        unit = length_units[unit_type]["MUL"]
        x1 = row["Position1_X_MUL"]
        x2 = row["Position2_X_MUL"]
        x3 = row["Position3_X_MUL"]
        xn = row["Neutral_X_MUL"]
        return Distance([x1, x2, x3, xn], unit).to("m")

    def map_vertical_positions(self, row, unit_type):
        unit = length_units[unit_type]["MUL"]
        y1 = row["Position1_Y_MUL"]
        y2 = row["Position2_Y_MUL"]
        y3 = row["Position3_Y_MUL"]
        yn = row["Neutral_Y_MUL"]
        return Distance([y1, y2, y3, yn], unit).to("m")


