from abc import abstractmethod, ABC
import logging
from typing import Any, Optional, TypedDict

from .helpers import slugify
from .enums import DataType, HAEntityType, RegisterTypes, Parameter, HADeviceClass, WriteParameter
from .modbus_client import ModbusClient
from .options import DeviceOptions

logger = logging.getLogger(__name__)


class ModbusDevice(ABC):
    """
    Base Device class. Represents modbus Device: its name, serial, model, modbus slave_id. e.g. SungrowInverter(Device).

    Includes functions to be abstracted by model/ manufacturer-specific implementations for
    decoding, encoding data read/ write, reading model code, setting up model-specific registers and checking availability.
    """

    def __init__(self, name, modbus_id) -> None:
        self.name: str = name
        self.modbus_id: int = modbus_id

        self.serial: str = "unknown"
        self._model: str = "unknown"

    @property
    @abstractmethod
    def supported_models(self) -> tuple[str, ...]:
        """ Return a tuple of string names of all supported models for the implementation."""

    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """ Return a string manufacturer name for the implementation."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Parameter]:
        """ Return a dictionary of parameter names and parameter objects."""

    @property
    @abstractmethod
    def write_parameters(self) -> dict[str, WriteParameter]:
        """ Return a dictionary of WriteParameter names and WriteParameter objects."""

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

    @staticmethod
    @abstractmethod
    def _decoded(registers: list, dtype: DataType):
        """
        Device-specific decoding for registers read.

        Parameters:
        -----------
        registers: list: list of ints as read from 16-bit ModBus Registers
        dtype: (DataType.U16, DataType.I16, DataType.U32, DataType.I32, ...)
        """

    @staticmethod
    @abstractmethod
    def _encoded(value: int, dtype: DataType) -> list[int]:
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

    def set_model(self):
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

    def is_available(self, register_name="Device type code"):
        """ Contacts any Device register and returns true if the Device is available """
        logger.info(f"Verifying availability of Device {self.name}")

        available = True

        address = self.parameters[register_name]["addr"]
        dtype = self.parameters[register_name]["dtype"]
        count = self.parameters[register_name]['count']
        register_type = self.parameters[register_name]['register_type']
        slave_id = self.modbus_id

        response = self.connected_client.read(
            address, count, slave_id, register_type)

        if response.isError():
            self.connected_client._handle_error_response(response)
            available = False

        return available

    def read_registers(self, parameter_name: str):
        """ 
        Read a group of registers (parameter) using pymodbus

            Requires implementation of the abstract method 'Device._decoded()'

            Parameters:
            -----------
                - parameter_name: str: slave parameter name string as defined in register map
        """
        device_class_to_rounding: dict[HADeviceClass, int] = {    # TODO define in deviceClass type
            HADeviceClass.REACTIVE_POWER: 0,
            HADeviceClass.ENERGY: 1,
            HADeviceClass.FREQUENCY: 1,
            HADeviceClass.POWER_FACTOR: 1,
            HADeviceClass.APPARENT_POWER: 0, 
            HADeviceClass.CURRENT: 1,
            HADeviceClass.VOLTAGE: 0,
            HADeviceClass.POWER: 0
        }
        param = self.parameters.get(parameter_name, self.write_parameters.get(parameter_name))  # type: ignore
        if param is None:
            logger.info(f"No parameter {parameter_name=} for Device {self.name} defined. Attempt to read.")
            raise ValueError(f"No parameter {parameter_name=} for Device {self.name} defined. Attempt to read.")

        address = param["addr"]
        dtype = param["dtype"]
        multiplier = param["multiplier"]
        # count = param.get('count', dtype.size // 2) #TODO
        count = param["count"]  # TODO
        # unit = param["unit"]
        device_class = param.get("device_class")
        modbus_id = self.modbus_id
        register_type = param["register_type"]

        # TODO count
        logger.debug(
            f"Reading param {parameter_name} ({register_type}) of {dtype=} from {address=}, {multiplier=}, {count=}, {self.modbus_id=}")

        result = self.connected_client.read(
            address, count, modbus_id, register_type)

        if result.isError():
            self.connected_client._handle_error_response(result)
            raise Exception(f"Error reading register {parameter_name}")

        logger.debug(f"Raw register begin value: {result.registers[0]}")
        val = self._decoded(result.registers, dtype)
        if multiplier != 1:
            val *= multiplier
        if device_class is not None and isinstance(val, int) or isinstance(val, float):
            val = round(
                val, device_class_to_rounding.get(device_class, 2)) # type: ignore
        # logger.debug(f"Decoded Value = {val} {unit}")

        return val
    
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

    def connect(self):
        if not self.is_available():
            logger.error(f"Device {self.name} not available")
            raise ConnectionError()
        self.set_model()
        self.setup_valid_registers_for_model()

    @classmethod
    def from_DeviceOptions(
        cls,
        opts: DeviceOptions,
        clients: list[ModbusClient]
    ):
        """
        Initialises modbus_mqtt.Device.Device from modbus_mqtt.loader.DeviceOptions object

        Parameters:
        -----------
            - sr_options: modbus_mqtt.loader.DeviceOptions - options as read from config json
            - clients: list[modbus_mqtt.client.Client] - list of all TCP/Serial clients connected to machine
        """
        name = opts.name
        serial = opts.serialnum
        modbus_id: int = opts.modbus_id  # modbus slave_id

        try:
            idx = [str(client) for client in clients].index(
                opts.connected_client
            )  # TODO ugly
        except ValueError:
            raise ValueError(
                f"Client {opts.connected_client} from Device {name} config not defined in client list"
            )
        connected_client = clients[idx]

        instance = cls(name, modbus_id)
        instance.serial = serial

        return instance
