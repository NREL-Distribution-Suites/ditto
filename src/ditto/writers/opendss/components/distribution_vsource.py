from ditto.writers.opendss.opendss_mapper import OpenDSSMapper

class DistributionVoltageSourceMapper(OpenDSSMapper):

    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Vsource_Z0Z1Z2"
    altdss_composition_name = "Vsource"
    opendss_file = "Master.dss"

    def map_name(self):
        self.opendss_dict['Name'] = self.model.name

    def map_bus(self):
        self.opendss_dict['Bus1'] = self.model.bus.name
        for phase in self.model.phases:
            self.opendss_dict['Bus1']+=self.phase_map[phase]

    def map_phases(self):
        #Handled in the map_bus function
        return

    def map_equipment(self):
        r1 = 0
        x1 = 0
        r0 = 0
        x0 = 0
        voltage = 0
        angle = 0
        for phase_source in self.model.equipment.sources:
            r1+=phase_source.r1
            r0+=phase_source.r0
            x1+=phase_source.x1
            x0+=phase_source.x0
            voltage += phase_source.voltage
            angle+=phase_source.angle

        r1 = r1.to('ohm')
        r0 = r0.to('ohm')
        x1 = x1.to('ohm')
        x0 = x0.to('ohm')
        voltage = voltage/len(self.model.equipment.sources)
        voltage = voltage.to("kilovolt")
        angle = angle/len(self.model.equipment.sources)
        angle = angle.to("degree")

        self.opendss_dict['Angle'] = angle.magnitude
        self.opendss_dict['pu1'] = 1.0
        self.opendss_dict['BasekV'] = voltage.magnitude
        self.opendss_dict['Z0'] = complex(r0.magnitude,x0.magnitude)
        self.opendss_dict['Z1'] = complex(r1.magnitude,x1.magnitude)





