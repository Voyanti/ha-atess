from time import sleep
from datetime import datetime, timedelta
import atexit
import logging
from typing import Callable

from .loader import load_validate_options
from .options import Options
from .modbus_client import ModbusClient, modbusClientFactory
from .implemented_servers import DeviceTypes
from .modbus_device import ModbusDevice
from .mqtt_client import HAMqttClient


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
    servers: list[ModbusDevice],
    modbus_clients: list[ModbusClient],
    mqtt_client: HAMqttClient,
) -> None:
    logger.info("Exiting")
    # publish offline availability for each server
    for server in servers:
        mqtt_client.publish_availability(False, server)
    logger.info("Closing client connections on exit")
    for client in modbus_clients:
        client.close()

    mqtt_client.loop_stop()


def instantiate_clients(OPTIONS: Options) -> list[ModbusClient]:
    return [modbusClientFactory(cl_options) for cl_options in OPTIONS.modbus_clients]


def instantiate_devices(
    OPTIONS: Options, clients: list[ModbusClient]
) -> list[ModbusDevice]:
    return [
        DeviceTypes[sr.server_type].value.from_ServerOptions(sr, clients)
        for sr in OPTIONS.devices
    ]


class App:
    def __init__(
        self,
        modbus_client_setup: Callable[
            [Options], list[ModbusClient]
        ] = instantiate_clients,
        modbus_device_setup: Callable[
            [Options, list[ModbusClient]], list[ModbusDevice]
        ] = instantiate_devices,
        options_rel_path=None,
    ) -> None:
        """
        Usage:
            Default:
                app = App()
                # change options here
                # instantiate modbus clients and devices:
                app.setup()
                # connect to modbus and mqtt broker:
                app.connect()
                # main loop:
                app.loop()

        Can inject custom setup functions to initialise
        """
        self.OPTIONS: Options
        # Read configuration
        if options_rel_path is not None:  # for running locally
            self.OPTIONS = load_validate_options(options_rel_path)
        else:  # default for running on homeassistant
            self.OPTIONS = load_validate_options()

        # app-level options
        self.midnight_sleep_enabled, self.minutes_wakeup_after = (
            self.OPTIONS.sleep_over_midnight,
            self.OPTIONS.sleep_midnight_minutes,
        )
        self.pause_interval = self.OPTIONS.pause_interval_seconds

        # Setup callbacks
        self.client_instantiator_callback = modbus_client_setup
        self.device_instantiator_callback = modbus_device_setup

    def setup(self) -> None:
        """
            Instantiate devices, modbus clients and mqtt wrapper
        """
        self.sleep_if_midnight()

        logger.info("Instantiate clients")
        self.modbus_clients: list[ModbusClient] = self.client_instantiator_callback(
            self.OPTIONS
        )
        logger.info(f"{len(self.modbus_clients)} clients set up")

        logger.info("Instantiate servers")
        self.devices: list[ModbusDevice] = self.device_instantiator_callback(
            self.OPTIONS, self.modbus_clients
        )
        logger.info(f"{len(self.devices)} devices set up")
        # if len(servers) == 0: raise RuntimeError(f"No supported servers configured")

        # Setup MQTT Client
        self.mqtt_client = HAMqttClient(
            self.OPTIONS.mqtt_base_topic,
            self.OPTIONS.mwtt_ha_discovery_topic,
        )
        self.mqtt_client.servers = self.devices  # TODO Remove

        atexit.register(exit_handler, self.devices, self.modbus_clients, self.mqtt_client)

    def connect(self) -> None:
        """
            Connect to devices, modbus clients and mqtt wrapper
        """
        for client in self.modbus_clients:
            client.connect()

        for device in self.devices:
            device.connect()

        # connect to mqtt
        self.mqtt_client.connect(
            self.OPTIONS.mqtt_host,
            self.OPTIONS.mqtt_port,
            self.OPTIONS.mqtt_user,
            self.OPTIONS.mqtt_password,
        )

        sleep(READ_INTERVAL)
        self.mqtt_client.loop_start()

        # Publish Discovery Topics
        for device in self.devices:
            self.mqtt_client.publish_discovery_topics(device)

    def loop(self, loop_once=False) -> None:
        if not self.devices or not self.modbus_clients:
            logger.info(f"In loop but app servers or clients not setup up")
            raise ValueError(f"In loop but app servers or clients not setup up")

        # every read_interval seconds, read the registers and publish to mqtt
        while True:
            for device in self.devices:
                # update server state from modbus
                device.read_batches()

                # index required registers from saved state
                # publish to ha
                for register_name in device.write_parameters:
                    value = device.read_from_state(register_name)
                    self.mqtt_client.publish_to_ha(register_name, value, device)

                logger.info(f"Published all Write parameter values for {device.name}")
                sleep(READ_INTERVAL)

                for register_name in device.parameters:
                    value = device.read_from_state(register_name)
                    self.mqtt_client.publish_to_ha(register_name, value, device)
                logger.info(f"Published all Read parameter values for {device.name}")
            logger.info("")

            if loop_once:
                break

            # publish availability
            sleep(self.pause_interval)

            self.sleep_if_midnight()

    def sleep_if_midnight(self) -> None:
        """
        Sleeps if the current time is within 3 minutes before or 5 minutes after midnight.
        Uses efficient sleep intervals instead of busy waiting.
        """
        while self.midnight_sleep_enabled:
            current_time = datetime.now()
            is_before_midnight = current_time.hour == 23 and current_time.minute >= 57
            is_after_midnight = (
                current_time.hour == 0
                and current_time.minute < self.minutes_wakeup_after
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
                    hour=0, minute=self.minutes_wakeup_after, second=0, microsecond=0
                )

            # Sleep until next check, but no longer than 30 seconds at a time
            sleep_duration = min(30, (next_check - current_time).total_seconds())
            sleep(sleep_duration)


if __name__ == "__main__":
    if len(sys.argv) <= 1:  # deployed on homeassistant
        app = App()
        app.setup()
        app.connect()
        app.loop()
    else:  # running locally: argv[1] = options_rel_path
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        from .modbus_client import SpoofClient

        def instantiate_spoof_clients(Options) -> list[SpoofClient]:
            return [SpoofClient()]

        app = App(
            modbus_client_setup=instantiate_spoof_clients,
            modbus_device_setup=instantiate_devices,
            options_rel_path=sys.argv[1],
        )
        app.OPTIONS.mqtt_host = "localhost"
        app.OPTIONS.mqtt_port = 1884
        app.OPTIONS.pause_interval_seconds = 10

        app.setup()
        for s in app.devices:
            s.connect = lambda: None
            s.model = "PCS500"
            s.setup_valid_registers_for_model()
            s.find_register_extent()
            s.create_batches()
        app.connect()
        app.loop(False)

    # finally:
    #     exit_handler(servers, clients, mqtt_client) TODO NB
