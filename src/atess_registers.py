from dataclasses import dataclass
from typing import Literal, Set, overload

from .enums import (
    DataType,
    DeviceClass,
    HAEntityType,
    Parameter,
    RegisterTypes,
    WriteParameter,
    WriteSelectParameter,
)

import logging
from .fault_key_validator import coerce_fault_name_key

logger = logging.getLogger(__name__)

ATESS_DEVICE_GROUP = Literal["PCS", "PBD", "HPS"]


@dataclass
class ParamWrapped:
    param_name: str
    param: Parameter | WriteParameter | WriteSelectParameter
    included_groups: Set[ATESS_DEVICE_GROUP] | None  # None = applicable to all groups
    is_write_param: bool


@dataclass
class ParamRegistry:
    registry: list[ParamWrapped]

    @overload
    def build_map(
        self, group: ATESS_DEVICE_GROUP, is_write_map: Literal[False] = False
    ) -> dict[str, Parameter]: ...
    @overload
    def build_map(
        self, group: ATESS_DEVICE_GROUP, is_write_map: Literal[True]
    ) -> dict[str, WriteParameter | WriteSelectParameter]: ...

    def build_map(self, group: ATESS_DEVICE_GROUP, is_write_map: bool = False):
        m: dict[str, Parameter | WriteParameter | WriteSelectParameter] = {}
        for r in self.registry:
            device_in_group = r.included_groups is None or group in r.included_groups
            should_include = (is_write_map == r.is_write_param) and device_in_group

            if should_include:
                m = m | {r.param_name: r.param}

        return m


