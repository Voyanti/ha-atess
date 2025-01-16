from server import Server
from pymodbus.client import ModbusSerialClient
import struct

U16_MAX = 2**16-1

class SungrowLogger(Server):
    
    manufacturer = "Sungrow"
    model = "Logger"

    # Read/Write Registers
    rw_registers = {
        'Date&Time': {'addr': 40000, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': '', 'device_class': 'timestamp'},
        'City': {'addr': 40002, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Daylight Saving Time': {'addr': 40004, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Transfer trip': {'addr': 40204, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Active adjustment': {'addr': 40420, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kW', 'device_class': 'power'},
        'Reactive adjustment': {'addr': 40422, 'count': 2, 'dtype': 'S32', 'multiplier': 10, 'unit': 'kVar', 'device_class': 'reactive_power'},
        'Active adjustment 2': {'addr': 40424, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kW', 'device_class': 'power'},
        'Reactive adjustment 2': {'addr': 40426, 'count': 2, 'dtype': 'S32', 'multiplier': 10, 'unit': 'kVar', 'device_class': 'reactive_power'},
        'Active power adjustment by percentage': {'addr': 40428, 'count': 1, 'dtype': 'U16', 'multiplier': 10, 'unit': '%', 'device_class': 'power'},
        'Power factor adjustment': {'addr': 40429, 'count': 1, 'dtype': 'S16', 'multiplier': 1000, 'unit': '', 'device_class': 'power_factor'},
        'CO2 emission reduction coefficient': {'addr': 41124, 'count': 1, 'dtype': 'U16', 'multiplier': 1000, 'unit': 'kg/kWh', 'device_class': 'enum'},
        'Communication abnormal shutdown': {'addr': 41947, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Communication abnormal detection time': {'addr': 41948, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': 's', 'device_class': 'duration'},
        'Auto start upon communication recovery': {'addr': 41949, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'SystemTime: year': {'addr': 42017, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'date'},
        'SystemTime: month': {'addr': 42018, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'date'},
        'SystemTime: day': {'addr': 42019, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'date'},
        'SystemTime: hour': {'addr': 42020, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'date'},
        'SystemTime: minute': {'addr': 42021, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'date'},
        'SystemTime: second': {'addr': 42022, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'date'},
        'Current error during scanning': {'addr': 42150, 'count': 1, 'dtype': 'U16', 'multiplier': 100, 'unit': '', 'device_class': 'enum'}
    }

    # Write Only Registers
    wo_registers = {
        'Power on': {'addr': 40200, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Power off': {'addr': 40201, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Power on/off': {'addr': 40202, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Power on/off 2': {'addr': 40203, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Array reset': {'addr': 40205, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'System reset': {'addr': 40723, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Fast device access': {'addr': 40724, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Device operation': {'addr': 40725, 'count': 11, 'dtype': 'MLD', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Inspection': {'addr': 42730, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'IV curve scanning': {'addr': 42779, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'}
    }

    # Read Only Registers
    # ro_registers = {
    #     # 'Time Zone': {'addr': 40005, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 's', 'device_class': 'duration'},
    #     # 'DST state': {'addr': 40007, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     # 'DST offset': {'addr': 40008, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': 'mins', 'device_class': 'duration'},
    #     # 'E-Daily': {'addr': 40562, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kWh', 'device_class': 'energy'},
    #     # 'E-Total': {'addr': 40560, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kWh', 'device_class': 'energy'},
    #     # 'Local Time': {'addr': 40009, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': '', 'device_class': 'timestamp'}
    # }

    #     'DC current': {'addr': 40500, 'count': 1, 'dtype': 'S16', 'multiplier': 10, 'unit': 'A', 'device_class': 'current'},
    #     'Input power': {'addr': 40521, 'count': 2, 'dtype': 'U32', 'multiplier': 1000, 'unit': 'kW', 'device_class': 'power'},
    #     'CO2 reduction': {'addr': 40523, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kg', 'device_class': 'weight'},
    #     'Active power': {'addr': 40525, 'count': 2, 'dtype': 'S32', 'multiplier': 1000, 'unit': 'kW', 'device_class': 'power'},
    #     'Power factor': {'addr': 40532, 'count': 1, 'dtype': 'S16', 'multiplier': 1000, 'unit': '', 'device_class': 'power_factor'},
    #     'Plant status': {'addr': 40543, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Reactive power': {'addr': 40544, 'count': 2, 'dtype': 'S32', 'multiplier': 1000, 'unit': 'kVar', 'device_class': 'reactive_power'},
    #     'CO2 reduction 2': {'addr': 40550, 'count': 4, 'dtype': 'U64', 'multiplier': 100, 'unit': 'kg', 'device_class': 'weight'},
    #     'DC current 2': {'addr': 40554, 'count': 2, 'dtype': 'S32', 'multiplier': 10, 'unit': 'A', 'device_class': 'current'},
    #     'Duration of daily power generation': {'addr': 40564, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'h', 'device_class': 'duration'},
    #     'Phase A current': {'addr': 40572, 'count': 1, 'dtype': 'S16', 'multiplier': 1, 'unit': 'A', 'device_class': 'current'},
    #     'Phase B current': {'addr': 40573, 'count': 1, 'dtype': 'S16', 'multiplier': 1, 'unit': 'A', 'device_class': 'current'},
    #     'Phase C current': {'addr': 40574, 'count': 1, 'dtype': 'S16', 'multiplier': 1, 'unit': 'A', 'device_class': 'current'},
    #     'Uab': {'addr': 40575, 'count': 1, 'dtype': 'U16', 'multiplier': 10, 'unit': 'V', 'device_class': 'voltage'},
    #     'Ubc': {'addr': 40576, 'count': 1, 'dtype': 'U16', 'multiplier': 10, 'unit': 'V', 'device_class': 'voltage'},
    #     'Uca': {'addr': 40577, 'count': 1, 'dtype': 'U16', 'multiplier': 10, 'unit': 'V', 'device_class': 'voltage'},
    #     'Inverter Efficiency': {'addr': 40685, 'count': 1, 'dtype': 'U16', 'multiplier': 100, 'unit': '%', 'device_class': 'enum'},
    #     'Max. reactive adjustment': {'addr': 40693, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kVar', 'device_class': 'reactive_power'},
    #     'Min. reactive adjustment': {'addr': 40695, 'count': 2, 'dtype': 'S32', 'multiplier': 10, 'unit': 'kVar', 'device_class': 'reactive_power'},
    #     'Max. active adjustment': {'addr': 40697, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kW', 'device_class': 'power'},
    #     'Locked': {'addr': 40699, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'DI status': {'addr': 40700, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'ESN': {'addr': 40713, 'count': 10, 'dtype': 'UTF-8', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Device access status': {'addr': 40736, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Active power control mode': {'addr': 40737, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Active power scheduling target value': {'addr': 40738, 'count': 2, 'dtype': 'U32', 'multiplier': 10, 'unit': 'kW', 'device_class': 'power'},
    #     'Reactive power control mode': {'addr': 40740, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Reactive power scheduling curve mode': {'addr': 40741, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Reactive power scheduling target value': {'addr': 40742, 'count': 2, 'dtype': 'S32', 'multiplier': 10, 'unit': 'kVar', 'device_class': 'reactive_power'},
    #     'Active scheduling percentage': {'addr': 40802, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': '%', 'device_class': 'power'},
    #     'PV module capacity': {'addr': 41934, 'count': 2, 'dtype': 'U32', 'multiplier': 1000, 'unit': 'kW', 'device_class': 'power'},
    #     'Rated plant capacity': {'addr': 41936, 'count': 2, 'dtype': 'U32', 'multiplier': 1000, 'unit': 'kW', 'device_class': 'power'},
    #     'Total rated capacity of grid-connected inverters': {'addr': 41938, 'count': 2, 'dtype': 'U32', 'multiplier': 1000, 'unit': 'kW', 'device_class': 'power'},
    #     'Conversion coefficient': {'addr': 41940, 'count': 2, 'dtype': 'U32', 'multiplier': 1000, 'unit': '', 'device_class': 'enum'},
    #     'Communication status': {'addr': 41942, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Alarm Info 1': {'addr': 50000, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
    #     'Alarm Info 2': {'addr': 50001, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'}
    # }

    registers = {
        'Serial Number': {'addr': 4990, 'count': 10, 'dtype': 'UTF-8', 'multiplier': 1, 'unit': '',  'device_class': 'enum'},
        'Device Type Code': {'addr': 5000, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Nominal Active Power': {'addr': 5001, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'kW', 'device_class': 'power'},
        'Output Type': {'addr': 5002, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},

        'Daily Power Yields': {'addr': 5003, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Total Power Yields': {'addr': 5004, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'kWh', 'device_class': 'energy'},
        'Total Running Time': {'addr': 5006, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'h', 'device_class': 'duration'},
        'Internal Temperature': {'addr': 5008, 'count': 1, 'dtype': 'S16', 'multiplier': 0.1, 'unit': '°C', 'device_class': 'temperature'},
        'Total Apparent Power': {'addr': 5009, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'VA', 'device_class': 'apparent_power'},
        'MPPT 1 Voltage': {'addr': 5011, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 1 Current': {'addr': 5012, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 2 Voltage': {'addr': 5013, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 2 Current': {'addr': 5014, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 3 Voltage': {'addr': 5015, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 3 Current': {'addr': 5016, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'Total DC Power': {'addr': 5017, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'A-B Line Voltage/Phase A Voltage': {'addr': 5019, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},              # 5019-5021 two output types check TODO
        'B-C Line Voltage/Phase B Voltage': {'addr': 5020, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'C-A Line Voltage/Phase C Voltage': {'addr': 5019, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'Phase A Current': {'addr': 5022, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'Phase B Current': {'addr': 5023, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'Phase C Current': {'addr': 5024, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'Total Active Power': {'addr': 5031, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Total Reactive Power': {'addr': 5033, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'var', 'device_class': 'reactive_power'},
        'Power Factor': {'addr': 5035, 'count': 1, 'dtype': 'S16', 'multiplier': 0.001, 'unit': 'no unit of measurement', 'device_class': 'power_factor'},                # >0: leading, <0 lagging
        'Grid Frequency': {'addr': 5036, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'Hz', 'device_class': 'frequency'},
        'Work State': {'addr': 5038, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Fault/Alarm Code 1': {'addr': 5045, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},

        'Nominal Reactive Power': {'addr': 5049, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'kVar', 'device_class': 'reactive_power'},
        'Array Insulation Resistance': {'addr': 5071, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': 'kΩ',  'device_class': 'enum'},
        'Active Power Regulation Setpoint': {'addr': 5077, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Reactive Power Regulation Setpoint': {'addr': 5079, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 'Var', 'device_class': 'reactive_power'},

        'Work State (Extended)': {'addr': 5081, 'count': 2, 'dtype': 'U32', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'Meter Power': {'addr': 5083, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Meter A Phase Power': {'addr': 5085, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Meter B Phase Power': {'addr': 5087, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Meter C Phase Power': {'addr': 5089, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Load Power': {'addr': 5091, 'count': 2, 'dtype': 'S32', 'multiplier': 1, 'unit': 'W', 'device_class': 'power'},
        'Daily Export Energy': {'addr': 5093, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Total Export Energy': {'addr': 5095, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Daily Import Energy': {'addr': 5097, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Total Import Energy': {'addr': 5099, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Daily Direct Energy Consumption': {'addr': 5101, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Total Direct Energy Consumption': {'addr': 5103, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Daily Running Time': {'addr': 5113, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': 'min', 'device_class': 'duration'},

        'Present Country': {'addr': 5114, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},

        'MPPT 4 Voltage': {'addr': 5115, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 4 Current': {'addr': 5116, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 5 Voltage': {'addr': 5117, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 5 Current': {'addr': 5118, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 6 Voltage': {'addr': 5119, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 6 Current': {'addr': 5120, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 7 Voltage': {'addr': 5121, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 7 Current': {'addr': 5122, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 8 Voltage': {'addr': 5123, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 8 Current': {'addr': 5124, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'Monthly Power Yields': {'addr': 5128, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'MPPT 9 Voltage': {'addr': 5130, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 9 Current': {'addr': 5131, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 10 Voltage': {'addr': 5132, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 10 Current': {'addr': 5133, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 11 Voltage': {'addr': 5134, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 11 Current': {'addr': 5135, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'MPPT 12 Voltage': {'addr': 5136, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'MPPT 12 Current': {'addr': 5137, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'A', 'device_class': 'current'},
        'Total Power Yields (Increased Accuracy)': {'addr': 5144, 'count': 2, 'dtype': 'U32', 'multiplier': 0.1, 'unit': 'kWh', 'device_class': 'energy'},
        'Negative Voltage to the Ground': {'addr': 5146, 'count': 1, 'dtype': 'S16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'Bus Voltage': {'addr': 5147, 'count': 1, 'dtype': 'U16', 'multiplier': 0.1, 'unit': 'V', 'device_class': 'voltage'},
        'Grid Frequency (Increased Accuracy)': {'addr': 5148, 'count': 1, 'dtype': 'U16', 'multiplier': 0.01, 'unit': 'Hz', 'device_class': 'frequency'},
        'PID Work State': {'addr': 5150, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'},
        'PID Alarm Code': {'addr': 5151, 'count': 1, 'dtype': 'U16', 'multiplier': 1, 'unit': '', 'device_class': 'enum'}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = SungrowLogger.model              # only 1000b model
        

    def _decoded(cls, content, dtype):
        def _decode_u16(registers):
            """ Unsigned 16-bit big-endian to int """
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.UINT16)
        
        def _decode_s16(registers):
            """ Signed 16-bit big-endian to int """
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.INT16)

        def _decode_u32(registers):
            """ Unsigned 32-bit big-endian word"""
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.UINT32)
        
        def _decode_s32(registers):
            """ Signed 32-bit mixed-endian word"""
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.INT32)

        def _decode_utf8(registers):
            return ModbusSerialClient.convert_from_registers(registers=registers, data_type=ModbusSerialClient.DATATYPE.STRING)
        
        if dtype == "UTF-8": return _decode_utf8(content)
        elif dtype == "U16": return _decode_u16(content)
        elif dtype == "U32": return _decode_u32(content)
        elif dtype == "S16": return _decode_s16(content)
        elif dtype == "S32": return _decode_s32(content)
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
