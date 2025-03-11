from dataclasses import dataclass
from typing import Union


@dataclass
class DeviceOptions:
    """ Modbus Server Options as read from config json"""
    name: str
    serialnum: str
    server_type: str
    connected_client: str
    modbus_id: int


@dataclass
class ModbusClientOptions:
    """ Modbus Client Options as read from config json"""
    name: str
    type: str


@dataclass
class ModbusTCPOptions(ModbusClientOptions):
    host: str
    port: int


@dataclass
class ModbusRTUOptions(ModbusClientOptions):
    mount: str
    baudrate: int
    bytesize: int
    parity: bool
    stopbits: int


@dataclass
class Options:
    """ Concatenated options for reading specific format of all options from config json """
    devices: list[DeviceOptions]
    modbus_clients: list[Union[ModbusRTUOptions, ModbusTCPOptions]]

    pause_interval_seconds: float

    sleep_over_midnight: bool
    sleep_midnight_minutes: int

    mqtt_host: str
    mqtt_port: int
    mqtt_user: str
    mqtt_password: str
    mwtt_ha_discovery_topic: str
    mqtt_base_topic: str
