from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from pocketbase import PocketBase
import httpx


from src.lib.di import AgentEnvelope

from src.apps.material_search.app.contracts import MaterialSearchApp
from src.apps.llm_tools.app.contracts import LLMToolsApp

from .adapters.out import (
    PBQuizRepository,
    AIPatchGenerator,
    AIQuizFinalizer,
    MeiliQuizIndexer,
)
from .domain.ports import (
    QuizFinalizer,
    QuizRepository,
    QuizIndexer,
    PatchGenerator,
)
from .app.usecases import QuizGeneratorAppImpl


async def init_quiz_generator_deps(
    meili: AsyncClient,
    lf: Langfuse,
    admin_pb: PocketBase,
    http: httpx.AsyncClient,
    llm_tools: LLMToolsApp,
) -> tuple[QuizRepository, PatchGenerator, QuizFinalizer, QuizIndexer]:
    quiz_repository = PBQuizRepository(admin_pb, http=http)
    patch_generator = AIPatchGenerator(
        lf=lf,
        quiz_repository=quiz_repository,
        output_type=AgentEnvelope,
    )
    finalizer = AIQuizFinalizer(
        lf=lf,
        quiz_repository=quiz_repository,
        output_type=AgentEnvelope,
    )
    quiz_indexer = await MeiliQuizIndexer.ainit(
        lf=lf,
        llm_tools=llm_tools,
        meili=meili,
        quiz_repository=quiz_repository,
    )
    return quiz_repository, patch_generator, finalizer, quiz_indexer


def init_quiz_generator_app(
    llm_tools: LLMToolsApp,
    material_search: MaterialSearchApp,
    quiz_repository: QuizRepository,
    quiz_indexer: QuizIndexer,
    patch_generator: PatchGenerator,
    finalizer: QuizFinalizer,
) -> QuizGeneratorAppImpl:
    """Factory for QuizGeneratorApp - all dependencies explicit"""
    return QuizGeneratorAppImpl(
        quiz_repository=quiz_repository,
        quiz_indexer=quiz_indexer,
        llm_tools=llm_tools,
        material_search=material_search,
        patch_generator=patch_generator,
        finalizer=finalizer,
    )
