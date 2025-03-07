from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm import DistributionSystem
from ditto.readers.reader import AbstractReader
from ditto.readers.cyme.utils import read_cyme_data
import ditto.readers.cyme as cyme_mapper
from loguru import logger


class Reader(AbstractReader):
    # Order of components is important
    component_types = [
            "DistributionBus",
            "DistributionCapacitor"
    ]

    def __init__(self, network_file, equipment_file):
        self.system = DistributionSystem(auto_add_composed_components=True)
        self.read(network_file, equipment_file)

    def read(self, network_file, equipment_file):

        # Section data read separately as it links to other tables
        section_id_sections = {}
        from_node_sections = {}
        to_node_sections = {}

        section_data = read_cyme_data(network_file,"SECTION")
        for idx, row in section_data.iterrows():
            section_id = row["SectionID"]
            section_id_sections[section_id] = row

            from_node = row["FromNodeID"]
            to_node = row["ToNodeID"]

            if not from_node in from_node_sections:
                from_node_sections[from_node] = []
            from_node_sections[from_node].append(row)    
            if not to_node in to_node_sections:
                to_node_sections[to_node] = []
            to_node_sections[to_node].append(row)    


        for component_type in self.component_types:
            mapper_name = component_type + "Mapper"
            if not hasattr(cyme_mapper, mapper_name):
                logger.warning(f"Mapper {mapper_name} not found. Skipping.")
            mapper = getattr(cyme_mapper, mapper_name)(self.system)
            cyme_file = mapper.cyme_file
            cyme_section = mapper.cyme_section

            data = None
            if cyme_file == "Network":
                data = read_cyme_data(network_file, cyme_section)
            elif cyme_file == "Equipment":
                data = read_cyme_data(equipment_file, cyme_section)
            else:
                raise ValueError(f"Unknown CYME file {cyme_file}")

            components = []
            for idx, row in data.iterrows():
                mapper_name = component_type + "Mapper"
                if mapper_name == "DistributionCapacitorMapper":
                    model_entry = mapper.parse(row, section_id_sections, equipment_file)
                if mapper_name == "DistributionBusMapper":
                    model_entry = mapper.parse(row, from_node_sections, to_node_sections)
                if model_entry is not None:
                    components.append(model_entry)
                self.system.add_component(model_entry)

    def get_system(self) -> DistributionSystem:
        return self.system
