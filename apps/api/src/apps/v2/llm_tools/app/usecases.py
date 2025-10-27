from src.lib.config import LLMS

from ..domain.ports import TextTokenizer, ImageTokenizer, Chunker

from .contracts import LLMToolsApp


class LLMToolsAppImpl(LLMToolsApp):
    def __init__(
        self,
        text_tokenizer: TextTokenizer,
        image_tokenizer: ImageTokenizer,
        chunker: Chunker,
    ):
        self.text_tokenizer = text_tokenizer
        self.image_tokenizer = image_tokenizer
        self.chunker = chunker

    def encode(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> list[int]:
        return self.text_tokenizer.encode(text, llm)

    def decode(self, tokens: list[int], llm: LLMS = LLMS.GPT_5_MINI) -> str:
        return self.text_tokenizer.decode(tokens, llm)

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        return self.text_tokenizer.count_text(text, llm)

    def count_image(self, width: int, height: int) -> int:
        return self.image_tokenizer.count_image(width, height)

    def chunk(self, text: str) -> list[str]:
        return self.chunker.chunk(text)
