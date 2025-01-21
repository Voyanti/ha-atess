import abc
import logging

logger = logging.getLogger(__name__)


class Server(metaclass=abc.ABCMeta):
    def __init__(self, name:str, nickname:str, serialnum:str, device_addr:int, connected_client=None):
        self.name: str = name
        self.nickname: str = nickname
        self.serialnum: str = serialnum
        self.connected_client = connected_client
        self.model:str | None = None
        self.model_info: dict | None = None
        self.device_addr:int| None = device_addr

    @classmethod
    def from_config(cls, server_cfg:dict, clients:list):
        """ Returns instance of Server/subclass after finding a pointer to the connected client, using its nickname as key.
        """
        # assume valid configLoader object
        try:
            idx = [str(client) for client in clients].index(server_cfg["connected_client"])  # TODO ugly
        except:
            raise ValueError(f"Client {server_cfg['connected_client']} from server {server_cfg['nickname']} config not defined in client list")

        instance = cls(server_cfg["name"], server_cfg["nickname"], server_cfg["serialnum"], server_cfg['device_addr'], connected_client=clients[idx])
        logger.info(f"Server {instance.nickname} set up.")
        return instance
        # return Server(server_cfg["name"], server_cfg["nickname"], server_cfg["serialnum"], server_cfg['device_addr'], connected_client=clients[idx])
    
    def read_model(self, device_type_code_param_key="Device type code"):
        logger.info(f"Reading model for server")
        modelcode = self.connected_client.read_registers(self, device_type_code_param_key, self.registers[device_type_code_param_key])
        self.model = self.device_info[modelcode]['model']
        self.model_info = self.device_info[modelcode]
        logger.info(f"Model read as {self.model}")

        if self.model not in self.supported_models: raise NotImplementedError(f"Model not supported in implementation of Server, {self}")

    def is_available(self, register_name="Device type code"):
        """ Contacts any server register and returns true if the server is available """
        logger.info(f"Verifying availability of server {self.nickname}")

        available = True

        address = self.registers[register_name]["addr"]
        count = self.registers[register_name]["count"]
        slave_id = self.device_addr
        register_type = self.registers[register_name]['register_type']
        response = self.connected_client._read(address, count, slave_id, register_type)

        if response.isError(): 
            self.sonnected_client._handle_error_response(response, register_name)
            available = False

        return available
    
    @classmethod
    @abc.abstractmethod
    def _decoded(cls, content, dtype):
        "Server-specific decoding must be implemented."
        pass

    @classmethod
    @abc.abstractmethod
    def _encoded(cls, content):
        "Server-specific encoding must be implemented."
        pass

    @abc.abstractmethod
    def setup_valid_registers_for_model(self):
        """ Server-specific logic for removing unsupported or selecting supported
            registers for the specific model must be implemented.
            Removes invalid registers for the specific model of inverter.
            Requires self.model. Call self.read_model() first."""
        pass
