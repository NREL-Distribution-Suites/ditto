from enum import Enum


class OpenDSSFileTypes(str, Enum):
    MASTER_FILE = "Master.dss"
    COORDINATE_FILE = "BusCoords.dss"
    TRANSFORMERS_FILE = "Transformers.dss"
    CAPACITORS_FILE = "Capacitors.dss"
    WIRES_FILE = "WireData.dss"
    CABLES_FILE = "CableData.dss"
    LINECODES_FILE = "LineCodes.dss"
    LINES_FILE = "Lines.dss"
    LOADS_FILE = "Loads.dss"
    LINE_GEOMETRIES_FILE = "LineGeometry.dss"
    SWITCH_CODES_FILE = "SwitchCodes.dss"
    SWITCH_FILE = "Switches.dss"
    FUSE_CODES_FILE = "FuseCodes.dss"
    FUSE_FILE = "Fuses.dss"
    RECLOSER_CODES_FILE = "RecloserCodes.dss"
    RECLOSER_FILE = "Reclosers.dss"
