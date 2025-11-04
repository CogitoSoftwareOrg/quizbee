from dataclasses import dataclass
import json
import logging

from src.lib.settings import settings

from ..domain.models import (
    Material,
    MaterialFile,
    MaterialKind,
    MaterialStatus,
    MaterialChunk,
)
from ..domain.ports import (
    LLMTools,
    MaterialIndexer,
    MaterialRepository,
    DocumentParsing,
)
from ..domain.errors import TooLargeFileError
from ..domain.constants import MAX_SIZE_MB, COMPLEX_EXTENSIONS

from .contracts import MaterialSearchApp, AddMaterialCmd, SearchCmd

logger = logging.getLogger(__name__)


class MaterialSearchAppImpl(MaterialSearchApp):
    def __init__(
        self,
        material_repository: MaterialRepository,
        document_parsing: DocumentParsing,
        llm_tools: LLMTools,
        indexer: MaterialIndexer,
    ):
        self.material_repository = material_repository
        self.document_parsing = document_parsing
        self.llm_tools = llm_tools
        self.indexer = indexer

    async def add_material(self, cmd: AddMaterialCmd) -> Material:

        ### я убрал возможность добавлять простые картинки поэтому кода для их обработки нет 

        logger.info("MaterialSearchAppImpl.add_material")
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
            )
            material.to_big()
            await self.material_repository.save(material)
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
        )


        if material.file.file_name.lower().endswith(COMPLEX_EXTENSIONS): # Просто парсим комплексные файлы через document_parsing. Парсер сам определит формат по расширению файла      
            try:
                doc_data = self.document_parsing.parse(
                    file_bytes=cmd.file.file_bytes,
                    file_name=cmd.file.file_name,
                    process_images=False,
                )

                # Все документы — это сложные материалы
                material.kind = MaterialKind.COMPLEX
                text = doc_data.text

                # Считаем токены для текста
                text_tokens = self.llm_tools.count_text(text)

                # Считаем токены для изображений и сохраняем их
                image_tokens = 0
                for image in doc_data.images:
                    image_tokens += self.llm_tools.count_image(
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

                # Сохраняем текст как файл
                text_bytes = text.encode("utf-8")
                material.text_file = MaterialFile(
                    file_name=f"{cmd.material_id}_text.txt",
                    file_bytes=text_bytes,
                )
                # ✅ Замена маркеров на URL (остаётся без изменений)
                if material.kind == MaterialKind.COMPLEX and len(text) > 0 and len(material.images) > 0:
                    marker_to_url = {}
                    for i, image in enumerate(doc_data.images):
                        marker = image.marker
                        if marker and i < len(material.images):
                            image_file_name = material.images[i].file_name
                            image_url = f"{settings.pb_url}api/files/materials/{material.id}/{image_file_name}"
                            marker_to_url[marker] = image_url
                    
                    for marker, url in marker_to_url.items():
                        text = text.replace(marker, f"\n{{quizbee_unique_image_url:{url}}}\n")

            except ValueError as e:
                # Неподдерживаемый формат файла
                logger.warning(f"Unsupported file format: {cmd.file.file_name} - {e}")
                material.status = MaterialStatus.UPLOADED
                await self.material_repository.save(material)
                raise

            except Exception as e:
                # Ошибка при парсинге
                logger.warning(f"Error parsing document {cmd.file.file_name}: {e}")
                material.status = MaterialStatus.UPLOADED
                await self.material_repository.save(material)
                raise



        else:                 # Простые текстовые файлы (TXT, MD и т.д.)
            try:
                # Декодируем содержимое файла как текст
                text = cmd.file.file_bytes.decode("utf-8")
                
                # Устанавливаем тип материала
                material.kind = MaterialKind.SIMPLE
                
                # Считаем токены для текста
                text_tokens = self.llm_tools.count_text(text)
                material.tokens = text_tokens
                
                # Сохраняем текст как файл
                material.text_file = MaterialFile(
                    file_name=f"{cmd.material_id}_text.txt",
                    file_bytes=cmd.file.file_bytes,
                )
                
            
                
            except UnicodeDecodeError as e:
                # Ошибка декодирования текста
                logger.warning(f"Error decoding text file {cmd.file.file_name}: {e}")
                material.status = MaterialStatus.UPLOADED
                await self.material_repository.save(material)
                raise
            
            except Exception as e:
                # Общая ошибка при обработке
                logger.warning(f"Error processing simple material {cmd.file.file_name}: {e}")
                material.status = MaterialStatus.UPLOADED
                await self.material_repository.save(material)
                raise
            

        # FOR ALL MATERIALS:
        await self.material_repository.save(material)
        material.status = MaterialStatus.INDEXING
        await self.material_repository.save(material)

        # Индексируем материал
        await self.indexer.index(material)
        material.status = MaterialStatus.INDEXED
        await self.material_repository.attach_to_quiz(material, cmd.quiz_id)
        await self.material_repository.save(material)

        return material
        
       

    async def search(self, cmd: SearchCmd) -> list[MaterialChunk]:
        logger.info("MaterialSearchAppImpl.search")
        limit_chunks = int(cmd.limit_tokens / self.llm_tools.chunk_size)
        ratio = 0.5 if len(cmd.query.strip().split()) > 3 else 0

        logger.info(
            f"Searching for material chunks for query: {cmd.query} (limit: {limit_chunks}, ratio: {ratio})"
        )
        chunks = await self.indexer.search(
            user_id=cmd.user.id,
            query=cmd.query,
            material_ids=cmd.material_ids,
            limit=limit_chunks,
            ratio=ratio,
        )

        return chunks

    async def _deduplicate_material(self, cmd: AddMaterialCmd) -> Material | None:
        material = await self.material_repository.get(cmd.material_id)
        if material is not None:
            return material
        return material
