from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.pdu import ExceptionResponse
# from pymodbus.constants import Endian
import struct
import logging
logger = logging.getLogger(__name__)

from time import time

from server import Server

DEBUG = True
def debug(content):
    if DEBUG: print(content)

class BaseClient:
    def __init__(self, name:str, nickname:str):
        self.name = name
        self.nickname = nickname
        self.client = None


    def read_registers(self, server:Server, register_name:str, register_info:dict):
        """ Read a group of registers using pymodbus 
        
            Reuires implementation of the abstract method 'Server._decoded()'
        """

        address = register_info["addr"]
        dtype =  register_info["dtype"]
        multiplier = register_info["multiplier"]
        count = register_info["count"]
        unit = register_info["unit"]
        slave_id = server.device_addr

        logger.info(f"Reading param {register_name} of {dtype=} from {address=}, {multiplier=}, {count=}, {slave_id=}")

        result = self.client.read_holding_registers(address=    address-1,
                                                    count=      count,
                                                    slave=      slave_id)
        if result.isError():
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

                error_message = exception_messages.get(exception_code, "Unknown Exception")
                logger.error(f"Modbus Exception Code {exception_code}: {error_message}")
            raise Exception(f"Error reading register {register_name}")
        logger.info(f"Raw register value: {result.registers[0]}")
        val = server._decoded(result.registers, dtype)
        if multiplier != 1: val*=multiplier

        logger.info(f"Decoded Value = {value} {unit}")

        return val

    def write_register(self, val, is_float:bool, server:Server, register_name: str, register_info:dict):
        """ Write to an individual register using pymodbus.

            Reuires implementation of the abstract methods 
            'Server._validate_write_val()' and 'Server._encode()'
        """
        # model specific write register validation
        server._validate_write_val(register_name, val)
        
        self.client.write_register(address=register_info["addr"],
                                    value=server._encoded(value),
                                    slave=server.device_addr)

    def connect(self):
        logger.info(f"Connecting to client {self}")

        try: self.client.connect()
        except: 
            logger.error("Client Connection Issue", exc_info=1)
            # raise ConnectionError("Client Connection Issue")

        logger.info(f"Sucessfully connected to {self}")

    def close(self):
        logger.info(f"Closing connection to {self}")
        self.client.close()

    def __str__(self):
        return f"{self.nickname}"


class CustomModbusRtuClient(BaseClient):
    def __init__(self, name:str, nickname:str, port:int, baudrate:int, bytesize:int=8, parity:bool=False, stopbits:int=1):
        super().__init__(name=name, nickname=nickname)
        self.client = ModbusSerialClient(   port=port, baudrate=baudrate, 
                                    bytesize=bytesize, parity='Y' if parity else 'N', stopbits=stopbits, 
                                    timeout=timeout)

    @classmethod
    def from_config(cls, client_cfg: dict, connection_cfg: dict):
        try:
            idx = [c['name'] for c in connection_cfg].index(client_cfg["connection_specs"])  # TODO ugly
        except:
            raise ValueError(f"Connection config {client_cfg['connection_specs']} for client {client_cfg['nickname']} not defined in options.")

        return cls(client_cfg["name"], client_cfg["nickname"], client_cfg["port"], 
                            connection_cfg[idx]["baudrate"], connection_cfg[idx]["bytesize"], 
                            connection_cfg[idx]["parity"], connection_cfg[idx]["stopbits"])


class CustomModbusTcpClient(BaseClient):
    def __init__(self, name:str, nickname:str, host:str, port:int):
        super().__init__(name=name, nickname=nickname)
        self.client = ModbusTcpClient(host=host, port=port)

    @classmethod
    def from_config(cls, client_cfg: dict, connection_cfg: dict):
        try:
            idx = [c['name'] for c in connection_cfg].index(client_cfg["connection_specs"])  # TODO ugly
        except:
            raise ValueError(f"Connection config {client_cfg['connection_specs']} for client {client_cfg['nickname']} not defined in options.")

        return cls(client_cfg["name"], client_cfg["nickname"], connection_cfg[idx]["host"], connection_cfg[idx]["port"]) 



class SpoofClient(BaseClient):
    def __init__(self, name:str, nickname:str, port:int, baudrate:int, bytesize:int=8, parity:bool=False, stopbits:int=1, timeout:int=1):
        self.name = name
        self.nickname = nickname
        self.client = None

    def read_registers(self, server:Server, register_name:str, register_info:dict):
        """ Read a group of registers using pymodbus 
        
            Reuires implementation of the abstract method 'Server._decoded()'
        """

        address = register_info["addr"]
        dtype =  register_info["dtype"]
        multiplier = register_info["multiplier"]
        unit = register_info["unit"]
        count = register_info["count"]

        # result = self.client.read_holding_registers(address-1,
                                                    # count=count,
                                                    # slave=server.device_addr)

        # if result.isError():
        #     raise Exception(f"Error reading register {register_name}")
        # logger.info("return spoof register value U16")

        val = server._decoded( [int(int(time())%2**16)], dtype="U16")

        if multiplier != 1: val*=multiplier
        return round(val, 4)

    def write_register(self, val, is_float:bool, server:Server, register_name: str, register_info:dict):
        """ Write to an individual register using pymodbus.

            Reuires implementation of the abstract methods 
            'Server._validate_write_val()' and 'Server._encode()'
        """
        # model specific write register validation
        server._validate_write_val(register_name, val)
        logger.info("validated write val")
        
        # self.client.write_register(address=register_info["addr"],
        #                             value=server._encoded(value),
        #                             slave=server.device_addr)
        return None

    def connect(self):
        logger.info("Connect spoof")

    def close(self):
        logger.info("Disconnect spoof")


