
from infrasys.system import System 
from gdm.quantities import (
    PositiveResistancePULength, 
    CapacitancePULength, 
    ReactancePULength, 
    PositiveDistance,
    PositiveCurrent, 
)
from gdm import (
    MatrixImpedanceBranchEquipment,
    MatrixImpedanceBranch, 
    DistributionBus, 
    ThermalLimitSet,
    GeometryBranch, 
)
import opendssdirect
import numpy as np

from ditto.readers.opendss.common import PHASE_MAPPER, UNIT_MAPPER

def get_ac_lines(system:System, dss:opendssdirect) -> list[MatrixImpedanceBranch | GeometryBranch]:
    """Function to return list of all line segments in opendss model.

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator

    Returns:
        list[MatrixImpedanceBranch | GeometryBranch]: List of line segment metadata object
    """    

    edges = []
    flag = dss.Lines.First()
    while flag > 0:
        if not dss.Lines.IsSwitch():
            section_name = dss.CktElement.Name().lower()
            buses = dss.CktElement.BusNames()
            bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]
            num_phase = dss.CktElement.NumPhases()
            nodes = ["1", "2", "3"] if num_phase == 3 else buses[0].split(".")[1:]
            if dss.Lines.Geometry():
                edges.append(
                    _build_branch_using_geometry(
                        system, dss, section_name, bus1, bus2, nodes, num_phase
                    )
                )
            else:
                edges.append(
                    _build_branch_using_martices(
                        system, dss, section_name, bus1, bus2, nodes, num_phase
                    )
                )
                ...
        flag = dss.Lines.Next()
    return edges

def _build_branch_using_geometry(
        system:System, 
        dss:opendssdirect,
        section_name: str,
        bus1: str, 
        bus2: str, 
        nodes: list[str], 
        num_phase: int
    ) -> GeometryBranch:
    """Method to build a GeometryBranch

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator
        section_name (str): line section unique identifier
        bus1 (str): From bus for the line
        bus2 (str): To bus for the line
        nodes (list[str]): list of Phase objects
        num_phase (int): Number of connected phases

    Raises:
        NotImplementedError: _description_

    Returns:
        GeometryBranch: returns a GeometryBranch object
    """   
     
    raise NotImplementedError("Geometry line type not yet implemented")
    branch = []
    return branch

def _build_branch_using_martices(
        system:System, 
        dss:opendssdirect,
        section_name: str, 
        bus1: str, 
        bus2: str, 
        nodes: list[str], 
        num_phase: int
    ) -> MatrixImpedanceBranch:
    """Method to build a MatrixImpedanceBranch

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator
        section_name (str): line section unique identifier
        bus1 (str): From bus for the line
        bus2 (str): To bus for the line
        nodes (list[str]): list of Phase objects
        num_phase (int): Number of connected phases
        
    Returns:
        MatrixImpedanceBranch: returns a MatrixImpedanceBranch object
    """    
    
    thermal_limits = ThermalLimitSet(
        limit_type="max",
        value=PositiveCurrent(dss.Lines.EmergAmps(), "ampere"),
    )
    system.add_component(thermal_limits)
    cmd = f"? {section_name}.units"
    length_units = dss.run_command(cmd)
    matrix_branch_equipment = MatrixImpedanceBranchEquipment(
        name=section_name + "_equipment",
        r_matrix=PositiveResistancePULength(
            np.reshape(np.array(dss.Lines.RMatrix()), (num_phase, num_phase)),
            f"ohm/{length_units}",
        ),
        x_matrix=ReactancePULength(
            np.reshape(np.array(dss.Lines.XMatrix()), (num_phase, num_phase)),
            f"ohm/{length_units}",
        ),
        c_matrix=CapacitancePULength(
            np.reshape(np.array(dss.Lines.CMatrix()), (num_phase, num_phase)),
            f"nanofarad/{length_units}",
        ),
        ampacity=PositiveCurrent(dss.Lines.NormAmps(), "ampere"),
        loading_limit=thermal_limits,
    )
    system.add_component(matrix_branch_equipment)

    branch = MatrixImpedanceBranch(
        name=section_name,
        buses=[
            system.components.get(DistributionBus, bus1),
            system.components.get(DistributionBus, bus2),
        ],
        length=PositiveDistance(dss.Lines.Length(), UNIT_MAPPER[dss.Lines.Units()]),
        phases=[PHASE_MAPPER[node] for node in nodes],
        equipment=matrix_branch_equipment,
        is_closed=dss.CktElement.Enabled(),
    )
    return branch