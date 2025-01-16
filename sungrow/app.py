from time import sleep
import atexit
import logging
import subprocess

from modbus_mqtt import MqttClient
from loader import ConfigLoader
from client import CustomModbusRtuClient, CustomModbusTcpClient
from server import Server
from sungrow_inverter import SungrowInverter

# from client import SpoofClient as Client

logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format with timestamp
    datefmt="%Y-%m-%d %H:%M:%S"  # Date format
)
logger = logging.getLogger(__name__)

mqtt_client = None
read_interval = 2


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


def find_ip():
    logger.info(f"Looking for MAC AC:19:9F:10:5F:89")
    command = "nmap -sP 10.0.0.1/24 | grep -B 2 'AC:19:9F:10:5F:89' | head -n 1 | awk '{print $5}'"
    ip = subprocess.run(command, shell=True, text=True, capture_output=True)
    logger.info(f"Found IP f{ip}")
    return ip

try:
    # Read configuration
    servers_cfgs, clients_cfgs, connection_specs, mqtt_cfg = ConfigLoader.load()

    # temp get ip of host
    ip = find_ip()
    connection_specs[0]['host'] = ip

    # Instantiate clients (modbus adapters)
    clients = []
    for client_cfg in clients_cfgs:
        if client_cfg["type"] == "RTU": clients.append(CustomModbusRtuClient.from_config(client_cfg, connection_specs))
        elif client_cfg["type"] == "TCP": clients.append(CustomModbusTcpClient.from_config(client_cfg, connection_specs))
    # Instantiate servers
    servers = [SungrowInverter.from_config(server_cfg, clients) for server_cfg in servers_cfgs]

    # Connect to clients
    for client in clients:
        client.connect()

    # Connect to Servers
    # for server in servers:
        # server.verify_serialnum()                              
            
        # server.read_model()
        # modelcode = server.connected_client.read_register(server, "Device Type Code", server.registers["Device Type Code"])
        # sever.model = server.device_info[modelcode]
        # TODO find valid registers
        # - get limits for settable params TODO

    # Setup MQTT Client
    mqtt_client = MqttClient(mqtt_cfg)
    mqtt_client.connect(host=mqtt_cfg["host"], port=mqtt_cfg["port"])
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

        # publish availability
        logger.info("Published all register values.")
        sleep(read_interval)
finally:
    exit_handler(servers, clients, mqtt_client)
