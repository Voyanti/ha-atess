from enum import Enum
from typing import Any, Optional, TypedDict

from src.homeassistant import HADeviceClass
from src.enums import DataType, Parameter, Unit


class RegisterType(Enum):
    INPUT_REGISTER = 3  # Read Only
    HOLDING_REGISTER = 4  # Read/ Write

class ModbusParameter(Parameter):
    def __init__(self, name: str, register_type: RegisterType, start_address: int, dtype: DataType, unit: Optional[Unit], num_registers: int = 1, multiplier: int = 1) -> None:
        super().__init__(name=name, value=None, unit=unit)
        self.register_type = register_type
        self.start_address = start_address  # 1-indexed
        self.num_registers = num_registers
        self.dtype = dtype
        self.multiplier = multiplier

    @property
    def end_address(self):
        """
            Exclusive end address (last value is stored at previous address)
        """
        return self.start_address + self.num_registers

    def __str__(self):
        """
        Used to convert from legacy implementation.
        """
        s = ""
        if self.num_registers == 1:
            s += f"ModbusParameter('{self.name}',\n\t\t{self.register_type}, {self.start_address}, {self.dtype}, '{self.unit}'"
        else:
            s += f"ModbusParameter('{self.name}',\n\t\t{self.register_type},  {self.start_address}, {self.dtype}, '{self.unit}', num_registers={self.num_registers}"

        if self.multiplier == 1:
            return s + ")"
        else:
            return s + f", multiplier={self.multiplier})"


# old:


WriteParameterReq = TypedDict(
    "WriteParameterReq",
    {
        "addr": int,
        "count": int,
        "dtype": DataType,
        "multiplier": float,
        "register_type": RegisterType,
        'ha_entity_type': Any,
    },
)

class WriteSelectParameterReq(WriteParameterReq, total=True):
    # select
    options: list[str] # required for select

class WriteSelectParameter(WriteSelectParameterReq, total=False):
    value_template: str
    command_template: str
    
class WriteParameter(WriteParameterReq, total=False):
    device_class: HADeviceClass # when not specified w=for a switch, a none type switch is used

    # number
    unit: str
    min: float  
    max: float

    # switch
    payload_off: int
    payload_on: int