not_PCS_parameters: dict[str, Parameter] = {
    # All except PCS
    "PV1 Voltage": {
        "addr": 0 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV1 DC Current": {
        "addr": 3 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV1 Power": {
        "addr": 51 + 1,
        "count": 1,
        "dtype": DataType.I16,  # Unsigned according to protocol, but observation says otherwise
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV Daily Power Generation": {
        "addr": 62 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total_increasing",
    },
    "Total PV Generation": {
        "addr": 64 + 1,
        "count": 2,
        "dtype": DataType.U32,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total_increasing",
    },
}
atess_parameters: dict[str, Parameter] = {
    ###############################
    # Available on all models:
    ###############################
    "Serial Number": {
        "addr": 180 + 1,
        "count": 5,
        "dtype": DataType.UTF8,
        "device_class": DeviceClass.ENUM,
        "multiplier": 1,
        "unit": "",
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },  # TODO count 5? p30
    # "Software Version": {
    #     "addr": 280 + 1,
    #     "count": 20,
    #     "dtype": DataType.UTF8,
    #     "device_class": DeviceClass.ENUM,
    #     "multiplier": 1,
    #     "unit": "",
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    "Device Type Code": {
        "addr": 43 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "device_class": DeviceClass.ENUM,
        "multiplier": 1,
        "unit": "",
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    # On/Off State
    "Device On/Off": {
        "addr": 0 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    # Voltage and Current Measurements
    "PV Voltage": {  # 0 on PCS
        "addr": 80 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    "PV Current": {  # constant on PCS500
        "addr": 83 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    "Battery Power": {  # checked
        "addr": 17 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Battery SOC": {  # checked
        "addr": 47 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "device_class": DeviceClass.BATTERY,
        "multiplier": 1,
        "unit": "%",
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "measurement",
    },
    # Input registers
    "Hardware Version": {
        "addr": 270 + 1,
        "count": 10,
        "dtype": DataType.UTF8,
        "device_class": DeviceClass.ENUM,
        "multiplier": 1,
        "unit": "",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Battery Voltage": {  # checked
        "addr": 1 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Battery Current": {  # checked
        "addr": 2 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Max Charge Current": Parameter(  # ALL
        addr=100 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        device_class=DeviceClass.CURRENT,
        register_type=RegisterTypes.INPUT_REGISTER,
        unit="A",
    ),
    "BMS Max Discharge Current": Parameter(  # ALL
        addr=101 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.INPUT_REGISTER,
        device_class=DeviceClass.CURRENT,
        unit="A",
    ),
    ###############################
    "Ambient temperature": {
        "addr": 36 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "device_class": DeviceClass.TEMPERATURE,
        "multiplier": 0.1,
        "unit": "°C",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # stored as two signed 8 bit ints inside a 16 bit register:
    "BMS Max. Temperature": {
        "addr": 171 + 1,
        "count": 1,
        "dtype": DataType.I8H,
        "device_class": DeviceClass.TEMPERATURE,
        "multiplier": 1,
        "unit": "°C",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Min. Temperature": {
        "addr": 171 + 1,
        "count": 1,
        "dtype": DataType.I8L,
        "device_class": DeviceClass.TEMPERATURE,
        "multiplier": 1,
        "unit": "°C",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Max. Cell Voltage": {  # checked
        "addr": 174 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "mV",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Min. Cell Voltage": {  # checked
        "addr": 175 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "mV",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Total Battery Discharge Energy": {  # checked
        "addr": 68 + 1,
        "count": 2,
        "dtype": DataType.U32,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total_increasing",
    },
    "Total Battery Charge Energy": {  # checked
        "addr": 72 + 1,
        "count": 2,
        "dtype": DataType.U32,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total_increasing",
    },
    "Float Charging Voltage": {
        "addr": 156 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "mV",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    "Float Charging Current": {
        "addr": 163 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 10,
        "unit": "mA",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    "Single PV to Off-grid": {
        "addr": 161 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "mV",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
}


PCS_parameters: dict[str, Parameter] = {  # battery inverters
    "System battery current": {
        "addr": 162 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "device_class": DeviceClass.CURRENT,
        "multiplier": 0.1,
        "unit": "A",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "System battery power": {
        "addr": 228 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "device_class": DeviceClass.POWER,
        "multiplier": 0.1,
        "unit": "kW",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "CP Power Limit": {
        "addr": 229 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "device_class": DeviceClass.POWER,
        "multiplier": 0.1,
        "unit": "kW",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Transformer temperature": {
        "addr": 35 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "device_class": DeviceClass.TEMPERATURE,
        "multiplier": 0.1,
        "unit": "°C",
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # "Battery Discharge Cutoff": { #
    #     "addr": 47 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "device_class": DeviceClass.ENUM,
    #     "multiplier": 1,
    #     "unit": "%",
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    "Frequency Shift Enable": {
        "addr": 79 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "device_class": DeviceClass.ENUM,
        "multiplier": 1,
        "unit": "",
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },  # 0: false, 1 = mode1, 2= mode2
    "Power factor symbol": {
        "addr": 22 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Power factor": {
        "addr": 23 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.001,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # "Charge Current Limit": {
    #     "addr": 154 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "device_class": DeviceClass.CURRENT,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    #     "min": 0,
    #     "max": 10000,
    # },
    # "Discharge Current Limit": {
    #     "addr": 155 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "device_class": DeviceClass.CURRENT,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    #     "min": 0,
    #     "max": 10000,
    # },
    "Charge Cutoff SOC": {
        "addr": 178 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "device_class": DeviceClass.BATTERY,
        "multiplier": 1,
        "unit": "%",
        "register_type": RegisterTypes.HOLDING_REGISTER,
        # "min": 0,
        # "max": 100,
    },
    # PCS
    "Output Voltage UV": {
        "addr": 4 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Voltage VW": {
        "addr": 5 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Voltage WU": {
        "addr": 6 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Bypass Current U": {
        "addr": 7 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Bypass Current V": {
        "addr": 8 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Bypass Current W": {
        "addr": 9 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Inductance Current A": {
        "addr": 10 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Inductance Current B": {
        "addr": 11 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Inductance Current C": {
        "addr": 12 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Grid Bypass Voltage UV": {
        "addr": 13 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Grid Bypass Voltage VW": {
        "addr": 14 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Grid Bypass Voltage WU": {
        "addr": 15 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Bypass Frequency": {
        "addr": 81 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.01,
        "unit": "Hz",
        "device_class": DeviceClass.FREQUENCY,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Frequency": {
        "addr": 16 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.01,
        "unit": "Hz",
        "device_class": DeviceClass.FREQUENCY,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Bypass Apparent Power": {  # fout
        "addr": 18 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "",
        "device_class": DeviceClass.APPARENT_POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Bypass Active Power": {  # fout
        "addr": 19 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "measurement",
    },
    "Bypass Reactive Power": {  # fout
        "addr": 20 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "",
        "device_class": DeviceClass.REACTIVE_POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Grid Frequency": {
        "addr": 21 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.01,
        "unit": "Hz",
        "device_class": DeviceClass.FREQUENCY,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Grid State": {
        "addr": 28 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "remarks": "0: abnormal, 1: normal",
    },
    "Output Apparent Power": {
        "addr": 78 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "",
        "device_class": DeviceClass.APPARENT_POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Active Power": {
        "addr": 79 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Reactive Power": {
        "addr": 80 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "",
        "device_class": DeviceClass.REACTIVE_POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Daily Power Consumption": {  # fout
        "addr": 82 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Daily Power From Grid": {  # checked
        "addr": 88 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Daily Power To Grid": {  # checked
        "addr": 94 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Current U": {  # checked TODO load vs output current
        "addr": 135 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Current V": {  # checked
        "addr": 136 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Current W": {  # checked
        "addr": 137 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # HPS/PCS/HPSTL model registers
    "Load Apparent Power": {
        "addr": 48 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "",
        "device_class": DeviceClass.APPARENT_POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Load Active Power": {
        "addr": 49 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Load Reactive Power": {
        "addr": 50 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "",
        "device_class": DeviceClass.REACTIVE_POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Load Power Factor": {
        "addr": 52 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.001,
        "unit": "",
        "device_class": DeviceClass.POWER_FACTOR,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Load Current U": {  # load current u on inverter disp
        "addr": 53 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Load Current V": {  # load current v on inverter disp
        "addr": 54 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Load Current W": {  # load current w on inverter disp
        "addr": 55 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Voltage U": {
        "addr": 56 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Voltage V": {
        "addr": 57 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Voltage W": {
        "addr": 58 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Total Grid Import": {
        "addr": 90 + 1,
        "count": 2,
        "dtype": DataType.U32,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total",
    },
    "Total Grid Export": {
        "addr": 96 + 1,
        "count": 2,
        "dtype": DataType.U32,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total",
    },
    "Total Load Energy": {
        "addr": 84 + 1,
        "count": 2,
        "dtype": DataType.U32,
        "multiplier": 0.1,
        "unit": "kWh",
        "device_class": DeviceClass.ENERGY,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "state_class": "total",
    },
    "BMS Battery Status": {
        "addr": 176 + 1,
        "count": 1,
        "dtype": DataType.U8H,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "value_template": """
                            {% set states = {
                            '0': 'Hold',
                            '1': 'Charging and discharging disable',
                            '2': 'Charging disable',
                            '3': 'Discharging disable',
                            '4': 'Charging',
                            '5': 'Discharging'
                            } %}
                            {{ states[value] if value in states else 'unknown' }}
                            """,
    },
    "BMS System Status": {
        "addr": 176 + 1,
        "count": 1,
        "dtype": DataType.U8L,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Running State": {
        "addr": 180 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "value_template": """
                        {% set states = {
                        '0': 'Waiting',
                        '1': 'Inspection',
                        '2': 'On-Grid',
                        '3': 'Fault',
                        '4': 'Permanentfault',
                        '5': 'Off-Grid',
                        '6': 'Single PV mode',
                        '7': 'Switch-to-off-grid',
                        '8': 'Switch-to-on-grid'
                        } %}
                        {{ states[value] if value in states else 'unknown' }}
                        """,
    },
    # PCS Input Registers 181-190 (Atess Modbus RTU v3.22)
    # TODO: also applicable to HPS inverters
    # PCS Fault Alarm registers 181-188 are decoded separately via PCS_FAULT_ALARM_BITS
    # and published as a single "PCS Active Faults" entity (see decode_pcs_faults)
    "Fault Alarm 1": {
        "addr": 181 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 2": {
        "addr": 182 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 3": {
        "addr": 183 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 4": {
        "addr": 184 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 5": {
        "addr": 185 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 6": {
        "addr": 186 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 7": {
        "addr": 187 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Fault Alarm 8": {
        "addr": 188 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # Register 189 is reserved
    "Operation Mode": {
        "addr": 192 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "value_template": """
                        {% set modes = {
                        '0': 'Peak',
                        '1': 'Flat',
                        '2': 'Valley',
                        '3': 'DG',
                        '4': 'Battery First',
                        '5': 'Load First',
                        '6': 'Peak Shaving',
                        '7': 'Time Schedule',
                        '8': 'EMS Mode',
                        '9': 'DC Source Mode',
                        '10': 'Manual Dispatching',
                        '11': 'Battery Protection',
                        '12': 'Backup Power Management',
                        '13': 'PCS Dispatching',
                        '14': 'Forced Charging',
                        '15': 'Smart Meter Mode',
                        '16': 'Bat-Smart Meter',
                        '17': 'Grid Access Control'
                        } %}
                        {{ modes[value] if value in modes else 'unknown' }}
                        """,
    },
    "Running State Bitwise": {
        "addr": 190 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Level 1 Alarm": {
        "addr": 177 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Level 2 Alarm": {
        "addr": 178 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Level 3 Protection": {
        "addr": 179 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Max V Group Nr": {
        "addr": 168 + 1,
        "count": 1,
        "dtype": DataType.U8H,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Min V Group Nr": {
        "addr": 168 + 1,
        "count": 1,
        "dtype": DataType.U8L,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Min V Unit Nr": {
        "addr": 172 + 1,
        "count": 1,
        "dtype": DataType.U8H,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Min V Unit Box Nr": {
        "addr": 172 + 1,
        "count": 1,
        "dtype": DataType.U8L,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Max V Unit Nr": {
        "addr": 173 + 1,
        "count": 1,
        "dtype": DataType.U8H,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Max V Unit Box Nr": {
        "addr": 173 + 1,
        "count": 1,
        "dtype": DataType.U8L,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Total Voltage": {
        "addr": 164 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "BMS Total Current": {
        "addr": 165 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
}
# TODO bypass p 37 atess-modbus-rtu-protocol-v37.pdf

PBD_parameters: dict[str, Parameter] = {
    # PBD
    "PV2 Voltage": {
        "addr": 105 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV2 DC Current": {
        "addr": 106 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV2 Power": {
        "addr": 107 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV Total Power": {
        "addr": 108 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Voltage": {
        "addr": 109 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Current": {
        "addr": 110 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "Output Power": {
        "addr": 113 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV Module Temperature": {  # 0 on PCS
        "addr": 114 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 0.1,
        "unit": "°C",
        "device_class": DeviceClass.TEMPERATURE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV3 Voltage": {
        "addr": 123 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV4 Voltage": {
        "addr": 124 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV5 Voltage": {
        "addr": 125 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "V",
        "device_class": DeviceClass.VOLTAGE,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV3 DC Current": {
        "addr": 126 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV4 DC Current": {
        "addr": 127 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV5 DC Current": {
        "addr": 128 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "A",
        "device_class": DeviceClass.CURRENT,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV3 Power": {
        "addr": 132 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV4 Power": {
        "addr": 133 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PV5 Power": {
        "addr": 134 + 1,
        "count": 1,
        "dtype": DataType.I16,
        "multiplier": 0.1,
        "unit": "kW",
        "device_class": DeviceClass.POWER,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # PBD Input Registers 206-215 (Atess Modbus RTU v3.22)
    "PBD Running State": {
        "addr": 206 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "value_template": """
                        {% set states = {
                        '0': 'Hold',
                        '1': 'Check',
                        '2': 'Run',
                        '3': 'Error',
                        '4': 'Permanent Error',
                        '6': 'Single PV mode'
                        } %}
                        {{ states[value] if value in states else 'unknown' }}
                        """,
    },
    "PBD Fault Alarm 1": {
        "addr": 207 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PBD Fault Alarm 2": {
        "addr": 208 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PBD Fault Alarm 3": {
        "addr": 209 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PBD Fault Alarm 4": {
        "addr": 210 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PBD Fault Alarm 5": {
        "addr": 211 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PBD Fault Alarm 6": {
        "addr": 212 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    "PBD Running State Bitwise": {
        "addr": 213 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
    },
    # Register 214 is reserved
    "PBD Operation Mode": {
        "addr": 215 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.INPUT_REGISTER,
        "value_template": """
                        {% set modes = {
                        '0': 'Normal',
                        '1': 'EMS Mode'
                        } %}
                        {{ modes[value] if value in modes else 'unknown' }}
                        """,
    },
}

# Fault Alarm Bit Information (Atess Modbus RTU v3.22, Figures 4.3.2 - 4.3.9)
# PCS Input Registers 181-188, byte-swapped before decoding
# Each dict maps bit position (D0-D15) to fault name
PCS_FAULT_ALARM_BITS: dict[int, dict[int, str]] = {
    1: {  # Figure 4.3.2 - Fault alarm bit information 1 (register 181)
        0: "PV_Inverse_Failure",
        1: "IGBT_Failure",
        2: "EEPROM_Write_Failure",
        3: "EEPROM_Read_Failure",
        4: "AC_MainContactor_Failure",
        5: "AC_SlaveContactor_Failure",
        6: "GFDI_Failure",
        7: "GFCI_Failure",
        8: "RISO_Failure",
    },
    2: {  # Figure 4.3.3 - Fault alarm bit information 2 (register 182)
        0: "PV_VoltHigh_Fault",
        1: "CANb_Communication_Fault",
        2: "PV_CurrHigh_Fault",
        3: "BMS_Communication_Fault",
        4: "PV_Insulation_Fault",
        5: "BMS_Fault",
        6: "DC_OCP_Fault",
        7: "Fire_Fault",
        8: "INT_PV_OverVolt_Fault",
        9: "PBD250_Communication_Fault",
        10: "INT_PV_OverCurr_Fault",
        11: "EMS_Communication_Fault",
        12: "IGBT_Converter_Fault",
        13: "IGBT_Buck_Fault",
        14: "Converter_L_OCP_Fault",
        15: "Buck_L_OCP_Fault",
    },
    3: {  # Figure 4.3.4 - Fault alarm bit information 3 (register 183)
        0: "AC_NoUtility_Fault",
        1: "AC_GridPhaseSeque_Fault",
        2: "AC_PLL_Fault",
        3: "AC_Volt_Unbalance_Fault",
        4: "AC_Curr_Unbalance_Fault",
        8: "AC_WU_OverVolt_Fault",
        9: "AC_WU_UnderVolt_Fault",
        10: "AC_VW_OverVolt_Fault",
        11: "AC_VW_UnderVolt_Fault",
        12: "AC_UV_OverVolt_Fault",
        13: "AC_UV_UnderVolt_Fault",
        14: "AC_OverFreq_Fault",
        15: "AC_UnderFreq_Fault",
    },
    4: {  # Figure 4.3.5 - Fault alarm bit information 4 (register 184)
        0: "AC_GridCurr_DcHigh_Fault",
        1: "Converter_LCurr_DcHigh_Fault",
        2: "Buck_LCurr_DcHigh_Fault",
        3: "GridCurr_High_Fault",
        4: "Converter_LCurr_High_Fault",
        5: "Buck_LCurr_High_Fault",
        6: "AC_Overload_Fault",
        7: "AC_Lightload_Fault",
        8: "AC_BackFeed_Fault",
        9: "LVRT_Fault",
        10: "Converter_Module_OverTemp_Fault",
        11: "Buck_Module_OverTemp_Fault",
        12: "Converter_L_OverTemp_Fault",
        13: "Buck_L_OverTemp_Fault",
        14: "Transformer_OverTemp_Fault",
        15: "LowTemp_Fault",
    },
    5: {  # Figure 4.3.6 - Fault alarm bit information 5 (register 185)
        0: "EPO_Stop",
        1: "KeyEmergencyStop",
        2: "LcdEmergencyStop",
        3: "CP_Communication_Fault",
        4: "AC_MainContactor_Fault",
        5: "DC_MainContactor_Fault",
        6: "PBD350_Communication_Fault",
        7: "AC_SlaveContactor_Fault",
        8: "GFDI_Ground_Fault",
        9: "GFDI_HallSense_Fault",
        10: "GFDI_AirSwitch_Fault",
        11: "PV_Thunder_Fault",
        12: "AC_Thunder_Fault",
        13: "BAT_Thunder_Fault",
        14: "Converter_L_Rly_Fault",
        15: "Buck_L_Rly_Fault",
    },
    6: {  # Figure 4.3.7 - Fault alarm bit information 6 (register 186)
        0: "DC_GFDI_Fault",
        1: "AC_GFDI_Fault",
        2: "PV_RISO_Fault",
        3: "BAT_RISO_Fault",
        4: "DC_GFCI_Fault",
        5: "AC_GFCI_Fault",
        6: "DC_Fuse_Fault",
        7: "AC_Fuse_Fault",
        8: "DC_SoftStart_Fault",
        9: "INV_SoftStart_Fault",
        10: "INT_ConverterL_OverCurr_Fault",
        11: "INT_BuckL_OverCurr_Fault",
        12: "Batt_OverVolt_Fault",
        13: "Batt_UnderVolt_Fault",
        14: "Batt_OverCurr_Fault",
        15: "Batt_OverCharge_Fault",
    },
    7: {  # Figure 4.3.8 - Fault alarm bit information 7 (register 187)
        0: "Fault_Feedback_Warning",
        1: "Fan_Buck_Fault_Warning",
        2: "Fan_Inv_Fault_Warning",
        3: "Parallel_Uneven_Flow_Warning",
        4: "Temp_Derating_Warning",
        5: "Batt_UnderVolt_Warning",
        6: "DCFuseOp_Alarm_Warning",
        7: "ACFuseOp_Alarm_Warning",
        8: "AC_WU_OverVolt_Rmt_Warning",
        9: "AC_WU_UnderVolt_Rmt_Warning",
        10: "AC_VW_OverVolt_Rmt_Warning",
        11: "AC_VW_UnderVolt_Rmt_Warning",
        12: "AC_UV_OverVolt_Rmt_Warning",
        13: "AC_UV_UnderVolt_Rmt_Warning",
        14: "AC_OverFreq_Rmt_Warning",
        15: "AC_UnderFreq_Rmt_Warning",
    },
    8: {  # Figure 4.3.9 - Fault alarm bit information 8 (register 188)
        0: "Batt_UnderVolt_Protect_Warning",
        1: "TimeSet_Warning",
        2: "Bypass_Contactor_Warning",
        3: "Bypass_Inter_Comm_Warning",
        4: "Bypass_Volt_different_Warning",
        5: "PBD_Communication_Warning",
        6: "Meter_Communication_Warning",
        8: "PBD250_Fault",
        9: "PBD350_Fault",
        10: "CP_Fault",
        11: "CANb_Communication_Fault",
        14: "Parallel_PLL_Signal_Fault",
        15: "Parallel_Sync_Signal_Fault",
    },
}


PBD_FAULT_ALARM_BITS: dict[int, dict[int, str]] = {
    1: {  # Figure 6.3.2 - Fault alarm bit information 1
        0: "PV_Inverse_Failure",
        1: "IGBT_Failure",
        2: "EEPROM_Write_Failure",
        3: "EEPROM_Read_Failure",
        4: "MainContactor_Failure",
        5: "SlaveContactor_Failure",
        6: "RISO_Failure",
        # 7: "Reseverd_Failure",
        8: "PV1_VoltHigh_Fault",
        9: "PV2_VoltHigh_Fault",
        10: "PV1_CurrHigh_Fault",
        11: "PV2_CurrHigh_Fault",
        12: "BAT_OverVolt_Fault",
        13: "BAT_UnderVolt_Fault",
        14: "BAT_OverCurr_Fault",
        15: "BAT_OverCharge_Fault",
    },
    2: {  # Figure 6.3.3 - Fault alarm bit information 2
        0: "OUT_OverVolt_Fault",
        1: "OUT_OverCurr_Fault",
        2: "PV_L1_BuckOverCurr_Fault",
        3: "PV_L2_BuckOverCurr_Fault",
        4: "OUT_L1_BuckOverCurr_Fault",
        5: "OUT_L2_BuckOverCurr_Fault",
        6: "BMS_Communication_Fault",
        7: "BMS_Fault",
        8: "PV_L1_BuckOverCurr_Fault_INT",
        9: "PV_L2_BuckOverCurr_Fault_INT",
        10: "OUT_L1_BuckOverCurr_Fault_INT",
        11: "OUT_L2_BuckOverCurr_Fault_INT",
        12: "PV1_OverVolt_Fault_INT",
        13: "PV2_OverVolt_Fault_INT",
        14: "BAT_OverVolt_Fault_INT",
        15: "OUT_OverVolt_Fault_INT",
    },
    3: {  # Figure 6.3.4 - Fault alarm bit information 3
        # NOTE: Document has a typo — row 1 says D1 (skipping D0) and rows 2-3
        # both say D2. With 16 rows for 16 bits, the intended mapping is D0–D15.
        0: "BUS_OverVolt_Fault_INT",
        1: "PV1_OverCurr_Fault_INT",
        2: "PV2_OverCurr_Fault_INT",
        3: "BAT_OverCurr_Fault_INT",
        4: "OUT_OverCurr_Fault_INT",
        5: "PV_L3_OverCurr_Fault_INT",
        6: "PV_L4_OverCurr_Fault_INT",
        7: "PV_L5_OverCurr_Fault_INT",
        8: "OUT1_OCP_Fault",
        9: "OUT2_OCP_Fault",
        10: "PV1_L1_OCP_Fault",
        11: "PV2_L2_OCP_Fault",
        12: "DC1_Thunder_Fault",
        13: "DC2_Thunder_Fault",
        14: "BAT_SoftStart_Fault",
        15: "OUT_SoftStart_Fault",
    },
    4: {  # Figure 6.3.5 - Fault alarm bit information 4
        0: "PV_Module_OverTemp_Fault",
        1: "OUT_Module_OverTemp_Fault",
        2: "PV_Inductor_OverTemp_Fault",
        3: "OUT_Inductor2_OverTemp_Fault",
        4: "LowTemp_Fault",
        5: "BUS_Insulation_Fault",
        6: "PV_IGBT_Fault",
        7: "OUT_IGBT_Fault",
        8: "EPO_Stop",
        9: "KeyEmergencyStop",
        10: "LcdEmergencyStop",
        11: "BAT_MainContactor1_Fault",
        12: "OUT_MainContactor2_Fault",
        13: "BAT_SlaveContactor_Fault",
        14: "OUT_SlaveContactor_Fault",
        # 15: "Reseverd_Failure",
    },
    5: {  # Figure 6.3.6 - Fault alarm bit information 5
        0: "Fault_Feedback_Warning",
        1: "Fan_1_Fault_Warning",
        2: "Fan_2_Fault_Warning",
        3: "Fan_3_Fault_Warning",
        4: "Temp_Derating_Warning",
        5: "BAT_UnderVolt_Warning",
        6: "PCS_Communication_Warning",
        # 7: "Reseverd_Failure",
        8: "PV3_VoltHigh_Fault",
        9: "PV4_VoltHigh_Fault",
        10: "PV5_VoltHigh_Fault",
        11: "PV3_CurrHigh_Fault",
        12: "PV4_CurrHigh_Fault",
        13: "PV5_CurrHigh_Fault",
        14: "PV_L3_OverCurr_Fault",
        15: "PV_L4_OverCurr_Fault",
    },
    6: {  # Figure 6.3.7 - Fault alarm bit information 6
        0: "PV_L5_OverCurr_Fault",
        1: "PV3_OverVolt_Fault_INT",
        2: "PV4_OverVolt_Fault_INT",
        3: "PV5_OverVolt_Fault_INT",
        4: "PV3_OverCurr_Fault_INT",
        5: "PV4_OverCurr_Fault_INT",
        6: "PV5_OverCurr_Fault_INT",
        7: "PVVolt_higher_Output",
        8: "DC3_Thunder_Fault",
        9: "DC4_Thunder_Fault",
        10: "DC5_Thunder_Fault",
        11: "PV1_L3_OCP_Fault",
        12: "PV2_L4_OCP_Fault",
        13: "PV2_L5_OCP_Fault",
        # 14: "Reseverd_Failure",
        # 15: "Reseverd_Failure",
    },
}

# Addresses for PCS fault alarm registers (0-indexed modbus addresses, +1 for 1-indexed)
PCS_FAULT_ALARM_ADDRS = [
    (181 + 1 + i) for i in range(8)
]  # registers 182-189 (1-indexed)


def decode_fault_alarms(
    state: list[int],
    base_addr: int,
    fault_bits: dict[int, dict[int, str]],
    fault_reg_base: int = 181,
) -> tuple[list[str], list[str]]:
    """Decode fault alarm registers into (active, inactive) fault-key lists.

    Swaps high and low bytes of each 16-bit register before decoding.

    Fault keys are coerced to the canonical fault-name-key schema (no GxDy prefix).
    If a register cannot be read, its bits are treated as inactive so the attribute
    array remains complete.
    """
    active_faults: list[str] = []
    inactive_faults: list[str] = []
    for group_num, bit_map in fault_bits.items():
        # group_num is 1-indexed (Fault Alarm 1 = fault_reg_base + 1, etc.)
        addr = fault_reg_base + group_num  # 1-indexed address
        idx = addr - base_addr
        readable = 0 <= idx < len(state)
        if not readable:
            logger.warning("Illegal address calculated during fault decoding: %s", idx)
            for fault_name in bit_map.values():
                if fault_name:
                    inactive_faults.append(coerce_fault_name_key(fault_name))
            continue
        raw = state[idx]
        # Swap high and low bytes
        swapped = ((raw & 0xFF) << 8) | ((raw >> 8) & 0xFF)
        for bit_num in range(16):
            fault_name = bit_map.get(bit_num)
            if not fault_name:
                continue
            key = coerce_fault_name_key(fault_name)
            if swapped & (1 << bit_num):
                active_faults.append(key)
            else:
                inactive_faults.append(key)
    return active_faults, inactive_faults


# Atess Modbus RTU v3.22 p127 fig 4.1.2
# register 43: Device Type Code -> str
model_code_to_name: dict[int, str] = {
    22001: "HPS30",
    22002: "HPS50",
    22003: "HPS100",
    22004: "HPS120",
    22005: "HPS150",
    22006: "HPS250",
    22007: "HPS7500TL",
    22008: "HPS20KTL",
    22009: "HPS10KTL",
    22010: "HPS10KTLS",
    22011: "HPS7500TLS",
    22012: "HPS5KTLS",
    22013: "HPS3500TLS",
    22014: "HPS20KTLS",
    22015: "HPS15KTL",
    22016: "HPS30KTL",
    22017: "HPS40KTL",
    21016: "PCS50",
    21017: "PCS50TL",
    21018: "PCS50U",
    21019: "PCS100",
    21020: "PCS100TL",
    21021: "PCS100U",
    21022: "PCS250",
    21023: "PCS250TL",
    21024: "PCS250U",
    21025: "PCS500",
    21026: "PCS500TL",
    21027: "PCS500U",
    21028: "PCS50 (new model)",
    21029: "PCS50TL",
    21030: "PCS50U",
    21031: "PCS100",
    21032: "PCS100TL",
    21033: "PCS100U",
    21034: "PCS250",
    21035: "PCS250TL",
    21036: "PCS250U",
    21037: "PCS500",
    21038: "PCS500TL",
    21039: "PCS500U",
    21040: "PCS630",
    23001: "PBD350 (old model)",
    23002: "PBD350 (new model)",
    23003: "PBD250",
}

atess_write_parameters: dict[str, WriteParameter | WriteSelectParameter] = {
    "Mode selection": WriteSelectParameter(  # ALL
        addr=26 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.SELECT,
        options=[
            "Load First",
            "Battery First",
            "Economy Mode",
            "Peak Shaving",
            "Time Schedule",
            "Manual Dispatch",
            "Battery Protect",
            "Backup Power Management",
            "Constant Power Discharge",
            "Forced Charging",
            "Smart Meter Mode",
            "Bat-Smart Meter",
            "Grid Access Control",
        ],
        value_template='{% set options = ["Load First", "Battery First", "Economy Mode", "Peak Shaving", "Time Schedule", "Manual Dispatch", "Battery Protect", "Backup Power Management", "Constant Power Discharge", "Forced Charging", "Smart Meter Mode", "Bat-Smart Meter", "Grid Access Control"] %}{% if value|int >= 0 and value|int < options|length %}{{ options[value|int] }}{% else %}{{ value }}{% endif %}',
        command_template='{% set options = ["Load First", "Battery First", "Economy Mode", "Peak Shaving", "Time Schedule", "Manual Dispatch", "Battery Protect", "Backup Power Management", "Constant Power Discharge", "Forced Charging", "Smart Meter Mode", "Bat-Smart Meter", "Grid Access Control"] %}{% if value in options %}{{ options.index(value) }}{% else %}{{ value }}{% endif %}',
    ),
    "Bypass Cabinet Enable": WriteParameter(  # PCS
        addr=13 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.SWITCH,
        payload_off=0,
        payload_on=1,
    ),
    "BMS Communication Enable": WriteParameter(  # PCS
        addr=14 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.SWITCH,
        payload_off=0,
        payload_on=1,
    ),
    # Battery. NOTE Actually all types have this holding register
    "Generator Start SOC": WriteParameter(  # ALL "SOC Up Limit" # When off-grid AND in diesel Generator (DG) mode
        addr=66 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=100,
        unit="%",
    ),
    "Grid Power Compensation": WriteParameter(  # ALL
        addr=44 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=100,
        unit="kW",
    ),
    "Generator Stop SOC": WriteParameter(  # ALL
        addr=67 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=100,
        unit="%",
    ),
    "Battery Charging Saturation": WriteParameter(  # ALL
        addr=150 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=10,
    ),
    "Charge Cutoff SOC": WriteParameter(  # ALL
        addr=178 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=100,
        unit="%",
    ),
    "Discharge Cutoff SOC": WriteParameter(  # ALL
        addr=47 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=100,
        unit="%",
    ),
    "Grid Charge Cutoff SOC": WriteParameter(  # ALL
        addr=340 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=100,
        unit="%",
    ),
    "Battery Power Export to Grid Set": WriteParameter(  # ALL
        addr=174 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=150,
        unit="kW",
    ),
    "CP Nominal Power": WriteParameter(  # ALL
        addr=118 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=1000,
        unit="kW",
    ),
    "Grid And PV Charge Together": WriteParameter(  # ALL
        addr=8 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.SWITCH,
        payload_off=0,
        payload_on=1,
    ),
    "Max Grid Charge Power": WriteParameter(  # ALL
        addr=225 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        min=0,
        max=150,  # TODO
        unit="kW",
    ),
    "Forced Charge Enable": WriteParameter(  # ALL
        addr=229 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.SWITCH,
        payload_off=0,
        payload_on=1,
    ),
    "Anti Reflux Enable": WriteParameter(  # HPS, PCS, HPSTL
        addr=16 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.SWITCH,
        payload_off=0,
        payload_on=1,
    ),
    # "PV Power Limit": WriteParameter( # ALL # "PV power setting"
    #     addr = 33 + 1,
    #     count = 1,
    #     dtype = DataType.U16,
    #     multiplier = 1,
    #     register_type = RegisterTypes.HOLDING_REGISTER,
    #     ha_entity_type = HAEntityType.NUMBER,
    #     unit="kW",
    #     min = 0,
    #     max = 500
    # ),
    "Output Power Limit": WriteParameter(  # ALL # "Output Power Upper Limit"
        addr=58 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="%",
        min=0,
        max=120,
    ),
    # "Load Power Limit": WriteParameter( # ALL # "Output Power Upper Limit"
    #     addr = 107 + 1,
    #     count = 1,
    #     dtype = DataType.U16,
    #     multiplier = 1,
    #     register_type = RegisterTypes.HOLDING_REGISTER,
    #     ha_entity_type = HAEntityType.NUMBER,
    #     unit="kW",
    #     min = 0,
    #     max = 500
    # ),
    "Grid Power UP Limit": WriteParameter(  # ALL # "Grid Power UP Limit"
        addr=65 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="kW",
        min=0,
        max=500,
    ),
    # "Max Grid Import Power": WriteParameter( # ALL # "Upper limit powerfeed from grid"
    #     addr = 169 + 1,
    #     count = 1,
    #     dtype = DataType.U16,
    #     multiplier = 1,
    #     register_type = RegisterTypes.HOLDING_REGISTER,
    #     ha_entity_type = HAEntityType.NUMBER,
    #     unit="kW",
    #     min = 0,
    #     max = 500
    # ),
    "Charge current limit": WriteParameter(  # ALL
        addr=154 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="A",
        min=0,
        max=1000,  # TODO "10000"
    ),
    "Discharge current limit": WriteParameter(  # ALL
        addr=155 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="A",
        min=0,
        max=1000,  # TODO "10000"
    ),
    # "Battery Discharge Current HPS": WriteParameter( # HPS # "Upper limit powerfeed from grid"
    #     addr = 172 + 1,
    #     count = 1,
    #     dtype = DataType.U16,
    #     multiplier = 1,
    #     register_type = RegisterTypes.HOLDING_REGISTER,
    #     ha_entity_type = HAEntityType.NUMBER,
    #     unit="A",
    #     min = 0,
    #     max = 1000 # TODO "10000"
    # ),
}
atess_PBD_write_parameters: dict[str, WriteParameter | WriteSelectParameter] = {
    "PV Start Voltage": WriteParameter(  # ALL
        addr=60 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="V",
        min=300,
        max=850,
    ),
    "Max MPPT Voltage": WriteParameter(  # ALL
        addr=61 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="V",
        min=300,
        max=1500,
    ),
    "Min MPPT Voltage": WriteParameter(  # ALL
        addr=62 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="V",
        min=300,
        max=1500,
    ),
    "PV Start Power": WriteParameter(  # ALL
        addr=63 + 1,
        count=1,
        dtype=DataType.U16,
        multiplier=0.1,
        register_type=RegisterTypes.HOLDING_REGISTER,
        ha_entity_type=HAEntityType.NUMBER,
        unit="kW",
        min=0,
        max=500,
    ),
}


atess_param_registry = ParamRegistry(
    registry=[
        *[ParamWrapped(n, p, None, False) for n, p in atess_parameters.items()],
        *[
            ParamWrapped(n, p, {"PBD", "HPS"}, False)
            for n, p in not_PCS_parameters.items()
        ],
        *[ParamWrapped(n, p, {"PCS"}, False) for n, p in PCS_parameters.items()],
        *[ParamWrapped(n, p, {"PBD"}, False) for n, p in PBD_parameters.items()],
        *[ParamWrapped(n, p, {"PCS"}, True) for n, p in atess_write_parameters.items()],
        *[
            ParamWrapped(n, p, {"PBD"}, True)
            for n, p in atess_PBD_write_parameters.items()
        ],
    ]
)


deprecated: dict[str, Parameter] = {
    # Voltage and Current Measurements
    # "PV Voltage Calibration": {
    #     "addr": 80 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Battery Voltage Calibration": {
    #     "addr": 81 + 1,
    #     "count": 1,
    #     "dtype": DataType.I16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Battery Current Calibration": {
    #     "addr": 82 + 1,
    #     "count": 1,
    #     "dtype": DataType.I16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "PV Current Calibration": {
    #     "addr": 83 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # Output Voltages
    # "Output Voltage U Calibration": {
    #     "addr": 84 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Output Voltage V Calibration": {
    #     "addr": 85 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Output Voltage W Calibration": {
    #     "addr": 86 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # Grid Currents
    # "Grid Current U Calibration": {
    #     "addr": 87 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Grid Current V Calibration": {
    #     "addr": 88 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Grid Current W Calibration": {
    #     "addr": 89 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # Grid Voltages
    # "Grid Voltage UV Calibration": {
    #     "addr": 90 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Grid Voltage VW Calibration": {
    #     "addr": 91 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Grid Voltage WU Calibration": {
    #     "addr": 92 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "V",
    #     "device_class": DeviceClass.VOLTAGE,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # Load Currents
    # "Load Current U Calibration": {
    #     "addr": 93 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Load Current V Calibration": {
    #     "addr": 94 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
    # "Load Current W Calibration": {
    #     "addr": 95 + 1,
    #     "count": 1,
    #     "dtype": DataType.U16,
    #     "multiplier": 0.1,
    #     "unit": "A",
    #     "device_class": DeviceClass.CURRENT,
    #     "register_type": RegisterTypes.HOLDING_REGISTER,
    # },
}


if __name__ == "__main__":

    def create_batches(
        parameters: dict[str, Parameter | WriteParameter | WriteSelectParameter],
    ):
        holding_params = [
            (k, v)
            for k, v in parameters.items()
            if v["register_type"] == RegisterTypes.HOLDING_REGISTER
        ]
        input_params = [
            (k, v)
            for k, v in parameters.items()
            if v["register_type"] == RegisterTypes.INPUT_REGISTER
        ]

        for params in (holding_params, input_params):
            params = sorted(params, key=lambda x: x[1]["addr"])
            print([i[1]["addr"] for i in params])

    def find_consecutive_groups(numbers):
        """
        Find groups of consecutive numbers in a list.

        Args:
            numbers: A list of integers

        Returns:
            A list of lists, where each inner list is a group of consecutive numbers
        """
        if not numbers:
            return []

        # Sort the input list
        numbers = sorted(numbers)

        # Initialize the result and the first group
        result = []
        current_group = [numbers[0]]

        # Iterate through the rest of the numbers
        for i in range(1, len(numbers)):
            # If the current number is consecutive to the previous one
            if numbers[i] == numbers[i - 1] + 1:
                current_group.append(numbers[i])
            # If not consecutive and not a duplicate
            elif numbers[i] != numbers[i - 1]:
                # Save the current group if it's not empty
                if current_group:
                    result.append(current_group)
                # Start a new group
                current_group = [numbers[i]]

        # Add the last group if it's not empty
        if current_group:
            result.append(current_group)

        return result

    # # Your two lists
    # list1 = [1, 9, 14, 15, 17, 27, 44, 45, 48, 59, 66, 67, 68, 80, 81, 84, 101, 102, 151, 156, 175, 179, 181, 226, 230, 341]
    # list2 = [2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 29, 36, 37, 48, 49, 50, 51, 53, 54, 55, 56, 57, 58, 59, 69, 73, 79, 80, 81, 82, 83, 85, 89, 91, 95, 97, 136, 137, 138, 163, 172, 172, 175, 176, 177, 177, 181, 229, 271]

    # # Find the consecutive groups in each list
    # groups_list1 = find_consecutive_groups(list1)
    # groups_list2 = find_consecutive_groups(list2)

    # # Print the results
    # print("Consecutive groups in list1:")
    # for i, group in enumerate(groups_list1):
    #     print(f"Group {i+1}: {group}")

    # print("\nConsecutive groups in list2:")
    # for i, group in enumerate(groups_list2):
    #     print(f"Group {i+1}: {group}")

    # # Count the number of groups in each list
    # print(f"\nNumber of consecutive groups in list1: {len(groups_list1)}")
    # print(f"Number of consecutive groups in list2: {len(groups_list2)}")

    # params: dict[str, Parameter | WriteParameter | WriteSelectParameter] = atess_parameters.copy()
    # # params.update(PCS_parameters)
    # params.update(PBD_parameters)
    # params.update(not_PCS_parameters)
    # # params.update(atess_write_parameters)
    # create_batches(params)

    all = (
        not_PCS_parameters
        | atess_parameters
        | PCS_parameters
        | PBD_parameters
        | atess_write_parameters
        | atess_PBD_write_parameters
    )
    import pandas as pd

    df = pd.DataFrame.from_dict(
        {k: {"addr": v["addr"] - 1} for k, v in all.items()}, orient="index"
    )

    df.to_csv("data/registers")
