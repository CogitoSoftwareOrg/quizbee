from fastapi import Depends, FastAPI
from mcp.server.fastmcp import FastMCP

from src.apps.billing import billing_router
from src.apps.quizes import quizes_router
from src.apps.messages import messages_router
from src.apps.materials import materials_router
from src.apps.quiz_attempts import quiz_attempts_router

from src.apps.v2.material_search.adapters.in_.http.router import (
    material_search_router as v2_material_search_router,
)

from .cors import cors_middleware
from .errors import all_exceptions_handler
from .deps import http_ensure_admin_pb
from .lifespan import lifespan
from .mcp import mcp
def create_app():
    app = FastAPI(
        lifespan=lifespan,
        dependencies=[
            Depends(http_ensure_admin_pb),
        ],
    )
    app.add_exception_handler(Exception, all_exceptions_handler)

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
