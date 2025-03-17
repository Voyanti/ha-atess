from implemented_servers import DeviceTypes
from modbus_client import ModbusClient, modbusClientFactory
from modbus_device import ModbusDevice
from options import DeviceOptions, ModbusRTUOptions, ModbusTCPOptions
import logging
logger = logging.getLogger(__name__)

class ModbusGroup:
    """Represents a physical bus or devices available through a common ip/ port
    """
    def __init__(self, client: ModbusClient, devices: list[ModbusDevice]):
        self.client: ModbusClient
        self.devices: list[ModbusDevice]

    def __repr__(self):
        return f"Bus: {self.client.name} with devices {[dev.name for dev in self.devices]} "

    def connect(self):
        self.client.connect()

        for device in self.devices:
            model_parameter = device.get_model_parameter()
            if model_parameter is not None:
                device.model = self.client.read(model_parameter.start_address, model_parameter.num_registers, device.modbus_id, model_parameter.register_type)
            
                device.setup_valid_registers_for_model()

    def disconnect(self):
        return self.client.close()
    
    def read_all_in_batches(self):
        """Reads registers in batches from all connected devices into addon internal state
        """
        for device in self.devices:
            for state_group in device.batched_parameters.values():
                for batch in state_group.batches:
                    logger.info(f"Reading input batch from {batch[0]} to {batch[-1]}, {len(batch)=}")
                    result = self.client.read(batch[0], len(batch), device.modbus_id, state_group.register_type)
                    state_group.state[batch[0], batch[-1]] = result.registers

    def update_all_values_from_state(self):
        for device in self.devices:
            device.update_all_values_from_state()

    @property
    def all_parameters(self):
        for device in device:
            


def busFactory(device_options: list[DeviceOptions], client_options: list[ModbusRTUOptions| ModbusTCPOptions]) -> list[ModbusGroup]:
    """Sets up a list of ModbusGroup (Busses) from options objects"""
    def match_client(client: ModbusRTUOptions| ModbusTCPOptions, device_options: DeviceOptions) -> bool:
        return device_options.connected_client == client.name
    
    groups: list[ModbusGroup] = []
    for client_configuration in client_options:
        # instantiate modbus client from client options
        client = modbusClientFactory(client_configuration)

        # find all connected devices
        device_configs = filter(match_client, device_options)

        # instantiate correct devicetype version of each ModbusDevice
        modbus_devices = []
        for dev in device_configs:
            device = DeviceTypes[dev.device_type].value(dev.name, dev.modbus_id)
            if dev.serialnum != "":
                device.serial = dev.serialnum
            modbus_devices.append(device)

        group = ModbusGroup(client, modbus_devices)
        groups.append(group)
        logger.info(f"{group}")

    logger.info(f"{len(groups)}Groups/ busses set up:")
    return groups
