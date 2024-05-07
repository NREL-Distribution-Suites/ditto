from pathlib import Path
from collections import defaultdict
from typing import Any

from altdss_schema import altdss_models

from ditto.writers.abstract_writer import AbstractWriter
import ditto.writers.opendss as opendss_mapper
from gdm.distribution.components.distribution_component import DistributionComponent


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

    def prepare_folder(self, output_path):
        directory = Path(output_path)
        files_to_remove = directory.rglob("*.dss")
        for dss_file in files_to_remove:
            print(f"Deleting existing file {dss_file}")
            dss_file.unlink()



    def write(
        self,
        output_path: Path = Path("./"),
        separate_substations: bool = True,
        separate_feeders: bool = True,
    ):
        base_redirect = set()
        feeders_redirect = defaultdict(set)
        substations_redirect = defaultdict(set)

        self.prepare_folder(output_path)
        component_types = self.system.get_component_types()
        seen_equipment = set()
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
                if not isinstance(model,DistributionComponent):
                    continue
                model_map = mapper(model)
                model_map.populate_opendss_dictionary()
                dss_string = self._get_dss_string(model_map)
                if dss_string.startswith('new Vsource'):
                    dss_string = dss_string.replace('new Vsource','Clear\n\nNew Circuit')
                equipment_dss_string = None
                equipment_map = None

                if hasattr(model,'equipment'):
                    equipment_mapper_name = model.equipment.__class__.__name__+"Mapper"
                    if not hasattr(opendss_mapper,equipment_mapper_name):
                        print(f"Equipment Mapper {equipment_mapper_name} not found. Skipping")
                    else:
                        equipment_mapper = getattr(opendss_mapper,equipment_mapper_name)
                        equipment_map = equipment_mapper(model.equipment)
                        equipment_map.populate_opendss_dictionary()
                        equipment_dss_string = self._get_dss_string(equipment_map)




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

                if equipment_dss_string is not None:
                    feeder_substation_equipment = model_map.substation+model_map.feeder+equipment_dss_string
                    if feeder_substation_equipment not in seen_equipment:
                        seen_equipment.add(feeder_substation_equipment)
                        with open(output_folder / equipment_map.opendss_file, "a", encoding="utf-8") as fp:
                            fp.write(equipment_dss_string)

                #TODO: Check that there aren't multiple voltage sources for the same master file
                with open(output_folder / model_map.opendss_file, "a", encoding="utf-8") as fp:
                    fp.write(dss_string)

                if model_map.opendss_file == "Master.dss" or model_map.opendss_file == "BusCoords.dss":
                    continue

                if separate_substations and separate_feeders:
                    substations_redirect[model_map.substation].add(
                        Path(model_map.feeder) / model_map.opendss_file
                    )
                    if equipment_map is not None:
                        substations_redirect[model_map.substation].add(
                            Path(model_map.feeder) / equipment_map.opendss_file
                        )

                elif separate_substations:
                    substations_redirect[model_map.substation].add(Path(model_map.opendss_file))
                    if equipment_map is not None:
                        substations_redirect[model_map.substation].add(Path(equipment_map.opendss_file))

                if separate_feeders:
                    combined_feeder_sub = Path(model_map.substation) / Path(model_map.feeder)
                    if combined_feeder_sub not in feeders_redirect:
                        feeders_redirect[combined_feeder_sub] = set()
                    feeders_redirect[combined_feeder_sub].add(Path(model_map.opendss_file))
                    if equipment_map is not None:
                        feeders_redirect[combined_feeder_sub].add(Path(equipment_map.opendss_file))

                base_redirect.add(output_redirect / model_map.opendss_file)
                if equipment_map is not None:
                    base_redirect.add(output_redirect / equipment_map.opendss_file)

        # Only use Masters that have a voltage source, and hence already written.
        if Path('Master.dss').is_file():
            with open('Master.dss','a') as base_master:
                # TODO: provide ordering so LineCodes before Lines
                for dss_file in base_redirect:
                    base_master.write("redirect "+str(dss_file))
                    base_master.write('\n')
        for substation in substations_redirect:
            if (Path(substation)/'Master.dss').is_file():
                with open(Path(substation)/'Master.dss','a') as substation_master:
                    # TODO: provide ordering so LineCodes before Lines
                    for dss_file in substations_redirect[substation]:
                        substation_master.write("redirect "+str(dss_file))
                        substation_master.write('\n')

        for feeder in feeders_redirect:
            if (Path(feeder)/'Master.dss').is_file():
                with open(Path(feeder)/'Master.dss','a') as feeder_master:
                    # TODO: provide ordering so LineCodes before Lines
                    for dss_file in feeders_redirect[feeder]:
                        feeder_master.write("redirect "+str(dss_file))
                        feeder_master.write('\n')
