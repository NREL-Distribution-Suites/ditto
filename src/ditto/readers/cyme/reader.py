from gdm.quantities import Distance, Current, ResistancePULength
from gdm.distribution.equipment.bare_conductor_equipment import BareConductorEquipment
from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm.distribution.distribution_system import DistributionSystem
from ditto.readers.reader import AbstractReader
from ditto.readers.cyme.utils import read_cyme_data
import ditto.readers.cyme as cyme_mapper
from loguru import logger
from pydantic import ValidationError
from rich.console import Console
from infrasys import Component
from rich.table import Table
from functools import partial


from gdm.distribution.components.distribution_bus import DistributionBus
from gdm.distribution.components import DistributionVoltageSource
from gdm.distribution.components.distribution_transformer import DistributionTransformer
from gdm.quantities import Voltage
from gdm.distribution.enums import VoltageTypes


class Reader(AbstractReader):
    # Order of components is important
    component_types = [
        "DistributionBus",
        "DistributionVoltageSource",
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
        "DistributionTransformerByPhase",
        "DistributionTransformer",
        "MatrixImpedanceBranch",
    ]

    validation_errors = []

    def __init__(self, network_file, equipment_file, load_file, feeder, load_model_id = None):
        self.system = DistributionSystem(auto_add_composed_components=True)
        self.read(network_file, equipment_file, load_file, feeder, load_model_id)

    def read(self, network_file, equipment_file, load_file, feeder, load_model_id = None):

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
        used_sections = set()

        section_data = read_cyme_data(network_file,"SECTION", node_feeder_map=node_feeder_map, feeder_voltage_map=feeder_voltage_map, parse_feeders=True)

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
                if load_model_id is not None:
                    data = data[data['LoadModelID'] == load_model_id]
                    logger.info(f"Filtered Load data by LoadModelID: {load_model_id}")
                else:
                    if len(data['LoadModelID'].unique()) > 1:
                        raise ValueError(f"Multiple LoadModelIDs found in load data: {data['LoadModelID'].unique()}. Please specify load_model_id")
            else:
                raise ValueError(f"Unknown CYME file {cyme_file}")

            argument_handler = {
                "DistributionCapacitorMapper": lambda: [section_id_sections,  read_cyme_data(equipment_file, "SHUNT CAPACITOR", index_col='ID')],
                "DistributionBusMapper": lambda: [from_node_sections, to_node_sections, node_feeder_map, feeder_voltage_map],
                "DistributionVoltageSourceMapper": lambda: [feeder_voltage_map],
                "DistributionLoadMapper": lambda: [section_id_sections, read_cyme_data(load_file, "LOADS", index_col='DeviceNumber')],
                "GeometryBranchMapper": lambda: [used_sections, section_id_sections],
                "GeometryBranchByPhaseMapper": lambda: [used_sections, section_id_sections],
                "BareConductorEquipmentMapper": lambda: [],
                "GeometryBranchEquipmentMapper": lambda: [read_cyme_data(equipment_file,"SPACING TABLE FOR LINE", index_col='ID')],
                "MatrixImpedanceSwitchMapper": lambda: [used_sections, section_id_sections, read_cyme_data(equipment_file, "SWITCH", index_col='ID')],
                "MatrixImpedanceFuseMapper": lambda: [used_sections, section_id_sections, read_cyme_data(equipment_file, "FUSE", index_col='ID')],
                "MatrixImpedanceRecloserMapper": lambda: [used_sections, section_id_sections, read_cyme_data(equipment_file, "RECLOSER", index_col='ID')],
                "GeometryBranchByPhaseEquipmentMapper": lambda: [read_cyme_data(equipment_file,"SPACING TABLE FOR LINE", index_col='ID')],
                "DistributionTransformerMapper": lambda: [used_sections, section_id_sections, read_cyme_data(equipment_file, "TRANSFORMER", index_col='ID').to_dict("index")],
                "DistributionTransformerByPhaseMapper": lambda: [used_sections, section_id_sections, read_cyme_data(equipment_file, "TRANSFORMER", index_col='ID').to_dict("index")],
                "MatrixImpedanceBranchMapper": lambda: [used_sections, section_id_sections],
            }

            args = argument_handler.get(mapper_name, lambda: [])()

            def parse_row(row):
                model_entry = mapper.parse(row, *args)
                return model_entry

            components = data.apply(parse_row, axis=1)
            components = [c for c in components if c is not None]
            components = [item for c in components for item in (c if isinstance(c, list) else [c])]

            self.system.add_components(*components)

        self.system = self.build_feeder(feeder)

        for component_type in self.system.get_component_types():
            components = self.system.get_components(component_type)
            self._add_components(components)

        self._validate_model()

    def _add_components(self, components: list[Component]):
        """Internal method to add components to the system."""

        if components:
            for component in components:
                try:
                    component.__class__.model_validate(component.model_dump())
                except ValidationError as e:
                    for error in e.errors():
                        self.validation_errors.append(
                            [
                                component.name,
                                component.__class__.__name__,
                                error["loc"][0] if error["loc"] else "On model validation",
                                error["type"],
                                error["msg"],
                            ]
                        )

            self.system.add_components(*components)

    def _validate_model(self):
        if self.validation_errors:
            error_table = Table(title="Validation warning summary")
            error_table.add_column("Model", justify="right", style="cyan", no_wrap=True)
            error_table.add_column("Type", style="green")
            error_table.add_column("Field", justify="right", style="bright_magenta")
            error_table.add_column("Error", style="bright_red")
            error_table.add_column("Message", justify="right", style="turquoise2")

            for row in self.validation_errors:
                print(row)
                error_table.add_row(*row)

            console = Console()
            console.print(error_table)
            raise Exception(
                "Validations errors occured when running the script. See the table above"
            )

    def get_system(self) -> DistributionSystem:
        return self.system
    

        
    def _get_bus_connected_components(
        self, type_lists, bus_name, component_type
    ):
        if "bus" in component_type.model_fields:
            return list(
                filter(
                    lambda x: x.bus.name == bus_name,
                    type_lists[component_type],
                )
            )
        elif "buses" in component_type.model_fields:
            return list(
                filter(
                    lambda x: bus_name in [bus.name for bus in x.buses],
                    type_lists[component_type],
                )
            )    

    def build_feeder(self, feeder_name):

        bus_queue = []

        type_lists = {}
        for component_type in self.system.get_component_types():
            type_lists[component_type] = list(self.system.get_components(component_type, filter_func=partial(filter_feeder, feeder_name=feeder_name)))

        voltage_sources = type_lists.get(DistributionVoltageSource, [])
        feeder_dist_sys = DistributionSystem(auto_add_composed_components=True)
        for vsource in voltage_sources:
            feeder_dist_sys.add_component(vsource)
            bus_queue.append(vsource.bus.name)

        while bus_queue:
            current_bus_name = bus_queue.pop(0)
            current_bus = self.system.get_component(DistributionBus, name=current_bus_name)
            current_voltage = current_bus.rated_voltage
            try:
                feeder_dist_sys.add_component(current_bus)
            except:
                pass
            for component_type in self.system.get_component_types():
                conn_objs = self._get_bus_connected_components(type_lists, current_bus.name, component_type)
                if conn_objs:
                    if conn_objs != []:
                        for obj in conn_objs:
                            if hasattr(obj, 'buses'):
                                for bus in obj.buses:
                                    if (bus.name != current_bus.name):
                                        if component_type == DistributionTransformer:
                                            for i, winding in enumerate(obj.equipment.windings):
                                                voltage = winding.rated_voltage
                                                voltage_type = winding.voltage_type

                                                if i > 0:
                                                    if voltage < current_voltage:
                                                        bus.voltage_type = voltage_type
                                                        bus.rated_voltage = voltage

                                            if (not feeder_dist_sys.has_component(bus)) and (bus.name not in bus_queue):
                                                bus_queue.append(bus.name)
                                        else:
                                            bus.rated_voltage = current_voltage
                                            if (not feeder_dist_sys.has_component(bus)) and (bus.name not in bus_queue):
                                                bus_queue.append(bus.name)
                            elif hasattr(obj, 'bus'):
                                if (obj.bus.name not in bus_queue) and (not feeder_dist_sys.has_component(obj.bus)):
                                    bus_queue.append(obj.bus.name)
                            try:
                                feeder_dist_sys.add_component(obj)
                            except:
                                pass  
        return feeder_dist_sys


def filter_feeder(object, feeder_name=None):
    if hasattr(object, 'bus'):
        if not hasattr(object.bus.feeder, "name"):
            return False
        if object.bus.feeder.name == feeder_name:
            return True
        return False
        
    elif hasattr(object, 'buses'):
        for bus in object.buses:
            if not hasattr(bus.feeder, "name"):
                return False
        if object.buses[0].feeder.name == feeder_name and object.buses[1].feeder.name == feeder_name: 
            return True
        return False