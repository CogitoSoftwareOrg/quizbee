from .domain.out import TextTokenizer, ImageTokenizer, Chunker
from .app.usecases import LLMToolsAppImpl
from .adapters.out import (
    TiktokenTokenizer,
    OpenAIImageTokenizer,
    SimpleChunker,
    VoyageEmbedder,
)
from .domain.out import Vectorizer


def init_llm_tools_deps() -> tuple[TextTokenizer, ImageTokenizer, Chunker, Vectorizer]:
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()
    chunker = SimpleChunker(text_tokenizer)
    vectorizer = VoyageEmbedder()
    return text_tokenizer, image_tokenizer, chunker, vectorizer


def init_llm_tools_app(
    text_tokenizer: TextTokenizer,
    image_tokenizer: ImageTokenizer,
    chunker: Chunker,
    vectorizer: Vectorizer,
) -> LLMToolsAppImpl:
    """Factory for LLMToolsApp - all dependencies explicit"""
    return LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
        vectorizer=vectorizer,
    )
