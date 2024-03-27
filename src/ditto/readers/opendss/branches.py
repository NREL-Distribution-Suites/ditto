from uuid import uuid4
from enum import Enum

from infrasys import System
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
)
import opendssdirect as odd
from loguru import logger
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


def get_geometry_branch_equipments(
    system: System,
) -> tuple[list[GeometryBranchEquipment], dict[str, str]]:
    """Helper function that return a list of GeometryBranchEquipment objects

    Args:
        system (System): Instance of System

    Returns:
        list[GeometryBranchEquipment]: list of GeometryBranchEquipment objects
        dict[str, str]: mapping line geometries to unique GeometryBranchEquipment names
    """

    logger.info("parsing geometry branch equipment...")

    mapped_geometry = {}
    geometry_branch_equipments_catalog = {}
    flag = odd.LineGeometries.First()

    while flag > 0:
        geometry_name = odd.LineGeometries.Name().lower()
        x_coordinates = []
        y_coordinates = []
        units = UNIT_MAPPER[odd.LineGeometries.Units()[0].value]
        odd.Text.Command(f"? LineGeometry.{geometry_name}.wires")
        wires = odd.Text.Result().strip("[]").split(", ")
        model_name = odd.Element.Name().lower().split(".")[1]
        conductor_elements = []

        for i, wire in enumerate(wires):
            odd.Text.Command(f"LineGeometry.{geometry_name}.cond={i+1}")
            odd.Text.Command(f"? LineGeometry.{geometry_name}.h")
            y_coordinates.append(float(odd.Text.Result()))
            odd.Text.Command(f"? LineGeometry.{geometry_name}.x")
            x_coordinates.append(float(odd.Text.Result()))

            equipments = list(
                system.get_components(BareConductorEquipment, filter_func=lambda x: x.name == wire)
            )
            if not equipments:
                equipments = list(
                    system.get_components(
                        ConcentricCableEquipment, filter_func=lambda x: x.name == wire
                    )
                )
            equipment = equipments[0]
            conductor_elements.append(equipment)

        geometry_branch_equipment = GeometryBranchEquipment(
            name=model_name,
            conductors=conductor_elements,
            horizontal_positions=[Distance(x, units) for x in x_coordinates],
            vertical_positions=[Distance(y, units) for y in y_coordinates],
        )
        model_dict = model_to_dict(geometry_branch_equipment)
        if str(model_dict) not in geometry_branch_equipments_catalog:
            geometry_branch_equipments_catalog[str(model_dict)] = geometry_branch_equipment
        else:
            equipment = geometry_branch_equipments_catalog[str(model_dict)]
            mapped_geometry[geometry_branch_equipment.name] = equipment.name
        flag = odd.LineGeometries.Next()

    return geometry_branch_equipments_catalog, mapped_geometry


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

    logger.info("parsing matrix branch equipment...")

    matrix_branch_equipments_catalog = {}
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
                    matrix_branch_equipments_catalog[str(model_dict)] = matrix_branch_equipment
            flag = module.Next()
    return matrix_branch_equipments_catalog


def get_branches(
    system: System, mapping: dict[str, str], matrix_branch_catalog, geometry_branch_catalog
) -> tuple[list[MatrixImpedanceBranch | GeometryBranch]]:
    """Method to build a model branches

    Args:
        system (System): Instance of System
        mapping (dict[str, str]): mapping line geometries to unique GeometryBranchEquipment names

    Returns:
        list[MatrixImpedanceBranch]: Returns a MatrixImpedanceBranch object
        list[GeometryBranch]: Returns a GeometryBranch object
    """

    logger.info("parsing branch components...")

    branches = []
    flag = odd.Lines.First()
    while flag > 0:
        logger.info(f"building line {odd.CktElement.Name()}...")

        buses = odd.CktElement.BusNames()
        bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]
        num_phase = odd.CktElement.NumPhases()
        nodes = ["1", "2", "3"] if num_phase == 3 else buses[0].split(".")[1:]
        geometry = odd.Lines.Geometry().lower()
        if geometry:
            if geometry in mapping:
                geometry = mapping[geometry]
            geometry_branch_equipment = system.get_component(GeometryBranchEquipment, geometry)
            n_conds = len(geometry_branch_equipment.conductors)
            for _ in range(
                n_conds - num_phase
            ):  # Any conductor after the phase conductors will be considered a neutral
                nodes.append("4")
            geometry_branch = GeometryBranch(
                name=odd.Lines.Name().lower(),
                equipment=geometry_branch_equipment,
                buses=[
                    system.get_component(DistributionBus, bus1),
                    system.get_component(DistributionBus, bus2),
                ],
                length=PositiveDistance(odd.Lines.Length(), UNIT_MAPPER[odd.Lines.Units()]),
                phases=[PHASE_MAPPER[node] for node in nodes],
            )
            branches.append(geometry_branch)
        else:
            matrix_branch_equipment = _build_matrix_branch(MatrixBranchTypes.LINE.value)
            equipment_from_libray = get_equipment_from_system(
                matrix_branch_equipment, MatrixImpedanceBranchEquipment, matrix_branch_catalog
            )
            if equipment_from_libray:
                equipment = equipment_from_libray
            else:
                equipment = matrix_branch_equipment

            matrix_branch = MatrixImpedanceBranch(
                name=odd.Lines.Name().lower(),
                buses=[
                    system.get_component(DistributionBus, bus1),
                    system.get_component(DistributionBus, bus2),
                ],
                length=PositiveDistance(odd.Lines.Length(), UNIT_MAPPER[odd.Lines.Units()]),
                phases=[PHASE_MAPPER[node] for node in nodes],
                equipment=equipment,
            )
            branches.append(matrix_branch)
        flag = odd.Lines.Next()

    return branches
