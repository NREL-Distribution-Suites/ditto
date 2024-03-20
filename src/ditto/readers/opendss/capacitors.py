from gdm import DistributionBus, DistributionCapacitor, CapacitorEquipment, PhaseCapacitorEquipment, ConnectionType
from gdm.quantities import PositiveReactivePower, PositiveResistance, PositiveReactance
from infrasys.system import System
import opendssdirect

from ditto.readers.opendss.common import PHASE_MAPPER

def get_capacitors(system:System, dss:opendssdirect) -> list[DistributionCapacitor]:
    """Function to return list of all capacitors in opendss model.

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator
    Returns:
        List[DistributionCapacitor]: List of DistributionCapacitor objects
    """
    
    capacitors = []
    flag = dss.Capacitors.First()
    while flag > 0:
        capacitor_name = dss.Capacitors.Name().lower()
        buses = dss.CktElement.BusNames()
        bus1 = buses[0].split(".")[0]
        num_phase = dss.CktElement.NumPhases()
        kvar_ = dss.Capacitors.kvar()
        ph_caps = []
        nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]

        for el in nodes:
            phase_capacitor = PhaseCapacitorEquipment(
                name=f"{capacitor_name}_{el}",
                rated_capacity=PositiveReactivePower(kvar_ / num_phase, "kilovar"),
                num_banks=dss.Capacitors.NumSteps(),
                num_banks_on=sum(dss.Capacitors.States()),
                resistance=PositiveResistance(0, "ohm"),
                reactance=PositiveReactance(0, "ohm"),
            )
            ph_caps.append(phase_capacitor)
        system.add_components(*ph_caps)

        capacitor_equipment = CapacitorEquipment(
            name=capacitor_name + "_equipment",
            phase_capacitors=ph_caps,
            connection_type=ConnectionType.DELTA
            if dss.Capacitors.IsDelta()
            else ConnectionType.STAR,
        )
        system.add_component(capacitor_equipment)

        capacitors.append(
            DistributionCapacitor(
                name=capacitor_name,
                bus=system.components.get(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                controllers=[],
                equipment=capacitor_equipment,
            )
        )
        flag = dss.Capacitors.Next()
    return capacitors