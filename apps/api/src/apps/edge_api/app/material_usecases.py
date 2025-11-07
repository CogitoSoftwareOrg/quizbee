from src.apps.material_search.app.contracts import (
    AddMaterialCmd,
    MaterialSearchApp,
    RemoveMaterialCmd,
)
from src.apps.material_search.domain.models import Material
from src.apps.user_auth.app.contracts import AuthUserApp

from ..domain._in import MaterialAPIApp, PublicAddMaterialCmd, PublicRemoveMaterialCmd


class MaterialAPIAppImpl(MaterialAPIApp):
    def __init__(self, material_search: MaterialSearchApp, user_auth: AuthUserApp):
        self._user_auth = user_auth
        self._material_search = material_search

    async def add_material(self, cmd: PublicAddMaterialCmd) -> Material:
        user = await self._user_auth.validate(cmd.token)
        material = await self._material_search.add_material(
            AddMaterialCmd(
                quiz_id=cmd.quiz_id,
                user=user,
                file=cmd.file,
                title=cmd.title,
                material_id=cmd.material_id,
            )
        )
        return material

    async def remove_material(self, cmd: PublicRemoveMaterialCmd) -> None:
        user = await self._user_auth.validate(cmd.token)
        await self._material_search.remove_material(
            RemoveMaterialCmd(
                user=user,
                material_id=cmd.material_id,
            )
        )
