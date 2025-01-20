from server import Server
from enums import RegisterTypes
from sungrow_logger import SungrowLogger
import struct
import logging

logger = logging.getLogger(__name__)

U16_MAX = 2**16-1

PT_RATIO = 1                        # Voltage Transfer
CT_RATIO = 40                       # Current Transfer

# Calculate actual multipliers using PT and CT ratios
VOLTAGE_MULTIPLIER = 0.1 * PT_RATIO
CURRENT_MULTIPLIER = 0.01 * CT_RATIO
POWER_MULTIPLIER = 0.001 * PT_RATIO * CT_RATIO
ENERGY_MULTIPLIER = 0.01 * PT_RATIO * CT_RATIO

class AcrelMeter(Server):
    supported_models = ('DTSD1352') 
    manufacturer = "Acrel"

    # subset of all registers in documentation
    relevant_registers = {
        "Phase A Voltage": {
            "addr": 0x0061,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "V",
            "device_class": "voltage",
            "multiplier": VOLTAGE_MULTIPLIER
        },
        "Phase B Voltage": {
            "addr": 0x0062,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "V",
            "device_class": "voltage",
            "multiplier": VOLTAGE_MULTIPLIER
        },
        "Phase C Voltage": {
            "addr": 0x0063,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "V",
            "device_class": "voltage",
            "multiplier": VOLTAGE_MULTIPLIER
        },
        "A-B Line Voltage": {
            "addr": 0x0078,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "V",
            "device_class": "voltage",
            "multiplier": VOLTAGE_MULTIPLIER
        },
        "B-C Line Voltage": {
            "addr": 0x0079,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "V",
            "device_class": "voltage",
            "multiplier": VOLTAGE_MULTIPLIER
        },
        "C-A Line Voltage": {
            "addr": 0x007A,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "V",
            "device_class": "voltage",
            "multiplier": VOLTAGE_MULTIPLIER
        },
        "Phase A Current": {
            "addr": 0x0064,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "A",
            "device_class": "current",
            "multiplier": CURRENT_MULTIPLIER
        },
        "Phase B Current": {
            "addr": 0x0065,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "A",
            "device_class": "current",
            "multiplier": CURRENT_MULTIPLIER
        },
        "Phase C Current": {
            "addr": 0x0066,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "A",
            "device_class": "current",
            "multiplier": CURRENT_MULTIPLIER
        },
        "Phase A Active Power": {
            "addr": 0x0164,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kW",
            "device_class": "power",
            "multiplier": POWER_MULTIPLIER
        },
        "Phase B Active Power": {
            "addr": 0x0166,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kW",
            "device_class": "power",
            "multiplier": POWER_MULTIPLIER
        },
        "Phase C Active Power": {
            "addr": 0x0168,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kW",
            "device_class": "power",
            "multiplier": POWER_MULTIPLIER
        },
        "PF": {
            "addr": 0x017F,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S32",
            "unit": None,
            "device_class": "power_factor",
            "multiplier": 0.001  # PF doesn't use PT or CT ratios
        },
        "Grid Frequency": {
            "addr": 0x0077,
            "count": 2,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "U32",
            "unit": "Hz",
            "device_class": "frequency",
            "multiplier": 0.01  # Frequency doesn't use PT or CT ratios
        },
        "Active Power": {
            "addr": 0x016A,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kW",
            "device_class": "power",
            "multiplier": POWER_MULTIPLIER
        },
        "Reactive Power": {
            "addr": 0x0172,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kVar",
            "device_class": "reactive_power",
            "multiplier": POWER_MULTIPLIER
        },
        "Apparent Power": {
            "addr": 0x017A,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kVA",
            "device_class": "apparent_power",
            "multiplier": POWER_MULTIPLIER
        },
        "Forward Active Energy": {
            "addr": 0x000A,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kWh",
            "device_class": "energy",
            "multiplier": ENERGY_MULTIPLIER
        },
        "Reverse Active Energy": {
            "addr": 0x0014,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kWh",
            "device_class": "energy",
            "multiplier": ENERGY_MULTIPLIER
        },
        "Forward Reactive Energy": {
            "addr": 0x0028,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kVarh",
            "device_class": "energy",
            "multiplier": ENERGY_MULTIPLIER
        },
        "Reverse Reactive Energy": {
            "addr": 0x0032,
            "count": 4,
            "register_type": RegisterTypes.HOLDING_REGISTER,
            "dtype": "S64",
            "unit": "kVarh",
            "device_class": "energy",
            "multiplier": ENERGY_MULTIPLIER
        }
    }

    registers = relevant_registers

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read_model(self):
        return
    
    def setup_valid_registers_for_model(self):
        # only support logger 1000 for now
        return
    
    def _decoded(cls, content, dtype):
        return SungrowLogger._decoded(SungrowLogger, content, dtype)
        
    def _encoded(cls, value):
        pass
   
    def _validate_write_val(register_name:str, val):
        raise NotImplementedError()
