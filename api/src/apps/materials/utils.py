import httpx
from pocketbase.models.dtos import Record
from pydantic_ai.messages import DocumentUrl, ImageUrl

from lib.settings import settings


async def materials_to_ai_docs(
    records: list[Record],
    force_download=settings.env == "local",
) -> list[DocumentUrl]:
    urls = []
    for m in records:
        mid = m.get("id")
        col = m.get("collectionName")
        fname = m.get("file")
        url = f"{settings.pb_url}/api/files/{col}/{mid}/{fname}"
        urls.append(url)
        # resp = await http.get(url)
        # resp.raise_for_status()
        # contents.append(resp.text)

    return [DocumentUrl(url=url, force_download=force_download) for url in urls]


async def load_materials_context(http: httpx.AsyncClient, quiz_id: str, file_name: str):
    url = f"{settings.pb_url}/api/files/quizes/{quiz_id}/{file_name}"
    resp = await http.get(url)
    resp.raise_for_status()
    return resp.text
