from server import Server
from enums import RegisterTypes
from pymodbus import ModbusSerialClient
import struct
import logging

logger = logging.getLogger(__name__)


class AbstractedServer(Server):
    supported_models = ('PCS150') 
    manufacturer = "Atess"
    # RS485 address is 1-32
    # adresses seem to be 0-indexed so +1

    registers = {
        'Serial Number': {'addr': 180+1, 'count': 6, 'dtype': 'UTF-8', 'device_class': 'enum', 'multiplier': 1, 'unit': '', 'register_type': RegisterTypes.HOLDING_REGISTER},                     # TODO count 5? p30
        # On/Off State
        'Device On/Off': {'addr': 0+1, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum', 'register_type': RegisterTypes.HOLDING_REGISTER},

        # Voltage and Current Measurements
        'PV Voltage': {'addr': 80+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Battery Voltage': {'addr': 81+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Battery Current': {'addr': 82+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'PV Current': {'addr': 83+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},

        # Output Voltages
        'Output Voltage U': {'addr': 84+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Output Voltage V': {'addr': 85+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Output Voltage W': {'addr': 86+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},

        # Grid Currents
        'Grid Current U': {'addr': 87+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Grid Current V': {'addr': 88+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Grid Current W': {'addr': 89+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},

        # Grid Voltages
        'Grid Voltage UV': {'addr': 90+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Grid Voltage VW': {'addr': 91+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Grid Voltage WU': {'addr': 92+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage', 'register_type': RegisterTypes.HOLDING_REGISTER},

        # Load Currents
        'Load Current U': {'addr': 93+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Load Current V': {'addr': 94+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},
        'Load Current W': {'addr': 95+1, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current', 'register_type': RegisterTypes.HOLDING_REGISTER},
    }

    def verify_serialnum(self, serialnum_name_in_definition = "Serial Number"):
        return super().verify_serialnum(serialnum_name_in_definition)

    def read_model(self, device_type_code_param_key="Device type code"):
        return
    
    def setup_valid_registers_for_model(self):
        return
    
    def _decoded(cls, content, dtype):
        def _decode_u16(registers):
            """ Unsigned 16-bit big-endian to int """
            return registers[0]
        
        def _decode_s16(registers):
            """ Signed 16-bit big-endian to int """
            sign = 0xFFFF if registers[0] & 0x1000 else 0
            packed = struct.pack('>HH', sign, registers[0])
            return struct.unpack('>i', packed)[0]
        
        def _decode_utf8(registers):
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.STRING)
        

        if dtype == "U16": return _decode_u16(content)
        elif dtype == "I16" or dtype == "S16": return _decode_s16(content)
        elif dtype == "UTF-8": return _decode_utf8(content)
        else: raise NotImplementedError(f"Data type {dtype} decoding not implemented")

    def _encoded(cls, value):
        raise NotImplementedError()
   
    def _validate_write_val(register_name:str, val):
        raise NotImplementedError()