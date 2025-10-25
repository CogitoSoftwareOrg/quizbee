from pydantic_ai import RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
    UserPromptPart,
)

from src.lib.clients import langfuse_client
from src.lib.settings import settings

from src.lib.ai import DynamicConfig, QuizerDeps, build_pre_prompt


async def inject_request_prompt(
    ctx: RunContext[QuizerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    quiz = ctx.deps.quiz
    prev_quiz_items = ctx.deps.prev_quiz_items

    dynamic_config = DynamicConfig(**quiz.get("dynamicConfig", {}))
    prev_questions = dynamic_config.negativeQuestions + [
        qi.get("question", "") for qi in prev_quiz_items
    ]
    prev_questions = "\n".join(set(prev_questions))

    difficulty = quiz.get("difficulty")

    extra_beginner = "\n".join(set(dynamic_config.extraBeginner))
    extra_expert = "\n".join(set(dynamic_config.extraExpert))
    more_on_topic = "\n".join(set(dynamic_config.moreOnTopic))
    less_on_topic = "\n".join(set(dynamic_config.lessOnTopic))
    adds = "\n".join(set(dynamic_config.adds))

    pre_parts = await build_pre_prompt(ctx.deps.http, ctx.deps.quiz)

    # POST PARTS, CAN VARY FOR EACH PATCH
    post_parts = []

    post_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "quizer/base", label=settings.env
            ).compile()
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
                content=langfuse_client.get_prompt(
                    "quizer/negative_questions", label=settings.env
                ).compile(questions=prev_questions),
            )
        )

    post_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                f"quizer/{difficulty}", label=settings.env
            ).compile()
        )
    )

    if len(extra_beginner) > 0:
        post_parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/extra_beginner", label=settings.env
                ).compile(questions=extra_beginner),
            )
        )
    if len(extra_expert) > 0:
        post_parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/extra_expert", label=settings.env
                ).compile(questions=extra_expert),
            )
        )
    if len(more_on_topic) > 0:
        post_parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/more_on_topic", label=settings.env
                ).compile(questions=more_on_topic),
            )
        )
    if len(less_on_topic) > 0:
        post_parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/less_on_topic", label=settings.env
                ).compile(questions=less_on_topic),
            )
        )

    return [ModelRequest(parts=pre_parts)] + messages + [ModelRequest(parts=post_parts)]
