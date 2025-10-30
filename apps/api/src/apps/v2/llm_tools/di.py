from typing import Annotated
from fastapi import Depends, Request, FastAPI


from .domain.ports import TextTokenizer, ImageTokenizer, Chunker


from .app.contracts import LLMToolsApp
from .app.usecases import LLMToolsAppImpl


def set_llm_tools(
    app: FastAPI,
    text_tokenizer: TextTokenizer,
    image_tokenizer: ImageTokenizer,
    chunker: Chunker,
):
    app.state.llm_tools = LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )


def get_llm_tools(request: Request) -> LLMToolsApp:
    return request.app.state.llm_tools


LLMToolsAppDep = Annotated[LLMToolsApp, Depends(get_llm_tools)]
