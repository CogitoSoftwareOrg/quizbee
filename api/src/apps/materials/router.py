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
    """
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    max_size_mb = 30

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
        if file.filename and file.filename.lower().endswith(".pdf"):
            try:
                token_count = count_pdf_tokens(file_bytes)
                dto["tokens"] = token_count
                dto["kind"] = "complex"
            except Exception as e:
                print(f"Error while counting tokens for {file.filename}: {e}")
        else:
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
        logging.error(f"Error while uploading material: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error while uploading material: {str(e)}"
        )
