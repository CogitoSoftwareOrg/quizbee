from dataclasses import dataclass
import logging
from typing import Annotated, Any, Literal
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

from src.lib.utils import update_span_with_result
from src.lib.config import LLMS
from src.lib.settings import settings

from ....domain.out import PatchGenerator, QuizRepository
from ....domain.models import Quiz, QuizItem, QuizItemStatus, QuizItemVariant


QUIZ_INSTANT_GENERATOR_LLM = LLMS.GPT_5_MINI
IN_QUERY = ""


@dataclass
class AIQuizInstantGeneratorDeps:
    quiz: Quiz


class AnswerSchema(BaseModel):
    answer: Annotated[str, Field(title="Answer", description="The answer text.")]
    explanation: Annotated[
        str, Field(title="Answer Explanation", description="The explanation text.")
    ]
    correct: Annotated[
        bool, Field(title="Correct", description="Whether the answer is correct.")
    ]


class QuizItemSchema(BaseModel):
    question: Annotated[
        str, Field(title="Question", description="The quiz question text.")
    ]
    answers: Annotated[
        list[AnswerSchema],
        Field(
            title="Answers",
            description="The answers to the question. 4 in total with ONLY one correct answer.",
            min_length=4,
            max_length=4,
        ),
    ]


class AIQuizInstantGeneratorOutput(BaseModel):
    mode: Literal["quiz"]
    quiz_items: Annotated[
        list[QuizItemSchema],
        Field(
            title="Quiz Items",
            description="An array of exactly 5 quiz items.",
            # min_length=5,
            # max_length=6,
        ),
    ]

    def merge(self, quiz: Quiz) -> None:
        generating_count = len(quiz.generating_items())
        if generating_count == 0:
            raise ValueError("No items in GENERATING status to merge results into")

        # Only process as many items as there are GENERATING items
        # This prevents errors if AI returns more items than expected
        items_to_process = min(len(self.quiz_items), generating_count)

        for schema in self.quiz_items[:items_to_process]:
            quiz.generation_step(
                question=schema.question,
                variants=[
                    QuizItemVariant(
                        content=a.answer,
                        is_correct=a.correct,
                        explanation=a.explanation,
                    )
                    for a in schema.answers
                ],
            )


class AIQuizInstantGenerator(PatchGenerator):
    def __init__(
        self,
        lf: Langfuse,
        quiz_repository: QuizRepository,
        output_type: Any,
    ):
        self._lf = lf
        self._quiz_repository = quiz_repository

        self._ai = Agent(
            history_processors=[self._inject_request_prompt],
            output_type=output_type,
            deps_type=AIQuizInstantGeneratorDeps,
            model=QUIZ_INSTANT_GENERATOR_LLM,
        )

    async def generate(self, quiz: Quiz, cache_key: str) -> None:
        logging.info(
            f"Generating quiz instant for quiz {quiz.id} (generation {quiz.generation})"
        )
        try:
            with self._lf.start_as_current_span(name=f"quiz-patch") as span:
                run = await self._ai.run(
                    IN_QUERY,
                    model=QUIZ_INSTANT_GENERATOR_LLM,
                    deps=AIQuizInstantGeneratorDeps(quiz=quiz),
                    model_settings={
                        "extra_body": {
                            "reasoning_effort": "low",
                            # "service_tier": "priority" if priority else "default",
                            "service_tier": "default",
                            "prompt_cache_key": cache_key,
                        },
                    },
                )

                if run.output.data.mode != "quiz":
                    raise ValueError(f"Unexpected output type: {run.output.data.mode}")
                payload: AIQuizInstantGeneratorOutput = run.output.data
                payload.merge(quiz)
                await self._quiz_repository.update(quiz, fresh_generated=True)

                await update_span_with_result(
                    self._lf,
                    run,
                    span,
                    quiz.author_id,
                    cache_key,
                    QUIZ_INSTANT_GENERATOR_LLM,
                )

        except Exception as e:
            logging.exception("Failed to generate quiz instant: %s", e)
            await self._catch_exception(e, quiz)

    async def _inject_request_prompt(
        self, ctx: RunContext[AIQuizInstantGeneratorDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        quiz = ctx.deps.quiz

        return (
            [ModelRequest(parts=self._build_pre_prompt(quiz))]
            + messages
            + [ModelRequest(parts=self._build_post_prompt(quiz))]
        )

    def _build_pre_prompt(self, quiz: Quiz) -> list[ModelRequestPart]:
        user_contents = []
        if quiz.query:
            user_contents.append(f"User query:\n{quiz.query}")

        if quiz.material_content:
            user_contents.append("Quiz materials:")
            user_contents.append(quiz.material_content)

        parts = []
        parts.append(UserPromptPart(content=user_contents))
        return parts

    def _build_post_prompt(self, quiz: Quiz) -> list[ModelRequestPart]:
        prev_quiz_items = quiz.prev_items()

        dynamic_config = quiz.gen_config
        prev_questions = dynamic_config.negative_questions + [
            qi.question for qi in prev_quiz_items
        ]
        prev_questions = "\n".join(set(prev_questions))

        difficulty = quiz.difficulty

        extra_beginner = "\n".join(set(dynamic_config.extra_beginner))
        extra_expert = "\n".join(set(dynamic_config.extra_expert))
        more_on_topic = "\n".join(set(dynamic_config.more_on_topic))
        less_on_topic = "\n".join(set(dynamic_config.less_on_topic))
        adds = "\n".join(set(dynamic_config.additional_instructions))

        post_parts = []

        post_parts.append(
            SystemPromptPart(
                content=self._lf.get_prompt("quizer/base", label=settings.env).compile()
            )
        )

        if len(adds) > 0:
            post_parts.append(
                UserPromptPart(
                    content=f"Additional questions: {adds}",
                )
            )

        if len(prev_questions) > 0:
            post_parts.append(
                SystemPromptPart(
                    content=self._lf.get_prompt(
                        "quizer/negative_questions", label=settings.env
                    ).compile(questions=prev_questions),
                )
            )

        post_parts.append(
            SystemPromptPart(
                content=self._lf.get_prompt(
                    f"quizer/{difficulty}", label=settings.env
                ).compile()
            )
        )

        if len(extra_beginner) > 0:
            post_parts.append(
                SystemPromptPart(
                    content=self._lf.get_prompt(
                        "quizer/extra_beginner", label=settings.env
                    ).compile(questions=extra_beginner),
                )
            )
        if len(extra_expert) > 0:
            post_parts.append(
                SystemPromptPart(
                    content=self._lf.get_prompt(
                        "quizer/extra_expert", label=settings.env
                    ).compile(questions=extra_expert),
                )
            )
        if len(more_on_topic) > 0:
            post_parts.append(
                SystemPromptPart(
                    content=self._lf.get_prompt(
                        "quizer/more_on_topic", label=settings.env
                    ).compile(questions=more_on_topic),
                )
            )
        if len(less_on_topic) > 0:
            post_parts.append(
                SystemPromptPart(
                    content=self._lf.get_prompt(
                        "quizer/less_on_topic", label=settings.env
                    ).compile(questions=less_on_topic),
                )
            )

        return post_parts

    async def _catch_exception(self, e: Exception, quiz: Quiz) -> None:
        logging.exception("Agent run failed for quiz %s: %s", quiz.id, e)
        quiz.fail()
        await self._quiz_repository.update(quiz)
