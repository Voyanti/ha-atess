from time import sleep
import atexit
import logging
import subprocess

from loader import ConfigLoader
from client import CustomModbusRtuClient, CustomModbusTcpClient
from sungrow_inverter import SungrowInverter
from sungrow_logger import SungrowLogger
from sungrow_meter import AcrelMeter
from modbus_mqtt import MqttClient
from paho.mqtt.enums import MQTTErrorCode


logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with timestamp
    datefmt="%Y-%m-%d %H:%M:%S"  # Date format
)
logger = logging.getLogger(__name__)

mqtt_client = None
pause_interval = 3
read_interval = 0.001

def exit_handler(servers, modbus_clients, mqtt_client):          
    logger.info("Exiting")
    # publish offline availability for each server
    for server in servers:
        mqtt_client.publish_availability(False, server)
    logger.info("Closing client connections on exit")
    for client in modbus_clients:
        client.close()

    mqtt_client.loop_stop()

atexit.register(exit_handler, mqtt_client)

try:
    # Read configuration
    servers_cfgs, clients_cfgs, connection_specs, mqtt_cfg = ConfigLoader.load()

    logger.info("Instantiate clients")
    clients = []
    for client_cfg in clients_cfgs:
        if client_cfg["type"] == "RTU": clients.append(CustomModbusRtuClient.from_config(client_cfg, connection_specs))
        elif client_cfg["type"] == "TCP": clients.append(CustomModbusTcpClient.from_config(client_cfg, connection_specs))
    logger.info(f"{len(clients)} clients set up")
    if len(clients) == 0: raise RuntimeError(f"No clients available")
    
    logger.info("Instantiate servers")
    servers = []
    for server_cfg in servers_cfgs:
        if server_cfg["server_type"] == "SUNGROW_INVERTER": servers.append(SungrowInverter.from_config(server_cfg, clients))
        elif server_cfg["server_type"] == "SUNGROW_LOGGER": servers.append(SungrowLogger.from_config(server_cfg, clients))
        elif server_cfg["server_type"] == "ACREL_METER": servers.append(AcrelMeter.from_config(server_cfg, clients))
        else:
            logging.error(f"Server type key '{server_cfg['server_type']}' not defined in ServerTypes.")
            raise ValueError(f"Server type key '{server_cfg['server_type']}' not defined in ServerTypes.")
    logger.info(f"{len(servers)} servers set up")
    if len(servers) == 0: raise RuntimeError(f"No supported servers configured")

    # Connect to clients
    for client in clients:
        client.connect()

    # Connect to Servers
    for server in servers:
        if not server.is_available():
            logger.error(f"Server {server.nickname} not available")
            raise ConnectionError()                             
        server.read_model()
        server.setup_valid_registers_for_model()

    # Setup MQTT Client
    mqtt_client = MqttClient(mqtt_cfg)
    succeed: MQTTErrorCode = mqtt_client.connect(host=mqtt_cfg["host"], port=mqtt_cfg["port"])
    if succeed.value != 0: logger.info(f"MQTT Connection error: {succeed.name}, code {succeed.value}")
    
    sleep(read_interval)
    mqtt_client.loop_start()
    
    # Publish Discovery Topics
    for server in servers:
        mqtt_client.publish_discovery_topics(server)

    # every read_interval seconds, read the registers and publish to mqtt
    while True:
        for server in servers:
            for register_name, details in server.registers.items():
                client = server.connected_client
                value = client.read_registers(server, register_name, details)
                mqtt_client.publish_to_ha(register_name, value, server)
                sleep(read_interval)
            logger.info(f"Published all parameter values for {server.name=}")   

        # publish availability
        sleep(pause_interval)
finally:
    exit_handler(servers, clients, mqtt_client)
