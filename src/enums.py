from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional, Any, TypedDict


Unit = Literal[
    "V", "mV", "A", "VA", "kW", "W", "var", "kWh", "°C", "Hz", "kVA", "kVar"
]

class Parameter:
    def __init__(self, name: str, value: Any, unit: Optional[Unit]) -> None:
        self.name = name
        self.value = value # None if uninitialised
        self.unit = unit

class DataType(Enum):
    """
    Data types used by server registers. Used to choose decoding method. depending op server.
    """

    # Unsigned integers
    U16 = "U16"
    U32 = "U32"
    U64 = "U64"

    # Signed integers
    I8L = "I8L"
    I8H = "I8H"
    I16 = "I16"
    I32 = "I32"
    I64 = "I64"

    # Floats
    F32 = "F32"
    F64 = "F64"

    # String
    UTF8 = "UTF8"

    @property
    def size(self) -> Optional[int]:
        """
        Returns the size in bytes for fixed-size types.
        Returns None for variable-size types (UTF8).
        """
        sizes = {
            DataType.I8L: 1,
            DataType.I8H: 1,
            DataType.U16: 2,
            DataType.I16: 2,
            DataType.U32: 4,
            DataType.I32: 4,
            DataType.F32: 4,
            DataType.F32: 4,
            DataType.U64: 8,
            DataType.I64: 8,
            DataType.UTF8: None,
        }
        return sizes[self]

    @property
    def min_value(self) -> Optional[int]:
        """Returns the minimum value for numeric types."""
        ranges = {
            DataType.I8L: -128,  # -2^7
            DataType.I8H: -128,  # -2^7
            DataType.U16: 0,
            DataType.U32: 0,
            DataType.I16: -32768,  # -2^15
            DataType.I32: -2147483648,  # -2^31
            DataType.U64: 0,
            DataType.I64: -18446744073709551616,
            DataType.UTF8: None,
        }
        return ranges[self]

    @property
    def max_value(self) -> Optional[int]:
        """Returns the maximum value for numeric types."""
        ranges = {
            DataType.I8L: 127,  # 2^7-1
            DataType.I8H: 127,  # 2^7-1
            DataType.U16: 65535,  # 2^16 - 1
            DataType.U32: 4294967295,  # 2^32 - 1
            DataType.I16: 32767,  # 2^15 - 1
            DataType.I32: 2147483647,  # 2^31 - 1
            DataType.U64: 18446744073709551615,
            DataType.I64: 9223372036854775807,
            DataType.UTF8: None,
        }
        return ranges[self]





# all parameters are required to have these fields
# @dataclass
# class ModbusParameter:
#     addr: int
#     count: int
#     dtype: DataType
#     register_type: RegisterType
#     multiplier: int = 1
#     unit: Optional[str] = None


# ParameterReq = TypedDict(
#     "ParameterReq",
#     {
#         "addr": int,
#         "count": int,
#         "dtype": DataType,
#         "multiplier": float,
#         "unit": str,
#         "device_class": HADeviceClass,
#         "register_type": RegisterType,
#     },
# )

# # inherit required parameters, add optional parameters
# class Parameter(ParameterReq, total=False):
#     remarks: str
#     state_class: Literal["measurement", "total", "total_increasing"]
#     value_template: str

    # all oarameters are required to have these fields

    

if __name__ == "__main__":
    print(DataType.U16.min_value)
