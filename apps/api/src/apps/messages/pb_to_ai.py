from pocketbase.models.dtos import Record
import logging
from pydantic_ai.messages import ModelMessage
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    SystemPromptPart,
)

PUBLIC_TOOLS = {"always_call"}


def pb_to_ai(pb_messages: list[Record]) -> list[ModelMessage]:
    ai: list[ModelMessage] = []

    for pb_message in pb_messages:
        # name = pb_message.get("sentBy")
        role = pb_message.get("role")
        meta = pb_message.get("metadata", {})
        content = (pb_message.get("content", "")).strip()

        logging.info(f"PB Message: {role} {content} {meta}")

        if role == "user":
            if content:
                ai.append(ModelRequest(parts=[UserPromptPart(content=f"{content}")]))
        elif role == "ai":
            parts = []
            for tc in meta.get("tool_calls", []):
                parts.append(
                    ToolCallPart(
                        tool_name=tc.get("tool_name"),
                        args=tc.get("args") or {},
                        tool_call_id=tc.get("tool_call_id"),
                    )
                )
            if parts:
                ai.append(ModelResponse(parts=parts))

            # CREARE REQUEST WITH TOOL RESULTS
            parts = []
            for tr in meta.get("tool_results", []):
                parts.append(
                    ToolReturnPart(
                        content=tr.get("result"),
                        tool_name=tr.get("tool_name"),
                        tool_call_id=tr.get("tool_call_id"),
                    )
                )
            if parts:
                ai.append(ModelRequest(parts=parts))

            if meta.get("tool_calls") and not meta.get("tool_results"):
                pass
            elif content:
                ai.append(ModelResponse(parts=[TextPart(content=f"{content}")]))

        else:
            pass

    return ai
