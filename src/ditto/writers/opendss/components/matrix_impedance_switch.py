from ditto.writers.opendss.components.distribution_branch import DistributionBranchMapper
from ditto.enumerations import OpenDSSFileTypes


class MatrixImpedanceSwitchMapper(DistributionBranchMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Line_LineCode"
    altdss_composition_name = "Line"
    opendss_file = OpenDSSFileTypes.SWITCH_FILE.value

    def map_name(self):
        name = self.model.name.replace(" ","_").replace(".","_")
        name = name + "_switch"
        self.opendss_dict["Name"] = name

    def map_equipment(self):
        self.opendss_dict["LineCode"] = self.model.equipment.name.replace(" ", "_").replace(".", "_")

    def map_is_closed(self):
        # Require every phase to be enabled for the OpenDSS line to be enabled.
        self.opendss_dict["Switch"] = "true"
