from ditto.writers.opendss.opendss_mapper import OpenDSSMapper
from ditto.enumerations import OpenDSSFileTypes


class DistributionBusMapper(OpenDSSMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Bus"
    altdss_composition_name = None
    opendss_file = OpenDSSFileTypes.COORDINATE_FILE.value

    def map_name(self):
        self.opendss_dict["Name"] = self.model.name

    def map_coordinate(self):
        if hasattr(self.model.coordinate, "x"):
            self.opendss_dict["X"] = self.model.coordinate.y
        if hasattr(self.model.coordinate, "y"):
            self.opendss_dict["Y"] = self.model.coordinate.x

    def map_nominal_voltage(self):
        kv_nominal_voltage = self.model.nominal_voltage.to("kV")
        if self.model.voltage_type == "line-to-ground":
            self.opendss_dict["kVLN"] = kv_nominal_voltage.magnitude
        elif self.model.voltage_type == "line-to-line":
            self.opendss_dict["kVLL"] = kv_nominal_voltage.magnitude

    def map_phases(self):
        # Not mapped for OpenDSS buses in BusCoords.dss files
        return

    def map_voltagelimits(self):
        # Not mapped for OpenDSS buses in BusCoords.dss files
        return

    def map_voltage_type(self):
        # Handled in map_nominal_voltage
        return
