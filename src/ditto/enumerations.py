from enum import Enum


class OpenDSSFileTypes(str, Enum):
    MASTER_FILE = "Master.dss"
    COORDINATE_FILE = "BusCoords.dss"
    WIRES_FILE = "WireData.dss"
    LINE_GEOMETRIES_FILE = "LineGeometry.dss"
    LINECODES_FILE = "LineCodes.dss"
    SWITCH_CODES_FILE = "SwitchCodes.dss"
    FUSE_CODES_FILE = "FuseCodes.dss"
    TRANSFORMERS_FILE = "Transformers.dss"
    CAPACITORS_FILE = "Capacitors.dss"
    LINES_FILE = "Lines.dss"
    LOADS_FILE = "Loads.dss"
    SWITCH_FILE = "Switches.dss"
    FUSE_FILE = "Fuses.dss"
    REGULATOR_CONTROLLERS_FILE = "RegControllers.dss"
