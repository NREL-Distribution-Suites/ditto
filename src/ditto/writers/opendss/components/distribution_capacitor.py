from ditto.writers.opendss.opendss_mapper import OpenDSSMapper

class DistributionCapacitorMapper(OpenDSSMapper):

    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Capacitor_kvarkV"
    altdss_composition_name = "Capacitor"
    opendss_file = "Capacitors.dss"

    def map_name(self):
        self.opendss_dict['Name'] = self.model.name

    def map_bus(self):
        self.opendss_dict['Bus1'] = self.model.bus.name
        #TODO: Should we include the phases its connected to here?
        kv_nominal_voltage = self.model.bus.nominal_voltage.to("kV")
        self.opendss_dict['kV'] = kv_nominal_voltage.magnitude

    def map_phases(self):
        self.opendss_dict['Phases'] = len(self.model.phases)
        # TODO: Do we need to remove neutrals?

    def map_controllers(self):
        controller = self.model.controllers
        #TODO: The controller isn't included in the capacitor mapping.


    def map_equipment(self):
        equipment = self.model.equipment
        connection = self.connection_map[equipment.connection_type]
        self.opendss_dict['Conn'] = connection
        total_resistance = []
        total_reactance = []
        total_rated_capacity = []
        #TODO: Note that this sets the NumSteps to be the number of phase capacitors. Is this right? Do we need to check if banked or not?
        for phase_capacitor in equipment.phase_capacitors:
            total_resistance.append(phase_capacitor.resistance.to("ohm").magnitude)
            total_reactance.append(phase_capacitor.reactance.to("ohm").magnitude)
            total_rated_capacity.append(phase_capacitor.rated_capacity.to("kvar").magnitude) #from general capacitor equipment
        self.opendss_dict['R'] = total_resistance
        self.opendss_dict['XL'] = total_reactance
        self.opendss_dict['kvar'] = total_rated_capacity
        #TODO: We're not building equipment for the Capacitors. This means that there's no guarantee that we're addressing all of the attributes in the equipment in a structured way like we are for the component.




