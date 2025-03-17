from time import sleep
from datetime import datetime, timedelta
import atexit
import logging
from typing import Callable

from mosbus_bus import ModbusGroup, busFactory
from src.loader import load_validate_options
from src.options import Options
from src.modbus_client import ModbusClient, modbusClientFactory
from src.implemented_servers import DeviceTypes
from src.modbus_device import ModbusDevice
from src.mqtt_client import HAMqttClient


import sys

logging.basicConfig(
    level=logging.INFO,  # Set logging level
    # Format with timestamp
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
)
logger = logging.getLogger(__name__)

READ_INTERVAL = 0.004


def exit_handler(
    busses: list[ModbusGroup],
    mqtt_client: HAMqttClient,
) -> None:
    logger.info("*======*")
    logger.info("| Exit |")
    logger.info("*======*")
    # # publish offline availability for each server
    # for server in servers:
    #     mqtt_client.publish_availability(False, server)
    logger.info("Closing client connections on exit")
    for bus in busses:
        bus.disconnect()

    mqtt_client.loop_stop()


class AddOn:
    def __init__(self):
        self.OPTIONS = load_validate_options()

    def setup(self):
        self.sleep_if_midnight()

        # Setup MQTT Client
        self.mqtt_client = HAMqttClient(
            self.OPTIONS.mqtt_base_topic,
            self.OPTIONS.mwtt_ha_discovery_topic,
        )

        # Setup busses
        self.busses = busFactory(self.OPTIONS.devices, self.OPTIONS.modbus_clients)

        atexit.register(exit_handler, self.busses, self.mqtt_client)

    def connect(self):
        for bus in self.busses:
            bus.connect()

        # connect to mqtt
        self.mqtt_client.connect(
            self.OPTIONS.mqtt_host,
            self.OPTIONS.mqtt_port,
            self.OPTIONS.mqtt_user,
            self.OPTIONS.mqtt_password,
        )
        self.mqtt_client.loop_start()

        # Publish Discovery Topics
        for device in self.devices:
            self.mqtt_client.publish_discovery_topics(device)  # TODO

    def loop(self, loop_once=False):
        while True:
            for bus in self.busses:
                bus.read_all_in_batches()  # TODO pass down read interval
                bus.update_all_values_from_state()

                # publisch to HA

            # publish availability
            sleep(self.pause_interval)

            if loop_once:
                break
            self.sleep_if_midnight()

    def sleep_if_midnight(self) -> None:
        """
        Sleeps if the current time is within 3 minutes before or 5 minutes after midnight.
        Uses efficient sleep intervals instead of busy waiting.
        """
        while self.OPTIONS.sleep_over_midnight:
            current_time = datetime.now()
            is_before_midnight = current_time.hour == 23 and current_time.minute >= 57
            is_after_midnight = (
                current_time.hour == 0
                and current_time.minute < self.OPTIONS.sleep_midnight_minutes
            )

            if not (is_before_midnight or is_after_midnight):
                break
            logger.info(f"Sleeping over midnight")

            # Calculate appropriate sleep duration
            if is_before_midnight:
                # Calculate time until midnight
                next_check = (current_time + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                # Calculate time until 5 minutes after midnight
                next_check = current_time.replace(
                    hour=0,
                    minute=self.OPTIONS.sleep_midnight_minutes,
                    second=0,
                    microsecond=0,
                )

            # Sleep until next check, but no longer than 30 seconds at a time
            sleep_duration = min(30, (next_check - current_time).total_seconds())
            sleep(sleep_duration)


if __name__ == "__main__":
    addon = AddOn()
    addon.setup()
    addon.connect()

    addon.loop(True)
