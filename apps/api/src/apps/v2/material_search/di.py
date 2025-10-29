from fastapi import FastAPI

from src.apps.v2.user_auth.app.contracts import AuthUserApp
from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    MaterialRepository,
    PdfParser,
    Indexer,
)

from .app.usecases import MaterialSearchAppImpl


# APP
def set_material_search_app(
    app: FastAPI,
    llm_tools: LLMToolsApp,
    pdf_parser: PdfParser,
    indexer: Indexer,
    material_repository: MaterialRepository,
    user_auth: AuthUserApp,
):
    app.state.material_search_app = MaterialSearchAppImpl(
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        llm_tools=llm_tools,
        indexer=indexer,
        user_auth=user_auth,
    )
