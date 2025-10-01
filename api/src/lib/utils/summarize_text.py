from pydantic_ai.direct import model_request
from pydantic_ai.messages import (
    ModelRequest,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models import ModelRequestParameters

from lib.config import LLMS


async def summarize_text(
    text: str,
    prompt_cache_key="",
    max_tokens=8000,
) -> str:
    extra_body = {}
    if prompt_cache_key:
        extra_body["prompt_cache_key"] = prompt_cache_key
    part = (
        await model_request(
            LLMS.GPT_5_MINI,
            messages=[
                ModelRequest(
                    parts=[
                        SystemPromptPart(
                            content="Summarize the following materials context:"
                        ),
                        UserPromptPart(content=text),
                    ]
                )
            ],
            model_settings={
                "max_tokens": max_tokens,
                "extra_body": extra_body,
                # "temperature": 0.2,
                # "top_p": 1.0,
            },
        )
    ).parts[0]
    return part.content if isinstance(part, TextPart) else ""
