from server import Server
from sungrow_inverter import SungrowInverter  
from pymodbus.client import ModbusSerialClient
import struct

U16_MAX = 2**16-1

class SungrowLogger(Server):
    
    manufacturer = "Sungrow"
    model = "Logger"

    # Sungrow 1.0.2.7 definitions 04 input registers
    logger_input_registers = {
        'Device type code': {
            'addr': 8000,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0x0705 Logger3000, 0x0710 Logger1000, 0x0718 Logger4000'
        },
        'Protocol number': {
            'addr': 8001,
            'dtype': 'U32',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum'
        },
        'Communication protocol version': {
            'addr': 8003,
            'dtype': 'U32',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum'
        },
        'Total devices connected': {
            'addr': 8005,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum'
        },
        'Total faulty devices': {
            'addr': 8006,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum'
        },
        'Digital input state': {
            'addr': 8021,
            'dtype': 'U32',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': 'Currently only the low 16 bits are used. Logger1000 only uses 8 bits, Logger3000 uses 16 bits, and Logger4000 uses 16 bits'
        },
        'ADC1 voltage': {
            'addr': 8029,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'V',
            'device_class': 'voltage'
        },
        'ADC1 current': {
            'addr': 8030,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'remarks': 'Logger1000/Logger3000'
        },
        'ADC2 voltage': {
            'addr': 8031,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'V',
            'device_class': 'voltage',
            'remarks': 'Logger1000/Logger3000'
        },
        'ADC2 current': {
            'addr': 8032,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current'
        },
        'ADC3 voltage': {
            'addr': 8033,
            'dtype': 'S16',
            'multiplier': '',
            'unit': '',
            'device_class': 'voltage',
            'remarks': 'Logger3000 and Logger1000 share the voltage. Logger3000 consumes 0.01mV, and Logger1000 consumes 0.01V'
        },
        'ADC4 voltage': {
            'addr': 8034,
            'dtype': 'S16',
            'multiplier': '',
            'unit': '',
            'device_class': 'voltage',
            'remarks': 'Logger3000 and Logger1000 share the voltage. Logger3000 consumes 0.01mV, and Logger1000 consumes 0.01V'
        },
        'ADC3 current': {
            'addr': 8035,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'remarks': 'Logger1000/Logger4000'
        },
        'ADC4 current': {
            'addr': 8036,
            'dtype': 'S16',
            'multiplier': 0.01,
            'unit': 'mA',
            'device_class': 'current',
            'remarks': 'Logger1000/Logger4000'
        },
        'Max. total nominal active power': {
            'addr': 8058,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kW',
            'device_class': 'power'
        },
        'Min. total nominal active power': {
            'addr': 8059,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kW',
            'device_class': 'power'
        },
        'Max. total nominal reactive power': {
            'addr': 8060,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Min. total nominal reactive power': {
            'addr': 8061,
            'dtype': 'S16',
            'multiplier': 1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Inverter preset total active power': {
            'addr': 8066,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'kW',
            'device_class': 'power'
        },
        'Inverter preset total reactive power': {
            'addr': 8067,
            'dtype': 'S16',
            'multiplier': 1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Logger On/Off state': {
            'addr': 8068,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0: Off, 1: On'
        },
        'Logger unlatch state': {
            'addr': 8069,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0: latched, 1: unlatched'
        },
        'Total active power': {
            'addr': 8070,
            'dtype': 'U64',
            'multiplier': 1,
            'unit': 'W',
            'device_class': 'power'
        },
        'Daily yield': {
            'addr': 8074,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy'
        },
        'Total reactive power': {
            'addr': 8076,
            'dtype': 'S64',
            'multiplier': 1,
            'unit': 'var',
            'device_class': 'reactive_power'
        },
        'Total yield': {
            'addr': 8080,
            'dtype': 'U64',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy'
        },
        'Min. adjustable active power': {
            'addr': 8084,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kW',
            'device_class': 'power'
        },
        'Max. adjustable active power': {
            'addr': 8086,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kW',
            'device_class': 'power'
        },
        'Min. adjustable reactive power': {
            'addr': 8088,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Max. adjustable reactive power': {
            'addr': 8090,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Nominal active power': {
            'addr': 8092,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'power'
        },
        'Nominal reactive power': {
            'addr': 8094,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Grid-connected devices': {
            'addr': 8096,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum'
        },
        'Off-grid devices': {
            'addr': 8097,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': 'Set',
            'device_class': 'enum'
        },
        'Monthly yield of array': {
            'addr': 8098,
            'dtype': 'U64',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy'
        },
        'Annual yield of array': {
            'addr': 8102,
            'dtype': 'U64',
            'multiplier': 0.1,
            'unit': 'kWh',
            'device_class': 'energy'
        },
        'Apparent power of array': {
            'addr': 8106,
            'dtype': 'U64',
            'multiplier': 1,
            'unit': 'VA',
            'device_class': 'apparent_power'
        }
    }

    # Sungrow Logger holding register 
    # The holding register is set to support single function only. All commands from the
    # broadcast address 0 are directly transparently transmitted to the inverter
    logger_holding_registers = {
        'Set the sub-array inverter on and off': {
            'addr': 8002,
            'dtype': 'U16',
            'multiplier': 1,
            'unit': '',
            'device_class': 'enum',
            'remarks': '0: Off\n1: On'
        },
        'Set active power of subarray inverter': {
            'addr': 8003,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': 'kW',
            'device_class': 'power'
        },
        'Set active power ratio of subarray inverter': {
            'addr': 8005,
            'dtype': 'U32',
            'multiplier': 0.1,
            'unit': '%',
            'device_class': 'power_factor'
        },
        'Set reactive power of subarray inverter': {
            'addr': 8007,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': 'kVar',
            'device_class': 'reactive_power'
        },
        'Setting reactive power ratio of subarray inverter': {
            'addr': 8009,
            'dtype': 'S32',
            'multiplier': 0.1,
            'unit': '%',
            'device_class': 'power_factor'
        },
        'Set the power factor of subarray inverter': {
            'addr': 8011,
            'dtype': 'S32',
            'multiplier': 0.001,
            'unit': '',
            'device_class': 'power_factor'
        },
    }

    # registers = logger_registers



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = SungrowLogger.model              # only 1000b model
        

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

        def _decode_utf8(registers):
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.STRING)
        
        if dtype == "UTF-8": return _decode_utf8(content)
        elif dtype == "U16": return _decode_u16(content)
        elif dtype == "U32": return _decode_u32(content)
        elif dtype == "I16" or dtype == "S16": return _decode_s16(content)
        elif dtype == "I32" or dtype == "S32": return _decode_s32(content)
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