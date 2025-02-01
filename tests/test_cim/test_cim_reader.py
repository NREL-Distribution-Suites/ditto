from pathlib import Path

import opendssdirect as odd
from loguru import logger
import numpy as np

from ditto.readers.cim_iec_61968_13.reader import Reader
from ditto.writers.opendss.write import Writer


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
    logger.info(f"Running OpenDSS command -> {cmd}")
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


def test_query_aclinesegment(ieee13_node_xml_file):
    ieee13_node_dss_file = (
        Path(__file__).parent.parent / "data" / "opendss_circuit_models" / "ieee13" / "Master.dss"
    )
    pre_converion_metrics = get_metrics(ieee13_node_dss_file)
    cim_reader = Reader(ieee13_node_xml_file)
    cim_reader.read()
    system = cim_reader.get_system()
    writer = Writer(system)
    new_dss_file = Path(__file__).parent / "model"
    writer.write(output_path=new_dss_file, separate_substations=False, separate_feeders=False)
    post_converion_metrics = get_metrics(new_dss_file / "Master.dss")
    assert np.allclose(
        pre_converion_metrics, post_converion_metrics, rtol=0.1, atol=0.1
    ), "Round trip coversion exceeds error tolerance"
