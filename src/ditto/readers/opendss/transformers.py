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
import opendssdirect

from ditto.readers.opendss.common import PHASE_MAPPER

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]

def get_transformers(system:System, dss:opendssdirect) -> list[DistributionTransformer]:
    """Method returns a list of DistributionTransformer objects

    Args:
        system (System): Instance of System
        dss (opendssdirect): Instance of OpenDSS simulator

    Returns:
        list[DistributionTransformer]: list of distribution transformers
    """    

    transformers = []
    flag = dss.Transformers.First()
    while flag > 0:
        all_reactances = [
            dss.Transformers.Xhl(),
            dss.Transformers.Xht(),
            dss.Transformers.Xlt(),
        ]
        number_windings = dss.Transformers.NumWindings()
        winding_phases = []
        xfmr_buses = []
        windings = []
        for wdg_index, bus_name in zip(range(number_windings), dss.CktElement.BusNames()):
            dss.Transformers.Wdg(wdg_index + 1)
            bus = bus_name.split(".")[0]
            num_phase = dss.CktElement.NumPhases()
            nodes = ["1", "2", "3"] if num_phase == 3 else bus.split(".")[1:]
            winding_phases.append([PHASE_MAPPER[node] for node in nodes])
            xfmr_buses.append(system.components.get(DistributionBus, bus))
            nominal_voltage = (
                dss.Transformers.kV() / 1.732 if num_phase == 3 else dss.Transformers.kV()
            )
            winding = WindingEquipment(
                rated_power=PositiveApparentPower(dss.Transformers.kVA(), "kilova"),
                num_phases=num_phase,
                connection_type=ConnectionType.DELTA
                if dss.Transformers.IsDelta()
                else ConnectionType.STAR,
                nominal_voltage=PositiveVoltage(nominal_voltage, "kilovolt"),
                resistance=dss.Transformers.R(),
                is_grounded=False,  # TODO @aadil
            )
            windings.append(winding)
        system.add_components(*windings)

        coupling_sequences = SEQUENCE_PAIRS[:1] if number_windings == 2 else SEQUENCE_PAIRS
        reactances = all_reactances[:1] if number_windings == 2 else all_reactances
        no_load_loss_pct, full_load_loss_pct = _xfmr_pct_loss_components(dss)

        dist_transformer = DistributionTransformerEquipment(
            name=dss.Transformers.Name().lower(),
            pct_no_load_loss=no_load_loss_pct,
            pct_full_load_loss=full_load_loss_pct,
            windings=windings,
            coupling_sequences=coupling_sequences,
            winding_reactances=reactances,
            is_center_tapped=_is_center_tapped(),
        )
        system.add_component(dist_transformer)

        transformer = DistributionTransformer(
            name=dss.Transformers.Name().lower(),
            buses=xfmr_buses,
            winding_phases=winding_phases,
            equipment=dist_transformer,
        )
        transformers.append(transformer)
        flag = dss.Transformers.Next()

    return transformers

def _xfmr_pct_loss_components(dss:opendssdirect) -> list[float, float]:
    """Calculates a transformer's no-load and full-load loss

    Args:
        dss (opendssdirect): Instance of OpenDSS simulator

    Returns:
        list[float, float]: return the transformer's no-load loss (%) and full-load loss (%)
    """    
    loss_vector = dss.Transformers.LossesByType()
    full_load_loss_kva = (loss_vector[2] + 1j * loss_vector[3]) / 1000
    no_load_loss_kva = (loss_vector[4] + 1j * loss_vector[5]) / 1000
    full_load_loss_pct = abs(full_load_loss_kva) / dss.Transformers.kVA() * 100
    no_load_loss_pct = abs(no_load_loss_kva) / dss.Transformers.kVA() * 100
    return no_load_loss_pct, full_load_loss_pct

def _is_center_tapped()-> bool:
    """The flag is true if the transformer is center tapped.

    Returns:
        bool: _description_
    """    
    
    # TODO: implement the correct logic here
    return False