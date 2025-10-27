import logging
from fastapi import Request
from fastapi.responses import JSONResponse

from src.apps.v2.material_search.domain.errors import (
    TooLargeFileError,
    TooManyTextTokensError,
)

ERROR_MAP = {
    TooLargeFileError: (413, "TOO_LARGE_FILE"),
    TooManyTextTokensError: (413, "TOO_MANY_TEXT_TOKENS"),
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
