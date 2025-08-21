from ditto.readers.opendss.reader import Reader

from pydantic import ValidationError
from opendssdirect import dss

import pytest


def test_model():
    dss(
        """
        clear
        new Circuit.test bus1=bus_1.1 BasekV=7.2 pu=1.03 Angle=0.0 Phases=1 Z1=[1e-05, 1e-05] Z0=[1e-05, 1e-05]
        new line.line_1  bus1=bus_1.1 bus2=bus_2.2 phases=1
        new line.line_2  bus1=bus_1.1 bus2=bus_2.2 phases=1 length=-10
        solve
    """
    )
    dss.Circuit.Save("test_circuit", options=0)
    with pytest.raises(ValidationError):
        reader = Reader("test_circuit/Master.dss")
        reader.get_system()
