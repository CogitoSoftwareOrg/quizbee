from typing import Annotated, Union
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
import httpx
from pocketbase import PocketBase
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.apps.v2.llm_tools.app.contracts import LLMToolsApp
from src.lib.settings import settings

from src.apps.v2.llm_tools.adapters.out import (
    TiktokenTokenizer,
    OpenAIImageTokenizer,
    SimpleChunker,
)


from src.apps.v2.user_auth.adapters.out import PBUserVerifier, PBUserRepository


from src.apps.v2.material_search.adapters.out import (
    FitzPDFParser,
    MeiliMaterialIndexer,
    PBMaterialRepository,
)

from src.apps.v2.message_owner.adapters.out import PBMessageRepository

from src.apps.v2.quiz_generator.adapters.out import (
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
)

from src.apps.v2.quiz_attempter.adapters.out import (
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
    admin_pb: PocketBase, meili: AsyncClient, llm_tools: LLMToolsApp
) -> tuple[PBMaterialRepository, FitzPDFParser, MeiliMaterialIndexer]:
    material_repository = PBMaterialRepository(admin_pb)
    pdf_parser = FitzPDFParser()
    material_indexer = await MeiliMaterialIndexer.ainit(
        llm_tools=llm_tools, meili=meili
    )
    return material_repository, pdf_parser, material_indexer


# Factory functions for dependency initialization
def init_quiz_attempter_deps(
    lf: Langfuse, admin_pb: PocketBase, http: httpx.AsyncClient, llm_tools: LLMToolsApp
) -> tuple[PBAttemptRepository, AIExplainer, AIAttemptFinalizer]:
    attempt_repository = PBAttemptRepository(admin_pb, http=http)
    explainer_ai = Agent(
        # instrument=True,
        model=EXPLAINER_LLM,
        deps_type=ExplainerDeps,
        history_processors=[],
        output_type=AgentEnvelope,
    )
    explainer = AIExplainer(
        lf=lf,
        ai=explainer_ai,
    )

    finalizer_ai = Agent(
        model=ATTEMPT_FINALIZER_LLM,
        deps_type=AttemptFinalizerDeps,
        history_processors=[],
        output_type=AgentEnvelope,
    )
    finalizer = AIAttemptFinalizer(
        lf=lf,
        attempt_repository=attempt_repository,
        ai=finalizer_ai,
    )
    return attempt_repository, explainer, finalizer


async def init_quiz_generator_deps(
    meili: AsyncClient,
    lf: Langfuse,
    admin_pb: PocketBase,
    http: httpx.AsyncClient,
    llm_tools: LLMToolsApp,
) -> tuple[PBQuizRepository, AIPatchGenerator, AIQuizFinalizer, MeiliQuizIndexer]:
    quiz_repository = PBQuizRepository(admin_pb, http=http)
    patch_generator_ai = Agent(
        model=PATCH_GENERATOR_LLM,
        deps_type=AIPatchGeneratorDeps,
        history_processors=[],
        output_type=AgentEnvelope,
    )
    patch_generator = AIPatchGenerator(
        lf=lf,
        quiz_repository=quiz_repository,
        ai=patch_generator_ai,
    )
    finalizer_ai = Agent(
        model=QUIZ_FINALIZER_LLM,
        deps_type=QuizFinalizerDeps,
        history_processors=[],
        output_type=AgentEnvelope,
    )
    finalizer = AIQuizFinalizer(
        lf=lf,
        quiz_repository=quiz_repository,
        ai=finalizer_ai,
    )
    quiz_indexer = await MeiliQuizIndexer.ainit(
        llm_tools=llm_tools,
        meili=meili,
        quiz_repository=quiz_repository,
    )
    return quiz_repository, patch_generator, finalizer, quiz_indexer
