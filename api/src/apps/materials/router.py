import asyncio
import logging
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
from .tokens_calculation import count_image_tokens, count_text_tokens
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
    logging.info(f"Starting upload for file: {file.filename}, material_id: {material_id}")
    
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    max_size_mb = 100

    logging.info(f"File size: {round(file_size_mb, 2)}MB")

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
            logging.warning(f"File too large: {round(file_size_mb, 2)}MB > {max_size_mb}MB")
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

        logging.info(f"Adding original file to dto")
        dto["file"] = FileUpload((file.filename, file_bytes))
        
        pdf_data = None
        if file.filename and file.filename.lower().endswith(".pdf"):
            logging.info(f"Processing PDF file: {file.filename}")
            try:
                # Шаг 1: Парсим PDF и получаем текст и изображения
                logging.info("Parsing PDF...")
                pdf_data = parse_pdf(file_bytes)
                
                logging.info(f"PDF parsed: text_length={len(pdf_data['text'])} chars, images_count={len(pdf_data['images'])}")
                
                # Шаг 2: Обрабатываем текст (сократить если > 50k токенов)
                extracted_text = pdf_data["text"]
                if extracted_text:
                    # Подсчитываем токены в исходном тексте
                    original_text_tokens = count_text_tokens(extracted_text)
                    logging.info(f"Original text tokens: {original_text_tokens}")
                    
                    # Если текст больше 50k токенов, обрабатываем через process_text_to_summary
                    if original_text_tokens > 50000:
                        logging.info(f"Text exceeds 50k tokens ({original_text_tokens}), processing with summarization...")
                        extracted_text = summarize_to_fixed_tokens(extracted_text, target_token_count=50000, context_window=2)
                        logging.info(f"Text summarized, new length: {len(extracted_text)} chars")
                
                # Шаг 3: Подсчитываем токены для обработанного текста
                text_tokens = 0
                if extracted_text:
                    text_tokens = count_text_tokens(extracted_text)
                    logging.info(f"Final text tokens: {text_tokens}")
                
                # Шаг 4: Подсчитываем токены для всех изображений
                image_tokens = 0
                for img_data in pdf_data["images"]:
                    img_tokens = count_image_tokens(img_data["width"], img_data["height"])
                    image_tokens += img_tokens
                
                logging.info(f"Image tokens: {image_tokens}")
                
                total_tokens = text_tokens + image_tokens
                logging.info(f"Total tokens: {total_tokens}")
                
                dto["tokens"] = total_tokens
                dto["kind"] = "complex"
                
                # Добавляем обработанный текст и изображения в dto
                if extracted_text:
                    logging.info(f"Adding text file to dto (length: {len(extracted_text)} chars)")
                    text_filename = f"{material_id}_text.txt"
                    text_bytes = extracted_text.encode("utf-8")
                    dto["textFile"] = FileUpload((text_filename, text_bytes))
                
                images_list = []        
                if pdf_data["images"]:
                    logging.info(f"Adding {len(pdf_data['images'])} images to dto")
                    for img_data in pdf_data["images"]:
                        images_list.append((
                            f"{material_id}_p{img_data['page']}_img{img_data['index']}.{img_data['ext']}",
                            img_data["bytes"]))
                    dto["images"] = FileUpload(*images_list)
                    
                logging.info(f"DTO prepared with keys: {list(dto.keys())}")
                
            except Exception as e:
                logging.error(f"Error while parsing PDF {file.filename}: {e}", exc_info=True)
                # Если парсинг не удался, сохраняем как обычный файл
                dto["kind"] = "simple"
                pdf_data = None
        else:
            logging.info(f"Processing non-PDF file: {file.filename}")
            # Для текстовых файлов
            token_count = count_text_tokens(file_bytes.decode("utf-8"))
            dto["tokens"] = token_count
            dto["kind"] = "simple"

        logging.info(f"Creating material in PocketBase...")
        material = await admin_pb.collection("materials").create(dto)
        logging.info(f"Material created successfully with id: {material.get('id')}")

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
        logging.error(f"Error while uploading material: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error while uploading material: {str(e)}"
        )
