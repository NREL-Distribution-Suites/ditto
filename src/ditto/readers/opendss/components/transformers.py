from typing import Any
from uuid import uuid4
from enum import Enum

from gdm.quantities import PositiveApparentPower, PositiveVoltage
from gdm import (
    DistributionTransformerEquipment,
    DistributionTransformer,
    WindingEquipment,
    DistributionBus,
    ConnectionType,
    SequencePair,
    VoltageTypes,
    Phase,
)
from infrasys.system import System
import opendssdirect as odd
from loguru import logger

from ditto.readers.opendss.common import PHASE_MAPPER, get_equipment_from_catalog

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class XfmrModelTypes(str, Enum):
    TRANSFORMERS = "Transformer"
    XFMRCODE = "XfmrCode"


def _build_xfmr_equipment(
    system: System,
    model_type: str,
    distribution_transformer_equipment_catalog: dict[int, DistributionTransformerEquipment],
    winding_equipment_catalog: dict[int, WindingEquipment],
) -> tuple[DistributionTransformerEquipment, list[DistributionBus], list[Phase]]:
    """Helper function to build a DistributionTransformerEquipment instance

    Args:
        system (System): Instance of infrasys System
        model_type (str): Opendss model type e.g. Transformer, XfmrCode
        distribution_transformer_equipment_catalog (dict[int, DistributionTransformerEquipment]): mapping of model hash to DistributionTransformerEquipment instance
        winding_equipment_catalog (dict[int, WindingEquipment]): mapping of model hash to WindingEquipment instance

    Returns:
        DistributionTransformerEquipment: instance of DistributionTransformerEquipment
        list[DistributionBus]: List of DistributionBus
        list[Phase]: List of Phase
    """

    model_name = odd.Element.Name().lower().split(".")[1]
    if model_type == XfmrModelTypes.XFMRCODE.value:
        equipment_uuid = model_name
    else:
        equipment_uuid = str(uuid4())

    def query(property: str, dtype: type):
        command = f"? {model_type}.{model_name}.{property}"
        odd.Text.Command(command)
        result = odd.Text.Result()
        if result is None:
            if dtype in [float, int]:
                return 0
            elif dtype == str:
                return ""
            else:
                return None
        return dtype(result)

    def set_ppty(property: str, value: Any):
        return odd.Command(f"{model_type}.{model_name}.{property}={value}")

    all_reactances = [
        query("xhl", float),
        query("xht", float),
        query("xlt", float),
    ]

    number_windings = query("windings", int)
    xfmr_bus_names = odd.CktElement.BusNames()
    winding_phases = []
    xfmr_buses = []
    windings = []

    for wdg_index, bus_name in zip(range(number_windings), xfmr_bus_names):
        set_ppty("Wdg", wdg_index + 1)
        bus = bus_name.split(".")[0]
        num_phase = query("phases", int)
        nodes = ["1", "2", "3"] if num_phase == 3 else bus_name.split(".")[1:]
        winding_phases.append([PHASE_MAPPER[node] for node in nodes])
        xfmr_buses.append(system.get_component(DistributionBus, bus))
        if query("conn", str).lower() == "delta":
            nominal_voltage = query("kv", float) / 1.732
        else:
            nominal_voltage = query("kv", float) / 1.732 if num_phase == 3 else query("kv", float)
        winding = WindingEquipment(
            rated_power=PositiveApparentPower(query("kva", float), "kilova"),
            num_phases=num_phase,
            connection_type=ConnectionType.DELTA
            if query("conn", str).lower() == "delta"
            else ConnectionType.STAR,
            nominal_voltage=PositiveVoltage(nominal_voltage, "kilovolt"),
            resistance=query("%r", float),
            is_grounded=True if "0" in nodes else False,
            voltage_type=VoltageTypes.LINE_TO_GROUND,
        )

        winding = get_equipment_from_catalog(winding, winding_equipment_catalog)
        windings.append(winding)

    coupling_sequences = SEQUENCE_PAIRS[:1] if number_windings == 2 else SEQUENCE_PAIRS
    reactances = all_reactances[:1] if number_windings == 2 else all_reactances

    dist_transformer = DistributionTransformerEquipment(
        name=equipment_uuid,
        pct_no_load_loss=query(r"%noloadloss", float),
        pct_full_load_loss=query(r"%loadloss", float),
        windings=windings,
        coupling_sequences=coupling_sequences,
        winding_reactances=reactances,
        is_center_tapped=_is_center_tapped(winding_phases),
    )

    dist_transformer = get_equipment_from_catalog(
        dist_transformer, distribution_transformer_equipment_catalog
    )

    return dist_transformer, xfmr_buses, winding_phases


def get_transformer_equipments(system: System) -> list[DistributionTransformerEquipment]:
    """Function to return list of all DistributionTransformerEquipment in Opendss model.

    Args:
        system (System): Instance of infrasys System

    Returns:
        list[DistributionTransformerEquipment]: List of DistributionTransformerEquipment objects
    """
    logger.info("parsing transformer equipment...")
    distribution_transformer_equipment_catalog = {}
    winding_equipment_catalog = {}
    odd_model_types = [v.value for v in XfmrModelTypes]
    for odd_model_type in odd_model_types:
        odd.Circuit.SetActiveClass(odd_model_type)
        flag = odd.ActiveClass.First()
        while flag > 0:
            _build_xfmr_equipment(
                system,
                odd_model_type,
                distribution_transformer_equipment_catalog,
                winding_equipment_catalog,
            )
            flag = odd.ActiveClass.Next()
    return distribution_transformer_equipment_catalog, winding_equipment_catalog


def get_transformers(
    system: System,
    distribution_transformer_equipment_catalog: dict[int, DistributionTransformerEquipment],
    winding_equipment_catalog: dict[int, WindingEquipment],
) -> list[DistributionTransformer]:
    """Method returns a list of DistributionTransformer objects

    Args:
        system (System):  Instance of System
        distribution_transformer_equipment_catalog (dict[int, DistributionTransformerEquipment]): mapping of model hash to DistributionTransformerEquipment instance
        winding_equipment_catalog (dict[int, WindingEquipment]): mapping of model hash to WindingEquipment instance

     Returns:
        list[DistributionTransformer]: list of distribution transformers
    """

    logger.info("parsing transformer components...")

    transformers = []
    flag = odd.Transformers.First()
    while flag > 0:
        logger.debug(f"building transformer {odd.Transformers.Name()}")
        xfmr_equipment, buses, phases = _build_xfmr_equipment(
            system,
            XfmrModelTypes.TRANSFORMERS.value,
            distribution_transformer_equipment_catalog,
            winding_equipment_catalog,
        )
        transformer = DistributionTransformer(
            name=odd.Transformers.Name().lower(),
            buses=buses,
            winding_phases=phases,
            equipment=xfmr_equipment,
        )
        transformers.append(transformer)
        flag = odd.Transformers.Next()

    return transformers


def _is_center_tapped(winding_phases: list[Phase]) -> bool:
    """The flag is true if the transformer is center tapped.

    Returns:
        bool: True if the transfomer equpment is split phase else False
    """

    is_split_phase = False
    if len(winding_phases) == 3:
        num_phases = [
            len(wdg_phases) == 2 and Phase.N in wdg_phases for wdg_phases in winding_phases[1:]
        ]
        if all(num_phases):
            is_split_phase = True
    return is_split_phase
