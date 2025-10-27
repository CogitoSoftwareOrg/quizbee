from pydantic import BaseModel, Field

from ....app.contracts import GenMode


class PatchQuizDto(BaseModel):
    attempt_id: str | None = Field(default=None)
    limit: int = Field(default=5)
    mode: GenMode = Field(default=GenMode.Continue)
