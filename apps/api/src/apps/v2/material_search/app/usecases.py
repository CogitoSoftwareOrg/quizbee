from dataclasses import dataclass
import json
import logging

from src.lib.settings import settings

from ..domain.models import Material, MaterialFile
from ..domain.ports import (
    MaterialPatch,
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

    async def add_material(self, cmd: AddMaterialCmd):
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
            file=file,
            images=[],
            title=title,
            user_id=user_id,
            status="uploaded",
            kind="simple",
            tokens=0,
            contents="",
        )
        if file.file_name.lower().endswith(".pdf"):
            try:
                material.kind = "complex"

                pdf_data = self.pdf_parser.parse(file.file_bytes)
                text = pdf_data.get("text") or ""
                pdf_images = pdf_data.get("images") or []
                text_tokens = self.tokenizer.count_text(text)

                image_tokens = 0
                for image in pdf_images:
                    image_tokens += self.image_tokenizer.count_image(
                        image["width"], image["height"]
                    )

                    image = MaterialFile(
                        file_name=f"{material_id}_p{image['page']}_img{image['index']}.{image['ext']}",
                        file_bytes=image["bytes"],
                    )
                    material.images.append(image)

                material.tokens = text_tokens + image_tokens
                material.contents = json.dumps(pdf_data.get("contents", []))
                material.is_book = pdf_data.get("isBook", False)

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
                marker = image.get("marker")
                if marker and i < len(pdf_images):
                    image_url = f"{settings.pb_url}api/files/materials/{material.id}/{image['file_name']}"
                    marker_to_url[marker] = image_url
            for marker, url in marker_to_url.items():
                text = text.replace(marker, f"\n{{quizbee_unique_image_url:{url}}}\n")

        text_filename = "full_text.txt"
        text_bytes = text.encode("utf-8")
        material = await self.material_repository.update(
            material.id or "",
            MaterialPatch(
                text_file=MaterialFile(
                    file_name=text_filename,
                    file_bytes=text_bytes,
                )
            ),
        )
