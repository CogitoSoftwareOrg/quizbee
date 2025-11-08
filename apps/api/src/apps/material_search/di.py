from src.apps.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    LLMTools,
    MaterialRepository,
    DocumentParser,
    MaterialIndexer,
    SearcherProvider,
)

from .adapters.out.llm_tools_adapter import LLMToolsAdapter
from .app.usecases import MaterialAppImpl


# APP
def init_material_search_app(
    document_parser: DocumentParser,
    llm_tools_app: LLMToolsApp,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
    searcher_provider: SearcherProvider,
):
    # Оборачиваем LLMToolsApp в адаптер для соблюдения гексагональной архитектуры
    llm_tools: LLMTools = LLMToolsAdapter(llm_tools_app)

    return MaterialAppImpl(
        document_parser=document_parser,
        material_repository=material_repository,
        llm_tools=llm_tools_app,
        indexer=indexer,
        searcher_provider=searcher_provider,
    )
