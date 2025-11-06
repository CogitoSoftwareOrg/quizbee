from fastapi import FastAPI
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from pocketbase import PocketBase
import httpx


from src.lib.di import AgentEnvelope, init_global_deps

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


async def init_quiz_generator_app(
    llm_tools: LLMToolsApp,
    material_search: MaterialSearchApp,
    quiz_repository: QuizRepository | None = None,
    quiz_indexer: QuizIndexer | None = None,
    patch_generator: PatchGenerator | None = None,
    finalizer: QuizFinalizer | None = None,
):
    if (
        quiz_repository is None
        or quiz_indexer is None
        or patch_generator is None
        or finalizer is None
    ):
        admin_pb, lf, meili, http = init_global_deps()
        (
            default_quiz_repository,
            default_patch_generator,
            default_finalizer,
            default_quiz_indexer,
        ) = await init_quiz_generator_deps(
            meili=meili,
            lf=lf,
            admin_pb=admin_pb,
            http=http,
            llm_tools=llm_tools,
        )
        quiz_repository = quiz_repository or default_quiz_repository
        quiz_indexer = quiz_indexer or default_quiz_indexer
        patch_generator = patch_generator or default_patch_generator
        finalizer = finalizer or default_finalizer

    return QuizGeneratorAppImpl(
        quiz_repository=quiz_repository,
        quiz_indexer=quiz_indexer,
        llm_tools=llm_tools,
        material_search=material_search,
        patch_generator=patch_generator,
        finalizer=finalizer,
    )
