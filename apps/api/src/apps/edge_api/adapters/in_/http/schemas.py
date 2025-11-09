from pydantic import BaseModel, Field

from src.apps.quiz_owner.app.contracts import GenMode

from ....app.contracts import (
    JobName,
    PublicAddMaterialCmd,
    PublicFinalizeAttemptCmd,
    PublicFinalizeQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicStartQuizCmd,
)


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


class FinalizeAttemptDto(BaseModel): ...


class JobDto(BaseModel):
    name: JobName
    payload: (
        PublicStartQuizCmd
        | PublicGenerateQuizItemsCmd
        | PublicFinalizeQuizCmd
        | PublicFinalizeAttemptCmd
        | PublicAddMaterialCmd
        | None
    )


class SheduleJobsDto(BaseModel):
    jobs: list[JobDto]
