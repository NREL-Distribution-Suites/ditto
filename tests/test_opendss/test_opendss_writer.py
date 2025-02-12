""" Module for testing writers."""

from gdm import (
    DistributionBus,
    SequenceImpedanceBranch,
    MatrixImpedanceBranch,
    GeometryBranch,
    DistributionCapacitor,
    DistributionTransformer,
    DistributionLoad,
    DistributionVoltageSource,
    DistributionSystem,
)
import pytest

from ditto.writers.opendss.write import Writer

MODULES = [
    DistributionBus,
    SequenceImpedanceBranch,
    MatrixImpedanceBranch,
    GeometryBranch,
    DistributionCapacitor,
    DistributionTransformer,
    DistributionLoad,
    DistributionVoltageSource,
    DistributionCapacitor,
]


@pytest.mark.parametrize("component", MODULES)
def test_component(component, tmp_path):
    system = DistributionSystem(name=f"test {component.__name__}", auto_add_composed_components=True)
    system.add_component(component.example())
    writer = Writer(system)
    writer.write(output_path=tmp_path, separate_substations=False, separate_feeders=False)


def test_all_types(tmp_path):
    system = DistributionSystem(name="test full system", auto_add_composed_components=True)
    for component in MODULES:
        system.add_component(component.example())
    writer = Writer(system)
    writer.write(output_path=tmp_path, separate_substations=True, separate_feeders=True)
