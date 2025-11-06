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


async def init_material_search_app(
    llm_tools: LLMToolsApp,
    pdf_parser: PdfParser | None = None,
    indexer: MaterialIndexer | None = None,
    material_repository: MaterialRepository | None = None,
):
    if (
        llm_tools is None
        or pdf_parser is None
        or indexer is None
        or material_repository is None
    ):
        admin_pb, lf, meili, _ = init_global_deps()
        default_material_repository, default_pdf_parser, default_indexer = (
            await init_material_search_deps(
                lf=lf,
                admin_pb=admin_pb,
                meili=meili,
                llm_tools=llm_tools,
            )
        )
        material_repository = material_repository or default_material_repository
        pdf_parser = pdf_parser or default_pdf_parser
        indexer = indexer or default_indexer

    return MaterialSearchAppImpl(
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        llm_tools=llm_tools,
        indexer=indexer,
    )
