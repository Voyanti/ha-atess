from server import Server
from enums import RegisterTypes
import struct
import logging
from enums import DataType

logger = logging.getLogger(__name__)

U16_MAX = 2**16-1

class AbstractedServer(Server):
    supported_models = ('SG110CX', 'SG33CX', 'SG80KTL-20', 'SG50CX') 
    manufacturer = "Sungrow"
    registers = {
        'Serial Number': {'addr': 4990, 'count': 10, 'dtype': DataType.UTF8, 'multiplier': 1, 'unit': '', 'device_class': 'enum', 'register_type': RegisterTypes.INPUT_REGISTER},
        'Device Type Code': {'addr': 5000, 'count': 1, 'dtype': DataType.U16, 'multiplier': 1, 'unit': '', 'device_class': 'enum', 'register_type': RegisterTypes.INPUT_REGISTER},
        'Nominal Active Power': {'addr': 5001, 'count': 1, 'dtype': DataType.U16, 'multiplier': 0.1, 'unit': 'kW', 'device_class': 'power', 'register_type': RegisterTypes.INPUT_REGISTER},
    }

    def read_model(self, device_type_code_param_key="Device type code"):
        return super().read_model(device_type_code_param_key)
    
    def setup_valid_registers_for_model(self):
        # only support logger 1000 for now
        return
    
    def verify_serialnum(self, serialnum_name_in_definition = "Serial Number"):
        return super().verify_serialnum(serialnum_name_in_definition)
    
    def _decoded(cls, registers, dtype):
        def _decode_u16(registers):
            """ Unsigned 16-bit big-endian to int """
            return registers[0]
        
        def _decode_s16(registers):
            """ Signed 16-bit big-endian to int """
            sign = 0xFFFF if registers[0] & 0x1000 else 0
            packed = struct.pack('>HH', sign, registers[0])
            return struct.unpack('>i', packed)[0]
        

        if dtype == DataType.U16: return _decode_u16(registers)
        elif dtype == "I16" or dtype == DataType.I16: return _decode_s16(registers)
        else: raise NotImplementedError(f"Data type {dtype} decoding not implemented")

    def _encoded(cls, value):
        """ Convert a float or integer to big-endian register.
            Supports U16 only.
        """

        if value > U16_MAX: raise ValueError(f"Cannot write {value=} to U16 register.")
        elif value < 0:     raise ValueError(f"Cannot write negative {value=} to U16 register.")

        if isinstance(value, float):
            # Convert the float value to 4 bytes using IEEE 754 format TODO
            # value_bytes = list(struct.pack('>f', value))
            raise NotImplemented(f"Writing floats to registers is not yet supported.")

        value_bytes = list(value.to_bytes(4, byteorder='big', signed=False))
            
        return value_bytes
   
    def _validate_write_val(register_name:str, val):
        raise NotImplementedError()