from fastapi import FastAPI

from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    MaterialRepository,
    PdfParser,
    MaterialIndexer,
)

from .app.usecases import MaterialSearchAppImpl


# APP
def set_material_search_app(
    app: FastAPI,
    llm_tools: LLMToolsApp,
    pdf_parser: PdfParser,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
):
    app.state.material_search_app = MaterialSearchAppImpl(
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        llm_tools=llm_tools,
        indexer=indexer,
    )
