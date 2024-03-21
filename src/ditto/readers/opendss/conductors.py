from uuid import uuid4

from gdm import BareConductorEquipment
from gdm.quantities import Reactance
from infrasys.system import System
import opendssdirect as odd

from ditto.readers.opendss.common import PHASE_MAPPER, model_to_dict, get_equipment_from_system