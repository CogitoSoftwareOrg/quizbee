from pydantic import BaseModel, Field


class CreateQuizDto(BaseModel):
    quiz_id: str = Field(default="")
    attempt_id: str | None = Field(default=None)
