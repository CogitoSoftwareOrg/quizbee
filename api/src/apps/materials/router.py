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
from .tokens_calculation import count_pdf_tokens, count_text_tokens
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
    max_size_mb = 30

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
                # Парсим PDF и получаем текст, изображения и токены
                logging.info("Parsing PDF and counting tokens...")
                pdf_data = count_pdf_tokens(file_bytes)
                
                logging.info(f"PDF parsed: text_tokens={pdf_data['text_tokens']}, image_tokens={pdf_data['image_tokens']}, total={pdf_data['total_tokens']}, images_count={len(pdf_data['images'])}")
                
                dto["tokens"] = pdf_data["total_tokens"]
                dto["kind"] = "complex"
                
                # Добавляем текст и изображения сразу в dto
                if pdf_data["text"]:
                    logging.info(f"Adding text file to dto (length: {len(pdf_data['text'])} chars)")
                    text_filename = f"{material_id}_text.txt"
                    text_bytes = pdf_data["text"].encode("utf-8")
                    dto["textFile"] = FileUpload((text_filename, text_bytes))
                

                # dto["images"] = []
                # if pdf_data["images"]:
                #     logging.info(f"Adding {len(pdf_data['images'])} images to dto")
                #     for img_data in pdf_data["images"]:
                #         dto['images'].append(FileUpload((
                #             f"{material_id}_p{img_data['page']}_img{img_data['index']}.{img_data['ext']}",
                #             img_data["bytes"])))
                   
                    
                
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
