from ditto.writers.opendss.components.distribution_branch import DistributionBranchMapper
from ditto.enumerations import OpenDSSFileTypes


class GeometryBranchMapper(DistributionBranchMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Line_LineGeometry"
    altdss_composition_name = "Line"
    opendss_file = OpenDSSFileTypes.LINES_FILE.value

    def map_equipment(self):
        self.opendss_dict["Geometry"] = self.model.equipment.name.replace(" ", "_").replace(".", "_")
