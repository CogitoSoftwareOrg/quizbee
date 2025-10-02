import json
from datetime import datetime, timezone
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
    UserPromptPart,
)
from pydantic_ai import RunContext
from .models import QuizerDeps
from src.lib.clients import langfuse_client
from src.lib.settings import settings


def inject_request_prompt(
    ctx: RunContext[QuizerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    prev_quiz_items = ctx.deps.prev_quiz_items
    difficulty = ctx.deps.quiz.get("difficulty")
    extra_beginner = "\n".join(ctx.deps.dynamic_config.extraBeginner)
    extra_expert = "\n".join(ctx.deps.dynamic_config.extraExpert)
    more_on_topic = "\n".join(ctx.deps.dynamic_config.moreOnTopic)
    less_on_topic = "\n".join(ctx.deps.dynamic_config.lessOnTopic)

    pre_parts = []
    post_parts = []

    # PRE PARTS, SIMMILAR FOR EACH PATCH
    pre_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                "quizer/base", label=settings.env
            ).compile()
        )
    )

    # POST PARTS, CAN VARY FOR EACH PATCH
    post_parts.append(
        SystemPromptPart(
            content=langfuse_client.get_prompt(
                f"quizer/{difficulty}", label=settings.env
            ).compile()
        )
    )

    if len(prev_quiz_items) > 0:
        post_parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/negative_questions", label=settings.env
                ).compile(questions=prev_quiz_items),
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
