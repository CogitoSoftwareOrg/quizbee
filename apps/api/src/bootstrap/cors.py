from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.lib.settings import settings


def cors_middleware(app: FastAPI):
    allowed_origins = _allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=None,
        allow_methods=["GET", "POST", "OPTIONS", "PATCH", "PUT"],
        allow_credentials=True,
        allow_headers=["*"],
        # expose_headers=["Mcp-Session-Id"], # Only for stateful mode
    )


def _allowed_origins():
    allowed_origins: list[str] = []

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
            f"https://{pr}-app.quizbee.academy",
            f"https://{pr}-web.quizbee.academy",
        ]
    elif settings.env == "quality-assurance":
        allowed_origins = [
            "https://qa-app.quizbee.academy",
            "https://qa-web.quizbee.academy",
        ]
    elif settings.env == "production":
        allowed_origins = [
            "https://app.quizbee.academy",
            "https://web.quizbee.academy",
        ]

    return allowed_origins
