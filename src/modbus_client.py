from enum import Enum
from typing import Optional
from .options import ModbusTCPOptions, ModbusRTUOptions
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.pdu import ExceptionResponse, ModbusPDU
from pymodbus.exceptions import ModbusIOException
import logging
from .options import ModbusTCPOptions, ModbusRTUOptions
from time import sleep
logger = logging.getLogger(__name__)

# Enable pymodbus logging
# log = logging.getLogger("pymodbus")
# log.setLevel(logging.DEBUG)

class RegisterType(Enum):
    INPUT_REGISTER = 3  # Read Only
    HOLDING_REGISTER = 4  # Read/ Write



class ModbusClient:
    """
        Modbus client representation: name and pymodbus client.

        Wraps around pymodbus.client.ModbusSerialClient | pymodbus.client.ModbusTCPClient.
    """

    def __init__(self, name: str, client: ModbusSerialClient | ModbusTcpClient):
        """_summary_

        Args:
            name (str): _description_
            client (ModbusSerialClient | ModbusTcpClient): _description_
        """        
        self.name = name
        self.client = client

    def read(self, address: int, count: int, slave_id: int, register_type: RegisterType) -> ModbusPDU:
        """
        Calls the appropriate read function, based on the register type (input / holding).

        On ModbusIOException: wait 20s and retry

        Args:
            address (int): 1-indexed modbus register address
            count (int): number of consecutive 16-bit modbus registers to read
            slave_id (int): modbus slave_id
            register_type (RegisterType): holding or input register

        Raises:
            ValueError: for unsupported register_type

        Returns:
            ModbusPDU: _description_
        """        
        logger.debug(f"Reading param from {address=}, {count=} on {slave_id=}, {register_type=}")

        need_result = True
        while need_result:
            try:
                if register_type == RegisterType.HOLDING_REGISTER:
                    result = self.client.read_holding_registers(address=address-1,
                                                                count=count,
                                                                slave=slave_id)
                elif register_type == RegisterType.INPUT_REGISTER:
                    result = self.client.read_input_registers(address=address-1,
                                                            count=count,
                                                            slave=slave_id)
                else:
                    logger.info(f"unsupported register type {register_type}")
                    raise ValueError(f"unsupported register type {register_type}")
                
                # no IOexception:
                need_result = False
            except ModbusIOException as e:
                # need_result = True
                logger.info(str(e))
                logger.info(f"Sleep 20s and retry")
                sleep(20)

        return result
    
    def write(self, values: list[int], address: int, slave_id: int, register_type: RegisterType) -> ModbusPDU:
        """Writes a list of encoded ints to 16-bit registers, 
        starting at the 1-indexed address specified

        Args:
            values (list[int]): list of ints encoding the value
            address (int): modbus register address (1-indexed)
            slave_id (int): modbus slave_id
            register_type (RegisterType): only RegisterTypes.HOLDING_REGISTER. Used for validation 

        Raises:
            ValueError: if register_type not RegisterTypes.HOLDING_REGISTER

        Returns:
            ModbusPDU: modbus client response
        """        
        if register_type != RegisterType.HOLDING_REGISTER:
            raise ValueError(f"unsupported register type {register_type}")
        
        return self.client.write_registers(address=address-1,
                                            values=values,
                                            slave=slave_id)

    def connect(self, num_retries=2, sleep_interval=3) -> None:
        logger.info(f"Connecting to client {self}")

        for i in range(num_retries):
            connected: bool = self.client.connect()
            if connected:
                break

            logging.info(f"Couldn't connect to {self}. Retrying")
            sleep(sleep_interval)

        if not connected:
            logger.error(
                f"Client Connection Issue after {num_retries} attempts.")
            raise ConnectionError(f"Client {self} Connection Issue")

        logger.info(f"Sucessfully connected to {self}")

    def close(self):
        logger.info(f"Closing connection to {self}")
        self.client.close()

    def _handle_error_response(self, result):
        if isinstance(result, ExceptionResponse):
            exception_code = result.exception_code

            # Modbus exception codes and their meanings
            exception_messages = {
                1: "Illegal Function",
                2: "Illegal Data Address",
                3: "Illegal Data Value",
                4: "Slave Device Failure",
                5: "Acknowledge",
                6: "Slave Device Busy",
                7: "Negative Acknowledge",
                8: "Memory Parity Error",
                10: "Gateway Path Unavailable",
                11: "Gateway Target Device Failed to Respond"
            }

            error_message = exception_messages.get(
                exception_code, "Unknown Exception")
            logger.error(
                f"Modbus Exception Code {exception_code}: {error_message}")
        else:
            logger.error(
                f"Non Standard Modbus Exception. Cannot Decode Response")

def modbusClientFactory(modbus_client_options: ModbusTCPOptions | ModbusRTUOptions) -> ModbusClient:
    client: ModbusSerialClient | ModbusTcpClient

    if isinstance(modbus_client_options, ModbusTCPOptions):
        client = ModbusTcpClient(
            host=modbus_client_options.host, port=modbus_client_options.port)
    elif isinstance(modbus_client_options, ModbusRTUOptions):
        client = ModbusSerialClient(port=modbus_client_options.mount, baudrate=modbus_client_options.baudrate,
                                            bytesize=modbus_client_options.bytesize, parity='Y' if modbus_client_options.parity else 'N',
                                            stopbits=modbus_client_options.stopbits)
    return ModbusClient(modbus_client_options.name, client)

class SpoofClient:
    """
        Spoofed Modbus client representation: name, nickname (ha_display_name), and pymodbus client.

        Wraps around pymodbus.client.ModbusSerialClient | pymodbus.client.ModbusTCPClient to
        fan out dictionary information, and decode/ encode register values when reading/ writing/
    """
    class SpoofResponse:
        def __init__(self, registers: Optional[list[int]] = None):
            if registers: self.registers = registers

        def isError(self): return False

    def __init__(self):
        self.name = "Client1"

    def read(self, address, count, slave_id, register_type):
        logger.debug(f"SPOOFING READ")
        response = SpoofClient.SpoofResponse([73 for _ in range(count)])
        return response
    
    def write(self, values: list[int], address: int, slave_id: int, register_type):
        """Writes a list of encoded ints to 16-bit registers, 
        starting at the 1-indexed address specified

        Args:
            values (list[int]): list of ints encoding the value
            address (int): modbus register address (1-indexed)
            slave_id (int): modbus slave_id
            register_type (RegisterType): only RegisterTypes.HOLDING_REGISTER. Used for validation 

        Raises:
            ValueError: if register_type not RegisterTypes.HOLDING_REGISTER

        Returns:
            ModbusPDU: modbus client response
        """        
        if not register_type == RegisterType.HOLDING_REGISTER:
            logger.info(f"unsupported write register type {register_type}")
            raise ValueError(f"unsupported register type {register_type}")
        
        logger.info(f"Spoof Write of {values} at {address=} ({register_type=}) of {values=} on {slave_id=}")
        return SpoofClient.SpoofResponse()

    def connect(self, num_retries=2, sleep_interval=3):
        logger.info(f"SPOOFING CONNECT to {self}")

    def close(self):
        logger.info(f"SPOOFING DISCONNECT to {self}")

    def __str__(self):
        """
            self.nickname is used as a unique id for finding the client to which each server is connected.
        """
        return f"{self.name}"
