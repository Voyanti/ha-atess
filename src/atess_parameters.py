from enums import DataType
from modbus_types import ModbusParameter, RegisterType


atess_parameters: tuple[ModbusParameter] = (
    ModbusParameter('Serial Number',
            RegisterType.HOLDING_REGISTER,  181, DataType.UTF8, 'None', num_registers=5) ,

    ModbusParameter('Device Type Code',
            RegisterType.HOLDING_REGISTER, 44, DataType.U16, 'None') ,

    ModbusParameter('Device On/Off',
            RegisterType.HOLDING_REGISTER, 1, DataType.U16, 'None') ,

    ModbusParameter('PV Voltage',
            RegisterType.HOLDING_REGISTER, 81, DataType.U16, 'V', multiplier=0.1) ,

    ModbusParameter('PV Current',
            RegisterType.HOLDING_REGISTER, 84, DataType.U16, 'A', multiplier=0.1) ,

    ModbusParameter('Battery Power',
            RegisterType.INPUT_REGISTER, 18, DataType.I16, 'kW', multiplier=0.1) ,

    ModbusParameter('Battery SOC',
            RegisterType.INPUT_REGISTER, 48, DataType.U16, '%') ,

    ModbusParameter('Hardware Version',
            RegisterType.INPUT_REGISTER,  271, DataType.UTF8, 'None', num_registers=10) ,

    ModbusParameter('Battery Voltage',
            RegisterType.INPUT_REGISTER, 2, DataType.I16, 'V', multiplier=0.1) ,

    ModbusParameter('Battery Current',
            RegisterType.INPUT_REGISTER, 3, DataType.I16, 'A', multiplier=0.1) ,

    ModbusParameter('Ambient temperature',
            RegisterType.INPUT_REGISTER, 37, DataType.I16, '°C', multiplier=0.1) ,

    ModbusParameter('BMS Max. Temperature',
            RegisterType.INPUT_REGISTER, 172, DataType.I8H, '°C') ,

    ModbusParameter('BMS Min. Temperature',
            RegisterType.INPUT_REGISTER, 172, DataType.I8L, '°C') ,

    ModbusParameter('BMS Max. Cell Voltage',
            RegisterType.INPUT_REGISTER, 175, DataType.U16, 'mV') ,

    ModbusParameter('BMS Min. Cell Voltage',
            RegisterType.INPUT_REGISTER, 176, DataType.U16, 'mV') ,

    ModbusParameter('Total Battery Discharge Energy',
            RegisterType.INPUT_REGISTER,  69, DataType.U32, 'kWh', num_registers=2, multiplier=0.1) ,

    ModbusParameter('Total Battery Charge Energy',
            RegisterType.INPUT_REGISTER,  73, DataType.U32, 'kWh', num_registers=2, multiplier=0.1) ,

)

# atess_parameters: tuple[ModbusParameter] = (

# )