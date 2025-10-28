from typing import Annotated, Union
from fastapi import FastAPI
import logging
import contextlib
from contextlib import asynccontextmanager
from meilisearch_python_sdk import AsyncClient
import httpx
from pydantic import BaseModel, Field

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

from src.apps.v2.material_search.di import (
    set_material_search_app,
)
from src.apps.v2.material_search.adapters.out.pb_repository import PBMaterialRepository
from src.apps.v2.material_search.adapters.out.fitz_pdf_parser import FitzPDFParser
from src.apps.v2.material_search.adapters.out.meili_indexer import (
    MeiliIndexer as MeiliMaterialIndexer,
)

from src.apps.v2.quiz_generator.adapters.out.pb_quiz_repository import PBQuizRepository
from src.apps.v2.quiz_generator.adapters.out.pb_attempt_repository import (
    PBAttemptRepository,
)
from src.apps.v2.quiz_generator.adapters.out.ai_patch_generator import (
    AIPatchGenerator,
    AIPatchGeneratorOutput,
)
from src.apps.v2.quiz_generator.adapters.out.meili_indexer import (
    MeiliIndexer as MeiliQuizIndexer,
)

from src.lib.clients import set_admin_pb

from .mcp import mcp

AgentPayload = Annotated[
    Union[AIPatchGeneratorOutput],
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
    set_auth_user_app(app)

    # V2 MATERIAL SEARCH
    material_repository = PBMaterialRepository(app.state.admin_pb)
    pdf_parser = FitzPDFParser()
    indexer = MeiliMaterialIndexer(app.state.llm_tools, meili)
    set_material_search_app(
        app,
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        indexer=indexer,
        llm_tools=app.state.llm_tools,
    )

    # V2 QUIZ GENERATOR
    quiz_repository = PBQuizRepository(app.state.admin_pb, http)
    attempt_repository = PBAttemptRepository(app.state.admin_pb)
    patch_generator = AIPatchGenerator(
        lf=app.state.langfuse_client,
        quiz_repository=quiz_repository,
        shared_schema=AgentEnvelope,
    )
    quiz_indexer = MeiliQuizIndexer(app.state.llm_tools, meili, quiz_repository)
    set_quiz_generator_app(
        app,
        llm_tools=app.state.llm_tools,
        material_search=app.state.material_search_app,
        quiz_repository=quiz_repository,
        attempt_repository=attempt_repository,
        quiz_indexer=quiz_indexer,
        patch_generator=patch_generator,
    )

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logging.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await http.aclose()
    await meili.aclose()
