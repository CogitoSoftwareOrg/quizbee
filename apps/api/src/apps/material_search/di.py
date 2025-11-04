from src.apps.llm_tools.app.contracts import LLMToolsApp

from .domain.ports import (
    LLMTools,
    MaterialRepository,
    DocumentParsing,
    MaterialIndexer,
)

from .adapters.out.llm_tools_adapter import LLMToolsAdapter
from .adapters.out.document_parsing_adapter import DocumentParsingAdapter
from .app.usecases import MaterialSearchAppImpl


# APP
def init_material_search_app(
    llm_tools_app: LLMToolsApp,
    document_parsing: DocumentParsing,
    indexer: MaterialIndexer,
    material_repository: MaterialRepository,
):
    # Оборачиваем LLMToolsApp в адаптер для соблюдения гексагональной архитектуры
    llm_tools: LLMTools = LLMToolsAdapter(llm_tools_app)
    
    return MaterialSearchAppImpl(
        material_repository=material_repository,
        document_parsing=document_parsing,
        llm_tools=llm_tools,
        indexer=indexer,
    )
