from typing import Annotated, Union
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
import httpx
from pocketbase import PocketBase
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.apps.document_parser.domain import DocumentParserApp
from src.apps.llm_tools.app.contracts import LLMToolsApp
from src.apps.material_search.adapters.out.document_parsing_adapter import (
    DocumentParserAdapter,
)
from src.apps.material_search.domain.ports import DocumentParser
from src.lib.settings import settings

from src.apps.llm_tools.adapters.out import (
    TiktokenTokenizer,
    OpenAIImageTokenizer,
    SimpleChunker,
)


from src.apps.user_auth.adapters.out import PBUserVerifier, PBUserRepository


from src.apps.material_search.adapters.out import (
    MeiliMaterialIndexer,
    PBMaterialRepository,
)

from src.apps.message_owner.adapters.out import PBMessageRepository

from src.apps.quiz_generator.adapters.out import (
    PBQuizRepository,
    PATCH_GENERATOR_LLM,
    QUIZ_FINALIZER_LLM,
    AIPatchGenerator,
    AIPatchGeneratorDeps,
    AIQuizFinalizer,
    QuizFinalizerDeps,
    QuizFinalizerOutput,
    AIPatchGeneratorOutput,
    MeiliQuizIndexer,
    AIQuizInstantGenerator,
    AIQuizInstantGeneratorDeps,
    AIQuizInstantGeneratorOutput,
    QUIZ_INSTANT_GENERATOR_LLM,
)

from src.apps.quiz_attempter.adapters.out import (
    PBAttemptRepository,
    AIExplainer,
    ExplainerDeps,
    EXPLAINER_LLM,
    ExplainerOutput,
    AttemptFinalizerOutput,
    AttemptFinalizerDeps,
    ATTEMPT_FINALIZER_LLM,
    AIAttemptFinalizer,
)

AgentPayload = Annotated[
    Union[
        AIPatchGeneratorOutput,
        QuizFinalizerOutput,
        ExplainerOutput,
        AttemptFinalizerOutput,
    ],
    Field(discriminator="mode"),
]


class AgentEnvelope(BaseModel):
    data: AgentPayload


def init_message_owner_deps(admin_pb: PocketBase):
    message_repository = PBMessageRepository(admin_pb)
    return message_repository


def init_global_deps() -> tuple[PocketBase, Langfuse, AsyncClient, httpx.AsyncClient]:
    admin_pb = PocketBase(settings.pb_url)
    lf = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
        environment=settings.env,
    )
    meili = AsyncClient(settings.meili_url, settings.meili_master_key)
    http = httpx.AsyncClient()
    return admin_pb, lf, meili, http


def init_llm_tools_deps() -> (
    tuple[TiktokenTokenizer, OpenAIImageTokenizer, SimpleChunker]
):
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()
    chunker = SimpleChunker(text_tokenizer)
    return text_tokenizer, image_tokenizer, chunker


def init_user_auth_deps(admin_pb: PocketBase):
    user_repository = PBUserRepository(admin_pb)
    user_verifier = PBUserVerifier(user_repository=user_repository)
    return user_verifier, user_repository


async def init_material_search_deps(
    lf: Langfuse,
    admin_pb: PocketBase,
    meili: AsyncClient,
    llm_tools: LLMToolsApp,
    document_parser_app: DocumentParserApp,
):
    from src.apps.material_search.adapters.out import (
        PBMaterialRepository,
        DocumentParserAdapter,
        MeiliMaterialIndexer,
        MaterialSearcherProvider,
        MeiliMaterialQuerySearcher,
        MeiliMaterialDistributionSearcher,
    )
    from src.apps.material_search.adapters.out.llm_tools_adapter import LLMToolsAdapter

    material_repository = PBMaterialRepository(admin_pb)
    document_parser_adapter = DocumentParserAdapter(document_parser_app)
    
    # Создаем адаптер для LLM Tools
    llm_tools_adapter = LLMToolsAdapter(llm_tools)
    
    # Инициализируем материал индексер
    material_indexer = await MeiliMaterialIndexer.ainit(
        lf=lf, llm_tools=llm_tools_adapter, meili=meili
    )
    
    # Создаем searcher'ы
    query_searcher = MeiliMaterialQuerySearcher(
        lf=lf, llm_tools=llm_tools_adapter, meili=meili
    )
    distribution_searcher = MeiliMaterialDistributionSearcher(
        lf=lf, llm_tools=llm_tools_adapter, meili=meili
    )
    
    # Создаем provider
    searcher_provider = MaterialSearcherProvider(
        query_searcher=query_searcher,
        distribution_searcher=distribution_searcher,
    )
    
    return (
        material_repository,
        document_parser_adapter,
        material_indexer,
        searcher_provider,
    )


# Factory functions for dependency initialization
def init_quiz_attempter_deps(
    lf: Langfuse, admin_pb: PocketBase, http: httpx.AsyncClient, llm_tools: LLMToolsApp
) -> tuple[PBAttemptRepository, AIExplainer, AIAttemptFinalizer]:
    attempt_repository = PBAttemptRepository(admin_pb, http=http)
    explainer = AIExplainer(
        lf=lf,
        output_type=AgentEnvelope,
    )
    finalizer = AIAttemptFinalizer(
        lf=lf,
        attempt_repository=attempt_repository,
        output_type=AgentEnvelope,
    )
    return attempt_repository, explainer, finalizer


async def init_quiz_generator_deps(
    meili: AsyncClient,
    lf: Langfuse,
    admin_pb: PocketBase,
    http: httpx.AsyncClient,
    llm_tools: LLMToolsApp,
) -> tuple[PBQuizRepository, AIQuizInstantGenerator, AIQuizFinalizer, MeiliQuizIndexer]:
    quiz_repository = PBQuizRepository(admin_pb, http=http)
    instant_generator = AIQuizInstantGenerator(
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
    return quiz_repository, instant_generator, finalizer, quiz_indexer
