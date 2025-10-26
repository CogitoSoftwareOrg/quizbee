from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form

from src.apps.v2.user_auth.di import User

from ....di import MaterialSearchAppDep
from ....domain.errors import TooLargeFileError
from .deps import http_guard_and_set_user

materials_router = APIRouter(
    prefix="/v2/materials",
    tags=["materials"],
    dependencies=[Depends(http_guard_and_set_user)],
)


@materials_router.post("/")
async def add_material(
    material_search_app: MaterialSearchAppDep,
    user: User,
    file: UploadFile = File(...),
    title: str = Form(...),
    material_id: str = Form(...),
):
    try:
        file_bytes = await file.read()
        await material_search_app.add_material(
            file.filename or "unknown",
            file_bytes,
            title,
            material_id,
            user.get("id") or "",
        )
    except TooLargeFileError as e:
        raise HTTPException(status_code=400, detail=e.message)
