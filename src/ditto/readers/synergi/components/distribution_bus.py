from infrasys.location import Location
from ditto.readers.synergi.synergi_mapper import SynergiMapper

class DistributionBusMapper(SynergiMapper):
    def __init__(self, ):

        super().__init__(model)
    
    synergi_table = "Node"
    synergi_database = "Model"

    def parse(self, row):
        name = map_name(row)
        coordinates = map_coordinates(row)
        nominal_voltage = map_nominal_voltage(row)
        phases = map_phases(row)
        voltage_limits = map_voltagelimits(row)
        voltage_type = map_voltage_type(row)
        return DistributionBus(name=name,
                               coordinates=coordinates,
                               nominal_voltage=nominal_voltage,
                               phases=phases,
                               voltage_limits=voltage_limits,
                               voltage_type=voltage_type)

    def map_name(self, row):
        name = row["NodeID"]
        reutrn name

    def map_coordinates(self, row):
        X, Y = row["X"], row["Y"]
        crs = SAI_Control.ProjectionWKT
        location = Location(x = X, y = Y, crs = crs)
        return location

    def map_nominal_voltage(self):
        return None

    def map_phases(self):
        return None

    def map_voltagelimits(self):
        return None

    def map_voltage_type(self):
        return None

