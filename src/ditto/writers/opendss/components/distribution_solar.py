from gdm import ConnectionType

from ditto.writers.opendss.opendss_mapper import OpenDSSMapper
from ditto.enumerations import OpenDSSFileTypes


class DistributionSolarMapper(OpenDSSMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "PVSystem_PF"
    altdss_composition_name = "PVSystem"
    opendss_file = OpenDSSFileTypes.PV_FILE.value

    def map_name(self):
        self.opendss_dict["Name"] = self.model.name

    def map_bus(self):
        self.opendss_dict["Bus1"] = self.model.bus.name
        num_phases = len(self.model.phases)
        for phase in self.model.phases:
            self.opendss_dict["Bus1"] += self.phase_map[phase]
        # TODO: Should we include the phases its connected to here?
        nom_voltage = self.model.bus.nominal_voltage.to("kV").magnitude
        self.opendss_dict["kV"] = nom_voltage if num_phases == 1 else nom_voltage * 1.732

    def map_phases(self):
        self.opendss_dict["Phases"] = len(self.model.phases)
        """
        if (
            len(self.model.phases) == 2
            and self.model.equipment.connection_type == ConnectionType.DELTA
        ):
            self.opendss_dict["Phases"] = 1
        else:
            self.opendss_dict["Phases"] = len(self.model.phases)
        """
        # TODO: Add connection_type info to GDM for PV
        # TODO: Do we need to add connections?
        #self.opendss_dict["Conn"] = connection.
        # TODO: Do we need to remove neutrals?

    def map_controllers(self):
        # TODO: manage yearly profile mapping
        self.opendss_dict["PF"] = 1.0 # Provide default value
        self.opendss_dict["irradiance"] = 1
        self.opendss_dict["Model"] = 1
        if len(self.model.controllers) > 1:
            raise ValueError(f"Only expecting a single PV controller for {self.model.name}")
        for controller in self.model.controllers:
            if isinstance(controller, PowerfactorInverterController):
                self.opendss_dict["PF"] = controller.power_factor

            # TODO: Add volt-var controller too


    def map_equipment(self):
        equipment = self.model.equipment
        self.opendss_dict["%r"] = equipment.resistance
        self.opendss_dict["%x"] = equipment.reactance
        self.opendss_dict["%cutin"] = equipment.cutin_percent
        self.opendss_dict["%cutout"] = equipment.cutout_percent
        self.opendss_dict["kVA"] = equipment.rated_capacity.to("kilova").magnitude
        self.opendss_dict["Pmpp"] = equipment.solar_power.to("kilova").magnitude

        # TODO: We're not building equipment for the PVSystem. This means that there's no guarantee that we're addressing all of the attributes in the equipment in a structured way like we are for the component.
