from uuid import uuid4

from gdm import (
    DistributionBus,
    PhaseVoltageSourceEquipment,
    VoltageSourceEquipment,
    DistributionVoltageSource,
)
from infrasys.quantities import Angle, Resistance, Voltage
from infrasys.component import Component
from gdm.quantities import Reactance
from infrasys.system import System
import opendssdirect as odd
from loguru import logger

from ditto.readers.opendss.common import PHASE_MAPPER, model_to_dict, get_equipment_from_system


def _build_voltage_source_equipment() -> tuple[VoltageSourceEquipment, list[str], str, list[str]]:
    """Helper function to build a VoltageSourceEquipment instance

    Returns:
        VoltageSourceEquipment: instance of VoltageSourceEquipment
        list[str]: List of buses
        str:  Voltage source name
        list[str]: List of phases
    """
    equipment_uuid = uuid4()
    soure_name = odd.Vsources.Name().lower()
    buses = odd.CktElement.BusNames()
    num_phase = odd.CktElement.NumPhases()
    nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]
    angle = odd.Vsources.AngleDeg()
    angles = [Angle(angle + i * (360.0 / num_phase), "degree") for i in range(num_phase)]
    phase_slacks = []
    phase_src_properties = {}

    for ppty in ["r0", "r1", "x0", "x1"]:
        command_str = f"? vsource.{soure_name}.{ppty}"
        result = odd.run_command(command_str)
        phase_src_properties[ppty] = float(result)

    for node, angle in zip(nodes, angles):
        voltage = Voltage(odd.Vsources.BasekV() * odd.Vsources.PU(), "kilovolt")
        phase_slack = PhaseVoltageSourceEquipment(
            name=f"{equipment_uuid}_{node}",
            r0=Resistance(phase_src_properties["r0"], "ohm"),
            r1=Resistance(phase_src_properties["r1"], "ohm"),
            x0=Reactance(phase_src_properties["x0"], "ohm"),
            x1=Reactance(phase_src_properties["x1"], "ohm"),
            angle=angle,
            voltage=voltage / 1.732 if num_phase == 3 else voltage,
        )
        phase_slacks.append(phase_slack)

    slack_equipment = VoltageSourceEquipment(
        name=str(equipment_uuid),
        sources=phase_slacks,
    )
    return slack_equipment, buses, soure_name, nodes


def get_voltage_source_equipments() -> list[VoltageSourceEquipment]:
    """Function to return list of all voltage sources equipments in Opendss model.

    Returns:
        list[VoltageSourceEquipment]: List of VoltageSourceEquipment objects
    """

    logger.info("parsing voltage source equipment...")

    voltage_sources_equipment_catalog = {}
    flag = odd.Vsources.First()
    while flag:
        slack_equipment, _, _, _ = _build_voltage_source_equipment()
        model_dict = model_to_dict(slack_equipment)
        if str(model_dict) not in voltage_sources_equipment_catalog:
            voltage_sources_equipment_catalog[str(model_dict)] = slack_equipment

        flag = odd.Vsources.Next()
    return voltage_sources_equipment_catalog


def get_voltage_sources(
    system: System, catalog: dict[str, Component]
) -> list[DistributionVoltageSource]:
    """Function to return list of all voltage sources in Opendss model.

    Args:
        system (System): Instance of System

    Returns:
        list[DistributionVoltageSource]: List of DistributionVoltageSource objects
    """

    logger.info("parsing voltage sources components...")

    voltage_sources = []
    flag = odd.Vsources.First()
    while flag:
        slack_equipment, buses, soure_name, nodes = _build_voltage_source_equipment()
        equipment_from_libray = get_equipment_from_system(
            slack_equipment, VoltageSourceEquipment, catalog
        )
        if equipment_from_libray:
            equipment = equipment_from_libray
        else:
            equipment = slack_equipment
        bus1 = buses[0].split(".")[0]

        voltage_source = DistributionVoltageSource(
            name=soure_name,
            bus=system.get_component(DistributionBus, bus1),
            phases=[PHASE_MAPPER[el] for el in nodes],
            equipment=equipment,
        )
        voltage_sources.append(voltage_source)
        flag = odd.Vsources.Next()
    return voltage_sources
