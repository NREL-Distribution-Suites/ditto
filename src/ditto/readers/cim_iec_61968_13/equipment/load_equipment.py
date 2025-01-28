from gdm.distribution.equipment.phase_load_equipment import PhaseLoadEquipment
from gdm.distribution.equipment.load_equipment import LoadEquipment
from gdm.quantities import ActivePower, ReactivePower
from gdm import ConnectionType

from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper


class LoadEquipmentMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row):
        phases = row["phase"]
        if phases is None:
            self.phases = ["A", "B", "C"]
        else:
            self.phases = phases.split(",")

        return LoadEquipment(name=self.map_name(row), phase_loads=self.map_phase_loads(row))

    # NOTE: Names may not be unique. Should we append a number to the name?
    def map_name(self, row):
        return row["load"] + "_equipment"

    # No connection type information is included
    def map_connection_type(self, row):
        return ConnectionType.DELTA if row["conn"] == "D" else ConnectionType.STAR

    def map_phase_loads(self, row):
        phase_loads = []
        n_phases = len(self.phases)
        kw = float(row["active power"]) / n_phases
        kvar = float(row["reactive power"]) / n_phases
        for phase in self.phases:
            if kw > 0:
                mapper = PhaseLoadEquipmentMapper(self.system)
                phase_load = mapper.parse(row, kw, kvar, phase)
                phase_loads.append(phase_load)
        return phase_loads


class PhaseLoadEquipmentMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row, kw, kvar, phase):
        return PhaseLoadEquipment(
            name=self.map_name(row, phase),
            real_power=self.map_real_power(kw),
            reactive_power=self.map_reactive_power(kvar),
            z_real=self.map_z_real(row),
            z_imag=self.map_z_imag(row),
            i_real=self.map_i_real(row),
            i_imag=self.map_i_imag(row),
            p_real=self.map_p_real(row),
            p_imag=self.map_p_imag(row),
            num_customers=self.map_num_customers(row),
        )

    def map_name(self, row, phase):
        return row["load"] + "_phase_load_equipment_" + phase

    def map_real_power(self, kw):
        return ActivePower(kw, "watt")

    def map_reactive_power(self, kvar):
        return ReactivePower(kvar, "var")

    def map_z_real(self, row):
        return 1

    def map_z_imag(self, row):
        return 1

    def map_i_real(self, row):
        return 0

    def map_i_imag(self, row):
        return 0

    def map_p_real(self, row):
        return 0

    def map_p_imag(self, row):
        return 0

    def map_num_customers(self, row):
        return None
