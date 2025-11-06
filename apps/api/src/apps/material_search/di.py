from fastapi import FastAPI
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from src.apps.material_search.adapters.out.fitz_pdf_parser import FitzPDFParser
from pocketbase import PocketBase

from src.lib.di import init_global_deps
from src.apps.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    MaterialRepository,
    PdfParser,
    MaterialIndexer,
)
from .adapters.out import (
    MeiliMaterialIndexer,
    PBMaterialRepository,
)

from .app.usecases import MaterialSearchAppImpl


async def init_material_search_deps(
    lf: Langfuse, admin_pb: PocketBase, meili: AsyncClient, llm_tools: LLMToolsApp
) -> tuple[MaterialRepository, FitzPDFParser, MeiliMaterialIndexer]:
    material_repository = PBMaterialRepository(admin_pb)
    pdf_parser = FitzPDFParser()
    material_indexer = await MeiliMaterialIndexer.ainit(
        lf=lf, llm_tools=llm_tools, meili=meili
    )
    return material_repository, pdf_parser, material_indexer


def init_material_search_app(
    llm_tools: LLMToolsApp,
    pdf_parser: PdfParser,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
) -> MaterialSearchAppImpl:
    """Factory for MaterialSearchApp - all dependencies explicit"""
    return MaterialSearchAppImpl(
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        llm_tools=llm_tools,
        indexer=indexer,
    )
