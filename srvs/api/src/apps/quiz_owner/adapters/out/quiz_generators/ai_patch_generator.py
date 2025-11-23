import asyncio
from dataclasses import dataclass
import logging
import os
from typing import Annotated, Any, Literal
import httpx
from langfuse import Langfuse
from openai import OpenAI
from pydantic import BaseModel, Field

from src.lib.utils import update_span_with_result
from src.lib.config import LLMS
from src.lib.settings import settings

from ....domain.out import PatchGenerator, QuizRepository
from ....domain.models import Quiz, QuizItem, QuizItemStatus, QuizItemVariant


PATCH_GENERATOR_LLM = LLMS.GPT_5_MINI
IN_QUERY = "Generate Quiz Patch"


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
    hint: Annotated[
        str, Field(title="Hint", description="A hint for the question.", default="")
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
        self,
        lf: Langfuse,
        quiz_repository: QuizRepository,
        output_type: Any,
    ):
        self._lf = lf
        self._quiz_repository = quiz_repository
        self._output_type = output_type

        # Initialize OpenAI client for Grok API
        self._client = OpenAI(
            api_key=os.getenv("GROK_API_KEY"),
            base_url="https://api.x.ai/v1",
        )

    async def generate(self, quiz: Quiz, cache_key: str) -> None:
        logging.info(
            f"Generating quiz patch for quiz {quiz.id} (generation {quiz.generation})"
        )

        generation = quiz.generation
        cancelled = False

        # Кэшируем начальные generating items ДО начала стриминга
        initial_generating_items = quiz.generating_items()
        logging.info(f"Initial generating items count: {len(initial_generating_items)}")

        try:
            with self._lf.start_as_current_span(name=f"quiz-patch") as span:
                # Build messages for OpenAI API
                messages = self._build_messages(quiz)
                
                # Call OpenAI API with structured output
                completion = self._client.beta.chat.completions.parse(
                    model="grok-4-fast-non-reasoning",
                    messages=messages,  # type: ignore
                    response_format=self._output_type,
                )

                # Parse the result
                result: AIPatchGeneratorOutput = completion.choices[0].message.parsed  # type: ignore
                
                if result.mode != "quiz":
                    raise ValueError(f"Unexpected output type: {result.mode}")

                # Перезагружаем quiz для проверки generation
                fresh_quiz = await self._quiz_repository.get(quiz.id)
                if fresh_quiz.generation != generation:
                    logging.info(
                        "Quiz generation changed during patch generation: %s -> %s",
                        generation,
                        fresh_quiz.generation,
                    )
                    cancelled = True
                    return

                quiz = fresh_quiz

                # Обновляем все items
                for idx, schema in enumerate(result.quiz_items):
                    if idx >= len(initial_generating_items):
                        logging.warning(
                            f"More items returned ({len(result.quiz_items)}) than expected ({len(initial_generating_items)})"
                        )
                        break
                    
                    itm = initial_generating_items[idx]
                    
                    # Проверяем, не ответил ли пользователь уже
                    current_item = next(
                        (item for item in quiz.items if item.id == itm.id),
                        None,
                    )
                    if current_item and current_item.status == QuizItemStatus.FINAL:
                        logging.info(
                            f"Skipping update for item {itm.id} - already FINAL (user answered)"
                        )
                        continue

                    upd = QuizItem(
                        id=itm.id,
                        question=schema.question,
                        variants=[
                            QuizItemVariant(
                                content=a.answer,
                                is_correct=a.correct,
                                explanation=a.explanation,
                            )
                            for a in schema.answers
                        ],
                        order=itm.order,
                        status=QuizItemStatus.GENERATED,
                        hint=schema.hint,
                    )
                    quiz.update_item(upd)

                await self._quiz_repository.update(quiz)

                # Update span with results
                span.update(
                    output={"quiz_items_count": len(result.quiz_items)},
                    metadata={
                        "quiz_id": quiz.id,
                        "generation": generation,
                        "model": "grok-2-1212",
                    },
                )

        except Exception as e:
            logging.exception("Failed to generate quiz patch: %s", e)
            await self._catch_exception(e, cancelled, quiz)

    def _build_messages(self, quiz: Quiz) -> list[dict]:
        """Build messages array for OpenAI API"""
        messages = []
        
        # Add user content (query and materials)
        user_content_parts = []
        if quiz.query:
            user_content_parts.append(f"User query:\n{quiz.query}")
        
        if quiz.material_content:
            user_content_parts.append("Quiz materials:")
            user_content_parts.append(quiz.material_content)
        
        if user_content_parts:
            messages.append({
                "role": "user",
                "content": "\n\n".join(user_content_parts)
            })
        
        # Build system prompts
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
        
        # Base system prompt
        system_parts = []
        system_parts.append(
            self._lf.get_prompt("quizer/base", label=settings.env).compile()
        )
        
        # Add difficulty prompt
        system_parts.append(
            self._lf.get_prompt(f"quizer/{difficulty}", label=settings.env).compile()
        )
        
        messages.append({
            "role": "system",
            "content": "\n\n".join(system_parts)
        })
        
        # Add additional instructions if any
        if len(adds) > 0:
            messages.append({
                "role": "user",
                "content": f"Additional questions: {adds}"
            })
        
        # Add negative questions prompt
        if len(prev_questions) > 0:
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/negative_questions", label=settings.env
                ).compile(questions=prev_questions)
            })
        
        # Add extra beginner questions
        if len(extra_beginner) > 0:
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/extra_beginner", label=settings.env
                ).compile(questions=extra_beginner)
            })
        
        # Add extra expert questions
        if len(extra_expert) > 0:
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/extra_expert", label=settings.env
                ).compile(questions=extra_expert)
            })
        
        # Add more on topic
        if len(more_on_topic) > 0:
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/more_on_topic", label=settings.env
                ).compile(questions=more_on_topic)
            })
        
        # Add less on topic
        if len(less_on_topic) > 0:
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/less_on_topic", label=settings.env
                ).compile(questions=less_on_topic)
            })
        
        return messages

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
        await self._quiz_repository.update(quiz)
