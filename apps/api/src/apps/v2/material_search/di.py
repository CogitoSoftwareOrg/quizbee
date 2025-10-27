from typing import Annotated
from fastapi import Depends, Request, FastAPI

from src.apps.v2.llm_tools.app.usecases import LLMToolsApp
from src.lib.clients.meilisearch import MeilisearchClient
from src.lib.clients.pb import AdminPB

from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    MaterialRepository,
    PdfParser,
    Indexer,
)
from .adapters.out.pb_repository import PBMaterialRepository
from .adapters.out.fitz_pdf_parser import FitzPDFParser
from .adapters.out.meili_indexer import MeiliIndexer

from .app.usecases import MaterialSearchApp


# PDF PARSER
def set_pdf_parser(app: FastAPI):
    app.state.pdf_parser = FitzPDFParser()


def get_pdf_parser(request: Request) -> PdfParser:
    return request.app.state.pdf_parser


PdfParserDep = Annotated[PdfParser, Depends(get_pdf_parser)]


# REPOSITORY
def set_material_repository(app: FastAPI, admin_pb: AdminPB):
    app.state.material_repository = PBMaterialRepository(admin_pb)


def get_material_repository(request: Request) -> MaterialRepository:
    return request.app.state.material_repository


MaterialRepositoryDep = Annotated[MaterialRepository, Depends(get_material_repository)]


# INDEXER
async def aset_indexer(app: FastAPI, llm_tools: LLMToolsApp, meili: MeilisearchClient):
    app.state.indexer = await MeiliIndexer.ainit(llm_tools, meili)


def get_indexer(request: Request) -> Indexer:
    return request.app.state.indexer


IndexerDep = Annotated[Indexer, Depends(get_indexer)]


# APP
def set_material_search_app(
    app: FastAPI,
    material_repository: MaterialRepository,
    pdf_parser: PdfParser,
    llm_tools: LLMToolsApp,
    indexer: Indexer,
):
    app.state.material_search_app = MaterialSearchApp(
        material_repository, pdf_parser, llm_tools, indexer
    )


def get_material_search_app(request: Request) -> MaterialSearchApp:
    return request.app.state.material_search_app


MaterialSearchAppDep = Annotated[MaterialSearchApp, Depends(get_material_search_app)]
