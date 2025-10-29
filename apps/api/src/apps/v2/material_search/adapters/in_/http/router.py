from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
import logging

from fastapi.responses import JSONResponse

from src.apps.v2.user_auth.di import UserDeps

from ....di import MaterialSearchAppDep
from ....domain.models import MaterialFile
from ....app.usecases import AddMaterialCmd
from ....domain.errors import TooLargeFileError

from .deps import http_guard_and_set_user

material_search_router = APIRouter(
    prefix="/v2/materials",
    tags=["v2"],
    dependencies=[Depends(http_guard_and_set_user)],
)


@material_search_router.post("", status_code=201)
async def add_material(
    material_search_app: MaterialSearchAppDep,
    user: UserDeps,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    try:
        file_bytes = await file.read()
        material = await material_search_app.add_material(
            AddMaterialCmd(
                file=MaterialFile(
                    file_name=file.filename or "unknown",
                    file_bytes=file_bytes,
                ),
                title=title,
                material_id=material_id,
                user_id=user.id or "",
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
