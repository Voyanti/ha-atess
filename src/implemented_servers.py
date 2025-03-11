from enum import Enum

from .atess_inverter import AtessInverter

class DeviceTypes(Enum):
    ATESS_INVERTER = AtessInverter
