from uuid import uuid4

from gdm import (
    DistributionSolar,
    DistributionBus,
    SolarEquipment,
    PowerfactorInverterController,
    InverterEquipment,
)
from gdm.quantities import PositiveActivePower, PositiveApparentPower
from infrasys.system import System
import opendssdirect as odd
from loguru import logger

from ditto.readers.opendss.common import PHASE_MAPPER, get_equipment_from_catalog


def _build_pv_equipment(
    solar_equipment_catalog: dict[int, SolarEquipment],
) -> tuple[SolarEquipment, list[str], str, list[str]]:
    """Helper function to build a SolarEquipment instance

    Args:
        solar_equipment_catalog (dict[int, SolarEquipment]): mapping of model hash to SolarEquipment instance

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
    solar_equipment = get_equipment_from_catalog(solar_equipment, solar_equipment_catalog)
    return solar_equipment, buses, nodes


def get_pvsystems(system: System) -> list[DistributionSolar]:
    """Function to return list of DistributionSolar in Opendss model.

    Args:
        system (System): Instance of System

    Returns:
        List[DistributionSolar]: List of DistributionSolar objects
    """

    logger.info("parsing pvsystem components...")
    solar_equipment_catalog = {}
    pv_systems = []
    flag = odd.PVsystems.First()
    while flag > 0:
        logger.info(f"building pvsystem {odd.PVsystems.Name()}...")

        solar_equipment, buses, nodes = _build_pv_equipment(solar_equipment_catalog)
        bus1 = buses[0].split(".")[0]
        pv_systems.append(
            DistributionSolar(
                name=odd.PVsystems.Name().lower(),
                bus=system.get_component(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                controller=PowerfactorInverterController(
                    name=str(uuid4()),
                    power_factor=1.0,
                    equipment=InverterEquipment(
                        name=str(uuid4()),
                        capacity=PositiveApparentPower(odd.PVsystems.kVARated(), "kilova"),
                        rise_limit=None,
                        fall_limit=None,
                        eff_curve=None
                    ),
                ),
                equipment=solar_equipment,
            )
        )
        flag = odd.PVsystems.Next()
    return pv_systems
