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
)
from infrasys.system import System
import opendssdirect as odd

from ditto.readers.opendss.common import PHASE_MAPPER,  model_to_dict, get_equipment_from_system

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]

class XfmrModelTypes(str, Enum):
    TRANSFORMERS = "Transformer"
    XFMRCODE = "XfmrCode"

def _build_xfmr_equipment(system:System, model_type:str)-> DistributionTransformerEquipment:
    """Helper function to build a DistributionTransformerEquipment instance

    Args:
        system (System): Instance of infrasys System
        model_type (str): Opendss model type e.g. Transformer

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
        
    def query(property:str, dtype:type):
        command = f"? {model_type}.{model_name}.{property}"
        odd.Text.Command(command)
        result =odd.Text.Result()
        if result is None:
            if dtype in [float, int]:
                return 0
            elif dtype == str:
                return ""
            else:
                return None
        return dtype(result)
    
    def set_ppty(property:str, value:Any):
        return odd.Command(f"{model_type}.{model_name}.{property}={value}")

    all_reactances = [
        query("xhl", float),
        query("xht", float),
        query("xlt", float),
    ]
    
    number_windings = query("windings", int)
    winding_phases = []
    xfmr_buses = []
    windings = []
    for wdg_index, bus_name in zip(range(number_windings), odd.CktElement.BusNames()):
        set_ppty("Wdg", wdg_index + 1)
        bus = bus_name.split(".")[0]
        num_phase = query("phases", int)
        nodes = ["1", "2", "3"] if num_phase == 3 else bus.split(".")[1:]
        winding_phases.append([PHASE_MAPPER[node] for node in nodes])
        xfmr_buses.append(system.components.get(DistributionBus, bus))
        nominal_voltage = (
            query("kv", float) / 1.732 if num_phase == 3 else query("kv", float)
        )
        winding = WindingEquipment(
            rated_power=PositiveApparentPower(query("kva", float), "kilova"),
            num_phases=num_phase,
            connection_type=ConnectionType.DELTA
            if query("conn", str).lower() == "delta"
            else ConnectionType.STAR,
            nominal_voltage=PositiveVoltage(nominal_voltage, "kilovolt"),
            resistance=query(f"%r", float),
            is_grounded=False,  # TODO @aadil
        )
        windings.append(winding)

    coupling_sequences = SEQUENCE_PAIRS[:1] if number_windings == 2 else SEQUENCE_PAIRS
    reactances = all_reactances[:1] if number_windings == 2 else all_reactances

    dist_transformer = DistributionTransformerEquipment(
        name=equipment_uuid,
        pct_no_load_loss=query(f"%noloadloss", float),
        pct_full_load_loss=query(f"%loadloss", float),
        windings=windings,
        coupling_sequences=coupling_sequences,
        winding_reactances=reactances,
        is_center_tapped=_is_center_tapped(),
    )
    return dist_transformer, xfmr_buses, winding_phases
    
def get_transformer_equipments(system:System)-> list[DistributionTransformerEquipment]:
    """Function to return list of all DistributionTransformerEquipment in Opendss model.

    Args:
        system (System): Instance of infrasys System

    Returns:
        list[DistributionTransformerEquipment]: List of DistributionTransformerEquipment objects
    """ 
    
    xfmr_equipments_catalog = []
    xfmr_equipments = []
    odd_model_types = [v.value for v in XfmrModelTypes]
    for odd_model_type in odd_model_types:
        odd.Circuit.SetActiveClass(odd_model_type)
        flag = odd.ActiveClass.First()
        while flag > 0:
            xfmr_equipment, _, _ = _build_xfmr_equipment(system, odd_model_type)
            model_dict = model_to_dict(xfmr_equipment)
            if model_dict not in xfmr_equipments_catalog:
                xfmr_equipments_catalog.append(model_dict)
                xfmr_equipments.append(xfmr_equipment) 
            flag = odd.ActiveClass.Next()
    return xfmr_equipments
    

def get_transformers(system:System) -> list[DistributionTransformer]:
    """Method returns a list of DistributionTransformer objects

    Args:
        system (System): Instance of System
        
    Returns:
        list[DistributionTransformer]: list of distribution transformers
    """    

    transformers = []
    flag = odd.Transformers.First()
    while flag > 0:
        
        xfmr_equipment, buses, phases = _build_xfmr_equipment(system, XfmrModelTypes.TRANSFORMERS.value)
        equipment_from_libray = get_equipment_from_system(xfmr_equipment, DistributionTransformerEquipment, system)
        if equipment_from_libray:
            equipment = equipment_from_libray
        else:
            equipment = xfmr_equipment
        transformer = DistributionTransformer(
            name=odd.Transformers.Name().lower(),
            buses=buses,
            winding_phases=phases,
            equipment=equipment,
        )
        transformers.append(transformer)
        flag = odd.Transformers.Next()

    return transformers


def _is_center_tapped()-> bool:
    """The flag is true if the transformer is center tapped.

    Returns:
        bool: _description_
    """    
    
    # TODO: implement the correct logic here
    return False