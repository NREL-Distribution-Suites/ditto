# Usage

DiTTo parsers (readers and writer) use the intermidiate Grid-Data-Models (GDM) (https://github.com/NREL-Distribution-Suites/grid-data-models) representation to convert models from one standard format to another. The interface allows for through validations of converted models, and robust serialization / deserialization capabilities  

The example below shows a simple example to read an existing OpenDSS model and serializing it to disk in GDM format

```python
from pathlib import Path
from ditto.readers.opendss.reader import Reader

opendss_file = Path("IEEE13NODE.dss")
export_file = Path("IEEE13NODE.json")

parser = Reader(opendss_file)
system = parser.get_system()

system.to_json(export_file, overwrite=True)
```

Once serialized to disk, systems can be deserialized. The example below is simple example to deserialize a saved model.

```python
from pathlib import Path
from gdm import DistributionSystem

import_path = Path("IEEE13NODE.json")
assert import_path.exists()

DistributionSystem.from_json(import_path)
```

This DistributionSystem is the core model representation in DiTTo. DistributionSystem is the basis for all model writers.
The example below shows models conversion from GDM representation to OpenDSS. 