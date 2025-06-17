from gdm.distribution.enums import VoltageTypes, ConnectionType, Phase
from gdm.quantities import Voltage, ApparentPower
from gdm.distribution.equipment import WindingEquipment

from ditto.readers.cim_iec_61968_13.cim_mapper import CimMapper
from ditto.readers.cim_iec_61968_13.common import phase_mapper


class WindingEquipmentMapper(CimMapper):
    def __init__(self, system):
        super().__init__(system)

    def parse(self, row):
        indices = row.index
        windings = []
        for i in range(1, 3):
            new_indices = [j for j in indices if j.startswith(f"wdg_{i}_")]
            windings.append(self._build_winding(row[new_indices], i, row["xfmr"]))

        return windings

    def _build_winding(self, row, index, xfmr_name):
        if f"wdg_{index}_phase" in row:
            self.phases = [phase_mapper[phs] for phs in row[f"wdg_{index}_phase"].replace("N", "")]
        else:
            self.phases = [Phase.A, Phase.B, Phase.C]
        self.n_phases = len(self.phases)

        mapping = {
            f"wdg_{index}_normal_tap": ["normal_tap", 0],
            f"wdg_{index}_max_tap": ["max_tap", 16],
            f"wdg_{index}_min_tap": ["min_tap", -16],
            f"wdg_{index}_dv": ["dv", 0.625],
        }

        for k, v in mapping.items():
            if k in row:
                if row[k]:
                    setattr(self, v[0], float(row[k]))
                else:
                    setattr(self, v[0], v[1])
            else:
                setattr(self, v[0], v[1])

        self.dv = self.dv / 100.0
        self.total_taps = self.max_tap - self.min_tap
        self.pu_tap = self.normal_tap * self.dv + 1
        self.max_tap_pu = self.max_tap * self.dv + 1
        self.min_tap_pu = self.min_tap * self.dv + 1

        return WindingEquipment(
            name=self.map_name(index, xfmr_name),
            resistance=self.map_resistance(row, index),
            is_grounded=self.map_is_grounded(row, index),
            rated_voltage=self.map_rated_voltage(row, index),
            voltage_type=self.map_voltage_type(row, index),
            rated_power=self.map_rated_power(row, index),
            num_phases=self.map_num_phases(row, index),
            connection_type=self.map_connection_type(row, index),
            tap_positions=self.map_tap_positions(row, index),
            total_taps=self.map_total_taps(row, index),
            min_tap_pu=self.map_min_tap_pu(row, index),
            max_tap_pu=self.map_max_tap_pu(row, index),
        )

    def map_name(self, winding_number, xfmr_name):
        return f"{xfmr_name}_winding_{winding_number}"

    def map_resistance(self, row, winding_number):
        s = float(row[f"wdg_{winding_number}_apparent_power"])
        v = float(row[f"wdg_{winding_number}_rated_voltage"])
        r = float(row[f"wdg_{winding_number}_per_resistance"])
        per_r = r / (v**2 / s) * 100
        return per_r

    def map_is_grounded(self, row, winding_number):
        return False

    def map_rated_voltage(self, row, winding_number):
        voltage = float(row[f"wdg_{winding_number}_rated_voltage"])
        if self.n_phases > 1:
            return Voltage(voltage / 1.732, "volt")
        else:
            return Voltage(voltage, "volt")

    def map_voltage_type(self, row, winding_number):
        return VoltageTypes.LINE_TO_GROUND

    def map_rated_power(self, row, winding_number):
        rated_power = float(row[f"wdg_{winding_number}_apparent_power"])
        return ApparentPower(rated_power, "va")

    def map_num_phases(self, row, winding_number):
        return self.n_phases

    def map_connection_type(self, row, winding_number):
        connection = row[f"wdg_{winding_number}_conn"]

        if connection == "D":
            return ConnectionType.DELTA
        else:
            return ConnectionType.STAR

    # TODO: Check if this is correct
    def map_tap_positions(self, row, winding_number):
        return [self.pu_tap] * self.n_phases

    def map_total_taps(self, row, winding_number):
        return self.total_taps

    def map_min_tap_pu(self, row, winding_number):
        return self.min_tap_pu

    def map_max_tap_pu(self, row, winding_number):
        return self.max_tap_pu
