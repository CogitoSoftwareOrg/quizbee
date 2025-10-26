import tiktoken

from src.lib.config import LLMS

from ...domain.ports import Tokenizer


class TiktokenTokenizer(Tokenizer):
    def __init__(self):
        self.encoders = {
            # llm: tiktoken.encoding_for_model(llm.split(":")[-1])
            llm: tiktoken.encoding_for_model(llm)
            for llm in LLMS
            # if "openai" in llm and llm != LLMS.GPT_5
        }

    def encode(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> list[int]:
        return self.encoders[llm].encode(text)

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        return len(self.encode(text, llm))
