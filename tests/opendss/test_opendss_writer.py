""" Module for testing writers."""
from pathlib import Path

import pytest

from ditto.writers.opendss.write import Writer
from gdm import DistributionBus
from infrasys.system import System


def test_write_bus():
    test_bus = DistributionBus.example()
    system = System(name='test bus', auto_add_composed_components=True)
    system.add_component(test_bus)
    writer = Writer(system)
    writer.write()

