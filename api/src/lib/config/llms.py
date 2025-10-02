from enum import StrEnum


class LLMS(StrEnum):
    # OpenAI
    GPT_5 = "openai:gpt-5"
    GPT_5_MINI = "openai:gpt-5-mini"
    GPT_5_NANO = "openai:gpt-5-nano"
    GPT_4O_MINI = "openai:gpt-4o-mini"
    GPT_4O_NANO = "openai:gpt-4o-nano"
    TEXT_EMBEDDING_3_SMALL = "openai:text-embedding-3-small"

    # Gemini
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"

    # Grok
    GROK_4_FAST = "grok:grok-4-fast"
