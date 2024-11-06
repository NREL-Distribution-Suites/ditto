from infrasys.location import Location
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm import VoltageTypes
from ditto.readers.synergi.synergi_mapper import SynergiMapper

class DistributionBusMapper(SynergiMapper):
    def __init__(self, ):

        super().__init__()
    
    synergi_table = "Node"
    synergi_database = "Model"

    def parse(self, row):
        name = self.map_name(row)
        coordinate = self.map_coordinate(row)
        nominal_voltage = self.map_nominal_voltage(row)
        phases = self.map_phases(row)
        voltage_limits = self.map_voltagelimits(row)
        voltage_type = self.map_voltage_type(row)
        return DistributionBus(name=name,
                               coordinate=coordinate,
                               nominal_voltage=nominal_voltage,
                               phases=phases,
                               voltagelimits=voltage_limits,
                               voltage_type=voltage_type)

    def map_name(self, row):
        name = row["NodeId"]
        return name

    def map_coordinate(self, row):
        X, Y = row["X"], row["Y"]
        #crs = SAI_Control.ProjectionWKT
        crs = None
        location = Location(x = X, y = Y, crs = crs)
        return location

    def map_nominal_voltage(self, row):
        return []

    def map_phases(self, row):
        return []

    def map_voltagelimits(self, row):
        return []

    def map_voltage_type(self, row):
        return VoltageTypes.LINE_TO_LINE.value

