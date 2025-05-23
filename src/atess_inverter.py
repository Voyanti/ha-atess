from typing import final, Literal
from .server import Server
import struct
import logging
from .enums import DataType
from .atess_registers import atess_parameters, PBD_parameters, PCS_parameters, not_PCS_parameters, model_code_to_name, atess_write_parameters, atess_PBD_write_parameters
from pymodbus.client import ModbusSerialClient

logger = logging.getLogger(__name__)

@final
class AtessInverter(Server):
    # RS485 address is 1-32
    # adresses seem to be 0-indexed so +1
    def __init__(self, name, serial, modbus_id, connected_client):
        super().__init__(name, serial, modbus_id, connected_client)

        self._manufacturer = "Atess"
        self._supported_models = ('PCS150', 'PCS500', 'PBD250') 
        self._serialnum = "unknown"
        self._parameters = dict.copy(atess_parameters)
        self._write_parameters = {}

    @property
    def manufacturer(self):
        return self._manufacturer
    
    @property
    def supported_models(self):
        return self._supported_models
    
    @property
    def parameters(self):
        return self._parameters
    
    @property
    def write_parameters(self):
        return self._write_parameters
    
    def is_available(self, register_name="Device On/Off"):
        # self.verify_serialnum()
        return super().is_available(register_name)
    
    def verify_serialnum(self, serialnum_name_in_definition:str="Serial Number") -> bool:
        """ Verify that the serialnum specified in config.yaml matches 
        with the num in the regsiter as defined in implementation of Server

        Arguments:
        ----------
            - serialnum_name_in_definition: str: Name of the register in server.registers containing the serial number
        """
        logger.info("Verifying serialnumber")
        serialnum = self.read_registers(serialnum_name_in_definition)                                                

        if serialnum is None: 
            logger.info(f"Server with serial {self.serial} not available")
            return False
        elif self.serial != serialnum: raise ValueError(f"Mismatch in configured serialnum {self.serial} \
                                                                        and actual serialnum {serialnum} for server {self.name}.")
        return True
        
    def read_model(self):
        model_code = self.read_registers("Device Type Code")

        model_name = model_code_to_name.get(model_code)
        if not model_name: 
            raise ValueError(f"Device Type Code read {model_code=} not in mappiong to string")

        return model_name
    
    def setup_valid_registers_for_model(self):
        logger.info(f"{self.model}")
        if "PCS" in self.model:
            self._parameters.update(PCS_parameters)
            self._write_parameters.update(atess_write_parameters)
            logger.info("Added PCS-Specific Registers.")
        else:
            self._parameters.update(not_PCS_parameters)
            logger.info("Added Registers. common to all except PCS models")

            if "PBD" in self.model:
                self._parameters.update(PBD_parameters)
                self._write_parameters.update(atess_PBD_write_parameters)
                logger.info("Added PBD-Specific Registers.")

    def _decoded(cls, registers, dtype):
        def _decode_i8(registers, low_or_high=Literal["low", "high"]):
            """ Unsigned 32-bit big-endian to int """
            if low_or_high == "low":
                extracted = registers[0] & 0x00FF
            elif low_or_high == "high":
                extracted = (registers[0] & 0xFF00) >> 8

            else:
                raise ValueError(f"Invalid 8-bit type")

            # Convert to signed 8-bit integer
            if extracted & 0x80:  # Check sign bit
                extracted -= 0x100  # Convert to negative

            return extracted

        def _decode_u16(registers):
            """ Unsigned 16-bit big-endian to int """
            return registers[0]
        
        def _decode_u32(registers):
            """ Unsigned 32-bit big-endian to int """
            low = registers[1]
            high = registers[0]
            packed = struct.pack('>HH', high, low)
            return struct.unpack('>I', packed)[0]
        
        def _decode_i16(registers):
            """ Signed 16-bit big-endian to int """
            return struct.unpack('>h', struct.pack('>H', registers[0]))[0]
        
        def _decode_utf8(registers): # TODO
            """ Two ASCII chars per 16-bit register """
            
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.STRING)   

        if dtype == DataType.U16: return _decode_u16(registers)
        elif dtype == DataType.I16: return _decode_i16(registers)
        elif dtype == DataType.I8L: return _decode_i8(registers, "low")
        elif dtype == DataType.I8H: return _decode_i8(registers, "high")
        elif dtype == DataType.U32: return _decode_u32(registers)
        elif dtype == DataType.UTF8: return _decode_utf8(registers)
        else: raise NotImplementedError(f"Data type {dtype} decoding not implemented")

    def _encoded(cls, value, dtype):
        def _encode_u16(value):
            """ Unsigned 16-bit big-endian to int """
            U16_MAX = 2**16-1

            if value > U16_MAX: raise ValueError(f"Cannot write {value=} to U16 register.")
            elif value < 0:     raise ValueError(f"Cannot write negative {value=} to U16 register.")

            if isinstance(value, float):
                value = int(value)
                
            return [value]

        if dtype==DataType.U16: return _encode_u16(value)
   
if __name__ == "__main__":
    inv = AtessInverter("", "", "", "")
    inv.model = "PBD250"
    inv.setup_valid_registers_for_model()
    inv.find_register_extent()
    inv.create_batches()

    print([i for i in inv.input_batches])
    print([i for i in inv.input_batches])
    print([i for i in inv.holding_batches])

    # print(inv._decoded([0x6154, 0x5461, 0x8854], DataType.UTF8))# aT = 0x61, 0x54
    # print(inv._decoded([2**16-1], DataType.I16))
    # print(inv._decoded([0x0304], DataType.I8H))