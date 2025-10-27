import asyncio
from fastapi import (
    APIRouter,
    File,
    UploadFile,
    HTTPException,
    Form,
    Depends,
    BackgroundTasks,
)
from pocketbase import FileUpload
from fastapi.responses import JSONResponse

from .tokens_calculation import count_text_tokens, calculate_image_tokens
from .pdf_parser import parse_pdf
from .important_sentences import summarize_to_fixed_tokens
from src.apps.auth import User
from src.apps.auth import User, auth_user
from src.lib.clients import AdminPBDeps as AdminPB
from src.lib.settings import settings

materials_router = APIRouter(
    prefix="/materials", tags=["materials"], dependencies=[Depends(auth_user)]
)


@materials_router.post("/upload")
async def upload_material(
    admin_pb: AdminPB,
    user: User,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    """
    Uploads material to PocketBase with automatic token counting for PDF files.
    For PDFs, extracts text and images, saves them separately with token counts.
    """
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    max_size_mb = 100

    dto = {
        "id": material_id,
        "title": title,
        "user": user.get("id"),
        "bytes": len(file_bytes),
        "status": "uploaded",
        "kind": "simple",
    }

    try:
        if file_size_mb > max_size_mb:
            dto["status"] = "too big"

            material = await admin_pb.collection("materials").create(dto)

            return JSONResponse(
                content={
                    "id": material.get("id"),
                    "title": material.get("title"),
                    "filename": file.filename,
                    "status": material.get("status"),
                    "file_size_mb": round(file_size_mb, 2),
                    "max_size_mb": max_size_mb,
                    "success": False,
                    "message": f"File is too large ({round(file_size_mb, 2)}MB). Maximum size: {max_size_mb}MB",
                }
            )

        dto["file"] = FileUpload((file.filename, file_bytes))
        pdf_data = None
        if file.filename and file.filename.lower().endswith(".pdf"):
            try:
                # Парсим PDF и получаем текст, изображения и токены
                pdf_data = parse_pdf(file_bytes)

                # Обрабатываем текст (сократить если > 50k токенов)
                extracted_text = pdf_data["text"]

                # Подсчитываем токены для текста
                text_tokens = count_text_tokens(extracted_text) if extracted_text else 0

                # Подсчитываем токены для изображений
                image_tokens = 0
                if pdf_data["images"]:
                    for img_data in pdf_data["images"]:
                        image_tokens += calculate_image_tokens(
                            img_data["width"], img_data["height"]
                        )

                # Общее количество токенов
                total_tokens = text_tokens + image_tokens

                dto["tokens"] = total_tokens
                dto["kind"] = "complex"

                # Сначала загружаем изображения в материал
                images_list = []
                if pdf_data["images"]:
                    for img_data in pdf_data["images"]:
                        images_list.append(
                            (
                                f"{material_id}_p{img_data['page']}_img{img_data['index']}.{img_data['ext']}",
                                img_data["bytes"],
                            )
                        )
                    dto["images"] = FileUpload(*images_list)

            except Exception as e:
                # Если парсинг не удался, сохраняем как обычный файл
                dto["kind"] = "simple"
                pdf_data = None
        else:
            # Проверяем, является ли файл изображением
            is_image = False
            if file.filename:
                image_extensions = (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".webp",
                    ".bmp",
                    ".svg",
                    ".ico",
                )
                is_image = file.filename.lower().endswith(image_extensions)

            if is_image:
                # Для изображений подсчитываем токены на основе размера
                # Примерная оценка: используем фиксированное количество токенов для изображений
                # или можно добавить реальный подсчет через PIL если нужно
                dto["tokens"] = (
                    0  # Для простых изображений можно не считать текстовые токены
                )
                dto["kind"] = "simple"
            else:
                # Для текстовых файлов
                try:
                    text_content = file_bytes.decode("utf-8")
                    token_count = count_text_tokens(text_content)
                    dto["tokens"] = token_count
                    dto["kind"] = "simple"
                except UnicodeDecodeError:
                    # Если не удается декодировать как текст, это бинарный файл
                    dto["tokens"] = 0
                    dto["kind"] = "simple"

        # Создаем материал в БД
        material = await admin_pb.collection("materials").create(dto)

        # Если это PDF с извлеченным текстом, сохраняем textFile и contents
        if pdf_data and pdf_data.get("text"):
            extracted_text = pdf_data["text"]

            # Получаем ID материала
            material_id_str = material.get("id")
            if not material_id_str:
                raise HTTPException(500, "Material ID not found after creation")

            # Если есть изображения, заменяем маркеры на реальные URLs
            if pdf_data.get("images"):
                image_files = material.get("images", [])

                # Создаем словарь маркер -> URL
                marker_to_url = {}
                pb_base_url = settings.pb_url.rstrip("/")

                for idx, img_data in enumerate(pdf_data["images"]):
                    marker = img_data.get("marker")
                    if marker and idx < len(image_files):
                        # Формируем URL изображения
                        image_filename = image_files[idx]
                        image_url = f"{pb_base_url}/api/files/materials/{material_id_str}/{image_filename}"
                        marker_to_url[marker] = image_url

                # Заменяем все маркеры на URLs с уникальным префиксом
                for marker, url in marker_to_url.items():
                    extracted_text = extracted_text.replace(
                        marker, f"\n{{quizbee_unique_image_url:{url}}}\n"
                    )

            # Обновляем материал с текстом (независимо от наличия изображений)
            text_filename = f"{material_id_str}_text.txt"
            text_bytes = extracted_text.encode("utf-8")

            await admin_pb.collection("materials").update(
                material_id_str, {"textFile": FileUpload((text_filename, text_bytes))}
            )

            # Если есть оглавление из parse_pdf, сохраняем его

            if pdf_data.get("isBook"):
                is_book_doc = pdf_data["isBook"]
                await admin_pb.collection("materials").update(
                    material_id_str, {"isBook": True if is_book_doc else False}
                )

            if pdf_data.get("contents"):
                import json

                toc_json = json.dumps(pdf_data["contents"])
                await admin_pb.collection("materials").update(
                    material_id_str, {"contents": toc_json}
                )

            # Обновляем объект material для ответа
            material = await admin_pb.collection("materials").get_one(material_id_str)

        response_data = {
            "id": material.get("id"),
            "title": material.get("title"),
            "filename": file.filename,
            "status": "uploaded",
            "file_size_mb": round(file_size_mb, 2),
            "success": True,
            "message": "Material uploaded successfully",
            "tokens": material.get("tokens"),
            "kind": material.get("kind"),
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while uploading material: {str(e)}"
        )
