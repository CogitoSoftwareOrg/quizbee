from pydantic_ai import RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    SystemPromptPart,
)

from lib.clients import langfuse_client
from lib.settings import settings

from lib.ai import DynamicConfig, QuizerDeps, build_pre_prompt


async def inject_request_prompt(
    ctx: RunContext[QuizerDeps], messages: list[ModelMessage]
) -> list[ModelMessage]:
    quiz = ctx.deps.quiz
    prev_quiz_items = ctx.deps.prev_quiz_items

    dynamic_config = DynamicConfig(**quiz.get("dynamicConfig", {}))
    difficulty = quiz.get("difficulty")

    extra_beginner = "\n".join(dynamic_config.extraBeginner)
    extra_expert = "\n".join(dynamic_config.extraExpert)
    more_on_topic = "\n".join(dynamic_config.moreOnTopic)
    less_on_topic = "\n".join(dynamic_config.lessOnTopic)

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

    if len(dynamic_config.adds) > 0:
        post_parts.append(
            SystemPromptPart(
                content=langfuse_client.get_prompt(
                    "quizer/adds", label=settings.env
                ).compile(questions=dynamic_config.adds),
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
