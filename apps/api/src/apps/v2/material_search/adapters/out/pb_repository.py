import json
from typing import Any
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from ...domain.models import Material, MaterialFile, MaterialKind, MaterialStatus
from ...domain.ports import MaterialRepository


class PBMaterialRepository(MaterialRepository):
    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def create(self, create: Material) -> Material:
        dto: dict[str, Any] = {}
        total_bytes = 0
        images_bytes = []
        file_bytes = b""
        text_bytes = b""

        # Простые поля
        dto["id"] = create.id
        dto["title"] = create.title
        dto["user"] = create.user_id
        dto["status"] = create.status
        dto["kind"] = create.kind
        dto["tokens"] = create.tokens
        dto["contents"] = create.contents
        dto["isBook"] = create.is_book

        # Файлы
        file_bytes = create.file.file_bytes
        total_bytes += len(file_bytes)
        dto["file"] = FileUpload((create.file.file_name, file_bytes))

        if create.text_file is not None and create.text_file.file_bytes:
            text_bytes = create.text_file.file_bytes
            total_bytes += len(text_bytes)
            dto["textFile"] = FileUpload((create.text_file.file_name, text_bytes))

        # Изображения
        if create.images:
            images_list = []
            for image in create.images:
                total_bytes += len(image.file_bytes)
                images_bytes.append(image.file_bytes)
                images_list.append((image.file_name, image.file_bytes))
            dto["images"] = FileUpload(*images_list)

        dto["bytes"] = total_bytes

        res = await self.pb.collection("materials").create(dto)

        return self._to_material(res, file_bytes, text_bytes, images_bytes)

    async def update(self, upd: Material) -> Material:
        dto: dict[str, Any] = {}

        total_bytes = 0
        images_bytes = []
        file_bytes = b""
        text_bytes = b""

        # Обновляем только простые поля без bytes
        dto["title"] = upd.title
        dto["user"] = upd.user_id
        dto["status"] = upd.status
        dto["kind"] = upd.kind
        dto["tokens"] = upd.tokens
        dto["contents"] = upd.contents
        dto["isBook"] = upd.is_book

        if upd.file.file_bytes:
            file_bytes = upd.file.file_bytes
            total_bytes += len(file_bytes)

        if upd.images:
            images_bytes = []
            for image in upd.images:
                total_bytes += len(image.file_bytes)
                images_bytes.append(image.file_bytes)

        # Если нужно обновить textFile
        if upd.text_file is not None and upd.text_file.file_bytes:
            text_bytes = upd.text_file.file_bytes
            total_bytes += len(text_bytes)
            dto["textFile"] = FileUpload(
                (upd.text_file.file_name, upd.text_file.file_bytes)
            )

        dto["bytes"] = total_bytes

        rec = await self.pb.collection("materials").update(upd.id, dto)
        return self._to_material(
            rec,
            file_bytes,
            text_bytes,
            images_bytes,
        )

    def _to_material(
        self,
        rec: Record,
        file_bytes: bytes = b"",
        text_bytes: bytes = b"",
        images_bytes: list[bytes] | None = None,
    ) -> Material:
        if images_bytes is None:
            images_bytes = []

        return Material(
            id=rec.get("id") or "",
            title=rec.get("title") or "",
            user_id=rec.get("user") or "",
            status=MaterialStatus(rec.get("status") or ""),
            kind=MaterialKind(rec.get("kind") or ""),
            tokens=rec.get("tokens") or 0,
            file=MaterialFile(
                file_name=rec.get("file") or "",
                file_bytes=file_bytes,
            ),
            images=[
                MaterialFile(
                    file_name=image,
                    file_bytes=image_bytes,
                )
                for image, image_bytes in zip(rec.get("images", []), images_bytes or [])
            ],
            contents=json.dumps(rec.get("contents") or {}),
            is_book=rec.get("isBook") or False,
            text_file=(
                MaterialFile(
                    file_name=rec.get("textFile") or "",
                    file_bytes=text_bytes,
                )
                if rec.get("textFile")
                else None
            ),
        )
