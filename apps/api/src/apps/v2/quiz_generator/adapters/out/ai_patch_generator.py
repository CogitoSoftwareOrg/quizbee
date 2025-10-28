from dataclasses import dataclass, field
import logging
from typing import Annotated, Any, Literal, Type
import httpx
from langfuse import Langfuse
from pydantic import BaseModel, Field
from pocketbase.models.dtos import Record
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

from ...domain.ports import PatchGenerator, QuizRepository
from ...domain.models import Quiz, QuizItem, QuizItemStatus, QuizItemVariant


@dataclass
class AIPatchGeneratorDeps:
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


class AIPatchGeneratorOutput(BaseModel):
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


class AIPatchGenerator(PatchGenerator):
    def __init__(
        self, lf: Langfuse, quiz_repository: QuizRepository, shared_schema: Any
    ):
        self._lf = lf
        self._quiz_repository = quiz_repository
        self._ai = Agent(
            # instrument=True,
            model=LLMS.GPT_5_MINI,
            deps_type=AIPatchGeneratorDeps,
            output_type=shared_schema,
            history_processors=[self._inject_request_prompt],
            retries=3,
        )

    async def generate(self, quiz: Quiz, cache_key: str) -> None:
        generation = quiz.generation
        seen = 0
        cancelled = False

        generating_items = quiz.generating_items()

        try:
            with self._lf.start_as_current_span(name=f"quiz-patch") as span:
                async with self._ai.run_stream(
                    deps=AIPatchGeneratorDeps(quiz=quiz),
                    model_settings={
                        "extra_body": {
                            "reasoning_effort": "low",
                            # "service_tier": "priority" if priority else "default",
                            "service_tier": "default",
                            "prompt_cache_key": cache_key,
                        },
                    },
                ) as run:
                    async for output in run.stream_output():
                        if output.data.mode != "quiz":
                            raise ValueError(f"Unexpected output type: {type(output)}")

                        quiz = await self._quiz_repository.get(quiz.id)
                        if quiz.generation != generation:
                            logging.info(
                                "Quiz generation changed during patch generation: %s -> %s",
                                generation,
                                quiz.generation,
                            )
                            cancelled = True
                            break

                        logging.info(
                            f"Quiz generation is the same: {generation} == {quiz.generation}"
                        )

                        payload: AIPatchGeneratorOutput = output.data
                        items = payload.quiz_items or []
                        if len(items) > 0:
                            for item, schema in zip(
                                generating_items[seen : len(items)], items[seen:]
                            ):
                                domain_item = self._item_schema_to_domain(
                                    item.id, item.order, schema
                                )
                                await self._quiz_repository.save_item(domain_item)
                                seen += 1

        except Exception as e:
            logging.exception("Failed to generate quiz patch: %s", e)
            await self._catch_exception(e, cancelled, quiz)

    async def _inject_request_prompt(
        self, ctx: RunContext[AIPatchGeneratorDeps], messages: list[ModelMessage]
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

    def _item_schema_to_domain(
        self, id: str, order: int, item: QuizItemSchema
    ) -> QuizItem:
        return QuizItem(
            id=id,
            question=item.question,
            variants=[
                QuizItemVariant(
                    content=a.answer,
                    is_correct=a.correct,
                    explanation=a.explanation,
                )
                for a in item.answers
            ],
            order=order,
            status=QuizItemStatus.GENERATED,
        )

    async def _catch_exception(self, e: Exception, cancelled: bool, quiz: Quiz) -> None:
        if isinstance(e, httpx.ReadError):
            if cancelled:
                logging.info(
                    "Quiz %s stream ended due to graceful cancellation: %s",
                    quiz.id,
                    e,
                )
                return
            raise

        if isinstance(e, RuntimeError):
            if cancelled and "asynchronous generator is already running" in str(e):
                logging.info(
                    "Quiz %s stream ended due to graceful cancellation (generator already running): %s",
                    quiz.id,
                    e,
                )
                return
            raise

        if cancelled:
            logging.info(
                "Quiz %s stream ended due to graceful cancellation: %s",
                quiz.id,
                e,
            )
            return

        logging.exception("Agent run failed for quiz %s: %s", quiz.id, e)
        quiz.fail()
        await self._quiz_repository.save(quiz)
