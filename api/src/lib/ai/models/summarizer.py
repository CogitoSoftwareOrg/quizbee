from typing import Literal
from pydantic import BaseModel
from dataclasses import dataclass
from pocketbase.models.dtos import Record

from lib.clients import HTTPAsyncClient


@dataclass
class SummarizerDeps:
    materials_context: str
    http: HTTPAsyncClient
    quiz: Record


class SummarizerOutput(BaseModel):
    mode: Literal["summary"]
    summary: str
