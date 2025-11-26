import asyncio
import logging

from google import genai
from google.genai import types
from langfuse import Langfuse

from ...domain.out import ImageDescriber
from ...domain.models import DocumentImage
from src.lib.settings import settings

logger = logging.getLogger(__name__)

IMAGE_DESCRIPTION_PROMPT = (
    "Transform the information (visual and textual) from the image into detailed text. "
    "Make it sound just like a factoid from the presentation. "
    "Don't notice any pictures in the output, just the facts! "
    "Make the output concise and informative, no redundancies."
)


class GeminiImageDescriber(ImageDescriber):
    def __init__(
        self,
        lf: Langfuse,
        model: str = "gemini-2.5-flash-lite",
        api_key: str | None = None,
    ):
        self.model = model
        self._lf = lf
        self.gemini_client = genai.Client(api_key=api_key or settings.gemini_api_key)

    async def describe(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        try:
            with self._lf.start_as_current_span(name="gemini_describe_image") as span:
                span.update(input={"mime_type": mime_type, "image_size": len(image_bytes)})
                
                response = await asyncio.to_thread(
                    self.gemini_client.models.generate_content,
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                        IMAGE_DESCRIPTION_PROMPT,
                    ],
                )
                result = response.text or ""
                span.update(output=result, model=self.model)
                return result
        except Exception as e:
            logger.error(f"❌ Ошибка при описании изображения через Gemini: {str(e)}")
            return ""

    async def describe_batch(self, images: list[DocumentImage]) -> dict[str, str]:
        with self._lf.start_as_current_span(name="gemini_describe_images_batch") as span:
            span.update(input={"images_count": len(images)})

            async def process_single(img: DocumentImage) -> tuple[str, str]:
                if not img.marker:
                    return ("", "")
                mime_type = f"image/{img.ext}" if img.ext != "jpg" else "image/jpeg"
                description = await self.describe(img.bytes, mime_type)
                if description:
                    logger.info(f"✓ Описание для {img.marker}: {description[:100]}...")
                return (img.marker, description)

            results = await asyncio.gather(*[process_single(img) for img in images])
            result_dict = {marker: desc for marker, desc in results if marker}
            span.update(output={"described_count": len(result_dict)})
            return result_dict
