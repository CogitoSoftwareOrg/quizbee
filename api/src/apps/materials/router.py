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
from apps.auth import User
from apps.auth import User, auth_user
from lib.clients import AdminPB

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
                            img_data["width"], 
                            img_data["height"]
                        )
                
                # Общее количество токенов
                total_tokens = text_tokens + image_tokens

                dto["tokens"] = total_tokens
                dto["kind"] = "complex"

                # Добавляем обработанный текст и изображения в dto
                if extracted_text:
                    text_filename = f"{material_id}_text.txt"
                    text_bytes = extracted_text.encode("utf-8")
                    dto["textFile"] = FileUpload((text_filename, text_bytes))

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
            # Для текстовых файлов
            token_count = count_text_tokens(file_bytes.decode("utf-8"))
            dto["tokens"] = token_count
            dto["kind"] = "simple"

        material = await admin_pb.collection("materials").create(dto)

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
