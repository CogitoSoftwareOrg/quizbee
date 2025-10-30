import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from src.apps..material_search.domain.errors import (
    TooLargeFileError,
    TooManyTextTokensError,
)
from src.apps..quiz_generator.domain.errors import (
    NotQuizOwnerError,
    NotEnoughQuizItemsError,
)
from src.apps..user_auth.domain.errors import ForbiddenError, NoTokenError

ERROR_MAP = {
    NotQuizOwnerError: (403, "NOT_QUIZ_OWNER"),
    NotEnoughQuizItemsError: (402, "NOT_ENOUGH_QUIZ_ITEMS"),
    TooLargeFileError: (413, "TOO_LARGE_FILE"),
    TooManyTextTokensError: (413, "TOO_MANY_TEXT_TOKENS"),
    NoTokenError: (401, "NO_TOKEN"),
    ForbiddenError: (403, "FORBIDDEN"),
}


async def all_exceptions_handler(request: Request, exc: Exception):
    for etype, (status, code) in ERROR_MAP.items():
        if isinstance(exc, etype):
            return JSONResponse(
                status_code=status,
                content={"error": {"code": code, "message": str(exc)}},
            )

    logging.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL", "message": "unexpected error"}},
    )
