from fastapi import FastAPI

from src.apps..llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    MaterialRepository,
    PdfParser,
    MaterialIndexer,
)

from .app.usecases import MaterialSearchAppImpl


# APP
def init_material_search_app(
    llm_tools: LLMToolsApp,
    pdf_parser: PdfParser,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
):
    return MaterialSearchAppImpl(
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        llm_tools=llm_tools,
        indexer=indexer,
    )
