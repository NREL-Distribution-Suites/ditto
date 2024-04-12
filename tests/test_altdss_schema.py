from pathlib import Path
import sys

base_path = Path(__file__).parent
module_path = base_path / ".." / "AltDSS-Schema" / "python"
assert module_path.exists()
sys.path.insert(1, str(module_path.absolute()))


def test_altdss_parsing():
    assert module_path.exists()
