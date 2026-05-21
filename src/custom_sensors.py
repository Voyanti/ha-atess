"""Loader for user-defined custom sensors.

Reads sensor/register definitions from a Python file mounted at
``/share/ha-atess/mysensors.py``. The user's file declares a list called
``MY_SENSORS`` of :class:`ParamWrapped` entries which are appended to the
built-in register registry on add-on startup.

A template (with commented-out examples) is written to that path on first
run if the file does not already exist.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from .atess_registers_v2 import (
    HPS_ONLY,
    HPS_PCS,
    HPS_PCS_HPSTL,
    HPSTL_ONLY,
    HPSTL_PBD,
    NOT_PCS,
    PBD_ONLY,
    PCS_ONLY,
    ParamWrapped,
)
from .enums import (
    DataType,
    DeviceClass,
    HAEntityType,
    Parameter,
    RegisterTypes,
    WriteParameter,
    WriteSelectParameter,
)

logger = logging.getLogger(__name__)

CUSTOM_DIR = "/share/ha-atess"
CUSTOM_FILE = "mysensors.py"

TEMPLATE = '''"""Custom sensor definitions for the Atess Inverter add-on.

This file is loaded by the add-on on startup. Any entries added to
``MY_SENSORS`` are merged into the built-in register map for every Atess
device managed by the add-on. Restart the add-on after editing this file.

The following names are pre-injected — no imports needed:

    ParamWrapped, Parameter, WriteParameter, WriteSelectParameter,
    DataType, DeviceClass, HAEntityType, RegisterTypes,
    NOT_PCS, HPS_PCS_HPSTL, HPS_PCS, HPSTL_PBD,
    PBD_ONLY, PCS_ONLY, HPS_ONLY, HPSTL_ONLY

Each ``ParamWrapped`` entry takes:
    1. param_name      - unique sensor name shown in Home Assistant
    2. param           - dict (read sensor) or WriteParameter / WriteSelectParameter
    3. included_groups - set of device groups, or None for "all groups"
    4. is_write_param  - False for read sensor, True for write parameter

Note: register addresses in the protocol PDF are 0-indexed; the add-on uses
1-indexed Modbus addresses. Use ``addr = pdf_address + 1``.
"""

MY_SENSORS = [
    # --- Example 1: read an input register as a power sensor (all device groups) ---
    # ParamWrapped(
    #     "Custom Inverter Power",
    #     {
    #         "addr": 100 + 1,
    #         "count": 1,
    #         "dtype": DataType.I16,
    #         "multiplier": 0.1,
    #         "unit": "kW",
    #         "device_class": DeviceClass.POWER,
    #         "register_type": RegisterTypes.INPUT_REGISTER,
    #     },
    #     None,
    #     False,
    # ),

    # --- Example 2: read a holding register as a cumulative energy total (PCS only) ---
    # ParamWrapped(
    #     "Custom PCS Energy",
    #     {
    #         "addr": 200 + 1,
    #         "count": 2,
    #         "dtype": DataType.U32,
    #         "multiplier": 0.1,
    #         "unit": "kWh",
    #         "device_class": DeviceClass.ENERGY,
    #         "register_type": RegisterTypes.HOLDING_REGISTER,
    #         "state_class": "total_increasing",
    #     },
    #     PCS_ONLY,
    #     False,
    # ),

    # --- Example 3: writable number entity for HPS/PCS devices ---
    # ParamWrapped(
    #     "Custom Setpoint",
    #     WriteParameter(
    #         addr=210 + 1,
    #         count=1,
    #         dtype=DataType.U16,
    #         multiplier=1,
    #         register_type=RegisterTypes.HOLDING_REGISTER,
    #         ha_entity_type=HAEntityType.NUMBER,
    #         unit="%",
    #         min=0,
    #         max=100,
    #     ),
    #     HPS_PCS,
    #     True,
    # ),
]
'''


_cached: list[ParamWrapped] | None = None


def _ensure_template() -> str:
    path = os.path.join(CUSTOM_DIR, CUSTOM_FILE)
    try:
        os.makedirs(CUSTOM_DIR, exist_ok=True)
    except OSError as e:
        logger.warning(f"Could not create custom sensor directory {CUSTOM_DIR}: {e}")
        return path
    if not os.path.exists(path):
        try:
            with open(path, "w") as f:
                f.write(TEMPLATE)
            logger.info(f"Wrote custom sensor template to {path}")
        except OSError as e:
            logger.warning(f"Could not write custom sensor template to {path}: {e}")
    return path


def load_custom_params() -> list[ParamWrapped]:
    """Load custom ``ParamWrapped`` entries from the user's mysensors.py.

    Result is cached for the lifetime of the process. Returns an empty list
    if the file is missing, unreadable, or contains no valid entries.
    """
    global _cached
    if _cached is not None:
        return _cached

    path = _ensure_template()
    if not os.path.exists(path):
        _cached = []
        return _cached

    namespace: dict[str, Any] = {
        "ParamWrapped": ParamWrapped,
        "Parameter": Parameter,
        "WriteParameter": WriteParameter,
        "WriteSelectParameter": WriteSelectParameter,
        "DataType": DataType,
        "DeviceClass": DeviceClass,
        "HAEntityType": HAEntityType,
        "RegisterTypes": RegisterTypes,
        "NOT_PCS": NOT_PCS,
        "HPS_PCS_HPSTL": HPS_PCS_HPSTL,
        "HPS_PCS": HPS_PCS,
        "HPSTL_PBD": HPSTL_PBD,
        "PBD_ONLY": PBD_ONLY,
        "PCS_ONLY": PCS_ONLY,
        "HPS_ONLY": HPS_ONLY,
        "HPSTL_ONLY": HPSTL_ONLY,
    }

    try:
        with open(path) as f:
            source = f.read()
        exec(compile(source, path, "exec"), namespace)
    except Exception as e:
        logger.error(f"Failed to load custom sensors from {path}: {e}")
        _cached = []
        return _cached

    raw = namespace.get("MY_SENSORS", [])
    if not isinstance(raw, list):
        logger.error(f"{path}: MY_SENSORS must be a list, got {type(raw).__name__}")
        _cached = []
        return _cached

    valid: list[ParamWrapped] = []
    for entry in raw:
        if isinstance(entry, ParamWrapped):
            valid.append(entry)
        else:
            logger.warning(
                f"{path}: skipping entry of type {type(entry).__name__}; expected ParamWrapped"
            )

    if valid:
        logger.info(f"Loaded {len(valid)} custom sensor(s) from {path}")
    else:
        logger.info(f"No custom sensors defined in {path}")

    _cached = valid
    return _cached
