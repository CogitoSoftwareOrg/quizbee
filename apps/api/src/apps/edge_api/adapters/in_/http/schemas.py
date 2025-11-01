from pydantic import BaseModel, Field

from src.apps.quiz_generator.app.contracts import GenMode


class StartQuizDto(BaseModel):
    attempt_id: str


class PatchQuizDto(BaseModel):
    attempt_id: str
    mode: GenMode = Field(default=GenMode.Continue)


class FinalizeQuizDto(BaseModel):
    attempt_id: str


class CreateStripeCheckoutDto(BaseModel):
    price: str
    return_url: str = ""
    idempotency_key: str | None = None


class CreateBillingPortalSessionDto(BaseModel):
    return_url: str = ""
