from typing import Annotated
from fastapi import Depends, Request, FastAPI

from src.apps.v2.llm_tools.app.usecases import LLMToolsApp
from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    MaterialRepository,
    PdfParser,
    Indexer,
)

from .app.contracts import MaterialSearchApp
from .app.usecases import MaterialSearchAppImpl


# APP
def set_material_search_app(
    app: FastAPI,
    llm_tools: LLMToolsApp,
    pdf_parser: PdfParser,
    indexer: Indexer,
    material_repository: MaterialRepository,
):
    app.state.material_search_app = MaterialSearchAppImpl(
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        llm_tools=llm_tools,
        indexer=indexer,
    )


def get_material_search_app(request: Request) -> MaterialSearchApp:
    return request.app.state.material_search_app


MaterialSearchAppDep = Annotated[MaterialSearchApp, Depends(get_material_search_app)]
