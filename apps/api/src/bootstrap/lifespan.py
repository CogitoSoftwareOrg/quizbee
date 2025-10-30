from typing import Annotated, Union
from fastapi import FastAPI
import logging
import contextlib
from contextlib import asynccontextmanager
from meilisearch_python_sdk import AsyncClient
import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.lib.settings import settings

from src.apps.v2.llm_tools.di import set_llm_tools
from src.apps.v2.llm_tools.adapters.out import (
    TiktokenTokenizer,
    OpenAIImageTokenizer,
    SimpleChunker,
)


from src.apps.v2.quiz_generator.di import set_quiz_generator_app

from src.lib.clients import set_admin_pb, set_langfuse

from src.apps.v2.user_auth.di import set_auth_user_app
from src.apps.v2.user_auth.adapters.out import PBUserVerifier, PBUserRepository

from src.apps.v2.material_search.di import (
    set_material_search_app,
)
from src.apps.v2.material_search.adapters.out import (
    FitzPDFParser,
    MeiliMaterialIndexer,
    PBMaterialRepository,
)

from src.apps.v2.message_owner.di import set_message_owner_app
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

from src.apps.v2.quiz_attempter.di import set_quiz_attempter_app
from src.apps.v2.quiz_attempter.adapters.out import (
    PBAttemptRepository,
    AIExplainer,
    ExplainerDeps,
    EXPLAINER_LLM,
    ExplainerOutput,
)


from src.lib.clients import set_admin_pb

from .mcp import mcp


logger = logging.getLogger(__name__)

AgentPayload = Annotated[
    Union[AIPatchGeneratorOutput, QuizFinalizerOutput, ExplainerOutput],
    Field(discriminator="mode"),
]


class AgentEnvelope(BaseModel):
    data: AgentPayload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logger.info("Starting Quizbee API server")

    # GLOBAL
    http = httpx.AsyncClient()
    set_admin_pb(app)
    set_langfuse(app)
    meili = AsyncClient(settings.meili_url, settings.meili_master_key)

    # V2 LLM TOOLS
    text_tokenizer = TiktokenTokenizer()
    image_tokenizer = OpenAIImageTokenizer()
    chunker = SimpleChunker(text_tokenizer)
    set_llm_tools(
        app,
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )

    # V2 USER AUTH
    user_repository = PBUserRepository(app.state.admin_pb)
    user_verifier = PBUserVerifier(user_repository=user_repository)
    set_auth_user_app(app, user_verifier=user_verifier, user_repository=user_repository)

    # V2 MATERIAL SEARCH
    material_repository, pdf_parser, material_indexer = await init_material_search_deps(
        app, meili
    )
    set_material_search_app(
        app,
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        indexer=material_indexer,
        llm_tools=app.state.llm_tools,
        user_auth=app.state.auth_user_app,
    )

    # V2 QUIZ GENERATOR
    quiz_repository, patch_generator, finalizer, quiz_indexer = (
        await init_quiz_generator_deps(app, http, meili)
    )
    set_quiz_generator_app(
        app,
        user_auth=app.state.auth_user_app,
        llm_tools=app.state.llm_tools,
        material_search=app.state.material_search_app,
        quiz_repository=quiz_repository,
        quiz_indexer=quiz_indexer,
        patch_generator=patch_generator,
        finalizer=finalizer,
    )

    # V2 MESSAGE OWNER
    message_repository = PBMessageRepository(app.state.admin_pb)
    set_message_owner_app(app, message_repository=message_repository)

    # V2 QUIZ ATTEMPTER
    attempt_repository, explainer = init_quiz_attempter_deps(app, http)
    set_quiz_attempter_app(
        app,
        attempt_repository=attempt_repository,
        user_auth=app.state.auth_user_app,
        explainer=explainer,
        message_owner=app.state.message_owner_app,
        llm_tools=app.state.llm_tools,
    )

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logger.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await http.aclose()
    await meili.aclose()


async def init_material_search_deps(
    app: FastAPI, meili: AsyncClient
) -> tuple[PBMaterialRepository, FitzPDFParser, MeiliMaterialIndexer]:
    material_repository = PBMaterialRepository(app.state.admin_pb)
    pdf_parser = FitzPDFParser()
    material_indexer = await MeiliMaterialIndexer.ainit(
        llm_tools=app.state.llm_tools, meili=meili
    )
    return material_repository, pdf_parser, material_indexer


# Factory functions for dependency initialization
def init_quiz_attempter_deps(
    app: FastAPI, http: httpx.AsyncClient
) -> tuple[PBAttemptRepository, AIExplainer]:
    attempt_repository = PBAttemptRepository(app.state.admin_pb, http=http)
    explainer_ai = Agent(
        # instrument=True,
        model=EXPLAINER_LLM,
        deps_type=ExplainerDeps,
        history_processors=[],
        output_type=AgentEnvelope,
    )
    explainer = AIExplainer(
        lf=app.state.langfuse_client,
        ai=explainer_ai,
    )
    return attempt_repository, explainer


async def init_quiz_generator_deps(
    app: FastAPI, http: httpx.AsyncClient, meili: AsyncClient
) -> tuple[PBQuizRepository, AIPatchGenerator, AIQuizFinalizer, MeiliQuizIndexer]:
    quiz_repository = PBQuizRepository(app.state.admin_pb, http=http)
    patch_generator_ai = Agent(
        model=PATCH_GENERATOR_LLM,
        deps_type=AIPatchGeneratorDeps,
        history_processors=[],
        output_type=AgentEnvelope,
    )
    patch_generator = AIPatchGenerator(
        lf=app.state.langfuse_client,
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
        lf=app.state.langfuse_client,
        quiz_repository=quiz_repository,
        ai=finalizer_ai,
    )
    quiz_indexer = await MeiliQuizIndexer.ainit(
        llm_tools=app.state.llm_tools,
        meili=meili,
        quiz_repository=quiz_repository,
    )
    return quiz_repository, patch_generator, finalizer, quiz_indexer
