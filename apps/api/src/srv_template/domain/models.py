from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    id: str
