from dataclasses import dataclass
from typing import Protocol

from .models import ParsedDocument


@dataclass(slots=True, kw_only=True)
class DocumentParseCmd:
    file_bytes: bytes
    file_name: str


class DocumentParserApp(Protocol):
    async def parse(self, cmd: DocumentParseCmd) -> ParsedDocument:
        """
        Парсит документ.
        """
        ...
