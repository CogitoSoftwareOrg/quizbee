import logging.config
from fastapi import Depends, FastAPI

from src.lib.config import LOGGING_CONFIG


from src.apps.v2.material_search.adapters.in_.http.router import (
    material_search_router as v2_material_search_router,
)
from src.apps.v2.quiz_generator.adapters.in_.http.router import (
    quiz_generator_router as v2_quiz_generator_router,
)
from src.apps.v2.quiz_attempter.adapters.in_.http.router import (
    quiz_attempter_router as v2_quiz_attempter_router,
)

from .cors import cors_middleware
from .errors import all_exceptions_handler
from .deps import http_ensure_admin_pb
from .lifespan import lifespan
from .middleware import RequestContextMiddleware
from .mcp import mcp

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.debug("Logger Creating app DEBUG test")


def create_app():
    app = FastAPI(
        lifespan=lifespan,
        dependencies=[
            Depends(http_ensure_admin_pb),
        ],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(Exception, all_exceptions_handler)

    app.include_router(v2_material_search_router)
    app.include_router(v2_quiz_generator_router)
    app.include_router(v2_quiz_attempter_router)

    cors_middleware(app)

    mcp.settings.streamable_http_path = "/"
    app.mount("/mcp", mcp.streamable_http_app())

    # return socketio.ASGIApp(sio, app, socketio_path="/socket.io")
    return app


app = create_app()
