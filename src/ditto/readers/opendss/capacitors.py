from uuid import uuid4

from gdm import DistributionBus, DistributionCapacitor, CapacitorEquipment, PhaseCapacitorEquipment, ConnectionType
from gdm.quantities import PositiveReactivePower, PositiveResistance, PositiveReactance
from infrasys.system import System
import opendssdirect as odd

from ditto.readers.opendss.common import PHASE_MAPPER, model_to_dict, get_equipment_from_system

def _build_voltage_source_equipment()-> tuple[CapacitorEquipment, list[str], list[str]]:  
    """Helper function to build a CapacitorEquipment instance

    Returns:
        CapacitorEquipment: instance of CapacitorEquipment
        list[str]: List of buses
        list[str]: List of phases 
    """ 
    equipment_uuid = uuid4()
    buses = odd.CktElement.BusNames()
    num_phase = odd.CktElement.NumPhases()
    kvar_ = odd.Capacitors.kvar()
    ph_caps = []
    nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]

    for el in nodes:
        phase_capacitor = PhaseCapacitorEquipment(
            name=f"{equipment_uuid}_{el}",
            rated_capacity=PositiveReactivePower(kvar_ / num_phase, "kilovar"),
            num_banks=odd.Capacitors.NumSteps(),
            num_banks_on=sum(odd.Capacitors.States()),
            resistance=PositiveResistance(0, "ohm"),
            reactance=PositiveReactance(0, "ohm"),
        )
        ph_caps.append(phase_capacitor)
        
    capacitor_equipment = CapacitorEquipment(
        name= str(equipment_uuid),
        phase_capacitors=ph_caps,
        connection_type=ConnectionType.DELTA
        if odd.Capacitors.IsDelta()
        else ConnectionType.STAR,
    )
    return capacitor_equipment, buses, nodes
    
    

def get_capacitor_equipments()-> list[CapacitorEquipment]:
    """Function to return list of all CapacitorEquipment in Opendss model.

    Returns:
        list[CapacitorEquipment]: List of CapacitorEquipment objects
    """ 
    capacitor_equipments_catalog = []
    capacitor_equipments = []
    flag = odd.Capacitors.First()
    while flag > 0:
        
        capacitor_equipment, _, _ = _build_voltage_source_equipment()
        model_dict = model_to_dict(capacitor_equipment)
        if model_dict not in capacitor_equipments_catalog:
            capacitor_equipments_catalog.append(model_dict)
            capacitor_equipments.append(capacitor_equipment)

        flag = odd.Capacitors.Next()
    return capacitor_equipments 
    
    

def get_capacitors(system:System) -> list[DistributionCapacitor]:
    """Function to return list of all capacitors in Opendss model.

    Args:
        system (System): Instance of System

    Returns:
        List[DistributionCapacitor]: List of DistributionCapacitor objects
    """
    
    capacitors = []
    flag = odd.Capacitors.First()
    while flag > 0:
        
        capacitor_equipment, buses, nodes = _build_voltage_source_equipment()
        bus1 = buses[0].split(".")[0]
        equipment_from_libray = get_equipment_from_system(capacitor_equipment, CapacitorEquipment, system)
        if equipment_from_libray:
            equipment = equipment_from_libray
        else:
            equipment = capacitor_equipment
        capacitors.append(
            DistributionCapacitor(
                name=odd.Capacitors.Name().lower(),
                bus=system.components.get(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                controllers=[],
                equipment=equipment,
            )
        )
        flag = odd.Capacitors.Next()
    return capacitors