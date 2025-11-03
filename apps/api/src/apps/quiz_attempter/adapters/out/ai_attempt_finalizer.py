from dataclasses import dataclass
from typing import Annotated, Any, Literal
from pydantic import BaseModel, Field
from langfuse import Langfuse
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    RunContext,
    SystemPromptPart,
    UserPromptPart,
)

from src.lib.utils import update_span_with_result
from src.lib.config import LLMS
from src.lib.settings import settings

from ...domain.ports import AttemptFinalizer, AttemptRepository
from ...domain.models import Attempt, Feedback

ATTEMPT_FINALIZER_LLM = LLMS.GPT_5_MINI
IN_QUERY = "Finalize Attempt"


@dataclass
class AttemptFinalizerDeps:
    attempt: Attempt


class AttemptFinalizerOutput(BaseModel):
    mode: Literal["feedback"]
    overview: Annotated[
        str,
        Field(
            title="Small Overview",
            description="A brief overview of the quiz attempt and user results.",
        ),
    ]
    problem_topics: Annotated[
        list[str],
        Field(
            title="Problem Topics",
            description="A list of problem topics that the user struggled with.",
            max_length=3,
        ),
    ]
    uncovered_topics: Annotated[
        list[str],
        Field(
            title="Uncovered Topics",
            description="A list of topics that are presented in materials but not covered in the quiz.",
            max_length=3,
        ),
    ]

    def _merge(self, attempt: Attempt):
        attempt.set_feedback(
            Feedback(
                overview=self.overview,
                problem_topics=self.problem_topics,
                uncovered_topics=self.uncovered_topics,
            )
        )


class AIAttemptFinalizer(AttemptFinalizer):
    def __init__(
        self,
        lf: Langfuse,
        attempt_repository: AttemptRepository,
        ai: Agent[AttemptFinalizerDeps, Any],
    ):
        self._lf = lf
        self._attempt_repository = attempt_repository
        self._ai = ai
        self._ai.history_processors += [self._inject_request_prompt]  # type: ignore

    async def finalize(self, attempt: Attempt, cache_key: str) -> None:
        with self._lf.start_as_current_span(name="attempt-finalizer") as span:
            res = await self._ai.run(
                IN_QUERY,
                deps=AttemptFinalizerDeps(attempt=attempt),
                model_settings={
                    "extra_body": {
                        "reasoning_effort": "low",
                        "service_tier": "default",
                        "prompt_cache_key": cache_key,
                    }
                },
            )
            await update_span_with_result(
                self._lf,
                res,
                span,
                attempt.user_id,
                cache_key,
                ATTEMPT_FINALIZER_LLM,
            )
            if res.output.data.mode != "feedback":
                raise ValueError(f"Unexpected output type: {type(res.output)}")

            payload: AttemptFinalizerOutput = res.output.data

            payload._merge(attempt)
            await self._attempt_repository.update(attempt)

    async def _inject_request_prompt(
        self, ctx: RunContext[AttemptFinalizerDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        attempt = ctx.deps.attempt
        return (
            [ModelRequest(parts=self._build_pre_prompt(attempt))]
            + messages
            + [ModelRequest(parts=self._build_post_prompt(attempt))]
        )

    def _build_pre_prompt(self, attempt: Attempt) -> list[ModelRequestPart]:
        user_contents = []
        if attempt.quiz.query:
            user_contents.append(f"User query:\n{attempt.quiz.query}")

        if attempt.quiz.material_content:
            user_contents.append("Quiz materials:")
            user_contents.append(attempt.quiz.material_content)

        parts = []
        parts.append(UserPromptPart(content=user_contents))
        return parts

    def _build_post_prompt(self, attempt: Attempt) -> list[ModelRequestPart]:
        quiz_content = attempt.quiz_content()
        correct_content = attempt.correct_items_content()
        wrong_content = attempt.wrong_items_content()

        parts = []

        # SYSTEM PARTS
        parts.append(
            SystemPromptPart(
                content=self._lf.get_prompt(
                    "feedbacker/base", label=settings.env
                ).compile(
                    quiz_content=quiz_content,
                    correct_answers=correct_content,
                    wrong_answers=wrong_content,
                )
            )
        )

        return parts
