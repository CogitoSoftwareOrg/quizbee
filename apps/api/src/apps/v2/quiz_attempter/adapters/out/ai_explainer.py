import logging
from dataclasses import dataclass
from typing import Any, Literal, AsyncIterable

from langfuse import Langfuse
from pydantic import BaseModel
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    RunContext,
    SystemPromptPart,
    UserPromptPart,
    ToolCallPart,
    ToolReturn,
    ModelResponse,
    ToolReturnPart,
    TextPart,
)

from src.lib.config import LLMS
from src.lib.settings import settings
from src.lib.clients import update_span_with_result

from ...domain.models import (
    Attempt,
    QuizRef,
)
from ...domain.refs import (
    MessageRef,
    QuizItemRef,
    MessageRole,
    MessageStatus,
    MessageMetadata,
)
from ...domain.ports import Explainer

EXPLAINER_LLM = LLMS.GPT_5_MINI


@dataclass
class ExplainerDeps:
    quiz: QuizRef
    current_item: QuizItemRef


class ExplainerOutput(BaseModel):
    mode: Literal["explanation"]
    explanation: str


class AIExplainer(Explainer):
    def __init__(self, lf: Langfuse, ai: Agent[ExplainerDeps, Any]):
        self._lf = lf
        self._ai = ai
        self._ai.history_processors += [self._inject_system_prompt]  # type: ignore

    async def explain(
        self,
        query: str,
        attempt: Attempt,
        item: QuizItemRef,
        ai_msg: MessageRef,
        cache_key: str,
    ) -> AsyncIterable[MessageRef]:
        content = ""

        deps = ExplainerDeps(
            quiz=attempt.quiz,
            current_item=item,
        )

        with self._lf.start_as_current_span(name="explainer-agent") as span:
            async with self._ai.run_stream(
                query,
                message_history=self._ai_history(attempt.message_history),
                deps=deps,
                model_settings={
                    "extra_body": {
                        "reasoning_effort": "low",
                        "prompt_cache_key": cache_key,
                    }
                },
            ) as run:
                i = 0
                async for output in run.stream_output():
                    if output.data.mode != "explanation":
                        raise ValueError(f"Unexpected output type: {type(output)}")
                    text = output.data.explanation[len(content) :]
                    content += text
                    yield MessageRef(
                        id=ai_msg.id,
                        attempt_id=attempt.id,
                        content=text,
                        role=MessageRole.AI,
                        status=MessageStatus.STREAMING,
                        metadata=MessageMetadata(),
                    )

            await update_span_with_result(
                self._lf,
                run,
                span,
                attempt.user_id,
                cache_key,
                EXPLAINER_LLM,
            )

    async def _inject_system_prompt(
        self, ctx: RunContext[ExplainerDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        pre_parts = self._build_pre_prompt(ctx.deps)

        return [ModelRequest(parts=pre_parts)] + messages

    def _build_pre_prompt(self, deps: ExplainerDeps) -> list[ModelRequestPart]:
        user_contents = []
        if deps.quiz.query:
            user_contents.append(f"User query:\n{deps.quiz.query}")

        if deps.quiz.material_content:
            user_contents.append("Quiz materials:")
            user_contents.append(deps.quiz.material_content)

        parts = []
        parts.append(UserPromptPart(content=user_contents))
        parts.append(
            SystemPromptPart(
                content=self._lf.get_prompt(
                    "explainer/base", label=settings.env
                ).compile(
                    question=deps.current_item.question,
                    answers=deps.current_item.answers,
                    decision=deps.current_item.choice,
                )
            )
        )
        return parts

    def _ai_history(self, history: list[MessageRef]) -> list[ModelMessage]:
        ai: list[ModelMessage] = []

        for msg in history:
            # name = pb_message.get("sentBy")
            role = msg.role
            meta = msg.metadata
            content = msg.content.strip()

            logging.info(f"PB Message: {role} {content} {meta}")

            if role == "user":
                if content:
                    ai.append(
                        ModelRequest(parts=[UserPromptPart(content=f"{content}")])
                    )
            elif role == "ai":
                parts = []
                for tc in meta.tool_calls:
                    parts.append(
                        ToolCallPart(
                            tool_name=tc,
                            args=tc,
                            tool_call_id=tc,
                        )
                    )
                if parts:
                    ai.append(ModelResponse(parts=parts))

                # CREARE REQUEST WITH TOOL RESULTS
                parts = []
                for tr in meta.tool_results:
                    parts.append(
                        ToolReturnPart(
                            content=tr,
                            tool_name=tr,
                            tool_call_id=tr,
                        )
                    )
                if parts:
                    ai.append(ModelRequest(parts=parts))

                if meta.tool_calls and not meta.tool_results:
                    pass
                elif content:
                    ai.append(ModelResponse(parts=[TextPart(content=f"{content}")]))

            else:
                pass

        return ai
