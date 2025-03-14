from abc import abstractmethod, ABC
from dataclasses import dataclass
import logging
from typing import Any, Iterable, Optional, TypedDict

from src.enums import DataType
from src.modbus_types import ModbusParameter, RegisterType
from src.helpers import slugify
from src.homeassistant import device_class_to_rounding
from src.modbus_client import ModbusClient
from src.options import DeviceOptions

logger = logging.getLogger(__name__)

@dataclass
class ModbusRegisterExtent:
    """ Stores the minimum and maximum address to read 
    to internal state for each register type for the given device"""
    min: int
    max: int

class BatchedModbusParameters:
    def __init__(self, register_type: RegisterType, extent: ModbusRegisterExtent, batch_size: int = 125):
        self.register_type = register_type
        self.extent = extent

        self.batches = tuple(self.batch(range(extent.min, extent.max), batch_size))

        self.state: list[int] = [0]*(extent.max-extent.min)

    @staticmethod
    def batch(iterable, batch_size=1):
        l = len(iterable)
        for ndx in range(0, l, batch_size):
            yield iterable[ndx:min(ndx + batch_size, l)]
    

class ModbusDevice(ABC):
    """
    Base Device class. Represents modbus Device: its name, serial, model, modbus slave_id. e.g. SungrowInverter(Device).

    Includes functions to be abstracted in model/ manufacturer-specific implementations for
    decoding, encoding data read/ write, reading model code, setting up model-specific registers and checking availability.
    """

    def __init__(self, name, modbus_id, batch_size=125) -> None:
        self.name: str = name
        self.modbus_id: int = modbus_id

        self.serial: str = "unknown"
        self._model: str = "unknown"

        # batched state
        self.batched_parameters: dict[RegisterType, BatchedModbusParameters]
        for reg_type in RegisterType:
            extent = self._find_register_extent(reg_type)
            self.batched_parameters[reg_type] = BatchedModbusParameters(
                reg_type,
                extent,
            )

        logger.info(f"\nCreated batches for server {self.name}")
        logger.debug(f"{self.batched_parameters=}")

        logger.info(f"Server {self.name} set up.")

    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """ Return a string manufacturer name for the implementation."""

    @property
    @abstractmethod
    def supported_models(self) -> tuple[str, ...]:
        """ Return a tuple of string names of all supported models for the implementation."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, ModbusParameter]:
        """ Return a dictionary of parameter names and parameter objects."""

    def get_parameter(self, name: str) -> ModbusParameter:
        """get a ModbusParameter by name

        Args:
            name (str): 

        Raises:
            ValueError: if parameter with name not available

        Returns:
            ModbusParameter: 
        """        
        param = self.parameters.get(name)

        if param is None:
            raise ValueError(f"No parameter {name} for Device {self.name} defined. Attempt to read.")
        
        return param

    # @property
    # def write_parameters_slug_to_name(self) -> dict[str, str]:
    #     """ Return a dictionary of mapping slugs to writeparameter names."""
    #     write_parameters_slug_to_name: dict[str, str] = {slugify(name):name for name in self.write_parameters.copy()}
    #     return write_parameters_slug_to_name

    @abstractmethod
    def read_model(self) -> str:
        """
            Reads model name register if available and decodes it.

            :returns: model_name
        """

    @abstractmethod
    def setup_valid_registers_for_model(self):
        """ Device-specific logic for removing unsupported or selecting supported
            registers for the specific model must be implemented.
            Removes invalid registers for the specific model of inverter.
            Requires self.model. Call self.read_model() first."""

    def _find_register_extent(self, register_type: RegisterType) -> ModbusRegisterExtent:
        """ Find the minimum and maximum address of registers to be read for 
            holding and input register types.

            result: internal state for each:
                self.holding_min_addr int inclusive
                self.holding_max_addr int exclusive
                self.input_min_addr int inclusive
                self.input_max_addr int exclusive
        """
        logger.info(f"Finding register extents for reading batches")

        # filter parameters down by register type e.g. holding
        params  = filter(lambda x: x.register_type == register_type, self.parameters.values())

        def to_addr(item: ModbusParameter):
            return item.start_address
        
        # find min and max addresses
        holding_min_addr = min(params, key=to_addr).start_address
        holding_max_addr = max(params, key=to_addr).end_address

        extent = ModbusRegisterExtent(holding_min_addr, holding_max_addr)

        logger.info(f"self.name:")
        logger.info(f"{register_type}: {extent}")

        return extent

    @staticmethod
    @abstractmethod
    def decode_registers(registers: list, dtype: DataType) -> Any:
        """
        Device-specific decoding for registers read.

        Parameters:
        -----------
        registers: list: list of ints as read from 16-bit ModBus Registers
        dtype: (DataType.U16, DataType.I16, DataType.U32, DataType.I32, ...)
        """

    @staticmethod
    @abstractmethod
    def encode_value(value: int, dtype: DataType) -> list[int]:
        "Device-specific encoding of content"

    @property
    def model(self) -> str:
        """ Return a string model name for the implementation.
            Ahould be read in using Device.read_model(). 
            Device.set_model is called in Device.connect(), which sets the model.
            
            model is used in seupt_valid_registers_for_model
            Provided to fascilitate Device types where the model cannot be read."""
        return self._model
    
    @model.setter
    def model(self, value):
        self._model = value

    def set_model(self) -> None:
        """
            Reads model-holding register, decodes it and sets self.model: str to its value..
            Specify decoding in Device.device_info = {modelcode:    {name:modelname, ...}  }
        """
        logger.info(f"Reading model for Device {self.name}")
        self.model = self.read_model()
        logger.info(f"Model read as {self.model}")

        if self.model not in self.supported_models:
            raise ValueError(
                f"Model not supported in implementation of Device, {self}")

    @property
    @abstractmethod
    def availability_parameter(self) -> str:
        """ Return tha name of a parameter to use as health check"""
        
    
    # def read_batches(self) -> None:
    #     """
    #     Read holding and input registers for the server in batches of size 125, and save to internal state
    #     """
    #     self.holding_state = []
    #     self.input_state = []

    #     for batch in self.holding_batches:
    #         logger.info(f"Reading holding batch from {batch[0]} to {batch[-1]}, {len(batch)=}")
    #         result = self.connected_client.read(
    #             batch[0], len(batch), self.modbus_id, RegisterType.HOLDING_REGISTER)   # TODO check

    #         if result.isError():
    #             self.connected_client._handle_error_response(result)
    #             raise Exception(f"Error reading batch {batch=}")
            
    #         self.holding_state.extend(result.registers)
            
    #     for batch in self.input_batches:
    #         logger.info(f"Reading input batch from {batch[0]} to {batch[-1]}, {len(batch)=}")
    #         result = self.connected_client.read(
    #             batch[0], len(batch), self.modbus_id, RegisterType.INPUT_REGISTER)

    #         if result.isError():
    #             self.connected_client._handle_error_response(result)
    #             raise Exception(f"Error reading batch {batch=}")
            
    #         self.input_state.extend(result.registers)

    def update_all_value_from_state(self):
        modbus_id = self.modbus_id
            
        for parameter in self.parameters.values():

            logger.debug(
                f"Reading param {parameter}")
            
            relevant_state = self.batched_parameters[parameter.register_type]
            
            offset = parameter.address - relevant_state.extent.min
            # logger.debug(f"{address=}, {count=}, offset={self.holding_addr_extent[0]}")
            # logger.debug(f"start {address-self.holding_addr_extent[0]}, exclusive_end = { address+count-self.holding_addr_extent[0]}")
            result = self.holding_state[offset: offset+parameter.num_registers] # address is 1-indexed

            logger.debug(f"Raw register begin value: {result[0]}")
            val = self.decode_registers(result, parameter.dtype)
            if parameter.multiplier != 1:
                val *= parameter.multiplier
            # if device_class is not None and isinstance(val, int) or isinstance(val, float):
            #     val = round(
            #         val, device_class_to_rounding.get(device_class, 2)) # type: ignore
            # logger.debug(f"Decoded Value = {val} {unit}")

            parameter.value = val
    
    def write_registers(self, parameter_name_slug: str, value: Any, modbus_id_override: Optional[int]=None) -> None:
        """ 
        Write a group of registers (parameter) using pymodbus

        Requires implementation of the abstract method 'Device._encoded()'

        Finds correct write register name using mapping from Device.write_registers_slug_to_name
        """
        parameter_name = self.write_parameters_slug_to_name[parameter_name_slug]
        param: WriteParameter = self.write_parameters[parameter_name]

        address = param["addr"]
        dtype = param["dtype"]
        multiplier = param["multiplier"]
        count = param["count"]  # TODO
        if modbus_id_override is not None: 
            modbus_id = modbus_id_override
        else:
            modbus_id = self.modbus_id
        register_type = param["register_type"]

        if param["ha_entity_type"] == HAEntityType.SWITCH:
            value = int(value, base=0) # interpret string as integer literal. supports auto detecting base
        elif dtype != DataType.UTF8:
            value = float(value)
            if multiplier != 1:
                value /= multiplier
        print(value, dtype)
        values = self._encoded(value, dtype)

        logger.info(
            f"Writing {values} to param {parameter_name} ({register_type}) of {dtype=} from {address=}, {multiplier=}, {count=}, {modbus_id=}")

        result = self.connected_client.write(values, address, modbus_id, register_type)

        if result.isError():
            self.connected_client._handle_error_response(result)
            raise Exception(f"Error writing register {parameter_name}")

        if param.get("unit") is not None:
            logger.info(f"Wrote {value=} unit={param.get('unit')} as {values=} to {parameter_name}.")
        else:
            logger.info(f"Wrote {value=} as {values=} to {parameter_name}.")

    def connect(self) -> None:
        if not self.is_available():
            logger.error(f"Device {self.name} not available")
            raise ConnectionError()
        self.set_model()
        self.setup_valid_registers_for_model()
        self.find_register_extent()
        self.create_batches()

