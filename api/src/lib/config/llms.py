from enum import StrEnum


class LLMS(StrEnum):
    GPT_4O_MINI = "openai:gpt-4o-mini"
    GPT_4O_NANO = "openai:gpt-4o-nano"
    TEXT_EMBEDDING_3_SMALL = "openai:text-embedding-3-small"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
