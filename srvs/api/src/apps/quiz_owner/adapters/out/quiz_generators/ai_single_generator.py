from dataclasses import dataclass
import logging
from typing import Annotated
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

from ....domain.out import PatchGenerator, PatchGeneratorDto
from ....domain.models import Quiz, QuizItemVariant


QUIZ_GENERATOR_LLM = LLMS.GROK_4_FAST
IN_QUERY = ""


@dataclass
class AISingleGeneratorDeps:
    quiz: Quiz
    chunks: list[str]


class AnswerSchema(BaseModel):
    answer: Annotated[str, Field(title="Answer", description="The answer text.")]
    explanation: Annotated[
        str, Field(title="Answer Explanation", description="The explanation text.")
    ]
    correct: Annotated[
        bool, Field(title="Correct", description="Whether the answer is correct.")
    ]


class AIQuizInstantGeneratorOutput(BaseModel):
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

    def merge(self, quiz: Quiz):
        quiz.generation_step(
            question=self.question,
            variants=[
                QuizItemVariant(
                    content=a.answer,
                    is_correct=a.correct,
                    explanation=a.explanation,
                )
                for a in self.answers
            ],
        )


class AISingleGenerator(PatchGenerator):
    def __init__(self, lf: Langfuse):
        self._lf = lf

        self._ai = Agent(
            history_processors=[self._inject_request_prompt],
            output_type=AIQuizInstantGeneratorOutput,
            deps_type=AISingleGeneratorDeps,
            model=QUIZ_GENERATOR_LLM,
        )

    async def generate(self, dto: PatchGeneratorDto) -> None:
        logging.info(
            f"Generating quiz instant for quiz {dto.quiz.id} (generation {dto.quiz.generation})"
        )
        if dto.chunks is None:
            raise ValueError("Chunks are required")

        try:
            with self._lf.start_as_current_span(name=f"quiz-patch") as span:
                run = await self._ai.run(
                    IN_QUERY,
                    model=QUIZ_GENERATOR_LLM,
                    deps=AISingleGeneratorDeps(quiz=dto.quiz, chunks=dto.chunks),
                    model_settings={
                        "extra_body": {
                            "reasoning_effort": "low",
                            # "service_tier": "priority" if priority else "default",
                            "service_tier": "default",
                            "prompt_cache_key": dto.cache_key,
                        },
                    },
                )

                payload = run.output
                payload.merge(dto.quiz)

                await update_span_with_result(
                    self._lf,
                    run,
                    span,
                    dto.quiz.author_id,
                    dto.cache_key,
                    QUIZ_GENERATOR_LLM,
                )

        except Exception as e:
            logging.exception("Failed to generate quiz instant: %s", e)
            dto.quiz.fail()
            raise e

    async def _inject_request_prompt(
        self, ctx: RunContext[AISingleGeneratorDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        quiz = ctx.deps.quiz
        chunks = ctx.deps.chunks

        return (
            [ModelRequest(parts=self._build_pre_prompt(quiz, chunks))]
            + messages
            + [ModelRequest(parts=self._build_post_prompt(quiz))]
        )

    def _build_pre_prompt(
        self, quiz: Quiz, chunks: list[str]
    ) -> list[ModelRequestPart]:
        user_contents = []
        if quiz.query:
            user_contents.append(f"User query:\n{quiz.query}")

        if chunks:
            user_contents.append("Quiz materials:")
            user_contents.append("\n".join(chunks))

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
