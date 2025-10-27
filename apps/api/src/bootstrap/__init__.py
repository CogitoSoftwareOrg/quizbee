import logging
import contextlib
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import httpx

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
from src.lib.clients import init_meilisearch, ensure_admin_pb, init_admin_pb

from src.apps.v2.material_search.adapters.in_.http.router import (
    material_search_router as v2_material_search_router,
)
from src.apps.v2.user_auth.di import set_auth_user_app
from src.apps.v2.material_search.di import (
    set_tokenizer,
    set_image_tokenizer,
    set_pdf_parser,
    set_material_repository,
    set_chunker,
    set_material_search_app,
    aset_indexer,
)

from .cors import cors_middleware

mcp = FastMCP("MCP", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logging.info("Starting Quizbee API server")

    app.state.http = httpx.AsyncClient()
    init_admin_pb(app)
    await init_meilisearch(app)

    # PYDANTIC AI
    init_explainer(app)
    init_feedbacker(app)
    init_quizer(app)
    init_summarizer(app)
    init_trimmer(app)

    # V2 USER AUTH
    set_auth_user_app(app)

    # V2 MATERIAL SEARCH
    set_tokenizer(app)
    set_image_tokenizer(app)
    set_pdf_parser(app)
    set_material_repository(app, app.state.admin_pb)
    set_chunker(app, app.state.tokenizer)
    await aset_indexer(
        app, app.state.tokenizer, app.state.chunker, app.state.meilisearch_client
    )
    set_material_search_app(
        app,
        app.state.material_repository,
        app.state.pdf_parser,
        app.state.tokenizer,
        app.state.image_tokenizer,
        app.state.indexer,
    )

    # V2 QUIZ GENERATOR

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logging.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await app.state.http.aclose()
    await app.state.meilisearch_client.aclose()


def create_app():
    app = FastAPI(
        lifespan=lifespan,
        dependencies=[
            Depends(ensure_admin_pb),
        ],
    )

    app.include_router(billing_router)
    app.include_router(quizes_router)
    app.include_router(messages_router)
    app.include_router(materials_router)
    app.include_router(quiz_attempts_router)

    app.include_router(v2_material_search_router)

    cors_middleware(app)

    mcp.settings.streamable_http_path = "/"
    app.mount("/mcp", mcp.streamable_http_app())

    # return socketio.ASGIApp(sio, app, socketio_path="/socket.io")
    return app


app = create_app()
