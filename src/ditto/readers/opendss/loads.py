from uuid import uuid4

from gdm import DistributionBus, DistributionLoad, PhaseLoadEquipment, LoadEquipment, ConnectionType
from gdm.quantities import ActivePower, ReactivePower
from infrasys.system import System
import opendssdirect as odd

from ditto.readers.opendss.common import PHASE_MAPPER, LoadTypes

def _build_load_equipment()-> tuple[LoadEquipment, list[str], str, list[str]]:
    """Helper function to build a LoadEquipment instance

    Returns:
        LoadEquipment: instance of LoadEquipment
        list[str]: List of buses
        list[str]: List of phases 
    """  
    
    equipment_uuid = uuid4()
    buses = odd.CktElement.BusNames()
    num_phase = odd.CktElement.NumPhases()
    kvar_ = odd.Loads.kvar()
    kw_ = odd.Loads.kW()
    zip_params = odd.Loads.ZipV()
    model = odd.Loads.Model()
    nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]
    ph_loads = []
    for el in nodes:
        kw_per_phase = kw_ / num_phase
        kvar_per_phase = kvar_ / num_phase

        if model == LoadTypes.CONST_POWER:
            load = PhaseLoadEquipment(
                name=f"{equipment_uuid}_{el}",
                p_real=ActivePower(kw_per_phase, "kilowatt"),
                p_imag=ReactivePower(kvar_per_phase, "kilovar"),
            )
        elif model == LoadTypes.CONST_CURRENT:
            load = PhaseLoadEquipment(
                name=f"{equipment_uuid}_{el}",
                i_real=ActivePower(kw_per_phase, "kilowatt"),
                i_imag=ReactivePower(kvar_per_phase, "kilovar"),
            )
        elif model == LoadTypes.CONST_IMPEDANCE:
            load = PhaseLoadEquipment(
                name=f"{equipment_uuid}_{el}",
                z_real=ActivePower(kw_per_phase, "kilowatt"),
                z_imag=ReactivePower(kvar_per_phase, "kilovar"),
            )
        elif model == LoadTypes.ZIP:
            load = PhaseLoadEquipment(
                name=f"{equipment_uuid}_{el}",
                z_real=ActivePower(kw_per_phase * zip_params[0], "kilowatt"),
                z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
                i_real=ActivePower(kw_per_phase * zip_params[1], "kilowatt"),
                i_imag=ReactivePower(kvar_per_phase * zip_params[4], "kilovar"),
                p_real=ActivePower(kw_per_phase * zip_params[2], "kilowatt"),
                p_imag=ReactivePower(kvar_per_phase * zip_params[5], "kilovar"),
            )          
        elif model == LoadTypes.CONST_P__QUARDRATIC_Q:
            load = PhaseLoadEquipment(
                name=f"{equipment_uuid}_{el}",
                p_real=ActivePower(kw_per_phase * zip_params[2], "kilowatt"),
                z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
            )    
        elif model == LoadTypes.LINEAR_P__QUARDRATIC_Q:
            load = PhaseLoadEquipment(
                name=f"{equipment_uuid}_{el}",
                i_real=ActivePower(kw_per_phase * zip_params[1], "kilowatt"),
                z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
            )
        else:
            msg = f"Invalid load model type {model} passed. valid options are {LoadTypes}"
            raise ValueError(msg)  
        ph_loads.append(load)
    load_equipment = LoadEquipment(
        name=str(uuid4()),
        phase_loads=ph_loads,
        connection_type=ConnectionType.DELTA
        if odd.Loads.IsDelta()
        else ConnectionType.STAR,
    )    
    return load_equipment, buses, nodes

# def get_load_equipments(odd:Opendssdirect) -> list[LoadEquipment]:
#     """Function to return list of all LoadEquipment in Opendss model.

#     Args:
#         odd (Opendssdirect): Instance of Opendss simulator

#     Returns:
#         list[LoadEquipment]: List of LoadEquipment objects
#     """   

def get_loads(system:System) -> list[DistributionLoad]:
    """Function to return list of DistributionLoad in Opendss model.

    Args:
        system (System): Instance of System

    Returns:
        List[DistributionLoad]: List of DistributionLoad objects
    """
    loads = []
    flag = odd.Loads.First()
    while flag > 0:
        load_name = odd.Loads.Name().lower()
        LoadEquipment, buses, nodes = _build_load_equipment()
        bus1 = buses[0].split(".")[0]
        loads.append(
            DistributionLoad(
                name=load_name,
                bus=system.components.get(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                equipment=LoadEquipment,
            )
        )
        flag = odd.Loads.Next()
    return loads