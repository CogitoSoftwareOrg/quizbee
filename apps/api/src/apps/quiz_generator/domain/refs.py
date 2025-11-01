from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class MaterialRef:
    id: str
    text: str
    filename: str
    is_book: bool
