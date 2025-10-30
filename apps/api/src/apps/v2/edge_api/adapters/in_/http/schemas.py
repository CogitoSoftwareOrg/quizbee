from pydantic import BaseModel, Field

from src.apps.v2.quiz_generator.app.contracts import GenMode


class StartQuizDto(BaseModel):
    attempt_id: str


class PatchQuizDto(BaseModel):
    attempt_id: str
    mode: GenMode = Field(default=GenMode.Continue)


class FinalizeQuizDto(BaseModel):
    attempt_id: str
