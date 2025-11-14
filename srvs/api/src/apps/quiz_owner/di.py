from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from openai import AsyncOpenAI
from pocketbase import PocketBase
import httpx
from pydantic_ai.providers.openai import OpenAIProvider
import redis.asyncio as redis

from src.apps.material_owner.domain._in import MaterialApp
from src.apps.llm_tools.domain._in import LLMToolsApp

from .adapters.out import (
    PBQuizRepository,
    AIGrokGenerator,
    AIQuizFinalizer,
    MeiliQuizIndexer,
)
from .adapters.out.quiz_preprocesser import QuizPreprocessor
from .domain.out import (
    QuizFinalizer,
    QuizRepository,
    QuizIndexer,
    PatchGenerator,
)
from .app.usecases import QuizAppImpl


async def init_quiz_deps(
    meili: AsyncClient,
    lf: Langfuse,
    admin_pb: PocketBase,
    http: httpx.AsyncClient,
    llm_tools: LLMToolsApp,
    llm_provider: OpenAIProvider,
) -> tuple[QuizRepository, PatchGenerator, QuizFinalizer, QuizIndexer, QuizPreprocessor]:
    quiz_repository = PBQuizRepository(admin_pb, http=http)
    patch_generator = AIGrokGenerator(lf=lf, provider=llm_provider)
    quiz_preprocessor = QuizPreprocessor(lf=lf, provider=llm_provider)
    finalizer = AIQuizFinalizer(
        lf=lf,
        quiz_repository=quiz_repository,
    )
    quiz_indexer = await MeiliQuizIndexer.ainit(
        lf=lf,
        llm_tools=llm_tools,
        meili=meili,
        quiz_repository=quiz_repository,
    )
    return quiz_repository, patch_generator, finalizer, quiz_indexer, quiz_preprocessor


def init_quiz_app(
    llm_tools: LLMToolsApp,
    material: MaterialApp,
    quiz_repository: QuizRepository,
    quiz_indexer: QuizIndexer,
    patch_generator: PatchGenerator,
    finalizer: QuizFinalizer,
    quiz_preprocessor: QuizPreprocessor,
    redis_client: redis.Redis,
) -> QuizAppImpl:
    return QuizAppImpl(
        quiz_repository=quiz_repository,
        quiz_indexer=quiz_indexer,
        llm_tools=llm_tools,
        material=material,
        patch_generator=patch_generator,
        finalizer=finalizer,
        quiz_preprocessor=quiz_preprocessor,
        redis_client=redis_client,
    )
