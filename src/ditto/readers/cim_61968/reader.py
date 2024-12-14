from pathlib import Path

from ditto.readers.cim_61968.components.buses import get_buses
from gdm import DistributionSystem
from gdm import SequencePair
from loguru import logger
import rdflib

# from ditto.readers.cim_61968.components.conductors import get_conductors_equipment
# from ditto.readers.cim_61968.components.cables import get_cables_equipment
# from ditto.readers.cim_61968.components.sources import get_voltage_sources
# from ditto.readers.cim_61968.components.capacitors import get_capacitors
# from ditto.readers.cim_61968.graph_utils import update_split_phase_nodes
# from ditto.readers.cim_61968.components.pv_systems import get_pvsystems
# from ditto.readers.cim_61968.components.loads import get_loads
# from ditto.readers.cim_61968.components.transformers import (
#     get_transformer_equipments,
#     get_transformers,
# )
# from ditto.readers.cim_61968.components.branches import (
#     get_geometry_branch_equipments,
#     get_matrix_branch_equipments,
#     get_branches,
# )

from ditto.readers.reader import AbscractReader

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class Reader(AbscractReader):
    """Class interface for Opendss case file reader"""

    def __init__(self, cim_xml_file: Path | str, crs: str | None = None) -> None:
        """Constructor for the Opendss reader

        Args:
            cim_xml_file (Path): Path to the CIM xml file
            crs (str | None, optional): Coordinate reference system name. Defaults to None.
        """
        self._cim_xml_file = Path(cim_xml_file)
        self._system = DistributionSystem(auto_add_composed_components=True)
        self.rdf_graph = rdflib.Graph()

        self.crs = crs
        self.read()

    def read(self):
        """Parses the CIM xml file and build a GDM model

        Raises:
            FileNotFoundError: Error raised if the file is not found
        """

        logger.info("Loading CIM model.")

        if not self._cim_xml_file.exists():
            msg = f"File not found: {self._cim_xml_file}"
            raise FileNotFoundError(msg)

        self.rdf_graph.parse(self._cim_xml_file, format="xml")

        self._system.add_components(*get_buses(self.rdf_graph, self.crs))

        # self._add_components(get_voltage_sources(self.system))
        # self._add_components(get_capacitors(self.system))
        # self._add_components(get_loads(self.system))
        # self._add_components(get_pvsystems(self.system))
        # (
        #     distribution_transformer_equipment_catalog,
        #     winding_equipment_catalog,
        # ) = get_transformer_equipments(self.system)
        # self._add_components(distribution_transformer_equipment_catalog.values())
        # self._add_components(get_transformers(
        #     self.system, distribution_transformer_equipment_catalog, winding_equipment_catalog
        # ))
        # self._add_components(get_conductors_equipment())
        # self._add_components(get_cables_equipment())
        # matrix_branch_equipments_catalog, thermal_limit_catalog = get_matrix_branch_equipments()
        # for catalog in matrix_branch_equipments_catalog:
        #     self._add_components(matrix_branch_equipments_catalog[catalog].values())

        # geometry_branch_equipment_catalog, mapped_geometry = get_geometry_branch_equipments(
        #     self.system
        # )
        # self._add_components(geometry_branch_equipment_catalog.values())
        # branches = get_branches(
        #     self.system,
        #     mapped_geometry,
        #     geometry_branch_equipment_catalog,
        #     matrix_branch_equipments_catalog,
        #     thermal_limit_catalog,
        # )
        # self._add_components(branches)

        # logger.info("parsing complete...")
        # logger.info(f"\n{self.system.info()}")
        # logger.info("Building graph...")
        # graph = build_graph_from_system(self.system)
        # logger.info(graph)
        # logger.info("Graph build complete...")
        # logger.info("Updating graph to fix split phase representation...")
        # update_split_phase_nodes(graph, self.system)
        # logger.info("System update complete...")

    def get_system(self) -> DistributionSystem:
        """Returns an instance of DistributionSystem

        Returns:
            DistributionSystem: Instance of DistributionSystem
        """

        return self.system
