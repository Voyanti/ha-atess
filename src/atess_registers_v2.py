"""Refactored register definitions for ATESS inverters.

Each register is declared as a single ``ParamWrapped`` entry with the set of
device groups it applies to, sourced directly from the "Subordinate aircraft"
column of the ATESS Modbus RTU Communication Protocol V3.22 (pdfs/Atess
Modbus RTU 3.22.pdf).

Mapping convention:

* ``None``                 → "all model" / "All mode" (every group)
* ``NOT_PCS``              → "all model (Except PCS)"
* ``HPS_PCS_HPSTL``        → "HPS/PCS/HPSTL"
* ``HPS_PCS``              → "HPS/PCS"
* ``HPSTL_PBD``            → "HPSTL/PBD250/PBD350"
* ``PBD_ONLY``             → "PBD" / "PBD250/PBD350"
* ``PCS_ONLY``             → "PCS"
* ``HPS_ONLY``             → "HPS"
* ``HPSTL_ONLY``           → "HPSTL"

Compared to ``atess_registers.py`` (V1) this file drops the per-group dicts
(``atess_parameters``, ``not_PCS_parameters``, ``PCS_parameters``,
``PBD_parameters``, ``atess_write_parameters``, ``atess_PBD_write_parameters``)
in favour of a single flat registry. HPSTL is promoted to its own group because
the PDF frequently distinguishes it from HPS (for example PV1 Voltage is
"all model (Except PCS)" so it reaches HPSTL, but Output Voltage U/V/W at
registers 56-58 is "HPS/PCS" only).
"""

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

