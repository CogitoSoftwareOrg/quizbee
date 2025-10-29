from typing import Annotated
from fastapi import Depends, Request

from ....app.contracts import MaterialSearchApp


def get_material_search_app(request: Request) -> MaterialSearchApp:
    return request.app.state.material_search_app


MaterialSearchAppDeps = Annotated[MaterialSearchApp, Depends(get_material_search_app)]
