from uuid import uuid4
from enum import Enum

from infrasys.system import System
from gdm.quantities import (
    PositiveResistancePULength,
    CapacitancePULength,
    ReactancePULength,
    PositiveDistance,
    PositiveCurrent,
    Distance,
)
from gdm import (
    MatrixImpedanceBranchEquipment,
    GeometryBranchEquipment,
    ConcentricCableEquipment,
    BareConductorEquipment,
    MatrixImpedanceBranch,
    DistributionBus,
    ThermalLimitSet,
    GeometryBranch,
    SequencePair,
)
import opendssdirect as odd
import numpy as np

from ditto.readers.opendss.common import (
    PHASE_MAPPER,
    UNIT_MAPPER,
    model_to_dict,
    get_equipment_from_system,
)


class MatrixBranchTypes(str, Enum):
    LINE_CODE = "LineCodes"
    LINE = "Lines"


def get_geometry_branch_equipments(system: System) -> list[GeometryBranchEquipment]:
    """Helper function to build a GeometryBranchEquipment instance

    Args:
        system (System): Instance of System

    Returns:
        GeometryBranchEquipment: instance of GeometryBranchEquipment
    """

    geometry_branch_equipments_catalog = []
    geometry_branch_equipments = []
    flag = odd.LineGeometries.First()
    while flag > 0:
        conductors = odd.LineGeometries.Conductors()
        x_coordinates = odd.LineGeometries.Xcoords()
        y_coordinates = odd.LineGeometries.Ycoords()
        units = UNIT_MAPPER[odd.LineGeometries.Units()[0].value]
        model_name = odd.Element.Name().lower().split(".")[1]
        conductor_elements = []
        for conductor in conductors:
            try:
                equipment = system.get_component(BareConductorEquipment, conductor)
            except Exception as _:
                equipment = system.get_component(ConcentricCableEquipment, conductor)
            conductor_elements.append(equipment)

        sequence_pairs = [SequencePair(i, i + 1) for i in range(len(conductors) - 1)]
        horizontal_spacings = [
            Distance(x_coordinates[i + 1] - x_coordinates[i], units)
            for i in range(len(x_coordinates) - 1)
        ]
        y_coordinates = [Distance(y, units) for y in y_coordinates]
        geometry_branch_equipment = GeometryBranchEquipment(
            name=model_name,
            conductors=conductor_elements,
            spacing_sequences=sequence_pairs,
            horizontal_spacings=horizontal_spacings,
            heights=y_coordinates,
        )
        model_dict = model_to_dict(geometry_branch_equipment)
        if model_dict not in geometry_branch_equipments_catalog:
            geometry_branch_equipments_catalog.append(model_dict)
            geometry_branch_equipments.append(geometry_branch_equipment)
        flag = odd.LineGeometries.Next()
    return geometry_branch_equipments


def _build_matrix_branch(model_type: str) -> MatrixImpedanceBranchEquipment:
    """Helper function to build a MatrixImpedanceBranchEquipment instance

    Args:
        model_type (str): OpenDSS model type e.g. LineCode / Line

    Returns:
        MatrixImpedanceBranchEquipment: instance of MatrixImpedanceBranchEquipment
    """

    model_name = odd.Element.Name().lower().split(".")[1]
    if model_type == MatrixBranchTypes.LINE_CODE.value:
        equipment_uuid = model_name
    else:
        equipment_uuid = str(uuid4())
    module: odd.LineCodes | odd.Lines = getattr(odd, model_type)

    num_phase = module.Phases()
    thermal_limits = ThermalLimitSet(
        limit_type="max",
        value=PositiveCurrent(module.EmergAmps(), "ampere"),
    )
    length_units = UNIT_MAPPER[module.Units().value]

    r_matrix = module.RMatrix() if model_type == MatrixBranchTypes.LINE.value else module.Rmatrix()
    x_matrix = module.XMatrix() if model_type == MatrixBranchTypes.LINE.value else module.Xmatrix()
    c_matrix = module.CMatrix() if model_type == MatrixBranchTypes.LINE.value else module.Cmatrix()
    matrix_branch_equipment = MatrixImpedanceBranchEquipment(
        name=equipment_uuid,
        r_matrix=PositiveResistancePULength(
            np.reshape(np.array(r_matrix), (num_phase, num_phase)),
            f"ohm/{length_units}",
        ),
        x_matrix=ReactancePULength(
            np.reshape(np.array(x_matrix), (num_phase, num_phase)),
            f"ohm/{length_units}",
        ),
        c_matrix=CapacitancePULength(
            np.reshape(np.array(c_matrix), (num_phase, num_phase)),
            f"nanofarad/{length_units}",
        ),
        ampacity=PositiveCurrent(module.NormAmps(), "ampere"),
        loading_limit=thermal_limits,
    )
    return matrix_branch_equipment


def get_matrix_branch_equipments() -> tuple[list[MatrixImpedanceBranchEquipment]]:
    """Function to return list of all MatrixImpedanceBranchEquipment in Opendss model.

    Returns:
        list[MatrixImpedanceBranchEquipment]: List of MatrixImpedanceBranchEquipment objects
    """

    matrix_branch_equipments_catalog = []
    matrix_branch_equipments = []
    odd_model_types = [v.value for v in MatrixBranchTypes]
    for odd_model_type in odd_model_types:
        module: odd.LineCodes | odd.Lines = getattr(odd, odd_model_type)
        flag = module.First()
        while flag > 0:
            if odd_model_type == MatrixBranchTypes.LINE.value and module.Geometry():
                pass
            else:
                matrix_branch_equipment = _build_matrix_branch(odd_model_type)
                model_dict = model_to_dict(matrix_branch_equipment)
                if str(model_dict) not in matrix_branch_equipments_catalog:
                    matrix_branch_equipments_catalog.append(str(model_dict))
                    matrix_branch_equipments.append(matrix_branch_equipment)
            flag = module.Next()
    return matrix_branch_equipments


def get_branches(system: System) -> tuple[list[MatrixImpedanceBranch], list[GeometryBranch]]:
    """Method to build a model branches

    Args:
        system (System): Instance of System

    Returns:
        list[MatrixImpedanceBranch]: Returns a MatrixImpedanceBranch object
        list[GeometryBranch]: Returns a GeometryBranch object
    """

    matrix_branches = []
    geometry_branches = []
    flag = odd.Lines.First()
    while flag > 0:
        buses = odd.CktElement.BusNames()
        bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]
        num_phase = odd.CktElement.NumPhases()
        nodes = ["1", "2", "3"] if num_phase == 3 else buses[0].split(".")[1:]
        geometry = odd.Lines.Geometry()
        if geometry:
            geometry_branch_equipment = system.get_component(GeometryBranchEquipment, geometry)
            geometry_branch = GeometryBranch(
                name=odd.Lines.Name().lower(),
                equipment=geometry_branch_equipment,
                buses=[
                    system.components.get(DistributionBus, bus1),
                    system.components.get(DistributionBus, bus2),
                ],
                length=PositiveDistance(odd.Lines.Length(), UNIT_MAPPER[odd.Lines.Units()]),
                phases=[PHASE_MAPPER[node] for node in nodes],
                is_closed=odd.CktElement.Enabled(),
            )
            geometry_branches.append(geometry_branch)
        else:
            matrix_branch_equipment = _build_matrix_branch(MatrixBranchTypes.LINE.value)
            equipment_from_libray = get_equipment_from_system(
                matrix_branch_equipment, MatrixImpedanceBranchEquipment, system
            )
            if equipment_from_libray:
                equipment = equipment_from_libray
            else:
                equipment = matrix_branch_equipment

            matrix_branch = MatrixImpedanceBranch(
                name=odd.Lines.Name().lower(),
                buses=[
                    system.components.get(DistributionBus, bus1),
                    system.components.get(DistributionBus, bus2),
                ],
                length=PositiveDistance(odd.Lines.Length(), UNIT_MAPPER[odd.Lines.Units()]),
                phases=[PHASE_MAPPER[node] for node in nodes],
                equipment=equipment,
                is_closed=odd.CktElement.Enabled(),
            )
            matrix_branches.append(matrix_branch)
        flag = odd.Lines.Next()

    return matrix_branches, geometry_branches
