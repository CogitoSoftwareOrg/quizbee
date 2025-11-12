import tiktoken

from src.lib.config import LLMS

from ...domain.out import TextTokenizer


class TiktokenTokenizer(TextTokenizer):
    def __init__(self):
        self.encoders = {
            llm: tiktoken.encoding_for_model(
                LLMS.TEXT_EMBEDDING_3_SMALL.value.split(":")[-1]
                if "voyage" in llm.value
                else llm.value.split(":")[-1]
            )
            for llm in LLMS
            if "openai" in llm.value or llm.value == LLMS.TEXT_EMBEDDING_3_SMALL.value or "voyage" in llm.value
        }

    def encode(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> list[int]:
        return self.encoders[llm].encode(text)

    def decode(self, tokens: list[int], llm: LLMS = LLMS.GPT_5_MINI) -> str:
        return self.encoders[llm].decode(tokens)

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        return len(self.encode(text, llm))
