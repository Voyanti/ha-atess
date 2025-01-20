from server import Server
from sungrow_inverter import SungrowInverter  
from pymodbus.client import ModbusSerialClient
import struct
from enums import RegisterTypes
import logging

logger = logging.getLogger(__name__)


U16_MAX = 2**16-1

class SungrowLogger(Server):
    
    manufacturer = "Sungrow"
    model = "Logger 1000x"

    device_info = {
        0x0705: { "model":"Logger3000"},
        0x0710: { "model":"Logger1000"}, 
        0x0718: { "model":"Logger4000"}
    }

    supported_models = ("Logger1000")
                        #  "Logger3000", "Logger4000")

    # Sungrow 1.0.2.7 definitions 04 input registers
    logger_input_registers = {
        'Device type code': {
            'addr': 8000,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0x0705 Logger3000, 0x0710 Logger1000, 0x0718 Logger4000',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Protocol number': {
            'addr': 8001,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Communication protocol version': {
            'addr': 8003,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Total devices connected': {
            'addr': 8005,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Total faulty devices': {
            'addr': 8006,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Digital input state': {
            'addr': 8021,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': 'Currently only the low 16 bits are used. Logger1000 only uses 8 bits, Logger3000 uses 16 bits, and Logger4000 uses 16 bits',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC1 voltage': {
            'addr': 8029,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'V',
            'device_class': 'voltage',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC1 current': {
            'addr': 8030,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'remarks': 'Logger1000/Logger3000',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC2 voltage': {
            'addr': 8031,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'V',
            'device_class': 'voltage',
            'remarks': 'Logger1000/Logger3000',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC2 current': {
            'addr': 8032,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC3 voltage': {
            'addr': 8033,
            'dtype': 'S16',
            'count': 1,
            'multiplier': '',
            'unit': '',
            'device_class': 'voltage',
            'remarks': 'Logger3000 and Logger1000 share the voltage. Logger3000 consumes 0.01mV, and Logger1000 consumes 0.01V',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC4 voltage': {
            'addr': 8034,
            'count': 1,
            'dtype': 'S16',
            'multiplier': '',
            'unit': '',
            'device_class': 'voltage',
            'remarks': 'Logger3000 and Logger1000 share the voltage. Logger3000 consumes 0.01mV, and Logger1000 consumes 0.01V',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC3 current': {
            'addr': 8035,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'remarks': 'Logger1000/Logger4000',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'ADC4 current': {
            'addr': 8036,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'remarks': 'Logger1000/Logger4000',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Max. total nominal active power': {
            'addr': 8058,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kW',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Min. total nominal active power': {
            'addr': 8059,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kW',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Max. total nominal reactive power': {
            'addr': 8060,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Min. total nominal reactive power': {
            'addr': 8061,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Inverter preset total active power': {
            'addr': 8066,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kW',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Inverter preset total reactive power': {
            'addr': 8067,
            'count': 1,
            'dtype': 'S16',
            'multiplier': 1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Logger On/Off state': {
            'addr': 8068,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0: Off, 1: On',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Logger unlatch state': {
            'addr': 8069,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0: latched, 1: unlatched',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Total active power': {
            'addr': 8070,
            'count': 4,
            'dtype': 'U64',
            'multiplier': 1,
            'unit': 'W',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Daily yield': {
            'addr': 8074,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Total reactive power': {
            'addr': 8076,
            'count': 4,
            'dtype': 'S64',
            'multiplier': 1,
            'unit': 'var',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Total yield': {
            'addr': 8080,
            'count': 4,
            'dtype': 'U64',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Min. adjustable active power': {
            'addr': 8084,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kW',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Max. adjustable active power': {
            'addr': 8086,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kW',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Min. adjustable reactive power': {
            'addr': 8088,
            'count': 2,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Max. adjustable reactive power': {
            'addr': 8090,
            'count': 2,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Nominal active power': {
            'addr': 8092,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Nominal reactive power': {
            'addr': 8094,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Grid-connected devices': {
            'addr': 8096,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Off-grid devices': {
            'addr': 8097,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Monthly yield of array': {
            'addr': 8098,
            'count': 4,
            'dtype': 'U64',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Annual yield of array': {
            'addr': 8102,
            'count': 4,
            'dtype': 'U64',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy',
            'register_type': RegisterTypes.INPUT_REGISTER},
        'Apparent power of array': {
            'addr': 8106,
            'count': 4,
            'dtype': 'U64',
            'multiplier': 1,
            'unit': 'VA',
            'device_class': 'apparent_power',
            'register_type': RegisterTypes.INPUT_REGISTER
        }
    }

    # Sungrow Logger holding register 
    # The holding register is set to support single function only. All commands from the
    # broadcast address 0 are directly transparently transmitted to the inverter
    logger_holding_registers = {
        'Set the sub-array inverter on and off': {
            'addr': 8002,
            'count': 1,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'register_type': RegisterTypes.HOLDING_REGISTER,
            'remarks': '0: Off\n1: On'
        },
        'Set active power of subarray inverter': {
            'addr': 8003,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kW',
            'device_class': 'power',
            'register_type': RegisterTypes.HOLDING_REGISTER
        },
        'Set active power ratio of subarray inverter': {
            'addr': 8005,
            'count': 2,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': '%',
            'device_class': 'power_factor',
            'register_type': RegisterTypes.HOLDING_REGISTER
        },
        'Set reactive power of subarray inverter': {
            'addr': 8007,
            'count': 2,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power',
            'register_type': RegisterTypes.HOLDING_REGISTER
        },
        'Setting reactive power ratio of subarray inverter': {
            'addr': 8009,
            'count': 2,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': '%',
            'device_class': 'power_factor',
            'register_type': RegisterTypes.HOLDING_REGISTER
        },
        'Set the power factor of subarray inverter': {
            'addr': 8011,
            'count': 2,
            'dtype': 'S32',
            'multiplier': 0.001,
            'unit': '',
            'device_class': 'power_factor',
            'register_type': RegisterTypes.HOLDING_REGISTER
        },
    }

    registers = logger_input_registers



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = SungrowLogger.model              # only 1000b model

    def read_model(self, device_type_code_param_key="Device type code"):
        return super().read_model(device_type_code_param_key)
    
    def setup_valid_registers_for_model(self):
        # only support logger 1000 for now
        return

    def _decoded(cls, content, dtype):
        # def _decode_u16(registers):
        #     """ Unsigned 16-bit big-endian to int """
        #     return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.UINT16)
        
        # def _decode_s16(registers):
        #     """ Signed 16-bit big-endian to int """
        #     return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.INT16)

        # def _decode_u32(registers):
        #     """ Unsigned 32-bit big-endian word"""
        #     return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.UINT32)
        
        # def _decode_s32(registers):
        #     """ Signed 32-bit mixed-endian word"""
        #     return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.INT32)

        # def _decode_utf8(registers):
        #     return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.STRING)

        def _decode_u16(registers):
            """ Unsigned 16-bit big-endian to int """
            return registers[0]
        
        def _decode_s16(registers):
            """ Signed 16-bit big-endian to int """
            sign = 0xFFFF if registers[0] & 0x1000 else 0
            packed = struct.pack('>HH', sign, registers[0])
            return struct.unpack('>i', packed)[0]

        def _decode_u32(registers):
            """ Unsigned 32-bit mixed-endian word"""
            packed = struct.pack('>HH', registers[1], registers[0])
            return struct.unpack('>I', packed)[0]
        
        def _decode_s32(registers):
            """ Signed 32-bit mixed-endian word"""
            packed = struct.pack('>HH', registers[1], registers[0])
            return struct.unpack('>i', packed)[0]
        
        def _decode_u64(registers):
            """ Unsigned 64-bit big-endian word"""
            packed = struct.pack('>HHHH', *registers)
            return struct.unpack('>Q', packed)[0]
        
        def _decode_s64(registers):
            """ Signed 64-bit big-endian word"""
            packed = struct.pack('>HHHH', *registers)
            return struct.unpack('>q', packed)[0]

        def _decode_utf8(registers):
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.STRING)
        
        if dtype == "UTF-8": return _decode_utf8(content)
        elif dtype == "U16": return _decode_u16(content)
        elif dtype == "U32": return _decode_u32(content)
        elif dtype == "U64": return _decode_u64(content)
        elif dtype == "I16" or dtype == "S16": return _decode_s16(content)
        elif dtype == "I32" or dtype == "S32": return _decode_s32(content)
        elif dtype == "I64" or dtype == "S64": return _decode_s64(content)
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

if __name__ == "__main__":
    
    print(SungrowLogger._decoded(SungrowLogger, [0x0304, 0x0102], dtype="U32"))