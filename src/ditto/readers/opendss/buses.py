
from gdm import DistributionBus, VoltageLimitSet, VoltageTypes
from gdm.quantities import PositiveVoltage
from infrasys.location import Location
from infrasys.system import System
import opendssdirect as odd

from ditto.readers.opendss.common import PHASE_MAPPER

def get_buses(system:System, crs: str = None) -> list[DistributionBus]:
    """Function to return list of all buses in Opendss model

    Args:
        system (System): Instance of System
        crs (str, optional): Coordinate reference system name. Defaults to None.

    Returns:
        list[DistributionBus]: list of DistributionBus objects
    """        
        
    buses = []

    for bus in odd.Circuit.AllBusNames():
        odd.Circuit.SetActiveBus(bus)
        nominal_voltage = odd.Bus.kVBase()

        loc = Location(x=odd.Bus.Y(), y=odd.Bus.X(), crs=crs)
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
                phases=[PHASE_MAPPER[str(node)] for node in odd.Bus.Nodes()],
                coordinate=loc,
                voltagelimits=limitsets,
            )
        )
    return buses