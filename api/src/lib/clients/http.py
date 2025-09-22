from typing import Annotated
from fastapi import Depends
import httpx


def get_http_client():
    return httpx.AsyncClient()


HTTPAsyncClient = Annotated[httpx.AsyncClient, Depends(get_http_client)]
