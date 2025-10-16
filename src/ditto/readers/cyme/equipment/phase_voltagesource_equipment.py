from ditto.readers.cyme.cyme_mapper import CymeMapper
from gdm.distribution.equipment.phase_voltagesource_equipment import PhaseVoltageSourceEquipment
from gdm.quantities import Angle, Reactance, Resistance
from gdm.distribution.enums import VoltageTypes


class PhaseVoltageSourceEquipmentMapper(CymeMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, bus, feeder_voltage):
        sources = []
        num_phases = len(bus.phases)
        for i in range(num_phases):
            source = PhaseVoltageSourceEquipment.model_construct(
                name=f"phase-source-{i+1}",
                r0=Resistance(0.001, "ohm"),
                r1=Resistance(0.001, "ohm"),
                x0=Reactance(0.001, "ohm"),
                x1=Reactance(0.001, "ohm"),
                voltage=feeder_voltage / 1.732 if num_phases == 3 else feeder_voltage,
                voltage_type=VoltageTypes.LINE_TO_GROUND,
                angle=Angle(i * (360.0 / num_phases), "degree"),
            )
            sources.append(source)
        return sources