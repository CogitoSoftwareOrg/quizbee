from fastapi import FastAPI
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from src.apps.document_parser.adapters.out.concrete_parsers.pdf_parser import (
    FitzPDFParser,
)
from pocketbase import PocketBase

from src.lib.di import init_global_deps
from src.apps.llm_tools.app.contracts import LLMToolsApp
from src.apps.material_search.app.contracts import MaterialApp

from .domain.ports import (
    LLMTools,
    MaterialRepository,
    DocumentParser,
    MaterialIndexer,
    SearcherProvider,
)
from .adapters.out import (
    MeiliMaterialIndexer,
    PBMaterialRepository,
)

from .adapters.out.llm_tools_adapter import LLMToolsAdapter
from .app.usecases import MaterialAppImpl


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
    document_parser: DocumentParser,
    llm_tools_app: LLMToolsApp,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
    searcher_provider: SearcherProvider,
) -> MaterialApp:
    # Оборачиваем LLMToolsApp в адаптер для соблюдения гексагональной архитектуры
    llm_tools: LLMTools = LLMToolsAdapter(llm_tools_app)

    return MaterialAppImpl(
        document_parser=document_parser,
        material_repository=material_repository,
        llm_tools=llm_tools,
        indexer=indexer,
        searcher_provider=searcher_provider,
    )
