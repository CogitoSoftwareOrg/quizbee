from typing import Annotated, Any
from fastapi import Depends, Request, FastAPI


from .domain.ports import TextTokenizer, ImageTokenizer, Chunker


from .app.contracts import LLMToolsApp
from .app.usecases import LLMToolsAppImpl


def init_llm_tools(
    text_tokenizer: TextTokenizer,
    image_tokenizer: ImageTokenizer,
    chunker: Chunker,
):
    return LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )
