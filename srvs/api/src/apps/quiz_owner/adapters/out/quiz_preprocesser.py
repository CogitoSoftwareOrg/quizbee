from dataclasses import dataclass
import json
import logging
from typing import Annotated, Any
from langfuse import Langfuse
from pydantic import BaseModel, Field
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    RunContext,
    SystemPromptPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.lib.utils import update_span_with_result
from src.lib.config import LLMS
from src.lib.settings import settings

from ...domain.models import Quiz


PREPROCESSOR_LLM = LLMS.GROK_4_FAST
IN_QUERY = "Enhance the user query"
RETRIES = 5
TEMPERATURE = 0.3
TOP_P = 0.95

logger = logging.getLogger(__name__)


@dataclass
class QuizPreprocessorDeps:
    quiz: Quiz


class QuizPreprocessorOutput(BaseModel):
    enhanced_instructions: Annotated[
        str,
        Field(
            title="Enhanced Instructions",
            description="Enhanced instructions from the user about how to generate the quiz (e.g., 'ask long questions', 'make it harder'). Empty string if no instructions provided.",
        ),
    ]
    topics: Annotated[
        list[str],
        Field(
            title="Topics",
            description="Detailed list of specific topics to ask questions about. Each topic should be clearly and comprehensively described. Empty list if no topics specified.",
            min_length=0,
        ),
    ]


class QuizPreprocessor:
    def __init__(self, lf: Langfuse, provider: OpenAIProvider):
        self._lf = lf

        self._ai = Agent(
            history_processors=[self._inject_request_prompt],
            output_type=QuizPreprocessorOutput,
            deps_type=QuizPreprocessorDeps,
            model=OpenAIChatModel(PREPROCESSOR_LLM, provider=provider),
            retries=RETRIES,
        )

    async def enhance_query(self, quiz: Quiz, cache_key: str) -> tuple[str, list[str]]:
        logging.info(f"Enhancing query for quiz {quiz.id}")

        if not quiz.query:
            raise ValueError("Quiz query is required for preprocessing")

        try:
            with self._lf.start_as_current_span(name=f"quiz-preprocess") as span:
                run = await self._ai.run(
                    IN_QUERY,
                    model=PREPROCESSOR_LLM,
                    deps=QuizPreprocessorDeps(quiz=quiz),
                    model_settings={
                        "temperature": TEMPERATURE,
                        "top_p": TOP_P,
                    },
                )

                output = run.output

                await update_span_with_result(
                    self._lf,
                    run,
                    span,
                    quiz.author_id,
                    cache_key,
                    PREPROCESSOR_LLM,
                )

                return output.enhanced_instructions, output.topics

        except Exception as e:
            logging.exception("Failed to enhance query: %s", e)
            raise e

    async def _inject_request_prompt(
        self, ctx: RunContext[QuizPreprocessorDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        quiz = ctx.deps.quiz

        return [
            ModelRequest(parts=self._build_system_prompt()),
            ModelRequest(parts=self._build_user_prompt(quiz)),
        ] + messages

    def _build_system_prompt(self) -> list[ModelRequestPart]:
        return [
            SystemPromptPart(
                content=self._lf.get_prompt(
                    "quizer/preprocessor", label=settings.env
                ).compile()
            )
        ]

    def _build_user_prompt(self, quiz: Quiz) -> list[ModelRequestPart]:
        user_query = quiz.query or ""

        content_parts = [f"User query to enhance:\n{user_query}"]

        tocs = self._get_tocs_from_quiz(quiz)
        if tocs:
            content_parts.append("\n\nTable of Contents from attached materials:")
            for idx, (material_id, toc) in enumerate(tocs.items(), 1):
                try:
                    toc_json = json.dumps(toc, indent=2, ensure_ascii=False)
                    content_parts.append(
                        f"\n--- Material {material_id} TOC ---\n{toc_json}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to serialize table of contents for material {material_id}: {e}"
                    )

        return [UserPromptPart(content="\n".join(content_parts))]

    def _get_tocs_from_quiz(self, quiz: Quiz) -> dict[str, Any] | None:
        return getattr(quiz, "table_of_contents", None)
