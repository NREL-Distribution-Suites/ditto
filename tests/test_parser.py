""" Module for testing parsers."""
from pathlib import Path

import pytest

from ditto.readers.opendss.reader import Reader

OPENDSS_CASEFILES = (Path(__file__).parent / "data" / "Opendss_circuit_models").rglob("Master.dss")
OPENDSS_CASEFILES = [
    Path(
        r"C:\Users\alatif\Documents\GitHub\ditto\tests\data\Opendss_circuit_models\ckt24\Master.dss"
    )
]


@pytest.mark.parametrize("opendss_file", OPENDSS_CASEFILES)
def test_serialize_model(opendss_file: Path, tmp_path):
    parser = Reader(opendss_file)
    system = parser.get_system()
    json_path = Path(tmp_path) / (opendss_file.stem.lower() + ".json")
    system.to_json(json_path, overwrite=True)
    assert json_path.exists, "Failed to export the json file"
