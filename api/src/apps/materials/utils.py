import base64
import mimetypes
import httpx
from pocketbase.models.dtos import Record
from pydantic_ai import BinaryContent
from pydantic_ai.messages import ImageUrl

from lib.settings import settings


async def materials_to_ai_images(
    materials: list[Record],
) -> list[ImageUrl]:
    urls = []
    for m in materials:
        mid = m.get("id")
        col = m.get("collectionName")

        if m.get("kind") == "simple":
            fname = m.get("file", "")
            url = f"{settings.pb_url}api/files/{col}/{mid}/{fname}"
            if fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                urls.append(url)
        else:
            images = m.get("images", [])
            for img in images:
                urls.append(f"{settings.pb_url}api/files/{col}/{mid}/{img}")

    return [ImageUrl(url=url, force_download=True) for url in urls]


async def materials_to_ai_bytes(
    http: httpx.AsyncClient,
    materials: list[Record],
) -> list[BinaryContent]:
    contents: list[BinaryContent] = []

    for m in materials:
        mid = m.get("id")
        col = m.get("collectionName")

        urls = []
        if m.get("kind") == "simple":
            fname = m.get("file", "")
            if fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                urls.append(f"{settings.pb_url}api/files/{col}/{mid}/{fname}")
        else:
            for img in m.get("images", []):
                urls.append(f"{settings.pb_url}api/files/{col}/{mid}/{img}")

        for url in urls:
            res = await http.get(url)
            res.raise_for_status()
            data = res.content

            ctype, _ = mimetypes.guess_type(url)
            if ctype is None:
                ctype = "application/octet-stream"

            contents.append(BinaryContent(data=data, media_type=ctype))

    return contents


async def load_file_text(
    http: httpx.AsyncClient, col: str, rid: str, file_name: str
) -> str:
    url = f"{settings.pb_url}api/files/{col}/{rid}/{file_name}"
    try:
        resp = await http.get(url)
        resp.raise_for_status()
        return resp.text
    except httpx.ReadError as e:
        # Handle connection issues gracefully
        raise httpx.HTTPError(f"Failed to read file bytes from {url}: {e}")
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors
        raise httpx.HTTPError(f"HTTP error loading file bytes from {url}: {e}")


async def load_file_bytes(
    http: httpx.AsyncClient, col: str, rid: str, file_name: str
) -> bytes:
    url = f"{settings.pb_url}api/files/{col}/{rid}/{file_name}"
    try:
        resp = await http.get(url)
        resp.raise_for_status()
        return resp.content
    except httpx.ReadError as e:
        # Handle connection issues gracefully
        raise httpx.HTTPError(f"Failed to read file bytes from {url}: {e}")
    except httpx.HTTPStatusError as e:
        # Handle HTTP errors
        raise httpx.HTTPError(f"HTTP error loading file bytes from {url}: {e}")


def as_data_url(raw_bytes: bytes, filename: str) -> str:
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"
