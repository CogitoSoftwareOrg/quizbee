from dataclasses import dataclass
import json
import logging

from src.lib.settings import settings


from src.apps.v2.llm_tools.app.usecases import LLMToolsApp

from ..domain.models import (
    Material,
    MaterialFile,
    MaterialKind,
    MaterialStatus,
    MaterialChunk,
)
from ..domain.ports import (
    MaterialIndexer,
    MaterialRepository,
    PdfParser,
)
from ..domain.errors import TooLargeFileError
from ..domain.constants import MAX_SIZE_MB, IMAGE_EXTENSIONS

from .contracts import MaterialSearchApp, AddMaterialCmd, SearchCmd

logger = logging.getLogger(__name__)


class MaterialSearchAppImpl(MaterialSearchApp):
    def __init__(
        self,
        material_repository: MaterialRepository,
        pdf_parser: PdfParser,
        llm_tools: LLMToolsApp,
        indexer: MaterialIndexer,
    ):
        self.material_repository = material_repository
        self.pdf_parser = pdf_parser
        self.llm_tools = llm_tools
        self.indexer = indexer

    async def add_material(self, cmd: AddMaterialCmd) -> Material:
        logger.info("MaterialSearchAppImpl.add_material")
        # Validate file size

        file_size_mb = len(cmd.file.file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_SIZE_MB:
            raise TooLargeFileError(file_size_mb)

        # material = await self._deduplicate_material(cmd)
        # if material is not None:
        #     return material

        # try to parse file as pdf
        is_image = False
        text = ""
        pdf_images = []
        material = Material.create(
            id=cmd.material_id,
            user_id=cmd.user.id,
            title=cmd.title,
            file=cmd.file,
        )
        if cmd.file.file_name.lower().endswith(".pdf"):
            try:
                material.kind = MaterialKind.COMPLEX

                pdf_data = self.pdf_parser.parse(cmd.file.file_bytes)
                text = pdf_data.text
                pdf_images = pdf_data.images
                text_tokens = self.llm_tools.count_text(text)

                image_tokens = 0
                for image in pdf_images:
                    image_tokens += self.llm_tools.count_image(
                        image.width, image.height
                    )
                    image_file = MaterialFile(
                        file_name=f"{cmd.material_id}_p{image.page}_img{image.index}.{image.ext}",
                        file_bytes=image.bytes,
                    )
                    material.images.append(image_file)

                material.tokens = text_tokens + image_tokens
                material.contents = json.dumps(pdf_data.contents)
                material.is_book = pdf_data.is_book

                text_bytes = text.encode("utf-8")
                material.text_file = MaterialFile(
                    file_name=f"{cmd.material_id}_text.txt",
                    file_bytes=text_bytes,
                )

            except Exception as e:
                logger.warning(f"Error parsing PDF: {e}")
        else:
            is_image = cmd.file.file_name.lower().endswith(IMAGE_EXTENSIONS)
            if is_image:
                ...  # TODO: implement image parsing
            else:
                try:
                    text = cmd.file.file_bytes.decode("utf-8")
                    material.tokens = self.llm_tools.count_text(text)
                except UnicodeDecodeError as e:
                    logger.warning(f"Error decoding text: {e}")

        await self.material_repository.save(material)

        if material.kind == "complex" and len(text) > 0:
            marker_to_url = {}
            for i, image in enumerate(pdf_images):
                marker = image.marker
                if marker and i < len(material.images):
                    image_file_name = material.images[i].file_name
                    image_url = f"{settings.pb_url}api/files/materials/{material.id}/{image_file_name}"
                    marker_to_url[marker] = image_url
            for marker, url in marker_to_url.items():
                text = text.replace(marker, f"\n{{quizbee_unique_image_url:{url}}}\n")

        material.status = MaterialStatus.INDEXING
        await self.material_repository.save(material)

        await self.indexer.index(material)
        material.status = MaterialStatus.INDEXED
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
