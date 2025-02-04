
# DiTTo

DiTTo is the _Distribution Transformation Tool_. It is an open-source tool to convert and modify electrical distribution system models. The most common domain of electrical distribution systems is from substations to customers.

## How it Works
Flexible representations for power system components are defined in [Grid-Data-Models (GDM)](https://github.com/NREL-Distribution-Suites/grid-data-models) format. 
DiTTo implements a _many-to-one-to-many_ parsing framework, making it modular and robust. The [reader modules](https://github.com/NREL-Distribution-Suites/ditto/tree/main/src/ditto/readers) parse data files of distribution system format (e.g. OpenDSS) and create an object for each electrical component. These objects are stored in a [GDM DistributionSystem](https://github.com/NREL-Distribution-Suites/grid-data-models/blob/main/src/gdm/distribution/distribution_system.py) instance. The [writer modules](https://github.com/NREL-Distribution-Suites/ditto/tree/main/src/ditto/writers) are then used to export the data stored in memory to a selected output distribution system format (e.g. OpenDSS) which are written to disk.

Additional functionality can be found in the documentation [here](https://nrel.github.io/ditto).

## Quick Start

### Install DiTTo

```bash
git clone https://github.com/NREL-Distribution-Suites/ditto.git
```

Navigate to the clone directory and use the following command to install

```bash
pip install -e. 
```

### Basic Usage

The most basic capability of DiTTo is converting a distribution system from one format to another.
To convert a cyme model represented in ASCII format with network.txt, equipment.txt and load.txt files, the following python script can be run to perform the conversion

```python
from ditto.readers.cim_iec_61968_13.reader import Reader
from ditto.writers.opendss.write import Writer

cim_reader = Reader(ieee13_node_xml_file)
cim_reader.read()
system = cim_reader.get_system()
writer = Writer(system)
new_dss_file = Path(__file__).parent / "model"
writer.write(output_path=new_dss_file, separate_substations=False, separate_feeders=False)

```

The required input files for each reader format are defined in the folder of each reader

## Contributing
DiTTo is an open-source project and contributions are welcome! Either for a simple typo, a bugfix, or a new parser you want to integrate, feel free to contribute.

To contribute to Ditto in 3 steps:
- Fork the repository (button in the upper right corner of the DiTTo GitHub page).
- Create a feature branch on your local fork and implement your modifications there.
- Once your work is ready to be shared, submit a Pull Request on the DiTTo GitHub page. See the official GitHub documentation on how to do that [here](https://help.github.com/articles/creating-a-pull-request-from-a-fork/)

## Getting Help

If you are having issues using DiTTo, feel free to open an Issue on GitHub [here](https://github.com/NREL/ditto/issues/new)

All contributions are welcome. For questions about collaboration please email [Tarek Elgindy](mailto:tarek.elgindy@nrel.gov)
