import base64
import mimetypes
import httpx
from pocketbase.models.dtos import Record
from pydantic_ai.messages import ImageUrl

from lib.settings import settings


async def materials_to_ai_images(
    materials: list[Record],
) -> list[ImageUrl]:
    images = []
    for m in materials:
        mid = m.get("id")
        col = m.get("collectionName")

        if m.get("kind") == "simple":
            fname = m.get("file", "")
            url = f"{settings.pb_url}/api/files/{col}/{mid}/{fname}"
            if fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                images.append(url)
        else:
            images = m.get("images", [])
            for img in images:
                images.append(f"{settings.pb_url}/api/files/{col}/{mid}/{img}")

    return [ImageUrl(url=url, force_download=True) for url in images]


async def load_file_text(
    http: httpx.AsyncClient, col: str, rid: str, file_name: str
) -> str:
    url = f"{settings.pb_url}/api/files/{col}/{rid}/{file_name}"
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
    url = f"{settings.pb_url}/api/files/{col}/{rid}/{file_name}"
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
