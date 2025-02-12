from abc import ABC, abstractmethod
from pathlib import Path

from loguru import logger

from infrasys.system import System


class AbstractReader(ABC):
    @abstractmethod
    def get_system(self) -> System:
        """Method return parsed Infrasys system

        Returns:
            System: Instance of Infrasys system
        """
        ...

    def to_json(self, json_file: Path | str):
        """Exports system to a json file

        Args:
            json_file (Path | str): Export path for the GDM model
        """
        json_file = Path(json_file)
        assert hasattr(self, "system"), "Use the read method to build the system first"
        self.system.to_json(json_file, overwrite=True)
        logger.debug(f"GDM model exported to {json_file}")
