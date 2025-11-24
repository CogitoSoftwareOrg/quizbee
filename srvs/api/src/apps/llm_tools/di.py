from .domain.out import TextTokenizer, ImageTokenizer, Chunker, Reranker
from .app.usecases import LLMToolsAppImpl
from .adapters.out import (
    TiktokenTokenizer,
    OpenAIImageTokenizer,
    SimpleChunker,
    ChonkieRecursiveChunker,
    VoyageEmbedder,
    VoyageReranker,
)
from .domain.out import Vectorizer


def init_llm_tools_deps() -> tuple[TextTokenizer, ImageTokenizer, Chunker, Vectorizer, Reranker]:
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()
    chunker = ChonkieRecursiveChunker(text_tokenizer)
    vectorizer = VoyageEmbedder()
    reranker = VoyageReranker()
    return text_tokenizer, image_tokenizer, chunker, vectorizer, reranker


def init_llm_tools_app(
    text_tokenizer: TextTokenizer,
    image_tokenizer: ImageTokenizer,
    chunker: Chunker,
    vectorizer: Vectorizer,
    reranker: Reranker,
) -> LLMToolsAppImpl:
    """Factory for LLMToolsApp - all dependencies explicit"""
    return LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
        vectorizer=vectorizer,
        reranker=reranker,
    )
