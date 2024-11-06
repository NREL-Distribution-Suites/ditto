""" Module for testing parsers."""
from pathlib import Path
import os
import pytest
from ditto.readers.synergi.reader import Reader


base_path = Path(__file__).parent.parent
synergi_circuit_models = base_path / "data" / "synergi_test_cases"
assert synergi_circuit_models.exists, f"{synergi_circuit_models} does not exist"

# Require all models to be called Model.mdb and Equipment.mdb for testing

synergi_model_name = "Model.mdb"
synergi_equipment_name = "Equipment.mdb"

target_files = set([synergi_model_name, synergi_equipment_name])
matching_folders = []
for folder in Path(synergi_circuit_models).rglob("*"):
    if folder.is_dir():
        files_in_folder = set(f.name for f in folder.iterdir() if f.is_file())
        if target_files.issubset(files_in_folder):
            matching_folders.append(folder)

@pytest.mark.parametrize("synergi_folder", matching_folders)
def test_synergi_reader(synergi_folder: Path, tmp_path):

    export_path = base_path / "dump_from_tests" / "synergi" / synergi_folder.name
    if not export_path.exists():
        export_path.mkdir(parents=True, exist_ok=True)

    reader = Reader(synergi_folder/ synergi_model_name, synergi_folder / synergi_equipment_name )    
    system = reader.get_system()
    json_path = (export_path / synergi_folder.stem.lower()).with_suffix(".json")
    system.to_json(json_path, overwrite=True, indent=4)

    assert json_path.exists(), "Failed to export the json file"
