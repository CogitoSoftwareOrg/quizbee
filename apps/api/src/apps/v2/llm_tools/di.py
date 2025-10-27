from typing import Annotated
from fastapi import Depends, Request, FastAPI


from .adapters.out.tiktoken_tokenizer import TiktokenTokenizer
from .adapters.out.openai_image_tokenizer import OpenAIImageTokenizer
from .adapters.out.simple_chunker import SimpleChunker


from .app.contracts import LLMToolsApp
from .app.usecases import LLMToolsAppImpl


def set_llm_tools(app: FastAPI):
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()

    chunker = SimpleChunker(text_tokenizer)

    app.state.llm_tools = LLMToolsAppImpl(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )


def get_llm_tools(request: Request) -> LLMToolsApp:
    return request.app.state.llm_tools


LLMToolsAppDep = Annotated[LLMToolsApp, Depends(get_llm_tools)]
