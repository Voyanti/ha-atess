"""
    Parsing & Validation of user configuration 

    'config.yaml' (testing/local) OR 
    
    'config.json' (on homeassistant)
"""
import json
import os
import logging
import yaml
from cattrs import structure, unstructure, Converter
from src.options import *
from src.implemented_servers import DeviceTypes

logger = logging.getLogger(__name__)



def validate_names(names: list) -> None:
    """
    Verify unique alphanumeric names for clients and devices of options. Used as unique identifiers.
    """
    if len(set(names)) != len(names):
        raise ValueError(f"Device/ Client names must be unique")

    if not all([c.isalnum() for c in names]):
        raise ValueError(f"Client and Device names must be alphanumeric")


def validate_server_implemented(devices: list):
    """Validate that the specified server type is specified in implemented device enum."""
    for device in devices:
        if device.device_type not in [t.name for t in DeviceTypes]:
            raise ValueError(
                f"Device type {device.device_type} not defined in implemented_servers.ServerTypes"
            )


def validate_options(opts: Options) -> None:
    client_names = [c.name for c in opts.modbus_clients]
    server_names = [s.name for s in opts.devices]
    validate_names(client_names)
    validate_names(server_names)
    validate_server_implemented(opts.devices)


def read_json(json_rel_path):
    with open(json_rel_path) as f:
        data = json.load(f)
    return data


def read_yaml(json_rel_path):
    with open(json_rel_path) as file:
        data = yaml.load(file, Loader=yaml.FullLoader)["options"]
    return data


def load_options(json_rel_path="/data/options.json") -> Options:
    """Load device & client configurations and connection specs as dicts from options json."""
    converter = Converter()

    logger.info(
        f"Attempting to read configuration json at path {os.path.join(os.getcwd(), json_rel_path)}"
    )

    # Homeassistant add-ons parse the user confi.yaml into a json.
    # Support yaml parsing for testing purposes.
    if os.path.exists(json_rel_path):
        if json_rel_path[-4:] == "json":
            data = read_json(json_rel_path)
        elif json_rel_path[-4:] == "yaml":
            data = read_yaml(json_rel_path)
    else:
        logger.info("Error loading configuration at{os.path.join(os.getcwd(), json_rel_path)}")
        raise FileNotFoundError(
            f"Config options json/yaml not found at {os.path.join(os.getcwd(), json_rel_path)}")

    opts = converter.structure(data, Options)
    return opts


def load_validate_options(json_rel_path="/data/options.json") -> Options:
    """Load and Validate Options"""
    opts = load_options(json_rel_path)

    validate_options(opts)

    logger.info("Successfully read configuration")
    return opts


if __name__ == "__main__":
    import pprint

    opts = load_validate_options('config.yaml')
    pprint.pprint(opts)
