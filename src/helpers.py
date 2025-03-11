from random import getrandbits
from time import time


def slugify(text: str) -> str:
    return text.replace(' ', '_').replace('(', '').replace(')', '').replace('/', 'OR').replace('&', ' ').replace(':', '').replace('.', '').lower()

def generate_uuid() -> str:
    random_part = getrandbits(64)
    # Get current timestamp in milliseconds
    timestamp = int(time() * 1000)
    node = getrandbits(48)  # Simulating a network node (MAC address)

    uuid_str = f'{timestamp:08x}-{random_part >> 32:04x}-{random_part & 0xFFFF:04x}-{node >> 24:04x}-{node & 0xFFFFFF:06x}'
    return uuid_str