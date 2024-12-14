from gdm import DistributionBus
from rdflib import Graph
from loguru import logger


def get_buses(graph: Graph, crs: str = None) -> list[DistributionBus]:
    logger.info("Querying bus components from the CIM graph...")

    buses = []

    bus_query = """
    PREFIX cim: <http://iec.ch/TC57/CIM100#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?name
    WHERE {
        ?eq rdf:type cim:ACLineSegment .
        ?eq cim:IdentifiedObject.mRID ?mRID.
        ?eq cim:IdentifiedObject.name ?name.
    }"""

    results = graph.query(bus_query)
    for row in results:
        print(f"{row.name}")

    return buses
