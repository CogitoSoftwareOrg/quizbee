from .domain.ports import TextTokenizer, ImageTokenizer, Chunker
from .app.usecases import LLMToolsAppImpl
from .adapters.out import TiktokenTokenizer, OpenAIImageTokenizer, SimpleChunker


def init_llm_tools_deps() -> tuple[TextTokenizer, ImageTokenizer, Chunker]:
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()
    chunker = SimpleChunker(text_tokenizer)
    return text_tokenizer, image_tokenizer, chunker


def init_llm_tools_app(
    text_tokenizer: TextTokenizer | None = None,
    image_tokenizer: ImageTokenizer | None = None,
    chunker: Chunker | None = None,
) -> LLMToolsAppImpl:
    """Factory for LLMToolsApp"""
    if text_tokenizer is None or image_tokenizer is None or chunker is None:
        default_text_tokenizer, default_image_tokenizer, default_chunker = (
            init_llm_tools_deps()
        )
        text_tokenizer = text_tokenizer or default_text_tokenizer
        image_tokenizer = image_tokenizer or default_image_tokenizer
        chunker = chunker or default_chunker

    return LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )
