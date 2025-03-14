
from abc import ABC, abstractmethod

from modbus_device import ModbusDevice


class IHaMqttAdapter(ABC):
    """
        Responsible for translation of entities (e.g. ModbusDevice) to 
        HomeAssistant MQTT Integration format and vice-versa.
    
        
    """

    def __init__(self):
        self.
    @abstractmethod
    def build_discovery(ha_discovery_topic:str, base_topic: str, device: ModbusDevice):


class HADevice:
    def __init__(self):
        self.entities = dict[str, HAEntity]


class OLD:
        # custom functionality
    def message_handler(self, msg) -> None:
        # command_topic = f"{self.base_topic}/{server.nickname}/{slugify(register_name)}/set"
        server_ha_display_name: str = msg.topic.split('/')[1]
        s = None
        for s in self.servers: 
            if s.name == server_ha_display_name:
                server = s
        if s is None: raise ValueError(f"Server {server_ha_display_name} not available. Cannot write.")
        register_slug: str = msg.topic.split('/')[2]
        value: str = msg.payload.decode('utf-8')
        register_name = server.write_parameters_slug_to_name[register_slug]


        server.write_registers(register_slug, value)


        value = server.read_registers(register_name)
        logger.info(f"read {value=}")
        self.publish_to_ha(
            register_slug, value, server)
        

    def publish_discovery_topics(self, server) -> None:
        while not self.client.is_connected():
            logger.info(
                f"Not connected to mqtt broker yet, sleep 20ms and retry. Before publishing discovery topics.")
            sleep(0.02)
        # TODO check if more separation from server is necessary/ possible
        nickname = server.name
        if not server.model or not server.manufacturer or not server.serial or not nickname or not server.parameters:
            logging.info(
                f"Server not properly configured. Cannot publish MQTT info")
            raise ValueError(
                f"Server not properly configured. Cannot publish MQTT info")

        logger.info(f"Publishing discovery topics for {nickname}")
        device = {
            "manufacturer": server.manufacturer,
            "model": server.model,
            "identifiers": [f"{nickname}"],
            "name": f"{nickname}"
            # "name": f"{server.manufacturer} {server.serialnum}"
        }

        # publish discovery topics for legal registers
        # assume registers in server.registers
        availability_topic = f"{self.base_topic}_{nickname}/availability"

        parameters = server.parameters

        for register_name, details in parameters.items():
            state_topic = f"{self.base_topic}/{nickname}/{slugify(register_name)}/state"
            discovery_payload = {
                "name": register_name,
                "unique_id": f"{nickname}_{slugify(register_name)}",
                "state_topic": state_topic,
                "availability_topic": availability_topic,
                "device": device,
                "device_class": details["device_class"].value,
            }
            if details["unit"] != "":
                discovery_payload.update(unit_of_measurement=details["unit"])
            if "value_template" in details: #enum
                discovery_payload.update(value_template=details["value_template"])

            state_class = details.get("state_class", False)
            if state_class:
                discovery_payload['state_class'] = state_class
            discovery_topic = f"{self.ha_discovery_topic}/sensor/{nickname}/{slugify(register_name)}/config"

            self.client.publish(discovery_topic, json.dumps(
                discovery_payload), retain=True)

        self.publish_availability(True, server)

        for register_name, details in server.write_parameters.items():
            item_topic = f"{self.base_topic}/{nickname}/{slugify(register_name)}"
            discovery_payload = {
                # required
                "command_topic": item_topic + f"/set", 
                "state_topic": item_topic + f"/state",
                # optional
                "name": register_name,
                "unique_id": f"{nickname}_{slugify(register_name)}",
                # "unit_of_measurement": details["unit"],
                "availability_topic": availability_topic,
                "device": device
            }
            if details.get("unit") is not None:
                discovery_payload.update(unit_of_measurement=details["unit"])
            if details.get("options") is not None:
                discovery_payload.update(options=details["options"])
                if details.get("value_template") is not None:
                    discovery_payload.update(value_template=details["value_template"])
                if details.get("command_template") is not None:
                    discovery_payload.update(command_template=details["command_template"])
            if details.get("min") is not None and details.get("max") is not None:
                discovery_payload.update(min=details["min"], max=details["max"])
            if details.get("payload_off") is not None and details.get("payload_on") is not None:
                discovery_payload.update(payload_off=details["payload_off"], payload_on=details["payload_on"])

            discovery_topic = f"{self.ha_discovery_topic}/{details['ha_entity_type'].value}/{nickname}/{slugify(register_name)}/config"
            self.client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)

            # subscribe to write topics
            self.client.subscribe(discovery_payload["command_topic"])

    def publish_to_ha(self, register_name, value, server):
        nickname = server.name
        state_topic = f"{self.base_topic}/{nickname}/{slugify(register_name)}/state"
        self.publish(state_topic, value)  # , retain=True)

    def publish_availability(self, avail, server):
        nickname = server.name
        availability_topic = f"{self.base_topic}_{nickname}/availability"
        self.client.publish(availability_topic,
                     "online" if avail else "offline", retain=True)