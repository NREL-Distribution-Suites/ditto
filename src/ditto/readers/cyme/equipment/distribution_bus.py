from infrasys.location import Location
from gdm.distribution.components.distribution_bus import DistributionBus
from gdm import VoltageTypes, Phase, PositiveVoltage
from ditto.readers.cyme.cyme_mapping import CymeMapper


class DistributionBusMapper(CymeMapper):
    def __init__(self, cyme_model):
        super().__init__(cyme_model)

   cyme_file = 'Network'
   cyme_section = 'NODE'

   def parse(self, row, from_node_sections, to_node_sections):
       name = self.map_name(row)
       coordinate = self.map_coordinate(row)
       nominal_voltage = self.map_nominal_voltage(row)
       phases = self.map_phases(row, from_node_sections, to_node_sections)
       voltage_limits = self.map_voltagelimits(row)
       voltage_type = self.map_voltage_type(row)
       return DistributionBus(name=name, 
                              coordinate=coordinate, 
                              nominal_voltage=nominal_voltage, 
                              phases=phases, 
                              voltage_limits=voltage_limits, 
                              voltage_type=voltage_type)

    def map_name(self, row):
        name = row['NodeID']
        return name

    def map_coordinate(self, row):
        return Location(row['X'], row['Y'])

    def map_nominal_voltage(self, row):
        return PositiveVoltage(row['UserDefinedBaseVoltage'], "kilovolts")

   def map_phases(self, row, from_node_sections, to_node_sections):
        node_id = row["NodeId"]
        section = None
        all_phases = set()
        if node_id in from_node_sections:
            for section in from_node_sections[node_id]:
                phases = section["Phase"]
                for phase in phases:
                    all_phases.add(phase)
        if node_id in to_node_sections:
            for section in to_node_sections[node_id]:
                phases = section["Phase"]
                for phase in phases:
                    all_phases.add(phase)

        all_phases = sorted(list(all_phases))
        phases = []
        if "A" in all_phases:
            phases.append(Phase.A)
        if "B" in all_phases:
            phases.append(Phase.B)
        if "C" in all_phases:
            phases.append(Phase.C)
        if "N" in all_phases:
            phases.append(Phase.N)


    def map_voltagelimits(self, row):
        low_voltage = PositiveVoltage(row['LowVoltageLimit'], "kilovolts")
        high_voltage = PositiveVoltage(row['HighVoltageLimit'], "kilovolts")
        return [low_voltage, high_voltage]

    def map_voltage_type(self, row):
        return row['VoltageType']
