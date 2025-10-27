from dataclasses import dataclass
import json
import logging

from src.lib.settings import settings

from ..domain.models import Material, MaterialFile, MaterialKind, MaterialStatus
from ..domain.ports import (
    MaterialRepository,
    PdfParser,
    Tokenizer,
    ImageTokenizer,
)
from ..domain.errors import TooLargeFileError
from ..domain.constants import MAX_SIZE_MB, IMAGE_EXTENSIONS


@dataclass
class AddMaterialCmd:
    file: MaterialFile
    title: str
    material_id: str
    user_id: str


class MaterialSearchApp:
    def __init__(
        self,
        material_repository: MaterialRepository,
        pdf_parser: PdfParser,
        tokenizer: Tokenizer,
        image_tokenizer: ImageTokenizer,
    ):
        self.material_repository = material_repository
        self.pdf_parser = pdf_parser
        self.tokenizer = tokenizer
        self.image_tokenizer = image_tokenizer

    async def add_material(self, cmd: AddMaterialCmd) -> Material:
        file = cmd.file
        title = cmd.title
        material_id = cmd.material_id
        user_id = cmd.user_id

        # Validate file size
        file_size_mb = len(file.file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_SIZE_MB:
            raise TooLargeFileError(file_size_mb)

        # try to parse file as pdf
        is_image = False
        text = ""
        pdf_images = []
        material = Material(
            id=material_id,
            file=file,
            images=[],
            title=title,
            user_id=user_id,
            status=MaterialStatus.UPLOADED,
            kind=MaterialKind.SIMPLE,
            tokens=0,
            contents="",
        )
        if file.file_name.lower().endswith(".pdf"):
            try:
                material.kind = MaterialKind.COMPLEX

                pdf_data = self.pdf_parser.parse(file.file_bytes)
                text = pdf_data.text
                pdf_images = pdf_data.images
                text_tokens = self.tokenizer.count_text(text)

                image_tokens = 0
                for image in pdf_images:
                    image_tokens += self.image_tokenizer.count_image(
                        image.width, image.height
                    )

                    image_file = MaterialFile(
                        file_name=f"{material_id}_p{image.page}_img{image.index}.{image.ext}",
                        file_bytes=image.bytes,
                    )
                    material.images.append(image_file)

                material.tokens = text_tokens + image_tokens
                material.contents = json.dumps(pdf_data.contents)
                material.is_book = pdf_data.is_book

            except Exception as e:
                logging.warning(f"Error parsing PDF: {e}")
        else:
            is_image = file.file_name.lower().endswith(IMAGE_EXTENSIONS)
            if is_image:
                ...  # TODO: implement image parsing
            else:
                try:
                    text = file.file_bytes.decode("utf-8")
                    material.tokens = self.tokenizer.count_text(text)
                except UnicodeDecodeError as e:
                    logging.warning(f"Error decoding text: {e}")

        material = await self.material_repository.create(material)

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

        material = await self.material_repository.update(material)

        return material
