from fastapi import FastAPI
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient

from pocketbase import PocketBase

from src.apps.document_parser.domain._in import DocumentParserApp
from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.material_owner.domain._in import MaterialApp

from .domain.out import (
    LLMTools,
    MaterialRepository,
    MaterialIndexer,
    SearcherProvider,
    DocumentParser,
)
from .adapters.out import (
    MeiliMaterialIndexer,
    PBMaterialRepository,
    MaterialSearcherProvider,
    MeiliMaterialQuerySearcher,
    MeiliMaterialDistributionSearcher,
    DocumentParserAdapter,
    LLMToolsAdapter,
)
from .app.usecases import MaterialAppImpl


async def init_material_deps(
    lf: Langfuse,
    admin_pb: PocketBase,
    meili: AsyncClient,
    llm_tools: LLMToolsApp,
    document_parser_app: DocumentParserApp,
) -> tuple[
    MaterialRepository, DocumentParser, MaterialIndexer, SearcherProvider, LLMTools
]:
    # INTERNAL HEX DOMAIN ADAPTERS
    material_repository = PBMaterialRepository(admin_pb)
    material_indexer = await MeiliMaterialIndexer.ainit(
        lf=lf, llm_tools=llm_tools, meili=meili
    )
    searcher_provider = MaterialSearcherProvider(
        query_searcher=MeiliMaterialQuerySearcher(
            lf=lf, llm_tools=llm_tools, meili=meili
        ),
        distribution_searcher=MeiliMaterialDistributionSearcher(
            lf=lf, llm_tools=llm_tools, meili=meili
        ),
    )

    # EXTERNAL HEX ADAPTERS
    document_parser_adapter = DocumentParserAdapter(
        document_parser_app=document_parser_app
    )
    llm_tools_adapter = LLMToolsAdapter(llm_tools_app=llm_tools)
    return (
        material_repository,
        document_parser_adapter,
        material_indexer,
        searcher_provider,
        llm_tools_adapter,
    )


def init_material_app(
    document_parser_adapter: DocumentParser,
    llm_tools_adapter: LLMTools,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
    searcher_provider: SearcherProvider,
) -> MaterialApp:
    return MaterialAppImpl(
        document_parser=document_parser_adapter,
        material_repository=material_repository,
        llm_tools=llm_tools_adapter,
        indexer=indexer,
        searcher_provider=searcher_provider,
    )
