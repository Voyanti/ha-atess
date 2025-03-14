import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
import json
import logging

from interfaces.base_ha_mqtt_adapter import IHaMqttAdapter
from src.helpers import generate_uuid, slugify
from src.loader import Options

from time import sleep

from src.homeassistant import HAEntityType

logger = logging.getLogger(__name__)


class HAMqttClient():
    """
        paho MQTT abstraction for home assistant with info level logging
    """
    def __init__(self, base_topic: str, homeassisant_discovery_topic: str) -> None:
        self.base_topic = base_topic
        self.ha_discovery_topic = homeassisant_discovery_topic

        uuid = generate_uuid()
        self.client = mqtt.Client(CallbackAPIVersion.VERSION2, f"modbus-{uuid}")

        # callbacks
        def on_connect(client, userdata, connect_flags, reason_code, properties):
            if reason_code == 0:
                logger.info(f"Connected to MQTT broker.")
            else:
                logger.info(
                    f"Not connected to MQTT broker.\nReturn code: {reason_code=}")

        def on_disconnect(client, userdata, message):
            logger.info("Disconnected from MQTT broker")

        def on_message(client, userdata, message):
            logger.info("Received message on MQTT")
            self.message_handler(message)

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_message = on_message

    # Wrap paho-mqtt client functions
    def connect(self, host: str, port: int, username: str, password: str):
        logger.info(f"Connecting to MQTT broker asynchronously")

        self.client.username_pw_set(username, password)
        connection_error: MQTTErrorCode = self.client.connect(host, port)

        if connection_error:
            logger.info(f"MQTT Connection error: {connection_error.name}, code {connection_error.value}")

    def loop_stop(self):
        return self.client.loop_stop()
    
    def loop_start(self):
        return self.client.loop_start()

    # Custom functionality
    def build_discovery_topics(self, adapter: IHaMqttAdapter):
        
    def publish_discovery_topic(self):
        self.client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)