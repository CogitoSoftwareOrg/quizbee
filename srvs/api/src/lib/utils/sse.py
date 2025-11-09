import json
from typing import Any


def sse(ev: str, data: dict[str, Any]) -> str:
    return f"event: {ev}\ndata: {json.dumps(data)}\n\n"
