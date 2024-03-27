from pathlib import Path
import importlib
import os

from ditto.writers.abstract_writer import AbstractWriter
from ditto.writers.opendss.components.distribution_bus import DistributionBusMapper
from gdm import DistributionBus

altdss_models = importlib.import_module("ditto.formats.opendss.AltDSS-Schema.python.altdss_models") 
import ditto.writers.opendss as opendss_mapper



class Writer(AbstractWriter):

    def write(self, output_path: Path = Path('./'), separate_substations: bool=False, separate_feeders: bool=False):


        files_to_redirect = []
        feeders_redirect = {}
        substations_redirect = {}

        component_types = self.system.get_component_types()
        for component_type in component_types:
            # Example component_type is DistributionBus
            components = self.system.get_components(component_type)
            mapper_name = component_type.__name__+"Mapper"
            # Example mapper_name is string DistributionBusMapper
            if hasattr(opendss_mapper, mapper_name):
                print(f'Mapping components in {mapper_name}...')
                mapper = getattr(opendss_mapper, mapper_name)
                # Example mapper is class DistributionBusMapper

                for model in components:
                    # Example model is instance of DistributionBus
                    model_map = mapper(model)
                    # Example model_map is instance of DistributionBusMapper
                    model_map.populate_opendss_dictionary()
                    altdss_class = getattr(altdss_models, model_map.altdss_name)
                    # Example altdss_class is Bus
                    altdss_object = altdss_class.parse_obj(model_map.opendss_dict)
                    dss_string = altdss_object.dumps_dss()

                    output_folder = output_path
                    output_redirect = ""
                    if separate_substations:
                        output_folder = Path(output_path,model_map.substation)
                        output_redirect = model_map.substation
                        if not os.path.exists(output_folder):
                            os.makedires(output_folder)

                    else:
                        if not os.path.exists(output_folder):
                            os.makedirs(output_folder)

                    if separate_feeders:
                        output_folder = os.path.join(output_folder, model_map.feeder)
                        output_redirect = os.path.join(output_redirect, model_map.feeder)
                        if not os.path.exists(output_folder):
                            os.makedirs(output_folder)

                    with open(os.path.join(output_folder, model_map.opendss_file), "w",) as fp:
                        fp.write(dss_string)

                    if separate_substations and separate_feeders:
                        if model_map.substation not in self.substations_redirect:
                            substations_redirect[model_map.substation] = []
                        substations_redirect[model_map.substation].append(os.path.join(model_map.feeder_name, model_map.opendss_file))

                    elif separate_substations:
                        if model_map.substation not in substations_redirect:
                            substations_redirect[model_map.substation] = []
                        substations_redirect[model_map.substation_name].append(model_map.opendss_file)

                    if separate_feeders:
                        combined_feeder_sub = os.path.join(model_map.substation, model_map.feeder_name)
                        if combined_feeder_sub not in feeders_redirect:
                            feeders_redirect[combined_feeder_sub] = []
                        feeders_redirect[combined_feeder_sub].append(model_map.opendss_file)

                    files_to_redirect.append(os.path.join(output_redirect, model_map.opendss_file))

                    
            else:
                print(f'Mapper {mapper_name} not found. Skipping')

            #TODO: Set write_master for base and substation/feeder subclasses using this methodology: https://github.com/NREL/ditto/blob/master/ditto/writers/opendss/write.py#L3865

        
