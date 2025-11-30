import logging
from typing import Annotated, Literal
from langfuse import Langfuse
from pydantic import BaseModel, Field
from dataclasses import dataclass
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    RunContext,
    SystemPromptPart,
    UserPromptPart,
)


from src.lib.config import LLMS
from src.lib.settings import settings
from src.lib.utils import update_span_with_result

from ...domain.models import QuizCategory, Quiz
from ...domain.out import QuizFinalizer, QuizRepository


QUIZ_FINALIZER_LLM = LLMS.GROK_4_FAST
IN_QUERY = "Finilize Quiz"
RETRIES = 5


@dataclass
class QuizFinalizerDeps:
    quiz: Quiz


class QuizFinalizerOutput(BaseModel):
    mode: Literal["summary"]

    summary: Annotated[
        str, Field(title="Summary", description="The summary of the quiz.")
    ]
    quiz_title: Annotated[
        str, Field(title="Quiz Title", description="The title of the quiz.")
    ]
    quiz_slug: Annotated[
        str,
        Field(
            title="Quiz Slug",
            description="The slug of the quiz. 3 or 4 words. Formatting example: 'linear-algebra-basics'",
        ),
    ]
    quiz_tags: Annotated[
        list[str],
        Field(
            title="Quiz Tags",
            description="The topic tags of the quiz. More than 3 tags and less than 10 tags.",
            # min_length=3,
            # max_length=10,
        ),
    ]
    quiz_category: Annotated[
        QuizCategory,
        Field(
            title="Quiz Category",
            description="The category of the quiz.",
        ),
    ]

    def merge(self, quiz: Quiz):
        quiz.set_summary(self.summary)
        quiz.set_title(self.quiz_title)
        quiz.set_slug(self.quiz_slug)
        quiz.set_tags(self.quiz_tags)
        quiz.set_category(self.quiz_category)
        quiz.to_final()


class AIQuizFinalizer(QuizFinalizer):
    def __init__(
        self,
        lf: Langfuse,
        quiz_repository: QuizRepository,
    ):
        self._lf = lf
        self._quiz_repository = quiz_repository

        self._ai = Agent(
            history_processors=[self._inject_request_prompt],
            output_type=QuizFinalizerOutput,
            deps_type=QuizFinalizerDeps,
            model=QUIZ_FINALIZER_LLM,
            retries=RETRIES,
        )

    async def finalize(self, quiz: Quiz, cache_key: str) -> None:
        logging.info(f"Finalizing quiz {quiz.id}")
        # SUMMARIZE
        with self._lf.start_as_current_span(name="quiz-finalizer") as span:
            res = await self._ai.run(
                IN_QUERY,
                deps=QuizFinalizerDeps(quiz=quiz),
            )
            await update_span_with_result(
                self._lf,
                res,
                span,
                quiz.author_id,
                cache_key,
                QUIZ_FINALIZER_LLM,
            )

            payload = res.output
            payload.merge(quiz)
            await self._quiz_repository.update(quiz)

    async def _inject_request_prompt(
        self, ctx: RunContext[QuizFinalizerDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        pre_parts = self._build_pre_prompt(ctx.deps.quiz)

        items = ctx.deps.quiz.items
        items_content = "\n".join(
            [
                f"Question {i+1}: {qi.question}\nAnswer Options: {qi.variants}"
                for i, qi in enumerate(items)
            ]
        )

        post_parts = []
        post_parts.append(
            SystemPromptPart(
                content=self._lf.get_prompt(
                    "summarizer/base", label=settings.env
                ).compile(quiz=items_content)
            )
        )
        return (
            [ModelRequest(parts=pre_parts)]
            + messages
            + [ModelRequest(parts=post_parts)]
        )

    def _build_pre_prompt(self, quiz: Quiz) -> list[ModelRequestPart]:
        user_contents = []
        if quiz.query:
            user_contents.append(f"User query:\n{quiz.query}")

        if quiz.material_content:
            user_contents.append("Quiz materials:")
            user_contents.append(quiz.material_content)

        parts = []
        if user_contents:
            parts.append(UserPromptPart(content=user_contents))
        return parts
