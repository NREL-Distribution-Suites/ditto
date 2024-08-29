from ditto.writers.opendss.equipment.matrix_impedance_branch_equipment import (
    MatrixImpedanceBranchEquipmentMapper,
)
from ditto.enumerations import OpenDSSFileTypes


class MatrixImpedanceSwitchEquipmentMapper(MatrixImpedanceBranchEquipmentMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "LineCode_ZMatrixCMatrix"
    altdss_composition_name = "LineCode"
    opendss_file = OpenDSSFileTypes.SWITCH_CODES_FILE.value

    def map_controller(self):
        # Not mapped in OpenDSS
        pass
