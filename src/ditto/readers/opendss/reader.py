from pathlib import Path

from infrasys.system import System
from gdm import DistributionSystem
from gdm import SequencePair
import opendssdirect as odd

from ditto.readers.reader import AbscractReader
from ditto.readers.opendss.buses import get_buses
from ditto.readers.opendss.loads import get_loads
from ditto.readers.opendss.transformers import get_transformers, get_transformer_equipments
from ditto.readers.opendss.capacitors import get_capacitors, get_capacitor_equipments
from ditto.readers.opendss.sources import get_voltage_sources, get_voltage_source_equipments
from ditto.readers.opendss.lines import get_ac_lines

SEQUENCE_PAIRS = [SequencePair(1, 2), SequencePair(1, 3), SequencePair(2, 3)]


class Reader(AbscractReader):
    """Class interface for Opendss case file reader"""

    def __init__(self, Opendss_master_file: Path, crs: str | None = None) -> None:
        """Constructor for the Opendss reader

        Args:
            Opendss_master_file (Path): Path to the Opendss master file
            crs (str | None, optional): Coordinate reference system name. Defaults to None.
        """

        self.system = DistributionSystem(auto_add_composed_components=True)
        self.Opendss_master_file = Opendss_master_file
        self.crs = crs
        self.read()

    def read(self):
        """Takes the master file path and returns instance of OpendssParser

        Raises:
            FileNotFoundError: Error raised if the file is not found
        """

        if not self.Opendss_master_file.exists():
            msg = f"File not found: {self.Opendss_master_file}"
            raise FileNotFoundError(msg)

        odd.Text.Command("Clear")
        odd.Basic.ClearAll()
        odd.Text.Command(f'Redirect "{self.Opendss_master_file}"')
       
        self.system = System(name=odd.Circuit.Name(), auto_add_composed_components=True)
       
        buses = get_buses(self.system, self.crs)
        self.system.components.add(*buses)
        voltage_source_equipments = get_voltage_source_equipments()
        self.system.components.add(*voltage_source_equipments)
        voltage_sources = get_voltage_sources(self.system)
        self.system.components.add(*voltage_sources)
        capacitor_equipments = get_capacitor_equipments()
        self.system.components.add(*capacitor_equipments)
        caps = get_capacitors(self.system)
        self.system.components.add(*caps)        
        
        #TODO: should unique load equiments be calatoged to reduce replicated objects? 
        loads = get_loads(self.system)
        self.system.components.add(*loads)
        
        transformer_equipments = get_transformer_equipments(self.system)
        self.system.components.add(*transformer_equipments)
        transformers = get_transformers(self.system)
        self.system.components.add(*transformers)
        
        
        # # branches = get_ac_lines(self.system, odd)
        # # self.system.components.add(*branches)
       

    def get_system(self) -> System:
        """Returns an instance of DistributionSystem

        Returns:
            System: Instance of DistributionSystem
        """

        return self.system
    

    

   

   

  
