from pathlib import Path
from collections import defaultdict
from typing import Any

from altdss_schema import altdss_models

from ditto.writers.abstract_writer import AbstractWriter
import ditto.writers.opendss as opendss_mapper


class Writer(AbstractWriter):
    def _get_dss_string(self, model_map: Any) -> str:
        # Example model_map is instance of DistributionBusMapper
        altdss_class = getattr(altdss_models, model_map.altdss_name)
        # Example altdss_class is Bus
        altdss_object = altdss_class.model_validate(model_map.opendss_dict)
        if model_map.altdss_composition_name is not None:
            altdss_composition_class = getattr(altdss_models, model_map.altdss_composition_name)
            altdss_composition_object = altdss_composition_class(altdss_object)
            dss_string = altdss_composition_object.dumps_dss()
        else:
            dss_string = altdss_object.dumps_dss()

        return dss_string

    def write(
        self,
        output_path: Path = Path("./"),
        separate_substations: bool = True,
        separate_feeders: bool = True,
    ):
        files_to_redirect = []
        feeders_redirect = defaultdict(list)
        substations_redirect = defaultdict(list)

        component_types = self.system.get_component_types()
        for component_type in component_types:
            # Example component_type is DistributionBus
            components = self.system.get_components(component_type)
            mapper_name = component_type.__name__ + "Mapper"
            # Example mapper_name is string DistributionBusMapper
            if not hasattr(opendss_mapper, mapper_name):
                print(f"Mapper {mapper_name} not found. Skipping")
                continue

            print(f"Mapping components in {mapper_name}...")
            mapper = getattr(opendss_mapper, mapper_name)
            # Example mapper is class DistributionBusMapper

            for model in components:
                # Example model is instance of DistributionBus
                model_map = mapper(model)
                model_map.populate_opendss_dictionary()
                dss_string = self._get_dss_string(model_map)

                output_folder = output_path
                output_redirect = Path("")
                if separate_substations:
                    output_folder = Path(output_path, model_map.substation)
                    output_redirect = Path(model_map.substation)
                    output_folder.mkdir(exist_ok=True)

                else:
                    output_folder.mkdir(exist_ok=True)

                if separate_feeders:
                    output_folder /= model_map.feeder
                    output_redirect /= model_map.feeder
                    output_folder.mkdir(exist_ok=True)

                with open(output_folder / model_map.opendss_file, "a", encoding="utf-8") as fp:
                    fp.write(dss_string)

                if separate_substations and separate_feeders:
                    substations_redirect[model_map.substation].append(
                        Path(model_map.feeder) / model_map.opendss_file
                    )

                elif separate_substations:
                    substations_redirect[model_map.substation].append(Path(model_map.opendss_file))

                if separate_feeders:
                    combined_feeder_sub = Path(model_map.substation) / Path(model_map.feeder)
                    if combined_feeder_sub not in feeders_redirect:
                        feeders_redirect[combined_feeder_sub] = []
                    feeders_redirect[combined_feeder_sub].append(Path(model_map.opendss_file))

                files_to_redirect.append(output_redirect / model_map.opendss_file)