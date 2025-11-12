import time
from pocketbase import PocketBase

from src.lib.pb_admin import ensure_admin_auth
from src.lib.settings import settings


async def ensure_admin_pb(ctx: dict):
    """
    Обеспечивает валидную авторизацию админа для ARQ задач.

    Вызывается в начале каждой ARQ задачи перед использованием admin_pb.
    """
    pb: PocketBase = ctx["pb"]
    await ensure_admin_auth(pb)
