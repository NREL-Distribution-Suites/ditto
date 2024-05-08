from pathlib import Path

import opendssdirect as odd
from loguru import logger
import numpy as np

from ditto.writers.opendss.write import Writer
from ditto.readers.opendss.reader import Reader
from ditto.enumerations import OpenDSSFileTypes

test_folder = Path(__file__).parent.parent


IEEE_13_NODE_DSS_MODEL = (
    test_folder / "data" / "opendss_circuit_models" / "ieee13" / OpenDSSFileTypes.MASTER_FILE.value
)
IEEE_13_NODE_JSON_MODEL = (
    test_folder / "data" / "opendss_circuit_models" / "ieee13" / "ieee13.json"
)


def get_metrics(dss_model_path: Path | str):
    dss_model_path = Path(dss_model_path)
    assert dss_model_path.exists(), f"DSS model {dss_model_path} does not exist"
    cmd = f'redirect "{dss_model_path}"'
    logger.info(f"Running OpenDSS command -> {cmd}")
    odd.Text.Command("clear")
    odd.Text.Command(cmd)
    odd.Solution.Solve()

    feeder_head_p, feeder_head_q = odd.Circuit.TotalPower()
    voltages = odd.Circuit.AllBusMagPu()
    min_voltage = min(voltages)
    max_voltage = max(voltages)
    avg_voltage = sum(voltages) / len(voltages)

    return min_voltage, max_voltage, avg_voltage, feeder_head_p, feeder_head_q


def test_opendss_roundtrip_converion():
    pre_converion_metrics = get_metrics(IEEE_13_NODE_DSS_MODEL)
    reader = Reader(IEEE_13_NODE_DSS_MODEL)
    writer = Writer(reader.get_system())
    export_path = test_folder / "dump_from_tests" / "writer_export"
    # export_path = Path(".")
    assert export_path.exists(), f"Export path: {export_path}"
    writer.write(export_path, separate_substations=False, separate_feeders=False)
    dss_master_file = export_path / OpenDSSFileTypes.MASTER_FILE.value
    assert dss_master_file.exists()
    post_converion_metrics = get_metrics(dss_master_file)
    assert np.allclose(
        pre_converion_metrics, post_converion_metrics, rtol=0.001
    ), "Round trip coversion exceeds error tolerance"
