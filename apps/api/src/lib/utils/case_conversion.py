import re
from typing import Any


def snake_to_camel(
    keys: str | list[str] | dict[str, Any],
) -> str | list[str] | dict[str, Any]:
    if isinstance(keys, str):
        return _snake_to_camel_key(keys)
    elif isinstance(keys, list):
        return [_snake_to_camel_key(key) for key in keys]
    elif isinstance(keys, dict):
        return {_snake_to_camel_key(key): value for key, value in keys.items()}


def _snake_to_camel_key(key: str) -> str:
    parts = key.split("_")
    return "".join(parts[0].lower() + "".join(parts[1:]))


def camel_to_snake(
    keys: str | list[str] | dict[str, Any],
) -> str | list[str] | dict[str, Any]:
    if isinstance(keys, str):
        return _camel_to_snake_key(keys)
    elif isinstance(keys, list):
        return [_camel_to_snake_key(key) for key in keys]
    elif isinstance(keys, dict):
        return {_camel_to_snake_key(key): value for key, value in keys.items()}
    else:
        raise ValueError(f"Invalid keys type: {type(keys)}")


def _camel_to_snake_key(key: str) -> str:
    # Convert camelCase string to snake_case, e.g., userId -> user_id
    import re

    return re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
