from pocketbase.models.dtos import Record
from pydantic_ai.messages import ModelRequestPart, SystemPromptPart, UserPromptPart

from apps.materials import load_file_text, materials_to_ai_bytes
from lib.clients import HTTPAsyncClient

from .models import DynamicConfig


async def build_pre_prompt(
    http: HTTPAsyncClient, quiz: Record, materials_context: str | None = None
) -> list[ModelRequestPart]:
    quiz_id = quiz.get("id", "")
    materials = quiz.get("expand", {}).get("materials", [])

    dynamic_config = DynamicConfig(**quiz.get("dynamicConfig", {}))
    q = quiz.get("query", "")
    summary = quiz.get("summary", "")

    if materials_context is not None:
        text_materials = materials_context
    else:
        text_materials = await load_file_text(
            http, "quizes", quiz_id, quiz.get("materialsContext", "")
        )
    ai_bytes = await materials_to_ai_bytes(http, materials)

    user_contents = []
    if q:
        user_contents.append(f"User query:\n{q}")
    if text_materials:
        user_contents.append(f"Quiz materials:\n{text_materials}")
    if ai_bytes:
        user_contents.extend(ai_bytes)
    # if summary:
    #     user_contents.append(f"Materials summary:\n{summary}")

    parts = []
    parts.append(UserPromptPart(content=user_contents))
    return parts
