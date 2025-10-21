from enum import StrEnum

from pydantic import BaseModel


class LLMS(StrEnum):
    # OpenAI
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O_NANO = "gpt-4o-nano"
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"

    # Gemini
    # GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"

    # Grok
    # GROK_4_FAST = "grok:grok-4-fast"


class LLMCosts(BaseModel):
    input_nc: float
    input_cah: float
    output: float


class LLMSCosts:
    GPT_5_MINI = LLMCosts(
        input_nc=0.00000025,
        input_cah=0.000000025,
        output=0.000002,
    )
    GPT_5_MINI_PRIORITY = LLMCosts(
        input_nc=0.00000045,
        input_cah=0.000000045,
        output=0.0000036,
    )

    GROK_4_FAST = LLMCosts(
        input_nc=0.0000002,
        input_cah=0.00000005,
        output=0.0000005,
    )
