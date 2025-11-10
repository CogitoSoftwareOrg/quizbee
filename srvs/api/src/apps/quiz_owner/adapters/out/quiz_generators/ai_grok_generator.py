import logging
from typing import Annotated
from langfuse import Langfuse
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, model_validator

from src.lib.settings import settings

from ....domain.out import PatchGenerator, PatchGeneratorDto
from ....domain.models import Quiz, QuizItemVariant
from ....domain.constants import PATCH_LIMIT


QUIZ_GENERATOR_MODEL = "grok-4-fast-non-reasoning"
RETRIES = 1
TEMPERATURE = 0.5
TOP_P = 0.95


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

    @model_validator(mode="after")
    def _check_answers(self):
        if len(self.answers) != 4:
            raise ValueError("Exactly 4 answers are required.")
        if sum(1 for a in self.answers if a.correct) != 1:
            raise ValueError("Exactly one answer must be correct.")
        for a in self.answers:
            if not a.answer.strip() or not a.explanation.strip():
                raise ValueError("Answer and explanation must be non-empty.")
        return self


class AIGrokGeneratorOutput(BaseModel):
    quiz_items: Annotated[
        list[QuizItemSchema],
        Field(
            title="Quiz Items",
            description=f"An array of exactly {PATCH_LIMIT} quiz items.",
            min_length=PATCH_LIMIT,
            max_length=PATCH_LIMIT,
        ),
    ]

    def merge(self, quiz: Quiz):
        for schema in self.quiz_items:
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


class AIGrokGenerator(PatchGenerator):
    def __init__(self, lf: Langfuse):
        self._lf = lf
        self._client = OpenAI(
            api_key=settings.grok_api_key,
            base_url="https://api.x.ai/v1",
        )
        logging.info("✓ Grok client initialized")

    async def generate(self, dto: PatchGeneratorDto) -> None:
        logging.info(
            f"Generating quiz instant for quiz {dto.quiz.id} (generation {dto.quiz.generation})"
        )
        if dto.chunks is None:
            raise ValueError("Chunks are required")

        try:
            with self._lf.start_as_current_span(name="quiz-patch") as span:
                span.update_trace(
                    user_id=dto.quiz.author_id,
                    session_id=dto.cache_key,
                )
                
                # Build messages
                messages = self._build_messages(dto.quiz, dto.chunks)

                # Make API call with structured output
                completion = self._client.beta.chat.completions.parse(
                    model=QUIZ_GENERATOR_MODEL,
                    messages=messages,
                    response_format=AIGrokGeneratorOutput,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                )

                # Extract and merge results
                payload = completion.choices[0].message.parsed
                if payload is None:
                    raise ValueError("Failed to parse structured output")
                
                payload.merge(dto.quiz)

                # Update Langfuse generation
                usage = completion.usage
                self._lf.update_current_generation(
                    input=messages,
                    output=payload.model_dump(),
                    model=QUIZ_GENERATOR_MODEL,
                    usage_details={
                        "input": usage.prompt_tokens if usage else 0,
                        "output": usage.completion_tokens if usage else 0,
                        "total": usage.total_tokens if usage else 0,
                    } if usage else None,
                )

        except Exception as e:
            logging.exception("Failed to generate quiz instant: %s", e)
            dto.quiz.fail()
            raise e

    def _build_messages(self, quiz: Quiz, chunks: list[str]) -> list[ChatCompletionMessageParam]:
        """Build the messages array for the chat completion."""
        messages: list[ChatCompletionMessageParam] = []

        # Add user context (materials and query)
        user_contents = []
        if quiz.query:
            user_contents.append(f"User query:\n{quiz.query}\n")

        if chunks:
            user_contents.append("Quiz materials:\n")
            user_contents.append("\n".join(chunks))

        if user_contents:
            messages.append({
                "role": "user",
                "content": "\n".join(user_contents)
            })

        # Add system prompts
        messages.append({
            "role": "system",
            "content": self._lf.get_prompt("quizer/base", label=settings.env).compile()
        })

        # Add additional instructions if present
        dynamic_config = quiz.gen_config
        if dynamic_config.additional_instructions:
            adds = "\n".join(set(dynamic_config.additional_instructions))
            if adds:
                messages.append({
                    "role": "user",
                    "content": f"Additional questions: {adds}"
                })

        # Add negative questions (questions to avoid)
        prev_quiz_items = quiz.prev_items()
        prev_questions = dynamic_config.negative_questions + [
            qi.question for qi in prev_quiz_items
        ]
        if prev_questions:
            prev_questions_str = "\n".join(set(prev_questions))
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/negative_questions", label=settings.env
                ).compile(questions=prev_questions_str)
            })

        # Add difficulty level
        messages.append({
            "role": "system",
            "content": self._lf.get_prompt(
                f"quizer/{quiz.difficulty}", label=settings.env
            ).compile()
        })

        # Add extra beginner questions if present
        if dynamic_config.extra_beginner:
            extra_beginner = "\n".join(set(dynamic_config.extra_beginner))
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/extra_beginner", label=settings.env
                ).compile(questions=extra_beginner)
            })

        # Add extra expert questions if present
        if dynamic_config.extra_expert:
            extra_expert = "\n".join(set(dynamic_config.extra_expert))
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/extra_expert", label=settings.env
                ).compile(questions=extra_expert)
            })

        # Add more on topic questions if present
        if dynamic_config.more_on_topic:
            more_on_topic = "\n".join(set(dynamic_config.more_on_topic))
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/more_on_topic", label=settings.env
                ).compile(questions=more_on_topic)
            })

        # Add less on topic questions if present
        if dynamic_config.less_on_topic:
            less_on_topic = "\n".join(set(dynamic_config.less_on_topic))
            messages.append({
                "role": "system",
                "content": self._lf.get_prompt(
                    "quizer/less_on_topic", label=settings.env
                ).compile(questions=less_on_topic)
            })

        return messages
