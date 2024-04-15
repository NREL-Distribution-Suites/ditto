from uuid import uuid4
from enum import Enum

from infrasys import System, Component

from gdm.quantities import (
    PositiveResistancePULength,
    CapacitancePULength,
    ReactancePULength,
    PositiveDistance,
    PositiveCurrent,
    # Distance,
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
from infrasys.quantities import Distance
import opendssdirect as odd
from loguru import logger
import numpy as np

from ditto.readers.opendss.common import (
    get_equipment_from_catalog,
    PHASE_MAPPER,
    UNIT_MAPPER,
    hash_model,
)


class MatrixBranchTypes(str, Enum):
    LINE_CODE = "LineCodes"
    LINE = "Lines"


def get_geometry_branch_equipments(
    system: System,
) -> tuple[list[GeometryBranchEquipment], dict[str, int]]:
    """Helper function that return a list of GeometryBranchEquipment objects

    Args:
        system (System): Instance of System

    Returns:
        list[GeometryBranchEquipment]: list of GeometryBranchEquipment objects
        dict[str, int]: mapping of line geometries names to GeometryBranchEquipment hash
    """

    logger.info("parsing geometry branch equipment...")

    mapped_geometry = {}
    geometry_branch_equipment_catalog = {}
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
            horizontal_positions=Distance(x_coordinates, units),
            vertical_positions=Distance(y_coordinates, units),
        )
        geometry_branch_equipment = get_equipment_from_catalog(
            geometry_branch_equipment, geometry_branch_equipment_catalog
        )
        mapped_geometry[geometry_name] = hash_model(geometry_branch_equipment)

        flag = odd.LineGeometries.Next()

    return geometry_branch_equipment_catalog, mapped_geometry


def _build_matrix_branch(
    model_type: str,
    matrix_branch_equipments_catalog: dict[int, Component],
    thermal_limit_catalog: dict[int, Component],
) -> MatrixImpedanceBranchEquipment:
    """Helper function to build a MatrixImpedanceBranchEquipment instance

    Args:
        model_type (str): OpenDSS model type e.g. LineCode / Line
        matrix_branch_equipments_catalog (dict[int, Component]): mapping of model hash to MatrixImpedanceBranchEquipment instance
        thermal_limit_catalog (dict[int, Component]): mapping of model hash to ThermalLimitSet instance

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

    thermal_limits = get_equipment_from_catalog(thermal_limits, thermal_limit_catalog)

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

    matrix_branch_equipment = get_equipment_from_catalog(
        matrix_branch_equipment, matrix_branch_equipments_catalog
    )

    return matrix_branch_equipment


def get_matrix_branch_equipments() -> (
    tuple[dict[int, MatrixImpedanceBranchEquipment], dict[int, ThermalLimitSet]]
):
    """Function to return list of all MatrixImpedanceBranchEquipment in Opendss model.

    Returns:
        dict[int, MatrixImpedanceBranchEquipment]: mapping of model hash to MatrixImpedanceBranchEquipment instance
        dict[int, ThermalLimitSet]: mapping of model hash to ThermalLimitSet instance
    """

    logger.info("parsing matrix branch equipment...")

    matrix_branch_equipments_catalog = {}
    thermal_limit_catalog = {}
    odd_model_types = [v.value for v in MatrixBranchTypes]
    for odd_model_type in odd_model_types:
        module: odd.LineCodes | odd.Lines = getattr(odd, odd_model_type)
        flag = module.First()
        while flag > 0:
            if odd_model_type == MatrixBranchTypes.LINE.value and module.Geometry():
                pass
            else:
                _build_matrix_branch(
                    odd_model_type, matrix_branch_equipments_catalog, thermal_limit_catalog
                )
            flag = module.Next()
    return matrix_branch_equipments_catalog, thermal_limit_catalog


def get_branches(
    system: System,
    mapping: dict[str, str],
    geometry_branch_equipment_catalog: dict,
    matrix_branch_equipments_catalog: dict,
    thermal_limit_catalog: dict,
) -> tuple[list[MatrixImpedanceBranch | GeometryBranch]]:
    """Method to build a model branches

    Args:
        system (System): Instance of System
        mapping (dict[str, int]): mapping of line geometries names to GeometryBranchEquipment hash
        geometry_branch_equipment_catalog (dict): mapping of model hash to GeometryBranchEquipment instance
        matrix_branch_equipments_catalog (dict): mapping of model hash to MatrixImpedanceBranchEquipment instance
        thermal_limit_catalog (dict): mapping of model hash to ThermalLimitSet instance

    Returns:
        tuple[list[MatrixImpedanceBranch | GeometryBranch]]: Returns a list of system branches
    """

    logger.info("parsing branch components...")

    branches = []
    flag = odd.Lines.First()
    while flag > 0:
        logger.debug(f"building line {odd.CktElement.Name()}...")

        buses = odd.CktElement.BusNames()
        bus1, bus2 = buses[0].split(".")[0], buses[1].split(".")[0]
        num_phase = odd.CktElement.NumPhases()
        nodes = ["1", "2", "3"] if num_phase == 3 else buses[0].split(".")[1:]
        geometry = odd.Lines.Geometry().lower()
        if geometry:
            assert geometry in mapping
            geometry_hash = mapping[geometry]
            geometry_branch_equipment = geometry_branch_equipment_catalog[geometry_hash]
            n_conds = len(geometry_branch_equipment.conductors)
            for _ in range(n_conds - num_phase):
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
            equipment = _build_matrix_branch(
                MatrixBranchTypes.LINE.value,
                matrix_branch_equipments_catalog,
                thermal_limit_catalog,
            )
            equipment = get_equipment_from_catalog(equipment, matrix_branch_equipments_catalog)
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
