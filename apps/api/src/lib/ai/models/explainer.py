from pydantic import BaseModel
from dataclasses import dataclass
from pocketbase.models.dtos import Record
from typing import Any, Literal

from src.lib.clients import HTTPAsyncClient


@dataclass
class ExplainerDeps:
    http: HTTPAsyncClient
    quiz: Record
    current_item: Record
    current_decision: Any


class ExplainerOutput(BaseModel):
    mode: Literal["explanation"]
    explanation: str
