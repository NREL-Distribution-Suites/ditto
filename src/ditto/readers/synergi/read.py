from gdm.distribution.components.base.distribution_component_base import DistributionComponentBase
from gdm import DistributionSystem
from gdm.distribution.components.distribution_bus import DistributionBus
from ditto.writers.abstract_reader import AbstractReader
from utils import read_synergi_table, download_mdbtools

class Reader(AbstractReader):

    component_types = [
            DistributionBus,
    ]

    def __init__(self):
        download_mdbtools()
        self.system = DistributionSytem(auto_add_composed_components=True)

    def read(self, model_file, equipment_file):
        # TODO: Base this off of the components in the init file
        for component_type in self.component_types:

            mapper_name = component_type.__name__ + "Mapper"
            if not hasattr(synergi_mapper, mapper_name):
                logger.warning(f"Mapper for {mapper_name} not found. Skipping")
                continue
            mapper = getattr(synergi_mapper, mapper_name)()
            table_name = mapper.synergi_table
            database = mapper.synergi_database

            table_data = None
            if database == "Model":
                table_data = read_synergi_data(model_file,table)
            elif database == "Equipment":
                table_data = read_synergi_data(equipment_file,table)
            else:
                raise ValueError("Invalid database type")

            components = []
            for row in table_data:
                mapper_name = component_type.__name__ + "Mapper"
                model_entry = mapper(row)
                components.append(model_entry)
                self.system.add_components(*components)
