from fastapi import FastAPI
import logging
import contextlib
from contextlib import asynccontextmanager
from arq.connections import RedisSettings, create_pool

from quizbee_example_lib import greet

from src.apps.quiz_generator.di import init_quiz_generator_app
from src.apps.edge_api.di import init_edge_api_app

from src.apps.llm_tools.di import init_llm_tools_app

from src.apps.user_auth.di import init_auth_user_app

from src.apps.material_search.di import (
    init_material_search_app,
)

from src.apps.message_owner.di import init_message_owner_app

from src.apps.quiz_attempter.di import init_quiz_attempter_app

from src.lib.di import init_global_deps
from src.lib.settings import settings

from .mcp import mcp


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logger.info("Starting Quizbee API server")
    logger.info(greet("World"))

    # GLOBAL
    admin_pb, _, meili, http = init_global_deps()

    # V2 LLM TOOLS
    llm_tools = init_llm_tools_app()

    # V2 USER AUTH
    auth_user_app = init_auth_user_app()

    # V2 MATERIAL SEARCH
    material_search_app = await init_material_search_app(llm_tools=llm_tools)

    # V2 QUIZ GENERATOR
    quiz_generator_app = await init_quiz_generator_app(
        llm_tools=llm_tools,
        material_search=material_search_app,
    )

    # V2 MESSAGE OWNER
    message_owner_app = init_message_owner_app()

    # V2 QUIZ ATTEMPTER
    quiz_attempter_app = init_quiz_attempter_app(
        message_owner=message_owner_app,
        llm_tools=llm_tools,
    )

    # V2 EDGE API
    edge_api_app = init_edge_api_app(
        auth_user_app=auth_user_app,
        quiz_generator_app=quiz_generator_app,
        quiz_attempter_app=quiz_attempter_app,
        material_search_app=material_search_app,
    )

    # ARQ Redis pool для отправки задач
    redis_settings = RedisSettings.from_dsn(settings.redis_dsn)
    arq_pool = await create_pool(redis_settings)
    app.state.arq_pool = arq_pool

    app.state.edge_api_app = edge_api_app
    app.state.http = http
    app.state.admin_pb = admin_pb
    app.state.meili_client = meili

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logger.info("Shutting down Quizbee API server")
    await arq_pool.close()
    await http.aclose()
    await meili.aclose()
