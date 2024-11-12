from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm.distribution.equipment.geometry_branch_equipment import GeometryBranchEquipment
from gdm import DistributionSystem
from gdm.quantities import Distance
from ditto.readers.reader import AbstractReader
from ditto.readers.synergi.utils import read_synergi_data, download_mdbtools
import ditto.readers.synergi as synergi_mapper
from loguru import logger

class Reader(AbstractReader):

    # Order matters here
    component_types = [
            "DistributionBus",
            "DistributionCapacitor",
            "DistributionLoad",
            "DistributionTransformerEquipment",
            "DistributionTransformer",
            "ConductorEquipment",
            "GeometryBranchEquipment",
            "GeometryBranch",
    ]

    def __init__(self, model_file, equipment_file):
        download_mdbtools()
        self.system = DistributionSystem(auto_add_composed_components=True)
        default_geometries = []
        default_geometries.append(GeometryBranchEquipment(
                name="Default_OH_3PH",
                horizontal_positions = Distance([0,0.5,1.0, 1.5],"m"),
                vertical_positions = Distance([0,0,0,0],"m")))

        default_geometries.append(GeometryBranchEquipment(
                name="Default_OH_1PH",
                horizontal_positions = Distance([0,0.5],"m"),
                vertical_positions = Distance([0,0],"m")))

        default_geometries.append(GeometryBranchEquipment(
                name="Default_UG_3PH",
                horizontal_positions = Distance([0,0.5,1.0, 1.5],"m"),
                vertical_positions = Distance([-1,-1,-1,-1],"m")))

        default_geometries.append(GeometryBranchEquipment(
                name="Default_UG_1PH",
                horizontal_positions = Distance([0,0.5],"m"),
                vertical_positions = Distance([-1,-1],"m")))

        self.system.add_components(*default_geometries)

        self.read(model_file, equipment_file)

    def read(self, model_file, equipment_file):

        # Read the measurement unit
        unit_type = read_synergi_data(model_file,"SAI_Control").iloc[0]["LengthUnits"]

        # Section data read separately as it links to other tables
        section_id_sections = {}
        from_node_sections = {}
        to_node_sections = {}
        section_data = read_synergi_data(model_file,"InstSection")
        for idx, row in section_data.iterrows():
            section_id = row["SectionId"]
            section_id_sections[section_id] = row

            from_node = row["FromNodeId"]
            to_node = row["ToNodeId"]
            if not from_node in from_node_sections:
                from_node_sections[from_node] = []
            from_node_sections[from_node].append(row)    
            if not to_node in to_node_sections:
                to_node_sections[to_node] = []
            to_node_sections[to_node].append(row)    



        # TODO: Base this off of the components in the init file
        for component_type in self.component_types:

            mapper_name = component_type+ "Mapper"
            if not hasattr(synergi_mapper, mapper_name):
                logger.warning(f"Mapper for {mapper_name} not found. Skipping")
                continue
            mapper = getattr(synergi_mapper, mapper_name)(self.system)
            table_name = mapper.synergi_table
            database = mapper.synergi_database

            table_data = None
            if database == "Model":
                table_data = read_synergi_data(model_file,table_name)
            elif database == "Equipment":
                table_data = read_synergi_data(equipment_file,table_name)
            else:
                raise ValueError("Invalid database type")

            components = []
            for idx,row in table_data.iterrows():
                mapper_name = component_type+ "Mapper"
                model_entry = mapper.parse(row, unit_type, section_id_sections, from_node_sections, to_node_sections)
                components.append(model_entry)
            self.system.add_components(*components)

    def get_system(self) -> DistributionSystem:
        return self.system  
