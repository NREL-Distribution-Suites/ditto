from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm import DistributionSystem
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components.distribution_capacitor import DistributionCapacitor
from gdm.distribution.equipment.distribution_transformer_equipment import DistributionTransformerEquipment
from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.distribution.components.distribution_load import DistributionLoad
from gdm import DistributionSystem
from ditto.readers.reader import AbstractReader
from ditto.readers.synergi.utils import read_synergi_data, download_mdbtools
import ditto.readers.synergi as synergi_mapper
from loguru import logger

class Reader(AbstractReader):

    # Order matters here
    component_types = [
            DistributionBus,
            DistributionCapacitor,
            DistributionLoad,
            DistributionTransformerEquipment,
            DistributionTransformer,
    ]

    def __init__(self, model_file, equipment_file):
        download_mdbtools()
        self.system = DistributionSystem(auto_add_composed_components=True)
        self.read(model_file, equipment_file)

    def read(self, model_file, equipment_file):

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

            mapper_name = component_type.__name__ + "Mapper"
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
                mapper_name = component_type.__name__ + "Mapper"
                model_entry = mapper.parse(row, section_id_sections, from_node_sections, to_node_sections)
                components.append(model_entry)
            self.system.add_components(*components)

    def get_system(self) -> DistributionSystem:
        return self.system  
