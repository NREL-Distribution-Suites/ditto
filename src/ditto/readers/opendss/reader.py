from pathlib import Path

from infrasys.system import System
from gdm import DistributionSystem
from gdm import SequencePair
import opendssdirect as dss

from ditto.readers.reader import AbscractReader
from ditto.readers.opendss.buses import get_buses
from ditto.readers.opendss.loads import get_loads
from ditto.readers.opendss.transformers import get_transformers
from ditto.readers.opendss.capacitors import get_capacitors
from ditto.readers.opendss.sources import get_voltage_sources
from ditto.readers.opendss.lines import get_ac_lines

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class Reader(AbscractReader):
    """Class interface for OpenDSS case file reader"""

    def __init__(self, opendss_master_file: Path, crs: str | None = None) -> None:
        """Constructor for the OpenDSS reader

        Args:
            opendss_master_file (Path): Path to the OpenDSS master file
            crs (str | None, optional): Coordinate reference system name. Defaults to None.
        """

        self.system = DistributionSystem(auto_add_composed_components=True)
        self.opendss_master_file = opendss_master_file
        self.crs = crs
        self.read()

    def read(self):
        """Takes the master file path and returns instance of OpendssParser

        Raises:
            FileNotFoundError: Error raised if the file is not found
        """

        if not self.opendss_master_file.exists():
            msg = f"File not found: {self.opendss_master_file}"
            raise FileNotFoundError(msg)

        dss.Text.Command("Clear")
        dss.Basic.ClearAll()
        dss.Text.Command(f'Redirect "{self.opendss_master_file}"')
        
        buses = get_buses(self.system, dss, self.crs)
        self.system = System(name=dss.Circuit.Name(), auto_add_composed_components=False)
        self.system.components.add(*buses)
        caps = get_capacitors(self.system, dss)
        self.system.components.add(*caps)
        loads = get_loads(self.system, dss)
        self.system.components.add(*loads)
        voltage_sources = get_voltage_sources(self.system, dss)
        self.system.components.add(*voltage_sources)
        # branches = get_ac_lines(self.system, dss)
        # self.system.components.add(*branches)
        transformers = get_transformers(self.system, dss)
        self.system.components.add(*transformers)

    def get_system(self) -> System:
        """Returns an instance of DistributionSystem

        Returns:
            System: Instance of DistributionSystem
        """

        return self.system
    

    

   

   

  
