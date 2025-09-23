from pocketbase import PocketBase, FileUpload
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Form,
    Request,
    Query,
    HTTPException,
    File,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse, JSONResponse
import json
import logging
from typing import Annotated
import fitz  # PyMuPDF
import tiktoken
from PIL import Image
import io
import math

from pydantic import BaseModel, Field

from lib.clients.http import HTTPAsyncClient
from src.apps.messages import pb_to_ai
from src.lib.settings import settings
from src.lib.clients import AdminPB, langfuse_client


# --- Вспомогательные функции для подсчета токенов PDF ---

def _count_text_tokens(text: str) -> int:
    """
    Подсчитывает количество токенов в строке текста с помощью токенизатора OpenAI.
    """
    # 'cl100k_base' - это кодировка, используемая моделями gpt-4, gpt-3.5-turbo и др.
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # Резервный вариант для старых сред
        encoding = tiktoken.encoding_for_model("gpt-4")
        
    return len(encoding.encode(text, disallowed_special=()))

def _count_image_tokens(image_bytes: bytes) -> int:
    """
    Рассчитывает количество токенов для одного изображения на основе его размеров.
    Логика основана на ценообразовании токенов для модели GPT-4o/Vision.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size

        # 1. Масштабирование: модели "видят" изображения с максимальной длиной 2048px.
        # Это делает оценку более точной для изображений с высоким разрешением.
        if max(width, height) > 2048:
            scale = 2048 / max(width, height)
            width = int(width * scale)
            height = int(height * scale)

        # 2. Подсчет плиток 512x512 с округлением вверх.
        tiles_x = math.ceil(width / 512)
        tiles_y = math.ceil(height / 512)
        num_tiles = tiles_x * tiles_y

        # 3. Применение формулы: 170 токенов за каждую плитку + 85 базовых.
        total_tokens = (num_tiles * 170) + 85
        return total_tokens

    except Exception:
        # Если объект не является изображением или поврежден, не считаем его.
        return 0

def estimate_pdf_tokens(pdf_path: str) -> dict:
    """
    Универсальная функция для подсчета общего количества токенов в PDF-файле,
    включая как текст, так и изображения.

    Args:
        pdf_path (str): Путь к PDF-файлу.

    Returns:
        dict: Словарь с подробной информацией о количестве токенов
              или с сообщением об ошибке.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": f"Не удалось открыть или прочитать файл PDF: {e}"}

    total_text_tokens = 0
    total_image_tokens = 0
    image_count = 0
    full_text = ""
    page_count = len(doc)

    # 1. Извлекаем весь текст из документа
    for page in doc:
        full_text += page.get_text()
    
    # 2. Считаем токены для всего текста разом
    total_text_tokens = _count_text_tokens(full_text)

    # 3. Извлекаем изображения и считаем их токены
    for page_num in range(len(doc)):
        # Получаем список изображений на странице
        image_list = doc.get_page_images(page_num)
        image_count += len(image_list)

        for img_info in image_list:
            # Извлекаем байты изображения по его идентификатору
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Считаем токены для этого изображения и добавляем к общей сумме
            total_image_tokens += _count_image_tokens(image_bytes)
            
    doc.close()

    # 4. Формируем итоговый результат
    grand_total_tokens = total_text_tokens + total_image_tokens

    return {
        "pdf_path": pdf_path,
        "page_count": page_count,
        "image_count": image_count,
        "text_tokens": total_text_tokens,
        "image_tokens": total_image_tokens,
        "total_tokens": grand_total_tokens
    }


class FileToTokenize(BaseModel):
    material_id: str
    ext: str


utils_router = APIRouter(prefix="/utils", tags=["utils"])



@utils_router.get("/tokens")
async def check_amount_of_tokens(
    admin_pb: AdminPB,
    request: Request,
    dto: FileToTokenize
) -> dict:
    """
    Проверяет количество токенов в указанном материале (PDF файле) и возвращает информацию о токенах
    """
    # AUTH
    pb_token = request.cookies.get("pb_token")
    if not pb_token:
        raise HTTPException(status_code=401, detail="Unauthorized: no pb_token")
    
    try:
        pb = PocketBase(settings.pb_url)
        pb._inners.auth.set_user({"token": pb_token, "record": {}})
        user = (await pb.collection("users").auth.refresh()).get("record", {})
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {e}")

    user_id = user.get("id", "")
    
    # Get material info
    try:
        material = await admin_pb.collection("materials").get_one(dto.material_id)
        
        # Получаем путь к файлу из материала
        # Предполагаем, что в материале есть поле с файлом (например, 'file')
        file_name = material.get("file", "")
        if not file_name:
            raise HTTPException(status_code=404, detail="File not found in material")
        
        # Строим путь к файлу (предполагаем структуру хранения PocketBase)
        # Обычно PocketBase хранит файлы в папке pb_data/storage/{collection_id}/{record_id}/{filename}
        file_path = f"pb_data/storage/{material.get('collectionId', 'materials')}/{dto.material_id}/{file_name}"
        
        # Если это PDF файл, используем нашу функцию подсчета токенов
        if dto.ext.lower() == 'pdf':
            token_info = estimate_pdf_tokens(file_path)
            
            if "error" in token_info:
                raise HTTPException(status_code=500, detail=token_info["error"])
            
            return token_info
        else:
            # Для других типов файлов возвращаем базовую информацию
            return {
                "material_id": dto.material_id,
                "file_type": dto.ext,
                "total_tokens": 0,
                "error": f"Token counting for {dto.ext} files is not yet implemented"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing material: {e}")
