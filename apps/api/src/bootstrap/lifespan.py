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
from src.apps.v2.quiz_generator.di import set_quiz_generator_app

from src.apps.quiz_attempts import init_feedbacker
from src.apps.messages import init_explainer
from src.apps.quizes import (
    init_quizer,
    init_summarizer,
    init_trimmer,
)

from src.lib.clients import set_admin_pb, set_langfuse

from src.apps.v2.user_auth.di import set_auth_user_app
from src.apps.v2.user_auth.adapters.out import PBUserVerifier, PBUserRepository

from src.apps.v2.material_search.di import (
    set_material_search_app,
)
from src.apps.v2.material_search.adapters.out import (
    FitzPDFParser,
    MeiliIndexer as MeiliMaterialIndexer,
    PBMaterialRepository,
)

from src.apps.v2.quiz_generator.adapters.out import (
    PATCH_GENERATOR_LLM,
    FINALIZER_LLM,
    PBQuizRepository,
    AIPatchGenerator,
    AIPatchGeneratorDeps,
    AIPatchGeneratorOutput,
    AIFinalizer,
    FinalizerDeps,
    FinalizerOutput,
    MeiliIndexer as MeiliQuizIndexer,
)


from src.lib.clients import set_admin_pb

from .mcp import mcp

AgentPayload = Annotated[
    Union[AIPatchGeneratorOutput, FinalizerOutput],
    Field(discriminator="mode"),
]


class AgentEnvelope(BaseModel):
    data: AgentPayload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logging.info("Starting Quizbee API server")

    http = httpx.AsyncClient()
    set_admin_pb(app)
    set_langfuse(app)
    meili = AsyncClient(settings.meili_url, settings.meili_master_key)

    # PYDANTIC AI
    init_explainer(app)
    init_feedbacker(app)
    init_quizer(app)
    init_summarizer(app)
    init_trimmer(app)

    # V2 LLM TOOLS
    set_llm_tools(app)

    # V2 USER AUTH
    user_repository = PBUserRepository(app.state.admin_pb)
    user_verifier = PBUserVerifier(user_repository=user_repository)
    set_auth_user_app(app, user_verifier=user_verifier, user_repository=user_repository)

    # V2 MATERIAL SEARCH
    material_repository = PBMaterialRepository(app.state.admin_pb)
    pdf_parser = FitzPDFParser()
    material_indexer = await MeiliMaterialIndexer.ainit(
        llm_tools=app.state.llm_tools, meili=meili
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
    patch_generator_ai = Agent(
        model=PATCH_GENERATOR_LLM,
        deps_type=AIPatchGeneratorDeps,
        output_type=AgentEnvelope,
        history_processors=[],
        retries=3,
    )
    quiz_repository = PBQuizRepository(app.state.admin_pb, http)

    patch_generator = AIPatchGenerator(
        lf=app.state.langfuse_client,
        quiz_repository=quiz_repository,
        ai=patch_generator_ai,
    )

    finalizer_ai = Agent(
        model=FINALIZER_LLM,
        deps_type=FinalizerDeps,
        output_type=AgentEnvelope,
        history_processors=[],
        retries=3,
    )
    finalizer = AIFinalizer(
        lf=app.state.langfuse_client,
        quiz_repository=quiz_repository,
        ai=finalizer_ai,
    )
    quiz_indexer = await MeiliQuizIndexer.ainit(
        llm_tools=app.state.llm_tools,
        meili=meili,
        quiz_repository=quiz_repository,
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

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logging.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await http.aclose()
    await meili.aclose()
