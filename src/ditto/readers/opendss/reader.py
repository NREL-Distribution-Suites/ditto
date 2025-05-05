from pathlib import Path

from gdm.distribution.common import SequencePair
from gdm.distribution import DistributionSystem
import opendssdirect as odd
from loguru import logger
from infrasys import Component

from ditto.readers.opendss.components.conductors import get_conductors_equipment
from ditto.readers.opendss.components.cables import get_cables_equipment
from ditto.readers.opendss.components.sources import get_voltage_sources
from ditto.readers.opendss.components.capacitors import get_capacitors
from ditto.readers.opendss.graph_utils import update_split_phase_nodes
from ditto.readers.opendss.components.pv_systems import get_pvsystems
from ditto.readers.opendss.components.buses import get_buses
from ditto.readers.opendss.components.loads import get_loads
from ditto.readers.opendss.components.transformers import (
    get_transformer_equipments,
    get_transformers,
)
from ditto.readers.opendss.components.branches import (
    get_geometry_branch_equipments,
    get_matrix_branch_equipments,
    get_branches,
)

from ditto.readers.reader import AbstractReader


SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class Reader(AbstractReader):
    """Class interface for Opendss case file reader"""

    def __init__(self, Opendss_master_file: Path, crs: str | None = None) -> None:
        """Constructor for the Opendss reader

        Args:
            Opendss_master_file (Path): Path to the Opendss master file
            crs (str | None, optional): Coordinate reference system name. Defaults to None.
        """

        self.system = DistributionSystem(auto_add_composed_components=True)
        self.Opendss_master_file = Path(Opendss_master_file)
        self.crs = crs
        self._read()

    def _add_components(self, components: list[Component]):
        """Internal method to add components to the system."""
        if components:
            self.system.add_components(*components)

    def _read(self):
        """Takes the master file path and returns instance of OpendssParser

        Raises:
            FileNotFoundError: Error raised if the file is not found
        """

        logger.debug("Loading OpenDSS model.")
        if not self.Opendss_master_file.exists():
            msg = f"File not found: {self.Opendss_master_file}"
            raise FileNotFoundError(msg)

        odd.Text.Command("Clear")
        odd.Basic.ClearAll()
        odd.Text.Command(f'Redirect "{self.Opendss_master_file}"')
        odd.Text.Command("Solve")
        logger.debug(f"Model loaded from {self.Opendss_master_file}.")

        odd.Solution.Solve()

        self._add_components(get_buses(self.crs))
        self._add_components(get_voltage_sources(self.system))
        self._add_components(get_capacitors(self.system))
        self._add_components(get_loads(self.system))
        self._add_components(get_pvsystems(self.system))
        (
            distribution_transformer_equipment_catalog,
            winding_equipment_catalog,
        ) = get_transformer_equipments(self.system)
        self._add_components(distribution_transformer_equipment_catalog.values())
        self._add_components(
            get_transformers(
                self.system, distribution_transformer_equipment_catalog, winding_equipment_catalog
            )
        )
        self._add_components(get_conductors_equipment())
        self._add_components(get_cables_equipment())
        matrix_branch_equipments_catalog, thermal_limit_catalog = get_matrix_branch_equipments()
        for catalog in matrix_branch_equipments_catalog:
            self._add_components(matrix_branch_equipments_catalog[catalog].values())

        geometry_branch_equipment_catalog, mapped_geometry = get_geometry_branch_equipments(
            self.system
        )
        self._add_components(geometry_branch_equipment_catalog.values())
        branches = get_branches(
            self.system,
            mapped_geometry,
            geometry_branch_equipment_catalog,
            matrix_branch_equipments_catalog,
            thermal_limit_catalog,
        )
        self._add_components(branches)

        logger.debug("parsing complete...")
        logger.debug(f"\n{self.system.info()}")
        logger.debug("Building graph...")
        graph = self.system.get_undirected_graph()
        logger.debug(graph)
        logger.debug("Graph build complete...")
        logger.debug("Updating graph to fix split phase representation...")
        update_split_phase_nodes(graph, self.system)
        logger.debug("System update complete...")

    def get_system(self) -> DistributionSystem:
        """Returns an instance of DistributionSystem

        Returns:
            DistributionSystem: Instance of DistributionSystem
        """

        return self.system
