from ditto.writers.opendss.opendss_mapper import OpenDSSMapper

class DistributionBranchMapper(OpenDSSMapper):

    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Line_Common"
    altdss_composition_name = "Line"
    opendss_file = "Lines.dss"

    def map_name(self):
        self.opendss_dict['Name'] = self.model.name

    def map_buses(self):
        self.opendss_dict['Bus1'] = self.model.buses[0].name
        self.opendss_dict['Bus2'] = self.model.buses[1].name
        for phase in self.model.buses[0].phases:
            self.opendss_dict['Bus1']+=self.phase_map[phase]

        for phase in self.model.buses[1].phases:
            self.opendss_dict['Bus2']+=self.phase_map[phase]


    def map_length(self):
        self.opendss_dict['Length'] = self.model.length.magnitude
        model_unit = str(self.model.length.units)
        if model_unit not in self.length_units_map:
            raise ValueError(f"{model_unit} not mapped for OpenDSS")
        self.opendss_dict['Units'] = self.length_units_map[model_unit]

    def map_phases(self):
        # Redundant information - included in buses
        # TODO: remove from GDM?
        pass


class SwitchedDistributionBranchMapper(DistributionBranchMapper):

    def map_is_closed(self):
        # Require every phase to be enabled for the OpenDSS line to be enabled.
        is_enabled = True
        for phase_closed in self.model.is_closed:
            is_enabled = is_enabled and phase_closed
        self.opendss_dict['Enabled'] = is_enabled
