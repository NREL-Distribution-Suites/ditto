from uuid import uuid4

from gdm import (
    DistributionSolar,
    DistributionBus,
    SolarEquipment,
)
from gdm.quantities import PositiveActivePower
from infrasys.component import Component
from infrasys.system import System
import opendssdirect as odd
from loguru import logger

from ditto.readers.opendss.common import PHASE_MAPPER, get_equipment_from_system, model_to_dict


def _build_pv_equipment() -> tuple[SolarEquipment, list[str], str, list[str]]:
    """Helper function to build a SolarEquipment instance

    Returns:
        SolarEquipment: instance of SolarEquipment
        list[str]: List of buses
        list[str]: List of phases
    """

    logger.info("parsing pvsystem equipment...")
    pv_name = odd.PVsystems.Name()

    def query(ppty):
        odd.Text.Command(f"? pvsystem.{pv_name}.{ppty}")
        return odd.Text.Result()

    equipment_uuid = uuid4()
    buses = odd.CktElement.BusNames()
    num_phase = odd.CktElement.NumPhases()
    kva_ac = odd.PVsystems.kVARated()
    kw_dc = odd.PVsystems.Pmpp()
    nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]

    solar_equipment = SolarEquipment(
        name=str(equipment_uuid),
        rated_capacity=PositiveActivePower(kva_ac, "kilova"),
        solar_power=PositiveActivePower(kw_dc, "kilova"),
        resistance=float(query(r"%r")),
        reactance=float(query(r"%x")),
        cutout_percent=float(query(r"%cutout")),
        cutin_percent=float(query(r"%cutin")),
    )

    return solar_equipment, buses, nodes


def get_pv_equipments() -> list[SolarEquipment]:
    """Function to return list of all SolarEquipment in Opendss model.

    Args:
        odd (Opendssdirect): Instance of Opendss simulator

    Returns:
        list[SolarEquipment]: List of SolarEquipment objects
    """

    logger.info("parsing pvsystem components...")

    solar_equipment_catalog = {}
    flag = odd.PVsystems.First()
    while flag > 0:
        solar_equipment, _, _ = _build_pv_equipment()
        model_dict = model_to_dict(solar_equipment)
        if str(model_dict) not in solar_equipment_catalog:
            solar_equipment_catalog[str(model_dict)] = solar_equipment
        flag = odd.PVsystems.Next()
    return solar_equipment_catalog


def get_pvsystems(system: System, catalog: dict[str, Component]) -> list[DistributionSolar]:
    """Function to return list of DistributionSolar in Opendss model.

    Args:
        system (System): Instance of System
        catalog: dict[str, Component]: Catalog of SolarEquipment

    Returns:
        List[DistributionSolar]: List of DistributionSolar objects
    """

    logger.info("parsing pvsystem components...")

    pv_systems = []
    flag = odd.PVsystems.First()
    while flag > 0:
        logger.info(f"building pvsystem {odd.PVsystems.Name()}...")

        solar_equipment, buses, nodes = _build_pv_equipment()
        bus1 = buses[0].split(".")[0]
        equipment_from_libray = get_equipment_from_system(solar_equipment, SolarEquipment, catalog)
        if equipment_from_libray:
            equipment = equipment_from_libray
        else:
            equipment = solar_equipment
        pv_systems.append(
            DistributionSolar(
                name=odd.Capacitors.Name().lower(),
                bus=system.get_component(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                controllers=[],
                equipment=equipment,
            )
        )
        flag = odd.PVsystems.Next()
    return pv_systems
