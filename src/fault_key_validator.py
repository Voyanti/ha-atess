import re


FAULT_NAME_KEY_COMPATIBLE_RE = re.compile(r"^[a-z0-9][a-z_\-]*$")

def coerce_fault_name_key(value: str) -> str:
    """Coerce a validated fault name key to canonical form (lowercase, spaces → hyphens)."""
    return (
        value.lower()
        .replace(" ", "-")
        .replace("{", "_")
        .replace("}", "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace("[", "_")
        .replace("]", "_")
    )
