from gdm.quantities import Distance, Current, ResistancePULength
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
        "MatrixImpedanceRecloser",
        "MatrixImpedanceSwitch",
        "MatrixImpedanceFuse",
        "DistributionCapacitor",
        "DistributionLoad",
        "BareConductorEquipment",
        "GeometryBranchEquipment",
        "GeometryBranchByPhaseEquipment",
        "GeometryBranch",
        "GeometryBranchByPhase",
        "DistributionTransformerEquipment",
        "DistributionTransformerByPhase",
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
            ampacity=Current(600.0,'amp'),
            emergency_ampacity=Current(600.0,'amp'),
            ac_resistance=ResistancePULength(0.555000,'ohm/mile').to('ohm/km'),
            dc_resistance=ResistancePULength(0.555000,'ohm/mile').to('ohm/km'),
        )
        self.system.add_component(default_conductor)

        node_feeder_map = {}
        feeder_voltage_map = {}

        section_data = read_cyme_data(network_file,"SECTION", node_feeder_map, feeder_voltage_map, parse_feeders=True)

        section_id_sections = section_data.set_index("SectionID").to_dict(orient="index")
        from_node_sections = section_data.groupby("FromNodeID").apply(lambda df: df.to_dict(orient="records")).to_dict()
        to_node_sections = section_data.groupby("ToNodeID").apply(lambda df: df.to_dict(orient="records")).to_dict()



        for component_type in self.component_types:
            logger.info(f"Parsing Type: {component_type}")
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


            args = []
            mapper_name = component_type + "Mapper"
            if mapper_name == "DistributionCapacitorMapper":

                equipment_data = read_cyme_data(equipment_file, "SHUNT CAPACITOR")
                equipment_data.index = equipment_data['ID']
                args = [section_id_sections, equipment_data]

            elif mapper_name == "DistributionBusMapper":
                args = [from_node_sections, to_node_sections, node_feeder_map, feeder_voltage_map]

            elif mapper_name == "DistributionLoadMapper":

                equipment_data = read_cyme_data(load_file, "LOADS")
                equipment_data.index = equipment_data['DeviceNumber']
                args = [section_id_sections, equipment_data]

            elif mapper_name == "GeometryBranchMapper":
                args = [section_id_sections]
            
            elif mapper_name == "GeometryBranchByPhaseMapper":
                args = [section_id_sections]

            elif mapper_name == "BareConductorEquipmentMapper":
                args = []

            elif mapper_name == "GeometryBranchEquipmentMapper":
                args = [equipment_file]

            elif mapper_name == "MatrixImpedanceSwitchMapper":
                equipment_data = read_cyme_data(equipment_file, "SWITCH")
                equipment_data.index = equipment_data['ID']
                args = [section_id_sections, equipment_data]

            elif mapper_name == "MatrixImpedanceFuseMapper":
                equipment_data = read_cyme_data(equipment_file, "FUSE")
                equipment_data.index = equipment_data['ID']
                args = [section_id_sections, equipment_data]

            elif mapper_name == "MatrixImpedanceRecloserMapper":
                equipment_data = read_cyme_data(equipment_file, "RECLOSER")
                equipment_data.index = equipment_data['ID']
                args = [section_id_sections, equipment_data]

            elif mapper_name == "GeometryBranchByPhaseEquipmentMapper":
                spacing_ids = read_cyme_data(equipment_file,"SPACING TABLE FOR LINE")
                spacing_ids.index = spacing_ids['ID']
                args = [spacing_ids]

            elif mapper_name == "DistributionTransformerEquipmentMapper":
                transformer_network_data = read_cyme_data(network_file, 'TRANSFORMER SETTING')
                transformer_map = {}
                for idx, row in transformer_network_data.iterrows():
                    transformer_type = row['EqID']
                    transformer_map[transformer_type] = row

                byphase_transformer_network_data = read_cyme_data(network_file, "TRANSFORMER BYPHASE SETTING")
                for idx, row in byphase_transformer_network_data.iterrows():
                    for phase in ['1', '2', '3']:
                        transformer_type = row['PhaseTransformerID' + phase]
                        if transformer_type is not None and transformer_type != '':
                            transformer_map[transformer_type] = row
                args = [transformer_map]

            elif mapper_name == "DistributionTransformerMapper" or mapper_name == "DistributionTransformerByPhaseMapper":
                transformer_equipment_data = read_cyme_data(equipment_file, "TRANSFORMER")
                transformer_map = {}
                for idx, row in transformer_equipment_data.iterrows():
                    transformer_type = row['ID']
                    transformer_map[transformer_type] = row
                args = [section_id_sections, transformer_map]

            def parse_row(row):
                model_entry = mapper.parse(row, *args)
                return model_entry

            components = data.apply(parse_row, axis=1)
            components = [c for c in components if c is not None]
            components = [item for c in components for item in (c if isinstance(c, list) else [c])]
            self.system.add_components(*components)

    def get_system(self) -> DistributionSystem:
        return self.system
