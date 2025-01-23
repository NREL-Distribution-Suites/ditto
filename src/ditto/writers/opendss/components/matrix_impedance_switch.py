from ditto.writers.opendss.components.distribution_branch import DistributionBranchMapper
from ditto.enumerations import OpenDSSFileTypes


class MatrixImpedanceSwitchMapper(DistributionBranchMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Line_LineCode"
    altdss_composition_name = "Line"
    opendss_file = OpenDSSFileTypes.SWITCH_FILE.value

    def map_equipment(self):
        self.opendss_dict["LineCode"] = self.model.equipment.name

    def map_is_closed(self):
        # Require every phase to be enabled for the OpenDSS line to be enabled.
        self.opendss_dict["Switch"] = "true"

    def map_in_service(self):
        self.opendss_dict["enabled"] = self.model.in_service
