from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Request
import logging

from fastapi.responses import JSONResponse

from ....domain.models import MaterialFile
from ....app.usecases import AddMaterialCmd
from ....domain.errors import TooLargeFileError

from .deps import MaterialSearchAppDeps

material_search_router = APIRouter(
    prefix="/v2/materials",
    tags=["v2"],
    dependencies=[],
)


@material_search_router.post("", status_code=201)
async def add_material(
    request: Request,
    material_search_app: MaterialSearchAppDeps,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    token = request.cookies.get("pb_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized: no pb_token")

    try:
        file_bytes = await file.read()
        material = await material_search_app.add_material(
            AddMaterialCmd(
                token=token,
                file=MaterialFile(
                    file_name=file.filename or "unknown",
                    file_bytes=file_bytes,
                ),
                title=title,
                material_id=material_id,
            )
        )

        file_size_mb = len(file_bytes) / (1024 * 1024)
        return JSONResponse(
            content={
                "id": material.id,
                "title": material.title,
                "filename": file.filename,
                "status": "uploaded",
                "success": True,
                "file_size_mb": round(file_size_mb, 2),
                "message": "Material uploaded successfully",
                "tokens": material.tokens,
                "kind": material.kind,
            }
        )
    except TooLargeFileError as e:
        raise HTTPException(status_code=400, detail=e.message)
