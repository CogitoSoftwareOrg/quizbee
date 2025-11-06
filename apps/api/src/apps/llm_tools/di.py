from .domain.ports import TextTokenizer, ImageTokenizer, Chunker
from .app.usecases import LLMToolsAppImpl
from .adapters.out import TiktokenTokenizer, OpenAIImageTokenizer, SimpleChunker


def init_llm_tools_deps() -> tuple[TextTokenizer, ImageTokenizer, Chunker]:
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()
    chunker = SimpleChunker(text_tokenizer)
    return text_tokenizer, image_tokenizer, chunker


def init_llm_tools_app(
    text_tokenizer: TextTokenizer,
    image_tokenizer: ImageTokenizer,
    chunker: Chunker,
) -> LLMToolsAppImpl:
    """Factory for LLMToolsApp - all dependencies explicit"""
    return LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )
