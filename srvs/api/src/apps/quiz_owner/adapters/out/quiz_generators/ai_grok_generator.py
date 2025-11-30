from dataclasses import dataclass
import random
import logging
from typing import Annotated
from langfuse import Langfuse
from pydantic import BaseModel, Field, model_validator
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    PromptedOutput,
    RunContext,
    SystemPromptPart,
    UserPromptPart,
    UnexpectedModelBehavior,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from src.lib.utils import update_span_with_result
from src.lib.config import LLMS
from src.lib.settings import settings

from ....domain.out import PatchGenerator, PatchGeneratorDto
from ....domain.models import Quiz, QuizItemVariant
from ....domain.constants import PATCH_LIMIT


QUIZ_GENERATOR_LLM = LLMS.GROK_4_FAST
IN_QUERY = ""
RETRIES = 5
UNEXPECTED_BEHAVIOR_RETRIES = 3
TEMPERATURE = 0.4
TOP_P = 0.95

logger = logging.getLogger(__name__)


@dataclass
class AIGrokGeneratorDeps:
    quiz: Quiz
    chunks: list[str] | list[list[str]] | None


class AnswerSchema(BaseModel):
    answer: Annotated[str, Field(title="Answer", description="The answer text.")]
    explanation: Annotated[
        str, Field(title="Answer Explanation", description="The explanation text.")
    ]
    correct: Annotated[
        bool, Field(title="Correct", description="Whether the answer is correct.")
    ]


class AIGrokGeneratorOutputOnlyQuery(BaseModel):
    question: Annotated[
        str, Field(title="Question", description="The quiz question text.")
    ]
    hint: Annotated[
        str,
        Field(
            title="Hint",
            description="A helpful hint for the user to guide them towards the correct answer without revealing it directly.",
        ),
    ]
    answers: Annotated[
        list[AnswerSchema],
        Field(
            title="Answers",
            description="The answers to the question. 4 in total with ONLY one correct answer.",
            min_length=4,
        ),
    ]

    @model_validator(mode="after")
    def _check_answers(self):
        if not self.hint or not self.hint.strip():
            raise ValueError("Hint is required and cannot be empty.")

        parsed_answers = []
        for a in self.answers:
            if not a.answer.strip() or not a.explanation.strip():
                continue
            parsed_answers.append(a)

        if len(parsed_answers) < 4:
            raise ValueError("At least 4 valid answers are required.")

        if len(parsed_answers) > 4:
            logger.warning(f"More than 4 answers returned: {len(parsed_answers)}")

        correct_answers = [a for a in parsed_answers if a.correct]
        incorrect_answers = [a for a in parsed_answers if not a.correct]

        if len(correct_answers) == 0:
            raise ValueError("At least one correct answer is required.")
        if len(incorrect_answers) < 3:
            raise ValueError("At least 3 incorrect answers are required.")

        final_answers = [correct_answers[0]] + incorrect_answers[:3]
        random.shuffle(final_answers)

        self.answers = final_answers

        return self

    def merge(self, quiz: Quiz, item_order: int) -> list[int]:
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
            order=item_order,
            hint=self.hint,
        )
        return []


class AIGrokGeneratorOutputWithChunks(AIGrokGeneratorOutputOnlyQuery):
    used_chunk_indices: Annotated[
        list[int],
        Field(
            title="Used Chunk Indices",
            description="Indices of chunks (0-based) that were actually used to generate this question. Only include chunks that directly contributed to the question, answers, or explanations.",
            default_factory=list,
        ),
    ]

    @model_validator(mode="after")
    def _check_chunk_indices(self):
        if not isinstance(self.used_chunk_indices, list):
            raise ValueError("used_chunk_indices must be a list.")

        if len(self.used_chunk_indices) == 0:
            logger.warning("No chunk indices were marked as used for this question.")

        return self

    def merge(self, quiz: Quiz, item_order: int) -> list[int]:
        super().merge(quiz, item_order)
        return self.used_chunk_indices


