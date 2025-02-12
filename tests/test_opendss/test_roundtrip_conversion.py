from pathlib import Path
import glob
import os

import opendssdirect as odd
from loguru import logger
import numpy as np
import pytest

from ditto.writers.opendss.write import Writer
from ditto.readers.opendss.reader import Reader
from ditto.enumerations import OpenDSSFileTypes

test_folder = Path(__file__).parent.parent


TEST_MODELS = [
    test_folder
    / "data"
    / "opendss_circuit_models"
    / "ieee13"
    / OpenDSSFileTypes.MASTER_FILE.value,
    test_folder / "data" / "opendss_circuit_models" / "P4U" / OpenDSSFileTypes.MASTER_FILE.value,
]


def get_model_voltage_drop(model_name: str):
    model = getattr(odd, model_name)
    tr = model.First()
    dvs = []
    while tr:
        buses = odd.CktElement.BusNames()
        voltages = []
        for bus in buses:
            bus = bus.split(".")[0]
            odd.Circuit.SetActiveBus(bus)
            voltage = odd.Bus.puVmagAngle()[::2]
            voltages.append(voltage)

        for ii, v1 in enumerate(voltages):
            for jj, v2 in enumerate(voltages):
                if ii > jj:
                    if len(v1) == len(v2):
                        dv = np.abs(np.subtract(v1, v2))
                        dvs.extend(list(dv))
                    else:
                        dvs.append(abs(v1[0] - v2[0]))

        tr = model.Next()
    xfmr_dvs = [dv for dv in dvs if dv != 0]
    return min(xfmr_dvs), max(xfmr_dvs), sum(xfmr_dvs) / len(xfmr_dvs)


def get_metrics(dss_model_path: Path | str):
    dss_model_path = Path(dss_model_path)
    assert dss_model_path.exists(), f"DSS model {dss_model_path} does not exist"
    cmd = f'redirect "{dss_model_path}"'
    logger.debug(f"Running OpenDSS command -> {cmd}")
    odd.Text.Command("clear")
    odd.Text.Command(cmd)
    odd.Solution.Solve()

    feeder_head_p, feeder_head_q = odd.Circuit.TotalPower()
    voltages = odd.Circuit.AllBusMagPu()
    min_voltage = min(voltages)
    max_voltage = max(voltages)
    avg_voltage = sum(voltages) / len(voltages)

    max_dv_xfmr, min_dv_xfmr, avg_dv_xfmr = get_model_voltage_drop("Transformers")
    max_dv_line, min_dv_line, avg_dv_line = get_model_voltage_drop("Lines")

    base_metrics = [min_voltage, max_voltage, avg_voltage, feeder_head_p, feeder_head_q]
    xfmr_voltages = [max_dv_xfmr, min_dv_xfmr, avg_dv_xfmr]
    line_voltages = [max_dv_line, min_dv_line, avg_dv_line]
    base_metrics.extend(xfmr_voltages)
    base_metrics.extend(line_voltages)
    return base_metrics


@pytest.mark.parametrize("DSS_MODEL", TEST_MODELS)
def test_opendss_roundtrip_converion(DSS_MODEL):
    pre_converion_metrics = get_metrics(DSS_MODEL)
    reader = Reader(DSS_MODEL)
    writer = Writer(reader.get_system())
    export_path = test_folder / "dump_from_tests"

    csv_files = glob.glob(os.path.join(export_path, "*.dss"))
    for file in csv_files:
        os.remove(file)
        logger.debug(f"Deleted: {file}")

    assert export_path.exists(), f"Export path: {export_path}"
    writer.write(export_path, separate_substations=False, separate_feeders=False)
    dss_master_file = export_path / OpenDSSFileTypes.MASTER_FILE.value
    assert dss_master_file.exists()
    post_converion_metrics = get_metrics(dss_master_file)
    assert np.allclose(
        pre_converion_metrics, post_converion_metrics, rtol=0.01, atol=0.01
    ), "Round trip coversion exceeds error tolerance"
