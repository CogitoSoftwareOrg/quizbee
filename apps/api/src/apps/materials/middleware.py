from fastapi import HTTPException, Request

from src.lib.clients import AdminPB
from src.apps.auth.middleware import User


async def user_owns_materials(request: Request, admin_pb: AdminPB, user: User):
    dto = await request.json()
    user_id = user.get("id", "")
    material_ids = dto.get("material_ids", [])

    if not material_ids:
        return

    for material_id in material_ids:
        material = await admin_pb.collection("materials").get_one(material_id)
        if material.get("user") != user_id:
            raise HTTPException(
                status_code=401, detail=f"Unauthorized: material not owned by user"
            )
