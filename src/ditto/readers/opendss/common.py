from enum import IntEnum
from typing import Any

from infrasys.component_models import Component
from infrasys.system import System
import opendssdirect as odd
from gdm import Phase


PHASE_MAPPER = {
    "0": Phase.N,
    "1": Phase.A,
    "2": Phase.B,
    "3": Phase.C,
    "4": Phase.N,
}

UNIT_MAPPER = {0: "m", 1: "mi", 2: "kft", 3: "km", 4: "m", 5: "ft", 6: "in", 7: "cm"}


class LoadTypes(IntEnum):
    CONST_POWER = 1
    CONST_IMPEDANCE = 2
    CONST_P__QUARDRATIC_Q = 3
    LINEAR_P__QUARDRATIC_Q = 4
    CONST_CURRENT = 5
    ZIP = 8


def model_to_dict(model: Component) -> dict:
    """Converts models to a dict and resursively removes all 'name' kwargs

    Args:
        model (Component): Instance of a derived infrasys Component model

    Returns:
        tuple[str,dict]: Dictionary representation of the model
    """
    model_dict = model.model_dump(exclude={"name"})
    return model_dict


def get_equipment_from_system(
    model: Component, model_type: type[Component], system: System
) -> Component | None:
    """If the equipment already exixts in th system the equipment instalce is returned else None is returned

    Args:
        model (Component): Instance of GDM equipment
        model_type (type[Component]): Infrasys Component type
        system (System): Infrasys System instance


    Returns:
        Component | None: _description_
    """

    model_dict = model_to_dict(model)
    for equipment in system.get_components(model_type):
        equipment_dict = model_to_dict(equipment)
        if str(model_dict) == str(equipment_dict):
            return equipment


def query_model_data(model_type: str, model_name: str, property: str, dtype: type) -> Any:
    """query OpenDSS model property

    Args:
        model_type (str): OpenDSS model type
        model_name (str): OpenDSS model name
        property (str): OpenDSS model property
        dtype (type): data type e.g. str, float

    Returns:
        Any: OpenDSS model property value
    """
    command = f"? {model_type}.{model_name}.{property}"
    odd.Text.Command(command)
    result = odd.Text.Result()
    if result == "Property Unknown":
        return None
    return dtype(result)
