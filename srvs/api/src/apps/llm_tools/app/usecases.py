import logging

from src.lib.config import LLMS

from ..domain.out import TextTokenizer, ImageTokenizer, Chunker

from ..domain._in import LLMToolsApp

logger = logging.getLogger(__name__)


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

    @property
    def chunk_size(self) -> int:
        logger.debug("LLMToolsAppImpl.chunk_size")
        return self.chunker.chunk_size

    def encode(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> list[int]:
        logger.debug("LLMToolsAppImpl.encode")
        return self.text_tokenizer.encode(text, llm)

    def decode(self, tokens: list[int], llm: LLMS = LLMS.GPT_5_MINI) -> str:
        logger.debug("LLMToolsAppImpl.decode")
        return self.text_tokenizer.decode(tokens, llm)

    def count_text(self, text: str, llm: LLMS = LLMS.GPT_5_MINI) -> int:
        logger.debug("LLMToolsAppImpl.count_text")
        return self.text_tokenizer.count_text(text, llm)

    def count_image(self, width: int, height: int) -> int:
        logger.debug("LLMToolsAppImpl.count_image")
        return self.image_tokenizer.count_image(width, height)

    def chunk(self, text: str) -> list[str]:
        logger.debug("LLMToolsAppImpl.chunk")
        return self.chunker.chunk(text)
