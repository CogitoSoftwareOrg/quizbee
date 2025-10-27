import logging
import contextlib
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from meilisearch_python_sdk import AsyncClient
from pocketbase import PocketBase
from starlette.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import httpx

from src.lib.settings import settings

from src.apps.v2.llm_tools.di import set_llm_tools
from src.apps.v2.quiz_generator.di import set_quiz_generator_app

from src.apps.billing import billing_router
from src.apps.quiz_attempts import init_feedbacker, quiz_attempts_router
from src.apps.messages import init_explainer, messages_router
from src.apps.quizes import (
    init_quizer,
    init_summarizer,
    init_trimmer,
    quizes_router,
)
from src.apps.materials import materials_router
from src.lib.clients import ensure_admin_pb

from src.apps.v2.material_search.adapters.in_.http.router import (
    material_search_router as v2_material_search_router,
)
from src.apps.v2.user_auth.di import set_auth_user_app

from src.apps.v2.material_search.di import (
    set_material_search_app,
)
from src.apps.v2.material_search.adapters.out.pb_repository import PBMaterialRepository
from src.apps.v2.material_search.adapters.out.fitz_pdf_parser import FitzPDFParser
from src.apps.v2.material_search.adapters.out.meili_indexer import MeiliIndexer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logging.info("Starting Quizbee API server")

    http = httpx.AsyncClient()
    admin_pb = PocketBase(settings.pb_url)
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
    material_repository = PBMaterialRepository(admin_pb)
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
    set_quiz_generator_app(app, admin_pb=admin_pb, http=http)

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logging.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await http.aclose()
    await meili.aclose()
