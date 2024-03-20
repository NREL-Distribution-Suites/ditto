""" Module for testing parsers."""
from pathlib import Path

import pytest

from ditto.readers.opendss.reader import Reader

OPENDSS_CASEFILES = (Path(__file__).parent / "data"/ "opendss_circuit_models").rglob("Master.dss")


@pytest.mark.parametrize("opendss_file", OPENDSS_CASEFILES)
def test_serialize_model(opendss_file: Path, tmp_path):
    parser = Reader(opendss_file)
    system = parser.get_system()
    json_path = Path(tmp_path) / (opendss_file.stem.lower() + ".json")
    system.to_json(json_path, overwrite=True)
    print(json_path)
    import os
    os.system("pause")
    assert json_path.exists, "Failed to export the json file"
