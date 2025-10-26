import re
from dataclasses import asdict
from typing import Any
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from src.lib.utils.case_conversion import camel_to_snake, snake_to_camel
from src.lib.settings import settings

from ...domain.models import Material, MaterialFile
from ...domain.ports import MaterialPatch, MaterialRepository


class PBMaterialRepository(MaterialRepository):
    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def create(self, create: Material) -> Material:
        dto: dict[str, Any] = {}

        create_dict = snake_to_camel(asdict(create))
        if not isinstance(create_dict, dict):
            raise ValueError(f"Invalid create dict type: {type(create_dict)}")

        for key, value in create_dict.items():
            dto[key] = value

            if key == "textFile":
                url = f"{settings.pb_url}api/files/materials/{dto.get("id")}/{value.file_name}"
                dto[key] = FileUpload((url, value.file_bytes))
            elif key == "images":
                for image in value:
                    url = f"{settings.pb_url}api/files/materials/{dto.get("id")}/{image.file_name}"
                    dto[key].append(FileUpload((url, image.file_bytes)))

        res = await self.pb.collection("materials").create(dto)

        return self._to_material(res)

    async def update(self, m_id: str, upd: MaterialPatch) -> Material:
        dto = {}

        upd_dict = snake_to_camel(asdict(upd))
        if not isinstance(upd_dict, dict):
            raise ValueError(f"Invalid upd dict type: {type(upd_dict)}")

        for key, value in upd_dict.items():
            if key == "textFile":
                url = f"{settings.pb_url}api/files/materials/{m_id}/{value.file_name}"
                dto[key] = FileUpload((url, value.file_bytes))
            elif key == "images":
                for image in value:
                    url = (
                        f"{settings.pb_url}api/files/materials/{m_id}/{image.file_name}"
                    )
                    dto[key].append(FileUpload((url, image.file_bytes)))

        rec = await self.pb.collection("materials").update(m_id, dto)
        return self._to_material(rec)

    def _to_material(self, rec: Record) -> Material:
        return Material(
            id=rec.get("id"),
            title=rec.get("title") or "",
            user_id=rec.get("user") or "",
            status=rec.get("status") or "",
            kind=rec.get("kind") or "",
            tokens=rec.get("tokens") or 0,
            file=MaterialFile(
                file_name=rec.get("file") or "",
            ),
            images=[
                MaterialFile(
                    file_name=image,
                )
                for image in rec.get("images", [])
            ],
            text_file=MaterialFile(
                file_name=rec.get("textFile") or "",
            ),
        )
