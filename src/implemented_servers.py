from enum import Enum

from sungrow_inverter import SungrowInverter
from sungrow_logger import SungrowLogger
from sungrow_meter import AcrelMeter

class ServerTypes(Enum):
    SUNGROW_INVERTER = SungrowInverter
    SUNGROW_LOGGER = SungrowLogger
    ACREL_METER = AcrelMeter