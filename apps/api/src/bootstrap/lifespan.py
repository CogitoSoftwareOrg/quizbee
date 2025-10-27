from fastapi import FastAPI
import logging
import contextlib
from contextlib import asynccontextmanager
from meilisearch_python_sdk import AsyncClient
import httpx

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
from src.apps.v2.material_search.adapters.out.meili_indexer import MeiliIndexer

from src.lib.clients import set_admin_pb

from .mcp import mcp


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
    indexer = MeiliIndexer(app.state.llm_tools, meili)
    set_material_search_app(
        app,
        material_repository=material_repository,
        pdf_parser=pdf_parser,
        indexer=indexer,
        llm_tools=app.state.llm_tools,
    )

    # V2 QUIZ GENERATOR
    set_quiz_generator_app(app, admin_pb=app.state.admin_pb, http=http)

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logging.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await http.aclose()
    await meili.aclose()