basic_params = {
    "Device On/Off": {
        "addr": 0 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "multiplier": 1,
        "unit": "",
        "device_class": DeviceClass.ENUM,
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
    "Device Type Code": {
        "addr": 43 + 1,
        "count": 1,
        "dtype": DataType.U16,
        "device_class": DeviceClass.ENUM,
        "multiplier": 1,
        "unit": "",
        "register_type": RegisterTypes.HOLDING_REGISTER,
    },
}

# HPSTL is distinct from HPS in the PDF. The classifier in atess_inverter.py
# currently folds HPSTL models into "HPS", so until that is updated the
# HPSTL-only registers will not be reachable. Added here to match the PDF.
ATESS_DEVICE_GROUP = Literal["PCS", "PBD", "HPS", "HPSTL"]


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


# Group-set aliases mirroring the PDF's "Subordinate aircraft" column.
NOT_PCS: Set[ATESS_DEVICE_GROUP] = {"HPS", "HPSTL", "PBD"}
HPS_PCS_HPSTL: Set[ATESS_DEVICE_GROUP] = {"HPS", "PCS", "HPSTL"}
HPS_PCS: Set[ATESS_DEVICE_GROUP] = {"HPS", "PCS"}
HPSTL_PBD: Set[ATESS_DEVICE_GROUP] = {"HPSTL", "PBD"}
PBD_ONLY: Set[ATESS_DEVICE_GROUP] = {"PBD"}
PCS_ONLY: Set[ATESS_DEVICE_GROUP] = {"PCS"}
HPS_ONLY: Set[ATESS_DEVICE_GROUP] = {"HPS"}
HPSTL_ONLY: Set[ATESS_DEVICE_GROUP] = {"HPSTL"}


# ---------------------------------------------------------------------------
# Read registers (function codes 0x03 holding, 0x04 input)
# ---------------------------------------------------------------------------
read_params: list[ParamWrapped] = [
    # --- Input register 0: PV1 Voltage --- "all model (Except PCS)"
    ParamWrapped(
        "PV1 Voltage",
        {
            "addr": 0 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        NOT_PCS,
        False,
    ),
    # --- Input register 3: PV1 DC Current --- "all model (Except PCS)"
    ParamWrapped(
        "PV1 DC Current",
        {
            "addr": 3 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        NOT_PCS,
        False,
    ),
    # --- Input register 51: PV1 Power --- "all model (Except PCS)"
    # Protocol documents this as unsigned; observation shows it can go negative,
    # so we decode as signed.
    ParamWrapped(
        "PV1 Power",
        {
            "addr": 51 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        NOT_PCS,
        False,
    ),
    # --- Input register 62: PV daily power generation --- "all model (Except PCS)"
    ParamWrapped(
        "PV Daily Power Generation",
        {
            "addr": 62 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total_increasing",
        },
        NOT_PCS,
        False,
    ),
    # --- Input register 64-65: PV total power generation --- "all model (Except PCS)"
    ParamWrapped(
        "Total PV Generation",
        {
            "addr": 64 + 1,
            "count": 2,
            "dtype": DataType.U32,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total_increasing",
        },
        NOT_PCS,
        False,
    ),
    # --- Holding register 180-185: Serial Number --- "All mode"
    ParamWrapped(
        "Serial Number",
        {
            "addr": 180 + 1,
            "count": 5,
            "dtype": DataType.UTF8,
            "device_class": DeviceClass.ENUM,
            "multiplier": 1,
            "unit": "",
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Holding register 43: DTC (protocol) / Device Type Code --- "all model"
    ParamWrapped(
        "Device Type Code",
        {
            "addr": 43 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "device_class": DeviceClass.ENUM,
            "multiplier": 1,
            "unit": "",
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Holding register 0: on/off --- "all model"
    ParamWrapped(
        "Device On/Off",
        {
            "addr": 0 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Holding register 80: PV voltage (calibration) --- "All mode"
    ParamWrapped(
        "PV Voltage Calibration",
        {
            "addr": 80 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Holding register 83: PV current (calibration) --- "All mode"
    ParamWrapped(
        "PV Current Calibration",
        {
            "addr": 83 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 17: Battery power --- "all model"
    ParamWrapped(
        "Battery Power",
        {
            "addr": 17 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 47: Battery percentage --- "all model"
    ParamWrapped(
        "Battery SOC",
        {
            "addr": 47 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "device_class": DeviceClass.BATTERY,
            "multiplier": 1,
            "unit": "%",
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "measurement",
        },
        None,
        False,
    ),
    # --- Input register 270-279: Hardware version --- "All mode"
    ParamWrapped(
        "Hardware Version",
        {
            "addr": 270 + 1,
            "count": 10,
            "dtype": DataType.UTF8,
            "device_class": DeviceClass.ENUM,
            "multiplier": 1,
            "unit": "",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 1: Battery voltage --- "all model"
    ParamWrapped(
        "Battery Voltage",
        {
            "addr": 1 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 2: Battery current --- "all model"
    ParamWrapped(
        "Battery Current",
        {
            "addr": 2 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 100: BMS Max.Charge current --- "all model"
    ParamWrapped(
        "BMS Max Charge Current",
        Parameter(
            addr=100 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=0.1,
            device_class=DeviceClass.CURRENT,
            register_type=RegisterTypes.INPUT_REGISTER,
            unit="A",
        ),
        None,
        False,
    ),
    # --- Input register 101: BMS Max.Discharge current --- "all model"
    ParamWrapped(
        "BMS Max Discharge Current",
        Parameter(
            addr=101 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=0.1,
            register_type=RegisterTypes.INPUT_REGISTER,
            device_class=DeviceClass.CURRENT,
            unit="A",
        ),
        None,
        False,
    ),
    # --- Input register 36: Ambient temperature --- "all model"
    ParamWrapped(
        "Ambient temperature",
        {
            "addr": 36 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "device_class": DeviceClass.TEMPERATURE,
            "multiplier": 0.1,
            "unit": "°C",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 171: BMS maximum temperature (high byte) --- "all model"
    ParamWrapped(
        "BMS Max. Temperature",
        {
            "addr": 171 + 1,
            "count": 1,
            "dtype": DataType.I8H,
            "device_class": DeviceClass.TEMPERATURE,
            "multiplier": 1,
            "unit": "°C",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 171: BMS minimum temperature (low byte) --- "all model"
    ParamWrapped(
        "BMS Min. Temperature",
        {
            "addr": 171 + 1,
            "count": 1,
            "dtype": DataType.I8L,
            "device_class": DeviceClass.TEMPERATURE,
            "multiplier": 1,
            "unit": "°C",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 174: Maximum unit voltage --- "all model"
    ParamWrapped(
        "BMS Max. Cell Voltage",
        {
            "addr": 174 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "mV",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 175: Minimum cell voltage --- "all model"
    ParamWrapped(
        "BMS Min. Cell Voltage",
        {
            "addr": 175 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "mV",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 68-69: Total discharge capacity of battery --- "all model"
    ParamWrapped(
        "Total Battery Discharge Energy",
        {
            "addr": 68 + 1,
            "count": 2,
            "dtype": DataType.U32,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total_increasing",
        },
        None,
        False,
    ),
    # --- Input register 72-73: Total charge capacity of battery --- "all model"
    ParamWrapped(
        "Total Battery Charge Energy",
        {
            "addr": 72 + 1,
            "count": 2,
            "dtype": DataType.U32,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total_increasing",
        },
        None,
        False,
    ),
    # --- Holding register 156: Float charging voltage --- "All mode"
    ParamWrapped(
        "Float Charging Voltage",
        {
            "addr": 156 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "mV",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Holding register 163: Float charge current limit point setting --- "All mode"
    ParamWrapped(
        "Float Charging Current",
        {
            "addr": 163 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 10,
            "unit": "mA",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Holding register 161: Single PV to off-grid --- "All mode"
    ParamWrapped(
        "Single PV to Off-grid",
        {
            "addr": 161 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "mV",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 162: system battery current --- "PCS"
    ParamWrapped(
        "System battery current",
        {
            "addr": 162 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "device_class": DeviceClass.CURRENT,
            "multiplier": 0.1,
            "unit": "A",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    # --- Input register 228: System battery power --- "PCS"
    ParamWrapped(
        "System battery power",
        {
            "addr": 228 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "device_class": DeviceClass.POWER,
            "multiplier": 0.1,
            "unit": "kW",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    # --- Input register 229: CP power limit --- "PCS"
    ParamWrapped(
        "CP Power Limit",
        {
            "addr": 229 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "device_class": DeviceClass.POWER,
            "multiplier": 0.1,
            "unit": "kW",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    # --- Input register 35: Transformer temperature --- "HPS/PCS"
    ParamWrapped(
        "Transformer temperature",
        {
            "addr": 35 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "device_class": DeviceClass.TEMPERATURE,
            "multiplier": 0.1,
            "unit": "°C",
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    # --- Holding register 79: Frequency shift enable --- "PCS"
    # 0: Disable, 1: mode1, 2: mode2
    ParamWrapped(
        "Frequency Shift Enable",
        {
            "addr": 79 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "device_class": DeviceClass.ENUM,
            "multiplier": 1,
            "unit": "",
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    # --- Input register 22: Power factor symbol --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Power factor symbol",
        {
            "addr": 22 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 23: Power factor --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Power factor",
        {
            "addr": 23 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.001,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Holding register 178: Charging cut off SOC --- "HPS/PCS"
    ParamWrapped(
        "Charge Cutoff SOC",
        {
            "addr": 178 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "device_class": DeviceClass.BATTERY,
            "multiplier": 1,
            "unit": "%",
            "register_type": RegisterTypes.HOLDING_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    # --- Input register 4-6: Output voltage UV/VW/WU --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Output Voltage UV",
        {
            "addr": 4 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Output Voltage VW",
        {
            "addr": 5 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Output Voltage WU",
        {
            "addr": 6 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 7-9: Bypass current U/V/W --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Bypass Current U",
        {
            "addr": 7 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Bypass Current V",
        {
            "addr": 8 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Bypass Current W",
        {
            "addr": 9 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 10-12: Inductance1 current A/B/C --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Inductance Current A",
        {
            "addr": 10 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Inductance Current B",
        {
            "addr": 11 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Inductance Current C",
        {
            "addr": 12 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 13-15: Grid bypass voltage UV/VW/WU --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Grid Bypass Voltage UV",
        {
            "addr": 13 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Grid Bypass Voltage VW",
        {
            "addr": 14 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Grid Bypass Voltage WU",
        {
            "addr": 15 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 81: Bypass frequency --- "HPS/PCS"
    ParamWrapped(
        "Bypass Frequency",
        {
            "addr": 81 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.01,
            "unit": "Hz",
            "device_class": DeviceClass.FREQUENCY,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    # --- Input register 16: Output frequency --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Output Frequency",
        {
            "addr": 16 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.01,
            "unit": "Hz",
            "device_class": DeviceClass.FREQUENCY,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 18-20: Bypass apparent/active/reactive power --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Bypass Apparent Power",
        {
            "addr": 18 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "",
            "device_class": DeviceClass.APPARENT_POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Bypass Active Power",
        {
            "addr": 19 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "measurement",
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Bypass Reactive Power",
        {
            "addr": 20 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "",
            "device_class": DeviceClass.REACTIVE_POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 21: Grid frequency --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Grid Frequency",
        {
            "addr": 21 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.01,
            "unit": "Hz",
            "device_class": DeviceClass.FREQUENCY,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Grid State: v1 sourced this as INPUT register 28, which does not match
    # the PDF (input reg 28 is "PV2 insulation test positive" for HPSTL). The
    # content ("0: abnormal, 1: normal") matches *holding* reg 28 "Grid state"
    # documented as HPS Schneider project (non-standard). Keeping the original
    # register_type for behavioural parity but limiting the group to HPS.
    ParamWrapped(
        "Grid State",
        {
            "addr": 28 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "remarks": "0: abnormal, 1: normal",
        },
        HPS_ONLY,
        False,
    ),
    # --- Input register 78-80: Output apparent/active/reactive power --- "PCS"
    ParamWrapped(
        "Output Apparent Power",
        {
            "addr": 78 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "",
            "device_class": DeviceClass.APPARENT_POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    ParamWrapped(
        "Output Active Power",
        {
            "addr": 79 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    ParamWrapped(
        "Output Reactive Power",
        {
            "addr": 80 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "",
            "device_class": DeviceClass.REACTIVE_POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    # --- Input register 82: Daily power consumption of load --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Daily Power Consumption",
        {
            "addr": 82 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 88: Daily power intake from grid --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Daily Power From Grid",
        {
            "addr": 88 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 94: Daily power fed to grid --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Daily Power To Grid",
        {
            "addr": 94 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 135-137: Output current U/V/W --- "PCS"
    ParamWrapped(
        "Output Current U",
        {
            "addr": 135 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    ParamWrapped(
        "Output Current V",
        {
            "addr": 136 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    ParamWrapped(
        "Output Current W",
        {
            "addr": 137 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PCS_ONLY,
        False,
    ),
    # --- Input register 48-50: Load apparent/active/reactive power --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Load Apparent Power",
        {
            "addr": 48 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "",
            "device_class": DeviceClass.APPARENT_POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Load Active Power",
        {
            "addr": 49 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Load Reactive Power",
        {
            "addr": 50 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "",
            "device_class": DeviceClass.REACTIVE_POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 52: Load power factor --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Load Power Factor",
        {
            "addr": 52 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.001,
            "unit": "",
            "device_class": DeviceClass.POWER_FACTOR,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 53-55: Load current U/V/W --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Load Current U",
        {
            "addr": 53 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Load Current V",
        {
            "addr": 54 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    ParamWrapped(
        "Load Current W",
        {
            "addr": 55 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 56-58: Output voltage U/V/W --- "HPS/PCS"
    ParamWrapped(
        "Output Voltage U",
        {
            "addr": 56 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Output Voltage V",
        {
            "addr": 57 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Output Voltage W",
        {
            "addr": 58 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    # --- Input register 90-91: Total power intake from grid --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Total Grid Import",
        {
            "addr": 90 + 1,
            "count": 2,
            "dtype": DataType.U32,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total",
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 96-97: Total power fed to grid --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Total Grid Export",
        {
            "addr": 96 + 1,
            "count": 2,
            "dtype": DataType.U32,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total",
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 84-85: Total load consumption --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Total Load Energy",
        {
            "addr": 84 + 1,
            "count": 2,
            "dtype": DataType.U32,
            "multiplier": 0.1,
            "unit": "kWh",
            "device_class": DeviceClass.ENERGY,
            "register_type": RegisterTypes.INPUT_REGISTER,
            "state_class": "total",
        },
        HPS_PCS_HPSTL,
        False,
    ),
    # --- Input register 176: BMS battery/system status --- "all model"
    ParamWrapped(
        "BMS Battery Status",
        {
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
        None,
        False,
    ),
    ParamWrapped(
        "BMS System Status",
        {
            "addr": 176 + 1,
            "count": 1,
            "dtype": DataType.U8L,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 180: Running state --- "HPS/PCS"
    ParamWrapped(
        "Running State",
        {
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
        HPS_PCS,
        False,
    ),
    # --- Input registers 181-188: Fault alarms 1-8 --- "HPS/PCS"
    # Decoded collectively via PCS_FAULT_ALARM_BITS / decode_fault_alarms.
    ParamWrapped(
        "Fault Alarm 1",
        {
            "addr": 181 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 2",
        {
            "addr": 182 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 3",
        {
            "addr": 183 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 4",
        {
            "addr": 184 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 5",
        {
            "addr": 185 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 6",
        {
            "addr": 186 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 7",
        {
            "addr": 187 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    ParamWrapped(
        "Fault Alarm 8",
        {
            "addr": 188 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    # --- Input register 192: Operation mode --- "HPS/PCS"
    ParamWrapped(
        "Operation Mode",
        {
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
        HPS_PCS,
        False,
    ),
    # --- Input register 190: Running state (bitwise) --- "HPS/PCS"
    ParamWrapped(
        "Running State Bitwise",
        {
            "addr": 190 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPS_PCS,
        False,
    ),
    # --- Input registers 177-179: BMS alarm levels --- "all model"
    ParamWrapped(
        "BMS Level 1 Alarm",
        {
            "addr": 177 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    ParamWrapped(
        "BMS Level 2 Alarm",
        {
            "addr": 178 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    ParamWrapped(
        "BMS Level 3 Protection",
        {
            "addr": 179 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 168: Max/Min V group numbers (byte-packed) --- "all model"
    ParamWrapped(
        "BMS Max V Group Nr",
        {
            "addr": 168 + 1,
            "count": 1,
            "dtype": DataType.U8H,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    ParamWrapped(
        "BMS Min V Group Nr",
        {
            "addr": 168 + 1,
            "count": 1,
            "dtype": DataType.U8L,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 172: BMS min unit voltage numbers --- "all model"
    ParamWrapped(
        "BMS Min V Unit Nr",
        {
            "addr": 172 + 1,
            "count": 1,
            "dtype": DataType.U8H,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    ParamWrapped(
        "BMS Min V Unit Box Nr",
        {
            "addr": 172 + 1,
            "count": 1,
            "dtype": DataType.U8L,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 173: BMS max unit voltage numbers --- "all model"
    ParamWrapped(
        "BMS Max V Unit Nr",
        {
            "addr": 173 + 1,
            "count": 1,
            "dtype": DataType.U8H,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    ParamWrapped(
        "BMS Max V Unit Box Nr",
        {
            "addr": 173 + 1,
            "count": 1,
            "dtype": DataType.U8L,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 164: BMS total voltage --- "all model"
    ParamWrapped(
        "BMS Total Voltage",
        {
            "addr": 164 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 165: BMS total current --- "all model"
    ParamWrapped(
        "BMS Total Current",
        {
            "addr": 165 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        None,
        False,
    ),
    # --- Input register 105-108: PV2 voltage/current/power and PV total --- "HPSTL/PBD250/PBD350"
    ParamWrapped(
        "PV2 Voltage",
        {
            "addr": 105 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPSTL_PBD,
        False,
    ),
    ParamWrapped(
        "PV2 DC Current",
        {
            "addr": 106 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPSTL_PBD,
        False,
    ),
    ParamWrapped(
        "PV2 Power",
        {
            "addr": 107 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPSTL_PBD,
        False,
    ),
    ParamWrapped(
        "PV Total Power",
        {
            "addr": 108 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        HPSTL_PBD,
        False,
    ),
    # --- Input registers 109-134: PBD output + PV3/4/5 channels --- "PBD250/PBD350"
    ParamWrapped(
        "Output Voltage",
        {
            "addr": 109 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "Output Current",
        {
            "addr": 110 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "Output Power",
        {
            "addr": 113 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV Module Temperature",
        {
            "addr": 114 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 0.1,
            "unit": "°C",
            "device_class": DeviceClass.TEMPERATURE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV3 Voltage",
        {
            "addr": 123 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV4 Voltage",
        {
            "addr": 124 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV5 Voltage",
        {
            "addr": 125 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "V",
            "device_class": DeviceClass.VOLTAGE,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV3 DC Current",
        {
            "addr": 126 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV4 DC Current",
        {
            "addr": 127 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV5 DC Current",
        {
            "addr": 128 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "A",
            "device_class": DeviceClass.CURRENT,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV3 Power",
        {
            "addr": 132 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV4 Power",
        {
            "addr": 133 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PV5 Power",
        {
            "addr": 134 + 1,
            "count": 1,
            "dtype": DataType.I16,
            "multiplier": 0.1,
            "unit": "kW",
            "device_class": DeviceClass.POWER,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    # --- Input register 206: PBD running state --- "PBD"
    ParamWrapped(
        "PBD Running State",
        {
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
        PBD_ONLY,
        False,
    ),
    # --- Input registers 207-212: PBD fault alarms 1-6 --- "PBD"
    ParamWrapped(
        "PBD Fault Alarm 1",
        {
            "addr": 207 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PBD Fault Alarm 2",
        {
            "addr": 208 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PBD Fault Alarm 3",
        {
            "addr": 209 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PBD Fault Alarm 4",
        {
            "addr": 210 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PBD Fault Alarm 5",
        {
            "addr": 211 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    ParamWrapped(
        "PBD Fault Alarm 6",
        {
            "addr": 212 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    # --- Input register 213: PBD running state (bitwise) --- "PBD"
    ParamWrapped(
        "PBD Running State Bitwise",
        {
            "addr": 213 + 1,
            "count": 1,
            "dtype": DataType.U16,
            "multiplier": 1,
            "unit": "",
            "device_class": DeviceClass.ENUM,
            "register_type": RegisterTypes.INPUT_REGISTER,
        },
        PBD_ONLY,
        False,
    ),
    # --- Input register 215: PBD operation mode --- "PBD"
    ParamWrapped(
        "PBD Operation Mode",
        {
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
        PBD_ONLY,
        False,
    ),
]


# ---------------------------------------------------------------------------
# Write registers (function code 0x06)
# ---------------------------------------------------------------------------
write_params: list[ParamWrapped] = [
    # --- Holding register 26: Mode selection --- "all model"
    ParamWrapped(
        "Mode selection",
        WriteSelectParameter(
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
        None,
        True,
    ),
    # --- Holding register 13: Bypass Cabinet Enable (PCS) / ATS Enable (HPS) --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Bypass Cabinet Enable",
        WriteParameter(
            addr=13 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS_HPSTL,
        True,
    ),
    # --- Holding register 14: BMS communication enable --- "all model"
    ParamWrapped(
        "BMS Communication Enable",
        WriteParameter(
            addr=14 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        None,
        True,
    ),
    # --- Holding register 66: SOC Up Limit (Generator start SOC) --- "All mode"
    ParamWrapped(
        "Generator Start SOC",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 44: grid power compensation --- "HPS/PCS"
    ParamWrapped(
        "Grid Power Compensation",
        WriteParameter(
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
        HPS_PCS,
        True,
    ),
    # --- Holding register 67: SOC DownLimit (Generator stop SOC) --- "All mode"
    ParamWrapped(
        "Generator Stop SOC",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 150: Battery charging saturation --- "All mode"
    ParamWrapped(
        "Battery Charging Saturation",
        WriteParameter(
            addr=150 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            min=0,
            max=10,
        ),
        None,
        True,
    ),
    # --- Holding register 178: Charging cut off SOC --- "HPS/PCS"
    ParamWrapped(
        "Charge Cutoff SOC",
        WriteParameter(
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
        HPS_PCS,
        True,
    ),
    # --- Holding register 47: Discharge cut-off SOC --- "HPS/PCS"
    ParamWrapped(
        "Discharge Cutoff SOC",
        WriteParameter(
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
        HPS_PCS,
        True,
    ),
    # --- Holding register 340: grid charge cutoff SOC --- "HPS/PCS"
    ParamWrapped(
        "Grid Charge Cutoff SOC",
        WriteParameter(
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
        HPS_PCS,
        True,
    ),
    # --- Holding register 174: Battery power export to grid set --- "HPS/PCS"
    ParamWrapped(
        "Battery Power Export to Grid Set",
        WriteParameter(
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
        HPS_PCS,
        True,
    ),
    # --- Holding register 118: CP nominal power setting --- "All mode"
    ParamWrapped(
        "CP Nominal Power",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 8: Grid & PV Charge Together Enable --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Grid And PV Charge Together",
        WriteParameter(
            addr=8 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS_HPSTL,
        True,
    ),
    # --- Holding register 225: Grid charging power --- "HPS/PCS"
    ParamWrapped(
        "Max Grid Charge Power",
        WriteParameter(
            addr=225 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=0.1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            min=0,
            max=150,
            unit="kW",
        ),
        HPS_PCS,
        True,
    ),
    # --- Holding register 229: Forced charge enable --- "HPS/PCS"
    ParamWrapped(
        "Forced Charge Enable",
        WriteParameter(
            addr=229 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS,
        True,
    ),
    # --- Holding register 16: Anti-reflux enable --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Anti Reflux Enable",
        WriteParameter(
            addr=16 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS_HPSTL,
        True,
    ),
    # --- Holding register 58: Output power upper limit --- "All mode"
    ParamWrapped(
        "Output Power Limit",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 65: Grid Power UP Limit --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Grid Power UP Limit",
        WriteParameter(
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
        HPS_PCS_HPSTL,
        True,
    ),
    # --- Holding register 154: Charging current limit --- "All mode"
    ParamWrapped(
        "Charge current limit",
        WriteParameter(
            addr=154 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=0.1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="A",
            min=0,
            max=1000,
        ),
        None,
        True,
    ),
    # --- Holding register 155: Discharging current limit --- "All mode"
    ParamWrapped(
        "Discharge current limit",
        WriteParameter(
            addr=155 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=0.1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="A",
            min=0,
            max=1000,
        ),
        None,
        True,
    ),
    # --- Holding register 60: PV Start Voltage --- "All mode"
    ParamWrapped(
        "PV Start Voltage",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 61: Max MPPT Voltage --- "All mode"
    ParamWrapped(
        "Max MPPT Voltage",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 62: Min MPPT Voltage --- "All mode"
    ParamWrapped(
        "Min MPPT Voltage",
        WriteParameter(
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
        None,
        True,
    ),
    # --- Holding register 63: Start Power --- "All mode"
    ParamWrapped(
        "PV Start Power",
        WriteParameter(
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
        None,
        True,
    ),
    # ---------------------------------------------------------------------
    # Battery Config block (PDF section 3/5, registers 150-179)
    # Per-cell voltage settings use 0.001V scale → exposed as mV with
    # multiplier=1, matching how 156 (Float Charging Voltage) is already
    # modelled in read_params.
    # ---------------------------------------------------------------------
    # --- Holding register 151: Battery group number --- "All mode"
    ParamWrapped(
        "Battery Group Number",
        WriteParameter(
            addr=151 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            min=0,
            max=100,
        ),
        None,
        True,
    ),
    # --- Holding register 152: Battery unit number --- "All mode"
    ParamWrapped(
        "Battery Unit Number",
        WriteParameter(
            addr=152 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 153: Battery capacity --- "All mode"
    ParamWrapped(
        "Battery Capacity",
        WriteParameter(
            addr=153 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="Ah",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 156: Float charging voltage --- "All mode"
    ParamWrapped(
        "Float Charging Voltage",
        WriteParameter(
            addr=156 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 157: Low voltage warning (per cell) --- "All mode"
    ParamWrapped(
        "Battery Low Voltage Warning",
        WriteParameter(
            addr=157 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 158: Low voltage fault (per cell) --- "All mode"
    ParamWrapped(
        "Battery Low Voltage Fault",
        WriteParameter(
            addr=158 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 159: High voltage fault (per cell) --- "All mode"
    ParamWrapped(
        "Battery High Voltage Fault",
        WriteParameter(
            addr=159 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 160: Battery start voltage (per cell) --- "All mode"
    ParamWrapped(
        "Battery Start Voltage",
        WriteParameter(
            addr=160 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 161: Single PV to off-grid (per cell) --- "All mode"
    ParamWrapped(
        "Single PV to Off-grid",
        WriteParameter(
            addr=161 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 162: Discharge cut-off voltage (per cell) --- "All mode"
    ParamWrapped(
        "Discharge Cutoff Voltage",
        WriteParameter(
            addr=162 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="mV",
            min=0,
            max=50000,
        ),
        None,
        True,
    ),
    # --- Holding register 172: Battery discharging current --- "HPS"
    ParamWrapped(
        "Battery Discharging Current Setpoint",
        WriteParameter(
            addr=172 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="A",
            min=0,
            max=1000,
        ),
        HPS_ONLY,
        True,
    ),
    # --- Holding register 176: BMS voltage judge enable --- "HPS/PCS"
    # When enabled, SOC judge logic is bypassed in favour of BMS voltage.
    ParamWrapped(
        "BMS Voltage Judge Enable",
        WriteParameter(
            addr=176 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS,
        True,
    ),
    # --- Holding register 177: Discharge recover SOC --- "HPS/PCS"
    ParamWrapped(
        "Discharge Recover SOC",
        WriteParameter(
            addr=177 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="%",
            min=0,
            max=100,
        ),
        HPS_PCS,
        True,
    ),
    # --- Holding register 179: Grid charge SOC --- "HPS"
    ParamWrapped(
        "Grid Charge SOC Enable",
        WriteParameter(
            addr=179 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_ONLY,
        True,
    ),
    # --- Holding register 10: Active power regulation enable --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Active Power Regulation Enable",
        WriteParameter(
            addr=10 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS_HPSTL,
        True,
    ),
    # --- Holding register 12: Manual adjustment enable --- "HPS/PCS/HPSTL"
    ParamWrapped(
        "Manual Adjustment Enable",
        WriteParameter(
            addr=12 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.SWITCH,
            payload_off=0,
            payload_on=1,
        ),
        HPS_PCS_HPSTL,
        True,
    ),
    # --- Holding register 33: PV power setting --- "all model"
    ParamWrapped(
        "PV Power Setting",
        WriteParameter(
            addr=33 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="kW",
            min=0,
            max=500,
        ),
        None,
        True,
    ),
    # --- Holding register 59: Output power setting --- "all model"
    ParamWrapped(
        "Output Power Setting",
        WriteParameter(
            addr=59 + 1,
            count=1,
            dtype=DataType.U16,
            multiplier=1,
            register_type=RegisterTypes.HOLDING_REGISTER,
            ha_entity_type=HAEntityType.NUMBER,
            unit="kW",
            min=0,
            max=500,
        ),
        None,
        True,
    ),
]


atess_param_registry = ParamRegistry(registry=read_params + write_params)


# ---------------------------------------------------------------------------
# Fault alarm bit maps and model code lookup (unchanged from V1 — kept here so
# this module is a drop-in equivalent for consumers that import them).
# ---------------------------------------------------------------------------

# PCS/HPS Fault Alarm bit maps (Atess Modbus RTU v3.22, Figures 4.3.2 - 4.3.9).
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


# PBD Fault Alarm bit maps (Atess Modbus RTU v3.22, Figures 6.3.2 - 6.3.7).
PBD_FAULT_ALARM_BITS: dict[int, dict[int, str]] = {
    1: {  # Figure 6.3.2
        0: "PV_Inverse_Failure",
        1: "IGBT_Failure",
        2: "EEPROM_Write_Failure",
        3: "EEPROM_Read_Failure",
        4: "MainContactor_Failure",
        5: "SlaveContactor_Failure",
        6: "RISO_Failure",
        8: "PV1_VoltHigh_Fault",
        9: "PV2_VoltHigh_Fault",
        10: "PV1_CurrHigh_Fault",
        11: "PV2_CurrHigh_Fault",
        12: "BAT_OverVolt_Fault",
        13: "BAT_UnderVolt_Fault",
        14: "BAT_OverCurr_Fault",
        15: "BAT_OverCharge_Fault",
    },
    2: {  # Figure 6.3.3
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
    3: {  # Figure 6.3.4 — PDF row labels are inconsistent (D1 then two D2 rows);
        # there are 16 rows for 16 bits so the intended mapping is D0..D15.
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
    4: {  # Figure 6.3.5
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
    },
    5: {  # Figure 6.3.6
        0: "Fault_Feedback_Warning",
        1: "Fan_1_Fault_Warning",
        2: "Fan_2_Fault_Warning",
        3: "Fan_3_Fault_Warning",
        4: "Temp_Derating_Warning",
        5: "BAT_UnderVolt_Warning",
        6: "PCS_Communication_Warning",
        8: "PV3_VoltHigh_Fault",
        9: "PV4_VoltHigh_Fault",
        10: "PV5_VoltHigh_Fault",
        11: "PV3_CurrHigh_Fault",
        12: "PV4_CurrHigh_Fault",
        13: "PV5_CurrHigh_Fault",
        14: "PV_L3_OverCurr_Fault",
        15: "PV_L4_OverCurr_Fault",
    },
    6: {  # Figure 6.3.7
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
    },
}


# Addresses for PCS fault alarm registers (1-indexed modbus addresses).
PCS_FAULT_ALARM_ADDRS = [(181 + 1 + i) for i in range(8)]


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


# Atess Modbus RTU v3.22 p127 fig 4.1.2 — register 43 (DTC / Device Type Code)
# maps to a model name string.
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
