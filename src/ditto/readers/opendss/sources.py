from gdm import DistributionBus, PhaseVoltageSourceEquipment, VoltageSourceEquipment, DistributionVoltageSource
from gdm.quantities import Voltage, Resistance, Reactance
from infrasys.quantities import Angle
from infrasys.system import System
import opendssdirect

from ditto.readers.opendss.common import PHASE_MAPPER


def get_voltage_sources(system:System, dss:opendssdirect) -> list[DistributionVoltageSource]:
    """Function to return list of all voltage sources in opendss model.


    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator

    Returns:
        list[DistributionVoltageSource]: List of DistributionVoltageSource objects
    """    
    
    voltage_sources = []
    flag = dss.Vsources.First()
    while flag:
        soure_name = dss.Vsources.Name().lower()
        buses = dss.CktElement.BusNames()
        bus1 = buses[0].split(".")[0]
        num_phase = dss.CktElement.NumPhases()
        nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]
        angle = dss.Vsources.AngleDeg()
        angles = [Angle(angle + i * (360.0 / num_phase), "degree") for i in range(num_phase)]
        phase_slacks = []
        phase_src_properties = {}
        for ppty in ["r0", "r1", "x0", "x1"]:
            command_str = f"? vsource.{soure_name}.{ppty}"
            result = dss.run_command(command_str)
            phase_src_properties[ppty] = float(result)

        for node, angle in zip(nodes, angles):
            voltage = Voltage(dss.Vsources.BasekV() * dss.Vsources.PU(), "kilovolt")
            phase_slack = PhaseVoltageSourceEquipment(
                name=f"{soure_name}_{node}",
                r0=Resistance(phase_src_properties["r0"], "ohm"),
                r1=Resistance(phase_src_properties["r1"], "ohm"),
                x0=Reactance(phase_src_properties["x0"], "ohm"),
                x1=Reactance(phase_src_properties["x1"], "ohm"),
                angle=angle,
                voltage=voltage / 1.732 if num_phase == 3 else voltage,
            )
            phase_slacks.append(phase_slack)
        system.add_components(*phase_slacks)

        slack_equipment = VoltageSourceEquipment(
            name=soure_name,
            sources=phase_slacks,
        )
        system.add_components(slack_equipment)

        voltage_source = DistributionVoltageSource(
            name=soure_name,
            bus=system.components.get(DistributionBus, bus1),
            phases=[PHASE_MAPPER[el] for el in nodes],
            equipment=slack_equipment,
        )
        voltage_sources.append(voltage_source)
        flag = dss.Vsources.Next()
    return voltage_sources