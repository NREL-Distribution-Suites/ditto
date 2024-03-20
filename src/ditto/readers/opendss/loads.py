from gdm import DistributionBus, DistributionLoad, PhaseLoadEquipment, LoadEquipment, ConnectionType
from gdm.quantities import ActivePower, ReactivePower
from infrasys.system import System
import opendssdirect

from ditto.readers.opendss.common import PHASE_MAPPER, LoadTypes


def get_loads(system:System, dss:opendssdirect) -> list[DistributionLoad]:
    """Function to return list of all loads in opendss model.

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator
    Returns:
        List[DistributionLoad]: List of DistributionLoad objects
    """
    loads = []
    flag = dss.Loads.First()
    while flag > 0:
        load_name = dss.Loads.Name().lower()
        buses = dss.CktElement.BusNames()
        bus1 = buses[0].split(".")[0]
        num_phase = dss.CktElement.NumPhases()
        kvar_ = dss.Loads.kvar()
        kw_ = dss.Loads.kW()
        zip_params = dss.Loads.ZipV()
        model = dss.Loads.Model()
        ph_loads = []
        nodes = buses[0].split(".")[1:] if num_phase != 3 else ["1", "2", "3"]

        for el in nodes:
            kw_per_phase = kw_ / num_phase
            kvar_per_phase = kvar_ / num_phase

            if model == LoadTypes.CONST_POWER:
                load = PhaseLoadEquipment(
                    name=f"{load_name}_{el}",
                    p_real=ActivePower(kw_per_phase, "kilowatt"),
                    p_imag=ReactivePower(kvar_per_phase, "kilovar"),
                )
            elif model == LoadTypes.CONST_CURRENT:
                load = PhaseLoadEquipment(
                    name=f"{load_name}_{el}",
                    i_real=ActivePower(kw_per_phase, "kilowatt"),
                    i_imag=ReactivePower(kvar_per_phase, "kilovar"),
                )
            elif model == LoadTypes.CONST_IMPEDANCE:
                load = PhaseLoadEquipment(
                    name=f"{load_name}_{el}",
                    z_real=ActivePower(kw_per_phase, "kilowatt"),
                    z_imag=ReactivePower(kvar_per_phase, "kilovar"),
                )
            elif model == LoadTypes.ZIP:
                load = PhaseLoadEquipment(
                    name=f"{load_name}_{el}",
                    z_real=ActivePower(kw_per_phase * zip_params[0], "kilowatt"),
                    z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
                    i_real=ActivePower(kw_per_phase * zip_params[1], "kilowatt"),
                    i_imag=ReactivePower(kvar_per_phase * zip_params[4], "kilovar"),
                    p_real=ActivePower(kw_per_phase * zip_params[2], "kilowatt"),
                    p_imag=ReactivePower(kvar_per_phase * zip_params[5], "kilovar"),
                )          
            elif model == LoadTypes.CONST_P__QUARDRATIC_Q:
                load = PhaseLoadEquipment(
                    name=f"{load_name}_{el}",
                    z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
                    p_real=ActivePower(kw_per_phase * zip_params[2], "kilowatt"),
            
                )    
            elif model == LoadTypes.LINEAR_P__QUARDRATIC_Q:
                load = PhaseLoadEquipment(
                    name=f"{load_name}_{el}",
                    z_imag=ReactivePower(kvar_per_phase * zip_params[3], "kilovar"),
                    i_real=ActivePower(kw_per_phase * zip_params[1], "kilowatt"),
                )
            else:
                msg = f"Invalid load model type {model} passed. valid options are {LoadTypes}"
                raise ValueError(msg)
            system.add_component(load)
            ph_loads.append(load)

        load_equipment = LoadEquipment(
            name=load_name,
            phase_loads=ph_loads,
            connection_type=ConnectionType.DELTA
            if dss.Loads.IsDelta()
            else ConnectionType.STAR,
        )
        system.add_components(load_equipment)

        loads.append(
            DistributionLoad(
                name=load_name,
                bus=system.components.get(DistributionBus, bus1),
                phases=[PHASE_MAPPER[el] for el in nodes],
                equipment=load_equipment,
            )
        )

        flag = dss.Loads.Next()
    return loads