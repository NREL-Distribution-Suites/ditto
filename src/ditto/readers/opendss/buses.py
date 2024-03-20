
from gdm import DistributionBus, VoltageLimitSet, VoltageTypes
from gdm.quantities import PositiveVoltage
from infrasys.location import Location
from infrasys.system import System
import opendssdirect

from ditto.readers.opendss.common import PHASE_MAPPER

def get_buses(system:System, dss:opendssdirect,  crs: str = None) -> list[DistributionBus]:
    """Function to return list of all buses in opendss model

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator
        crs (str, optional): Coordinate reference system name. Defaults to None.

    Returns:
        list[DistributionBus]: list of DistributionBus objects
    """        
        
    buses = []

    for bus in dss.Circuit.AllBusNames():
        dss.Circuit.SetActiveBus(bus)
        nominal_voltage = dss.Bus.kVBase()

        loc = Location(x=dss.Bus.Y(), y=dss.Bus.X(), crs=crs)
        system.add_component(loc)

        limitsets = [
            VoltageLimitSet(
                limit_type="min",
                value=PositiveVoltage(nominal_voltage * 0.95, "kilovolt"),
            ),
            VoltageLimitSet(
                limit_type="max",
                value=PositiveVoltage(nominal_voltage * 1.05, "kilovolt"),
            ),
        ]
        system.add_components(*limitsets)
        buses.append(
            DistributionBus(
                voltage_type=VoltageTypes.LINE_TO_GROUND.value,
                name=bus,
                nominal_voltage=PositiveVoltage(nominal_voltage, "kilovolt"),
                phases=[PHASE_MAPPER[str(node)] for node in dss.Bus.Nodes()],
                coordinate=loc,
                voltagelimits=limitsets,
            )
        )
    return buses