from pathlib import Path


from infrasys.system import System
from gdm import DistributionSystem
from gdm import SequencePair
import opendssdirect as odd
from loguru import logger

from ditto.readers.opendss.branches import (
    get_matrix_branch_equipments,
    get_geometry_branch_equipments,
    get_branches,
)
from ditto.readers.opendss.sources import get_voltage_sources, get_voltage_source_equipments
from ditto.readers.opendss.transformers import get_transformers, get_transformer_equipments
from ditto.readers.opendss.capacitors import get_capacitors, get_capacitor_equipments
from ditto.readers.opendss.pv_systems import get_pv_equipments, get_pvsystems
from ditto.readers.opendss.conductors import get_conductors_equipment
from ditto.readers.opendss.cables import get_cables_equipment
from ditto.readers.opendss.loads import get_loads
from ditto.readers.opendss.buses import get_buses
from ditto.readers.reader import AbscractReader

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class Reader(AbscractReader):
    """Class interface for Opendss case file reader"""

    def __init__(self, Opendss_master_file: Path, crs: str | None = None) -> None:
        """Constructor for the Opendss reader

        Args:
            Opendss_master_file (Path): Path to the Opendss master file
            crs (str | None, optional): Coordinate reference system name. Defaults to None.
        """

        self.system = DistributionSystem(auto_add_composed_components=True)
        self.Opendss_master_file = Opendss_master_file
        self.crs = crs
        self.read()

    def read(self):
        """Takes the master file path and returns instance of OpendssParser

        Raises:
            FileNotFoundError: Error raised if the file is not found
        """

        logger.info("Loading OpenDSS model.")
        if not self.Opendss_master_file.exists():
            msg = f"File not found: {self.Opendss_master_file}"
            raise FileNotFoundError(msg)

        odd.Text.Command("Clear")
        odd.Basic.ClearAll()
        odd.Text.Command(f'Redirect "{self.Opendss_master_file}"')
        json_circuit = odd.Circuit.ToJSON()
        json_file = str(self.Opendss_master_file).lower().replace(".dss", ".json")
        with open(json_file, "w") as f:
            f.write(json_circuit)

        logger.info(f"Model loaded from {self.Opendss_master_file}.")
        self.system = System(name=odd.Circuit.Name(), auto_add_composed_components=True)

        buses = get_buses(self.system, self.crs)
        self.system.add_components(*buses)
        voltage_sources_equipment_catalog = get_voltage_source_equipments()
        self.system.add_components(*voltage_sources_equipment_catalog.values())
        voltage_sources = get_voltage_sources(self.system, voltage_sources_equipment_catalog)
        self.system.add_components(*voltage_sources)
        capacitor_equipments_catalog = get_capacitor_equipments()
        self.system.add_components(*capacitor_equipments_catalog.values())
        caps = get_capacitors(self.system, capacitor_equipments_catalog)
        self.system.add_components(*caps)
        # TODO: should unique load equiments be calatoged to reduce replicated objects?
        loads = get_loads(self.system)
        self.system.add_components(*loads)
        transformer_equipments_catalog = get_transformer_equipments(self.system)
        self.system.add_components(*transformer_equipments_catalog.values())
        transformers = get_transformers(self.system, transformer_equipments_catalog)
        self.system.add_components(*transformers)
        conductor_equipment = get_conductors_equipment()
        self.system.add_components(*conductor_equipment)
        concentric_cable_equipment = get_cables_equipment()
        self.system.add_components(*concentric_cable_equipment)
        matrix_branch_equipments_catalog = get_matrix_branch_equipments()
        self.system.add_components(*matrix_branch_equipments_catalog.values())
        geometry_branch_equipment_catalog, mapped_geometry = get_geometry_branch_equipments(
            self.system
        )
        self.system.add_components(*geometry_branch_equipment_catalog.values())
        branches = get_branches(
            self.system,
            mapped_geometry,
            matrix_branch_equipments_catalog,
            geometry_branch_equipment_catalog,
        )
        self.system.add_components(*branches)
        solar_equipment_catalog = get_pv_equipments()
        self.system.add_components(*solar_equipment_catalog.values())
        pv_systems = get_pvsystems(self.system, solar_equipment_catalog)
        self.system.add_components(*pv_systems)

        logger.info("parsing complete...")

    def get_system(self) -> System:
        """Returns an instance of DistributionSystem

        Returns:
            System: Instance of DistributionSystem
        """

        return self.system