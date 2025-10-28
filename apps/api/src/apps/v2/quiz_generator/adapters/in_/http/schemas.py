from pydantic import BaseModel, Field

from ....app.contracts import GenMode


class PatchQuizDto(BaseModel):
    attempt_id: str
    mode: GenMode = Field(default=GenMode.Continue)
