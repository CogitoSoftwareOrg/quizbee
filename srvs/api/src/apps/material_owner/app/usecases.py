from dataclasses import dataclass
import json
import logging
from typing import Any

from src.lib.settings import settings

from src.apps.document_parser.domain import DocumentParseCmd

from ..domain.models import (
    Material,
    MaterialFile,
    MaterialKind,
    MaterialStatus,
    MaterialChunk,
    SearchType,
)
from ..domain.out import (
    MaterialIndexer,
    MaterialRepository,
    SearchDto,
    SearcherProvider,
    DocumentParser,
    LLMTools,
)
from ..domain.errors import TooLargeFileError, TooManyTextTokensError
from ..domain.constants import MAX_SIZE_MB, COMPLEX_EXTENSIONS
from ..domain.out import LLMTools
from ..domain._in import MaterialApp, AddMaterialCmd, RemoveMaterialCmd, SearchCmd

logger = logging.getLogger(__name__)


class MaterialAppImpl(MaterialApp):
    def __init__(
        self,
        material_repository: MaterialRepository,
        document_parser: DocumentParser,
        llm_tools: LLMTools,
        indexer: MaterialIndexer,
        searcher_provider: SearcherProvider,
    ):
        self._document_parser = document_parser
        self._material_repository = material_repository
        self._llm_tools = llm_tools
        self._indexer = indexer
        self._searcher_provider = searcher_provider

    async def get_material(self, material_id: str) -> Material | None:
        return await self._material_repository.get(material_id)

    async def add_material(self, cmd: AddMaterialCmd) -> Material:

        ### я убрал возможность добавлять простые картинки поэтому кода для их обработки нет

        logger.info("MaterialAppImpl.add_material")
        # Validate file size

        file_size_mb = len(cmd.file.file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_SIZE_MB:
            material = Material.create(
                id=cmd.material_id,
                user_id=cmd.user.id,
                title=cmd.title,
                file=MaterialFile(
                    file_name=cmd.file.file_name,
                    file_bytes=cmd.file.file_bytes,
                ),
                hash=cmd.hash,
            )
            material.to_big()
            await self._material_repository.create(material)
            raise TooLargeFileError(file_size_mb)

        # material = await self._deduplicate_material(cmd)
        # if material is not None:
        #     return material

        # Создаём материал
        material = Material.create(
            id=cmd.material_id,
            user_id=cmd.user.id,
            title=cmd.title,
            file=cmd.file,
            hash=cmd.hash,
        )

        if material.file.file_name.lower().endswith(
            COMPLEX_EXTENSIONS
        ):  # Просто парсим комплексные файлы через document_parsing. Парсер сам определит формат по расширению файла
            try:
                doc_data = await self._document_parser.parse(
                    cmd=DocumentParseCmd(
                        file_bytes=cmd.file.file_bytes,
                        file_name=cmd.file.file_name,
                    ),
                )

                # Все документы — это сложные материалы
                material.kind = MaterialKind.COMPLEX
                text = doc_data.text

                # Считаем токены для текста
                text_tokens = self._llm_tools.count_text(text)

                # Считаем токены для изображений и сохраняем их
                image_tokens = 0
                for image in doc_data.images:
                    image_tokens += self._llm_tools.count_image(
                        image.width, image.height
                    )
                    image_file = MaterialFile(
                        file_name=f"{cmd.material_id}_p{image.page}_img{image.index}.{image.ext}",
                        file_bytes=image.bytes,
                    )
                    material.images.append(image_file)

                # Сохраняем статистику
                material.tokens = text_tokens + image_tokens
                material.contents = json.dumps(doc_data.contents)
                material.is_book = doc_data.is_book
                material.table_of_contents = (
                    doc_data.contents if doc_data.is_book else None
                )

                # Сохраняем текст как файл
                text_bytes = text.encode("utf-8")
                material.text_file = MaterialFile(
                    file_name=f"{cmd.material_id}_text.txt",
                    file_bytes=text_bytes,
                )

                # ✅ Замена маркеров на URL (остаётся без изменений)
                if (
                    material.kind == MaterialKind.COMPLEX
                    and len(text) > 0
                    and len(material.images) > 0
                ):
                    marker_to_url = {}
                    for i, image in enumerate(doc_data.images):
                        marker = image.marker
                        if marker and i < len(material.images):
                            image_file_name = material.images[i].file_name
                            image_url = f"{settings.pb_url}api/files/materials/{material.id}/{image_file_name}"
                            marker_to_url[marker] = image_url

                    for marker, url in marker_to_url.items():
                        text = text.replace(
                            marker, f"\n{{quizbee_unique_image_url:{url}}}\n"
                        )
            except Exception as e:
                logger.warning(f"Error parsing PDF: {e}")
        else:
            try:
                text = cmd.file.file_bytes.decode("utf-8")
                material.tokens = self._llm_tools.count_text(text)
            except UnicodeDecodeError as e:
                logger.warning(f"Error decoding text: {e}")

        await self._material_repository.create(material)

        # Проверяем количество токенов
        if material.tokens < 40:
            material.status = MaterialStatus.NO_TEXT
            await self._material_repository.update(material)

            if cmd.quiz_id:
                await self._material_repository.attach_to_quiz(material, cmd.quiz_id)
            return material

        material.status = MaterialStatus.INDEXING
        await self._material_repository.update(material)

        # Индексируем материал
        try:
            await self._indexer.index(material)
        except TooManyTextTokensError as e:
            material.status = MaterialStatus.TOO_BIG
            await self._material_repository.update(material)
            raise e

        material.status = MaterialStatus.INDEXED

        if cmd.quiz_id:
            await self._material_repository.attach_to_quiz(material, cmd.quiz_id)

        await self._material_repository.update(material)

        return material

    async def search(self, cmd: SearchCmd) -> list[MaterialChunk]:
        logger.info("MaterialAppImpl.search")

        limit_chunks = int(cmd.limit_tokens / self._llm_tools.chunk_size)

        ratio = 0.0
        if cmd.search_type is not None:
            search_type = cmd.search_type
        elif cmd.all_chunks:
            search_type = SearchType.ALL
        elif (
            cmd.vectors is not None and len(cmd.vectors) > 0 and cmd.query.strip() == ""
        ):
            search_type = SearchType.VECTOR
        elif cmd.query.strip() == "":
            search_type = SearchType.DISTRIBUTION
        else:
            search_type = SearchType.QUERY
            ratio = 0.5 if len(cmd.query.strip().split()) > 3 else 0

        searcher = self._searcher_provider.get(search_type=search_type)

        logger.info(
            f"Searching for material chunks (type: {search_type}, limit: {limit_chunks}, ratio: {ratio})"
        )
        chunks = await searcher.search(
            dto=SearchDto(
                user_id=cmd.user.id,
                material_ids=cmd.material_ids,
                query=cmd.query,
                rerank_prefix=cmd.rerank_prefix,
                limit=limit_chunks,
                ratio=ratio,
                vectors=cmd.vectors,
                vector_thresholds=cmd.vector_thresholds,
            )
        )

        return chunks

    async def remove_material(self, cmd: RemoveMaterialCmd) -> None:
        material = await self._material_repository.get(cmd.material_id)
        if material is None:
            raise ValueError("Material not found")

        if material.user_id != cmd.user.id:
            raise ValueError("User does not have permission to remove material")

        if material.status == MaterialStatus.INDEXED:
            await self._indexer.delete([cmd.material_id])

        await self._material_repository.delete(cmd.material_id)

    async def mark_chunks_as_used(self, chunk_ids: list[str]) -> None:
        """
        Отмечает чанки как использованные.

        Args:
            chunk_ids: Список ID чанков для пометки
        """
        logger.info(f"MaterialAppImpl.mark_chunks_as_used: {len(chunk_ids)} chunks")
        await self._indexer.mark_chunks_as_used(chunk_ids)

    async def get_chunks_info(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        """
        Получает информацию о чанках.

        Args:
            chunk_ids: Список ID чанков

        Returns:
            Список диктов с информацией о каждом чанке
        """
        logger.info(f"MaterialAppImpl.get_chunks_info: {len(chunk_ids)} chunks")
        chunks_info = await self._indexer.get_chunks_info(chunk_ids)
        return chunks_info

    async def _deduplicate_material(self, cmd: AddMaterialCmd) -> Material | None:
        material = await self._material_repository.get(cmd.material_id)
        if material is not None:
            return material
        return material
