from ditto.writers.opendss.components.distribution_branch import DistributionBranchMapper

class MatrixImpedanceBranchMapper(DistributionBranchMapper):

    def __init__(self, model):
        super().__init__(model)

    altdss_name = "Line_LineCode"
    altdss_composition_name = "Line"
    opendss_file = "Lines.dss"

    def map_equipment(self):
        self.opendss_dict['LineCode'] = self.model.equipment.name

