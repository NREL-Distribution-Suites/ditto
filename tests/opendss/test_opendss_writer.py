""" Module for testing writers."""
from pathlib import Path

import pytest

from ditto.writers.opendss.write import Writer
from gdm import DistributionBus, SequenceImpedanceBranch, SequenceImpedanceBranchEquipment, MatrixImpedanceBranch, GeometryBranch, DistributionCapacitor, DistributionTransformer
from infrasys.system import System


def test_bus():
    test_bus = DistributionBus.example()
    system = System(name='test bus', auto_add_composed_components=True)
    system.add_component(test_bus)
    writer = Writer(system)
    writer.write(separate_substations=False,separate_feeders=False)

def test_sequence_impedance_branch():
    test_branch = SequenceImpedanceBranch.example()
    system = System(name='test sequence impedance', auto_add_composed_components=True)
    system.add_component(test_branch)
    writer = Writer(system)
    writer.write(separate_substations=False,separate_feeders=False)

def test_matrix_impedance_branch():
    test_branch = MatrixImpedanceBranch.example()
    system = System(name='test matrix impedance', auto_add_composed_components=True)
    system.add_component(test_branch)
    writer = Writer(system)
    writer.write(separate_substations=False,separate_feeders=False)

def test_geometry_branch():
    test_branch3 = GeometryBranch.example()
    system = System(name='test geometry branch', auto_add_composed_components=True)
    system.add_component(test_branch)
    writer = Writer(system)
    writer.write(separate_substations=False,separate_feeders=False)

def test_capacitor():
    test_capacitor = DistributionCapacitor.example()
    system = System(name='test capacitor', auto_add_composed_components=True)
    system.add_component(test_capacitor)
    writer = Writer(system)
    writer.write(separate_substations=False,separate_feeders=False)

def test_transformer():
    test_transformer = DistributionTransformer.example()
    system = System(name='test transformer', auto_add_composed_components=True)
    system.add_component(test_transformer)
    writer = Writer(system)
    writer.write(separate_substations=False,separate_feeders=False)


