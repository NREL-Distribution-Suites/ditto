from gdm.quantities import Distance, PositiveCurrent, PositiveResistancePULength
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm.distribution.distribution_system import DistributionSystem
from ditto.readers.reader import AbstractReader
from ditto.readers.cyme.utils import read_cyme_data
import ditto.readers.cyme as cyme_mapper
from loguru import logger


class Reader(AbstractReader):
    # Order of components is important
    component_types = [
        "DistributionBus",
        "DistributionCapacitor",
        "DistributionLoad",
        "BareConductorEquipment",
        "GeometryBranchEquipment",
        "GeometryBranch",
        "DistributionTransformerEquipment",
        "DistributionTransformer"
    ]

    def __init__(self, network_file, equipment_file, load_file):
        self.system = DistributionSystem(auto_add_composed_components=True)
        self.read(network_file, equipment_file, load_file)

    def read(self, network_file, equipment_file, load_file):

        # Section data read separately as it links to other tables
        section_id_sections = {}
        from_node_sections = {}
        to_node_sections = {}
        default_conductor = BareConductorEquipment(
            name="Default",
            conductor_diameter=Distance(0.368000,'inch').to('mm'), 
            conductor_gmr=Distance(0.133200,'inch').to('mm'),
            ampacity=PositiveCurrent(600.0,'amp'),
            emergency_ampacity=PositiveCurrent(600.0,'amp'),
            ac_resistance=PositiveResistancePULength(0.555000,'ohm/mile').to('ohm/km'),
            dc_resistance=PositiveResistancePULength(0.555000,'ohm/mile').to('ohm/km'),
        )
        self.system.add_component(default_conductor)

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
            elif cyme_file == "Load":
                data = read_cyme_data(load_file, cyme_section)
            else:
                raise ValueError(f"Unknown CYME file {cyme_file}")

            transformer_network_data = read_cyme_data(network_file, 'TRANSFORMER SETTING')
            transformer_map = {}
            for idx, row in transformer_network_data.iterrows():
                transformer_type = row['EqID']
                transformer_map[transformer_type] = row
            

            components = []
            for idx, row in data.iterrows():
                mapper_name = component_type + "Mapper"
                if mapper_name == "DistributionCapacitorMapper":
                    model_entry = mapper.parse(row, section_id_sections, equipment_file)
                elif mapper_name == "DistributionBusMapper":
                    model_entry = mapper.parse(row, from_node_sections, to_node_sections)
                elif mapper_name == "DistributionLoadMapper":
                    model_entry = mapper.parse(row, section_id_sections, load_file)
                elif mapper_name == "GeometryBranchMapper":
                    model_entry = mapper.parse(row, section_id_sections)
                elif mapper_name == "GeometryBranchEquipmentMapper":
                    model_entry = mapper.parse(row, equipment_file)
                elif mapper_name == "DistributionTransformerEquipmentMapper":
                    network_row = None
                    if row['ID'] in transformer_map:
                        network_row = transformer_map[row['ID']]
                    model_entry = mapper.parse(row, network_row) 
                else:
                    model_entry = mapper.parse(row)
                if model_entry is not None:
                    components.append(model_entry)
            self.system.add_components(*components)

    def get_system(self) -> DistributionSystem:
        return self.system