class AIGrokGenerator(PatchGenerator):
    def __init__(self, lf: Langfuse, provider: OpenAIProvider):
        self._lf = lf
        self._ai = None
        self._provider = provider

    def _get_agent(self, has_chunks: bool):
        output_type = (
            AIGrokGeneratorOutputWithChunks
            if has_chunks
            else AIGrokGeneratorOutputOnlyQuery
        )

        return Agent(
            history_processors=[self._inject_request_prompt],
            output_type=output_type,
            deps_type=AIGrokGeneratorDeps,
            model=OpenAIChatModel(QUIZ_GENERATOR_LLM, provider=self._provider),
            retries=RETRIES,
        )

    async def generate(self, dto: PatchGeneratorDto) -> None:
        logging.info(
            f"Generating quiz instant for quiz {dto.quiz.id} (generation {dto.quiz.generation})"
        )
        if dto.item_order is None:
            raise ValueError("Item order is required")

        has_chunks = bool(dto.chunks)
        agent = self._get_agent(has_chunks)

        last_error: Exception | None = None

        for attempt in range(UNEXPECTED_BEHAVIOR_RETRIES):
            try:
                with self._lf.start_as_current_span(name=f"quiz-patch") as span:
                    run = await agent.run(
                        IN_QUERY,
                        model=QUIZ_GENERATOR_LLM,
                        deps=AIGrokGeneratorDeps(quiz=dto.quiz, chunks=dto.chunks or []),
                        model_settings={
                            "temperature": TEMPERATURE,
                            "top_p": TOP_P,
                            "extra_body": {},
                        },
                    )

                    payload = run.output
                    used_indices = payload.merge(dto.quiz, item_order=dto.item_order)

                    dto.used_chunk_indices = used_indices

                    await update_span_with_result(
                        self._lf,
                        run,
                        span,
                        dto.quiz.author_id,
                        dto.cache_key,
                        QUIZ_GENERATOR_LLM,
                    )

                return

            except UnexpectedModelBehavior as e:
                last_error = e
                if attempt < UNEXPECTED_BEHAVIOR_RETRIES - 1:
                    logger.warning(
                        f"UnexpectedModelBehavior on attempt {attempt + 1}/{UNEXPECTED_BEHAVIOR_RETRIES}, "
                        f"retrying: {e}"
                    )
                else:
                    logger.error(
                        f"UnexpectedModelBehavior on final attempt {attempt + 1}/{UNEXPECTED_BEHAVIOR_RETRIES}: {e}"
                    )

            except Exception as e:
                logging.exception("Failed to generate quiz instant: %s", e)
                dto.quiz.fail()
                raise e

        logging.exception("Failed to generate quiz instant after retries: %s", last_error)
        dto.quiz.fail()
        raise last_error  # type: ignore

    async def _inject_request_prompt(
        self, ctx: RunContext[AIGrokGeneratorDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        quiz = ctx.deps.quiz
        chunks = ctx.deps.chunks

        return (
            [ModelRequest(parts=self._build_pre_prompt(quiz, chunks))]
            + messages
            + [ModelRequest(parts=self._build_post_prompt(quiz))]
        )

    def _build_pre_prompt(
        self, quiz: Quiz, chunks: list[str] | list[list[str]] | None
    ) -> list[ModelRequestPart]:

        prompt_name = (
            "quizer/base_patch1" if chunks else "quizer/base_patch1_only_query"
        )

        parts: list[ModelRequestPart] = [
            SystemPromptPart(
                content=self._lf.get_prompt(prompt_name, label=settings.env).compile(
                    target_language=quiz.target_language
                )
            )
        ]

        user_contents = []
        if quiz.query:
            user_contents.append(f"User query:\n{quiz.query}\n")

        if chunks:
            user_contents.append("Quiz materials:\n")

            if len(chunks) > 0 and isinstance(chunks[0], list):
                from typing import cast

                chunks_nested = cast(list[list[str]], chunks)

                formatted_collections = []
                chunk_idx = 0
                for idx, chunk_list in enumerate(chunks_nested, 1):
                    collection_header = f"\n--- Chunk collection {idx} ---\n"
                    formatted_chunks = []
                    for chunk in chunk_list:
                        formatted_chunks.append(
                            f"[CHUNK {chunk_idx}]\n{chunk}\n[/CHUNK {chunk_idx}]"
                        )
                        chunk_idx += 1
                    formatted_collections.append(
                        collection_header + "\n".join(formatted_chunks)
                    )

                user_contents.append("\n".join(formatted_collections))
            else:
                from typing import cast

                chunks_flat = cast(list[str], chunks)

                formatted_chunks = []
                for chunk_idx, chunk in enumerate(chunks_flat):
                    formatted_chunks.append(
                        f"[CHUNK {chunk_idx}]\n{chunk}\n[/CHUNK {chunk_idx}]"
                    )

                user_contents.append("\n".join(formatted_chunks))

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

        # post_parts.append(
        #     SystemPromptPart(
        #         content=self._lf.get_prompt(
        #             "quizer/base_patch1", label=settings.env
        #         ).compile()
        #     )
        # )

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
