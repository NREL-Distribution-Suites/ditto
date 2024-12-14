from pathlib import Path

from ditto.readers.cim_61968.reader import Reader

BASE_PATH = Path(__file__).parent.parent
cim_circuit_models = BASE_PATH / "data" / "cim_61968_models"


def test_13node_model():
    cim_file = cim_circuit_models / "ieee13" / "IEEE13Nodeckt_CIM100x.XML"
    _ = Reader(cim_xml_file=cim_file)
