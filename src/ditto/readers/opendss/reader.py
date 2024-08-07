from pathlib import Path

from gdm import DistributionSystem
from gdm import SequencePair
import opendssdirect as odd
from loguru import logger

from ditto.readers.opendss.components.conductors import get_conductors_equipment
from ditto.readers.opendss.components.cables import get_cables_equipment
from ditto.readers.opendss.components.sources import get_voltage_sources
from ditto.readers.opendss.components.capacitors import get_capacitors
from ditto.readers.opendss.graph_utils import update_split_phase_nodes
from ditto.readers.opendss.components.pv_systems import get_pvsystems
from ditto.readers.opendss.components.buses import get_buses
from ditto.readers.opendss.components.loads import get_loads
from ditto.readers.opendss.components.admittance_matrix import get_admittance_matrix
from ditto.readers.opendss.components.transformers import (
    get_transformer_equipments,
    get_transformers,
)
from ditto.readers.opendss.components.branches import (
    get_geometry_branch_equipments,
    get_matrix_branch_equipments,
    get_branches,
)
from gdm import build_graph_from_system

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
        logger.info(f"Model loaded from {self.Opendss_master_file}.")

        models = ["load", "capacitor", "pvsystem", "storage"]

        for model in models:
            odd.Text.Command(f"batchedit {model}..* enabled=false")

        odd.Solution.Solve()

        impedance_matrix = get_admittance_matrix()
        self.system.add_components(impedance_matrix)

        for model in models:
            odd.Text.Command(f"batchedit {model}..* enabled=true")

        odd.Solution.Solve()

        buses = get_buses(self.crs)
        self.system.add_components(*buses)
        voltage_sources = get_voltage_sources(self.system)
        self.system.add_components(*voltage_sources)
        caps = get_capacitors(self.system)
        self.system.add_components(*caps)
        loads = get_loads(self.system)
        self.system.add_components(*loads)
        pv_systems = get_pvsystems(self.system)
        self.system.add_components(*pv_systems)
        (
            distribution_transformer_equipment_catalog,
            winding_equipment_catalog,
        ) = get_transformer_equipments(self.system)
        self.system.add_components(*distribution_transformer_equipment_catalog.values())
        transformers = get_transformers(
            self.system, distribution_transformer_equipment_catalog, winding_equipment_catalog
        )
        self.system.add_components(*transformers)
        conductor_equipment = get_conductors_equipment()
        self.system.add_components(*conductor_equipment)
        concentric_cable_equipment = get_cables_equipment()
        self.system.add_components(*concentric_cable_equipment)
        matrix_branch_equipments_catalog, thermal_limit_catalog = get_matrix_branch_equipments()
        for catalog in matrix_branch_equipments_catalog:
            self.system.add_components(*matrix_branch_equipments_catalog[catalog].values())

        geometry_branch_equipment_catalog, mapped_geometry = get_geometry_branch_equipments(
            self.system
        )
        self.system.add_components(*geometry_branch_equipment_catalog.values())
        branches = get_branches(
            self.system,
            mapped_geometry,
            geometry_branch_equipment_catalog,
            matrix_branch_equipments_catalog,
            thermal_limit_catalog,
        )
        self.system.add_components(*branches)

        logger.info("parsing complete...")
        logger.info(f"\n{self.system.info()}")
        logger.info("Building graph...")
        graph = build_graph_from_system(self.system)
        logger.info(graph)
        logger.info("Graph build complete...")
        logger.info("Updating graph to fix split phase representation...")
        update_split_phase_nodes(graph, self.system)
        logger.info("System update complete...")

    def get_system(self) -> DistributionSystem:
        """Returns an instance of DistributionSystem

        Returns:
            DistributionSystem: Instance of DistributionSystem
        """

        return self.system
