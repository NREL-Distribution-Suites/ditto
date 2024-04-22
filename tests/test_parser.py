""" Module for testing parsers."""
from pathlib import Path
import os

from infrasys import System
import pytest

from ditto.readers.opendss.reader import Reader


base_path = Path(__file__).parent
OPENDSS_CASEFILES = (Path(__file__).parent / "data" / "Opendss_circuit_models").rglob("Master.dss")
# OPENDSS_CASEFILES = [Path(r"C:/Users/alatif/Documents/GitHub/ditto/tests/data/opendss_circuit_models/ckt24/Master.dss")]
# OPENDSS_CASEFILES = [Path(r"C:/Users/alatif/Documents/GitHub/ditto/tests/data/opendss_circuit_models/ieee13/Master.dss")]
# OPENDSS_CASEFILES = [
#     Path(
#         r"C:/Users/alatif/Documents/GitHub/ditto/tests/data/opendss_circuit_models/p4u/Master.dss"
#     )
# ]


@pytest.mark.parametrize("opendss_file", OPENDSS_CASEFILES)
def test_serialize_opendss_model(opendss_file: Path, tmp_path):
    example_name = opendss_file.parent.name

    export_path = Path(tmp_path) / example_name
    # export_path = base_path / "dump_from_tests" / example_name

    if not export_path.exists():
        os.mkdir(export_path)
    parser = Reader(opendss_file)
    system = parser.get_system()
    json_path = export_path / (opendss_file.stem.lower() + ".json")
    system.to_json(json_path, overwrite=True)
    assert json_path.exists(), "Failed to export the json file"


JSON_CASEFILES = (Path(__file__).parent / "data" / "Opendss_circuit_models").rglob("*.json")


@pytest.mark.parametrize("json_file", JSON_CASEFILES)
def test_deserialize_model(json_file: Path, tmp_path):
    example_name = json_file.parent.name
    import_path = base_path / "dump_from_tests" / example_name / (json_file.stem.lower() + ".json")
    assert import_path.exists()
    System.from_json(import_path)
