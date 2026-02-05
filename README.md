# DiTTo - Distribution Transformation Tool

[![PyPI version](https://badge.fury.io/py/NREL-ditto.svg)](https://pypi.org/project/NREL-ditto/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DiTTo is an open-source tool developed by NREL's Distribution Suites team for converting and modifying electrical distribution system models. It enables seamless conversion between different distribution network formats, with the primary domain being substations to customers.

## Key Features

- **Multi-format Support**: Read and write models from OpenDSS, CIM/IEC 61968-13, and more
- **Robust Architecture**: Many-to-one-to-many parsing framework ensures modularity and extensibility
- **GDM Integration**: Built on [Grid-Data-Models (GDM)](https://github.com/NREL-Distribution-Suites/grid-data-models) for flexible power system component representation
- **Validation**: Thorough model validation during conversion
- **Serialization**: Full JSON serialization/deserialization support for converted models

## How It Works

DiTTo implements a **many-to-one-to-many** parsing framework:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   OpenDSS   │     │             │     │   OpenDSS   │
├─────────────┤     │    GDM      │     ├─────────────┤
│  CIM/IEC    │ ──▶ │ Distribution│ ──▶ │   CYME      │
├─────────────┤     │   System    │     ├─────────────┤
│    CYME     │     │             │     │    JSON     │
└─────────────┘     └─────────────┘     └─────────────┘
   READERS          INTERMEDIATE          WRITERS
```

1. **Readers** parse distribution system files and create component objects
2. All components are stored in a **GDM DistributionSystem** instance (intermediate format)
3. **Writers** export the data to the desired output format

## Installation

### From PyPI (Recommended)

```bash
pip install nrel-ditto
```

### From Source

```bash
git clone https://github.com/NREL-Distribution-Suites/ditto.git
cd ditto
pip install -e .
```

### Optional Dependencies

```bash
# For documentation building
pip install nrel-ditto[doc]

# For development (includes pytest, ruff)
pip install nrel-ditto[dev]
```

## Quick Start

### Reading an OpenDSS Model

```python
from pathlib import Path
from ditto.readers.opendss.reader import Reader

# Read an OpenDSS model
opendss_file = Path("path/to/IEEE13NODE.dss")
reader = Reader(opendss_file)
system = reader.get_system()

# Access components
print(f"Loaded {len(list(system.get_buses()))} buses")
```

### Converting CIM to OpenDSS

```python
from pathlib import Path
from ditto.readers.cim_iec_61968_13.reader import Reader
from ditto.writers.opendss.write import Writer

# Read CIM model
cim_reader = Reader("path/to/ieee13_cim.xml")
cim_reader.read()
system = cim_reader.get_system()

# Write to OpenDSS format
writer = Writer(system)
writer.write(
    output_path=Path("./output"),
    separate_substations=False,
    separate_feeders=False
)
```

### Serializing to JSON

```python
from pathlib import Path
from ditto.readers.opendss.reader import Reader

# Read and serialize
reader = Reader(Path("IEEE13NODE.dss"))
system = reader.get_system()
system.to_json(Path("IEEE13NODE.json"), overwrite=True)
```

### Loading from JSON

```python
from pathlib import Path
from gdm import DistributionSystem

# Deserialize a saved model
system = DistributionSystem.from_json(Path("IEEE13NODE.json"))
```

## Supported Formats

### Readers (Input)

| Format | Status | Description |
|--------|--------|-------------|
| OpenDSS | ✅ Complete | Full support for OpenDSS models |
| CIM/IEC 61968-13 | ✅ Complete | Common Information Model support |
| CYME | 🚧 In Progress | CYME network models |

### Writers (Output)

| Format | Status | Description |
|--------|--------|-------------|
| OpenDSS | ✅ Complete | Full DSS file generation |
| JSON/GDM | ✅ Complete | Serialized GDM format |

## Supported Components

DiTTo handles a comprehensive set of distribution system components:

- **Network**: Buses, Lines/Branches, Cables, Conductors
- **Transformers**: Distribution transformers with multiple windings
- **Loads**: Various load types (constant power, impedance, ZIP)
- **Generation**: PV systems, Voltage sources
- **Protection**: Fuses, Regulators with controllers
- **Storage**: Battery/energy storage systems
- **Capacitors**: Shunt capacitors
- **Time-Series**: Load shapes and profiles

## Project Structure

```
ditto/
├── src/ditto/
│   ├── readers/           # Format parsers
│   │   ├── opendss/       # OpenDSS reader
│   │   ├── cim_iec_61968_13/  # CIM reader
│   │   └── cyme/          # CYME reader
│   ├── writers/           # Format exporters
│   │   └── opendss/       # OpenDSS writer
│   └── enumerations.py    # Shared enumerations
├── tests/                 # Test suite
├── docs/                  # Documentation
└── pyproject.toml         # Project configuration
```

## Documentation

- [Architecture Guide](ARCHITECTURE.md) - System design and components
- [API Reference](API.md) - Reader and writer documentation
- [Examples](EXAMPLES.md) - Detailed usage examples
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

## Requirements

- Python 3.10, 3.11, or 3.12
- Dependencies are automatically installed:
  - `grid-data-models` - GDM intermediate representation
  - `opendssdirect.py` - OpenDSS interface
  - `rdflib` - RDF/XML parsing for CIM
  - `NREL-altdss-schema` - DSS output schema

## Contributing

DiTTo is an open-source project and contributions are welcome! Whether it's a typo fix, bug report, or a new parser, we appreciate your help.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Submit a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/NREL-Distribution-Suites/ditto/issues)
- **Questions**: Contact [Tarek Elgindy](mailto:tarek.elgindy@nrel.gov)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

DiTTo is developed and maintained by the [NREL Distribution Suites](https://github.com/NREL-Distribution-Suites) team at the National Renewable Energy Laboratory.
