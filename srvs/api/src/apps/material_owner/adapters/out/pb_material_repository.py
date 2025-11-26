import json
import logging
from typing import Any
from pocketbase import FileUpload, PocketBase
from pocketbase.models.dtos import Record

from ...domain.models import Material, MaterialFile, MaterialKind, MaterialStatus
from ...domain.out import MaterialRepository


class PBMaterialRepository(MaterialRepository):
    def __init__(self, pb: PocketBase):
        self.pb = pb

    async def get(self, id: str, file_bytes=b"") -> Material | None:
        try:
            rec = await self.pb.collection("materials").get_one(id)
        except Exception as e:
            logging.error(f"Error getting material: {e}")
            return None

        if rec.get("kind") == MaterialKind.COMPLEX:
            return self._to_material(rec, b"", file_bytes)
        else:
            return self._to_material(rec, file_bytes)

    async def create(self, material: Material):
        dto = self._to_record(material)
        try:
            await self.pb.collection("materials").create(dto)
        except Exception as e:
            raise

    async def update(self, material: Material):
        dto = self._to_record(material)
        try:
            await self.pb.collection("materials").update(material.id, dto)
        except Exception as e:
            raise

    async def attach_to_quiz(self, material: Material, quiz_id: str):
        try:
            await self.pb.collection("quizes").update(
                quiz_id, {"materials+": material.id}
            )
        except:
            raise

    async def delete(self, material_id: str):
        try:
            await self.pb.collection("materials").delete(material_id)
        except:
            raise

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
            size_bytes=rec.get("bytes") or 0,
            hash=rec.get("hash") or "",
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

    def _to_record(self, material: Material) -> dict[str, Any]:
        total_bytes = 0
        total_bytes += len(material.file.file_bytes)
        if material.text_file and material.text_file.file_bytes:
            total_bytes += len(material.text_file.file_bytes)
        if material.images:
            for image in material.images:
                total_bytes += len(image.file_bytes)

        return {
            "id": material.id,
            "title": material.title,
            "user": material.user_id,
            "status": material.status,
            "kind": material.kind,
            "tokens": material.tokens,
            "contents": material.contents,
            "isBook": material.is_book,
            "hash": material.hash,
            "file": FileUpload((material.file.file_name, material.file.file_bytes)),
            "textFile": (
                FileUpload(
                    (material.text_file.file_name, material.text_file.file_bytes)
                )
                if material.text_file
                else None
            ),
            "images": (
                FileUpload(
                    *[(image.file_name, image.file_bytes) for image in material.images]
                )
                if len(material.images) > 0
                else None
            ),
            "bytes": total_bytes,
        }
