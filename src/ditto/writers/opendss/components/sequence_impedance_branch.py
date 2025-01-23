from ditto.writers.opendss.components.distribution_branch import DistributionBranchMapper
from ditto.enumerations import OpenDSSFileTypes


class SequenceImpedanceBranchMapper(DistributionBranchMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Line_LineCode"
    altdss_composition_name = "Line"
    opendss_file = OpenDSSFileTypes.LINES_FILE.value

    def map_equipment(self):
        self.opendss_dict["LineCode"] = self.model.equipment.name

    def map_in_service(self):
        self.opendss_dict["enabled"] = self.model.in_service
