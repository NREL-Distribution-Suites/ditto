from ditto.writers.opendss.opendss_mapper import OpenDSSMapper
from ditto.enumerations import OpenDSSFileTypes


class MatrixImpedanceBranchEquipmentMapper(OpenDSSMapper):
    def __init__(self, model):
        super().__init__(model)

    altdss_name = "LineCode_ZMatrixCMatrix"
    altdss_composition_name = "LineCode"
    opendss_file = OpenDSSFileTypes.LINECODES_FILE.value

    def map_common(self):
        r_matrix_ohms = self.model.r_matrix.to("ohm/km")
        x_matrix_ohms = self.model.x_matrix.to("ohm/km")
        c_matrix_ohms = self.model.c_matrix.to("nanofarad/km")
        assert len(r_matrix_ohms) == len(x_matrix_ohms) == len(c_matrix_ohms)
        self.opendss_dict["NPhases"] = len(r_matrix_ohms.magnitude)
        self.opendss_dict["Units"] = "km"

    def map_name(self):
        self.opendss_dict["Name"] = self.model.name

    def map_r_matrix(self):
        r_matrix_ohms = self.model.r_matrix.to("ohm/km")
        self.opendss_dict["RMatrix"] = r_matrix_ohms.magnitude

    def map_x_matrix(self):
        x_matrix_ohms = self.model.x_matrix.to("ohm/km")
        self.opendss_dict["XMatrix"] = x_matrix_ohms.magnitude

    def map_c_matrix(self):
        c_matrix_nf = self.model.c_matrix.to("nanofarad/km")
        self.opendss_dict["CMatrix"] = c_matrix_nf.magnitude

    def map_ampacity(self):
        ampacity_amps = self.model.ampacity.to("ampere")
        self.opendss_dict["NormAmps"] = ampacity_amps.magnitude

    def map_construction(self):
        pass
