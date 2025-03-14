from enum import Enum
from typing import Literal, Optional

from src.enums import Unit

class HAEntity:
    def __init__(self) -> None:
        self.name: str
        self.value: str | int | float

        self.discovery_topic: str
        self.discovery_payload: str

        self.state_topic: str

# Read only (state)
class HAWriteEntity(HAEntity):
    def __init__(self) -> None:
        self.command_topic: str
        super().__init__()

class HASensor(HAEntity):
    def __init__(self) -> None:
        self.entity_type = 'sensor'
        super().__init__()
class HASwitch(HAEntity):
    def __init__(self) -> None:
        self.entity_type = 'switch'
        super().__init__()

# Read/Write (state/set)
class HANumber(HAWriteEntity):
    def __init__(self) -> None:
        self.entity_type = 'number'
        super().__init__()
class HABinarySensor(HAWriteEntity):
    def __init__(self) -> None:
        self.entity_type = 'binary_sensor'
        super().__init__()
class HASelect(HAWriteEntity):
    def __init__(self) -> None:
        self.entity_type = 'select'
        super().__init__()

class HAEntityType(Enum):
    NUMBER = 'number'
    SWITCH = 'switch'
    SELECT = 'select'

    SENSOR = 'sensor'
    BINARY_SENSOR = 'binary_sensor'

# https://www.home-assistant.io/integrations/sensor#device-class
class HADeviceClass(Enum):
    DATE = "date"
    ENUM = "enum"
    TIMESTAMP = "timestamp"
    APPARENT_POWER = "apparent_power"
    AQI = "aqi"
    ATMOSPHERIC_PRESSURE = "atmospheric_pressure"
    BATTERY = "battery"
    CARBON_MONOXIDE = "carbon_monoxide"
    CARBON_DIOXIDE = "carbon_dioxide"
    CURRENT = "current"
    DATA_RATE = "data_rate"
    DATA_SIZE = "data_size"
    DISTANCE = "distance"
    DURATION = "duration"
    ENERGY = "energy"
    ENERGY_STORAGE = "energy_storage"
    FREQUENCY = "frequency"
    GAS = "gas"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    IRRADIANCE = "irradiance"
    MOISTURE = "moisture"
    MONETARY = "monetary"
    NITROGEN_DIOXIDE = "nitrogen_dioxide"
    NITROGEN_MONOXIDE = "nitrogen_monoxide"
    NITROUS_OXIDE = "nitrous_oxide"
    OZONE = "ozone"
    PH = "ph"
    PM1 = "pm1"
    PM10 = "pm10"
    PM25 = "pm25"
    POWER_FACTOR = "power_factor"
    POWER = "power"
    PRECIPITATION = "precipitation"
    PRECIPITATION_INTENSITY = "precipitation_intensity"
    PRESSURE = "pressure"
    REACTIVE_POWER = "reactive_power"
    SIGNAL_STRENGTH = "signal_strength"
    SOUND_PRESSURE = "sound_pressure"
    SPEED = "speed"
    SULPHUR_DIOXIDE = "sulphur_dioxide"
    TEMPERATURE = "temperature"
    VOLATILE_ORGANIC_COMPOUNDS = "volatile_organic_compounds"
    VOLATILE_ORGANIC_COMPOUNDS_PARTS = "volatile_organic_compounds_parts"
    VOLTAGE = "voltage"
    VOLUME = "volume"
    VOLUME_STORAGE = "volume_storage"
    VOLUME_FLOW_RATE = "volume_flow_rate"
    WATER = "water"
    WEIGHT = "weight"
    WIND_SPEED = "wind_speed"

device_class_to_rounding: dict[HADeviceClass, int] = { 
        HADeviceClass.REACTIVE_POWER: 0,
        HADeviceClass.ENERGY: 1,
        HADeviceClass.FREQUENCY: 1,
        HADeviceClass.POWER_FACTOR: 1,
        HADeviceClass.APPARENT_POWER: 0, 
        HADeviceClass.CURRENT: 1,
        HADeviceClass.VOLTAGE: 0,
        HADeviceClass.POWER: 0
    }


unit_to_device_class: dict[Unit, HADeviceClass] = {
    # Volt/ Current
    'V': HADeviceClass.VOLTAGE,
    'mV': HADeviceClass.VOLTAGE,
    'A': HADeviceClass.CURRENT,

    # S
    'VA': HADeviceClass.APPARENT_POWER,

    # P
    'kW': HADeviceClass.POWER,
    'W': HADeviceClass.POWER,

    # Q
    'var': HADeviceClass.REACTIVE_POWER,

    # Energy
    'kWh': HADeviceClass.ENERGY,

    # Temperature
    "°C" : HADeviceClass.TEMPERATURE,

    # Frequency
    'Hz': HADeviceClass.FREQUENCY,

    # not supported currently ( since HA Core 2025.3 )
    'kVA': HADeviceClass.APPARENT_POWER,
    'kVar': HADeviceClass.REACTIVE_POWER,
}

# depends: homeassistant, mqtt integration
class HADevice:
    def __init__(self) -> None:
        self.entities: dict[str, HAEntity | HAWriteEntity]
        # = {entity.name: entity for entity in entities}





















# old
        # self.binary_sensors: dict[str, HABinarySensor]
        # self.numbers: dict[str, HABinarySensor]
        # self.selects: dict[str, HABinarySensor]
        # self.switches: dict[str, HABinarySensor]
    
    # @property
    # def entities(self):
    #     copy = self.sensors.copy()
    #     copy.update(self.binary_sensors, self.numbers, self.selects, self.switches)