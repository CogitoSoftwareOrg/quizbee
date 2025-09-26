import logging
import contextlib
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import httpx

from apps.auth.middleware import auth_user
from apps.billing.middleware import load_subscription
from apps.messages import messages_router
from apps.quizes import quizes_router
from apps.materials import materials_router
from lib.clients.pb import ensure_admin_pb, init_admin_pb
from lib.settings import settings

mcp = FastMCP("MCP", stateless_http=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logging.info("Starting Quizbee API server")

    app.state.http = httpx.AsyncClient()
    init_admin_pb(app)
    # await init_meilisearch(app)

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logging.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await app.state.http.aclose()


def create_app():
    app = FastAPI(
        lifespan=lifespan,
        dependencies=[
            Depends(ensure_admin_pb),
            Depends(auth_user),
            Depends(load_subscription),
        ],
    )

    app.include_router(quizes_router)
    app.include_router(messages_router)
    app.include_router(materials_router)

    # CORS: allow credentials from specific app origins (including PR subdomains)
    allowed_origins: list[str] = []
    allow_origin_regex: str | None = None

    if settings.env == "local":
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4321",
            "http://127.0.0.1:4321",
        ]
    elif settings.env == "preview":
        pr = settings.pr_id
        assert pr is not None
        allowed_origins = [
            f"https://{pr}-app-quizbee.cogitosoftware.nl",
            f"https://{pr}-web-quizbee.cogitosoftware.nl",
        ]
    elif settings.env == "production":
        # Production/base
        allowed_origins = [
            "https://app-quizbee.cogitosoftware.nl",
            "https://web-quizbee.cogitosoftware.nl",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=allow_origin_regex,
        allow_methods=["GET", "POST", "OPTIONS", "PATCH", "PUT"],
        allow_credentials=True,
        allow_headers=["*"],
        # expose_headers=["Mcp-Session-Id"], # Only for stateful mode
    )

    mcp.settings.streamable_http_path = "/"
    app.mount("/mcp", mcp.streamable_http_app())

    # return socketio.ASGIApp(sio, app, socketio_path="/socket.io")
    return app


app = create_app()
