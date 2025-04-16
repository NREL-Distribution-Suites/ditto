"""Module for testing writers."""

from gdm.distribution import DistributionSystem
from gdm.distribution.components import (
    DistributionVoltageSource,
    DistributionTransformer,
    SequenceImpedanceBranch,
    DistributionCapacitor,
    MatrixImpedanceBranch,
    DistributionLoad,
    DistributionBus,
    GeometryBranch,
)
import pytest

from ditto.writers.opendss.write import Writer

MODULES = [
    DistributionVoltageSource,
    DistributionTransformer,
    SequenceImpedanceBranch,
    DistributionCapacitor,
    MatrixImpedanceBranch,
    # DistributionSystem,
    DistributionLoad,
    DistributionBus,
    GeometryBranch,
]


@pytest.mark.parametrize("component", MODULES)
def test_component(component, fixed_tmp_path):
    system = DistributionSystem(
        name=f"test {component.__name__}", auto_add_composed_components=True
    )
    system.add_component(component.example())
    writer = Writer(system)
    writer.write(output_path=fixed_tmp_path, separate_substations=False, separate_feeders=False)


def test_all_types(fixed_tmp_path):
    system = DistributionSystem(name="test full system", auto_add_composed_components=True)
    for component in MODULES:
        system.add_component(component.example())
    writer = Writer(system)
    writer.write(output_path=fixed_tmp_path, separate_substations=True, separate_feeders=True)
