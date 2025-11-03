from fastapi import APIRouter

from src.lib.settings import settings

from .schemas import SheduleJobsDto

internal_router = APIRouter(prefix="/internal", tags=["internal"])


@internal_router.post("/shedule")
async def shedule_jobs(dto: SheduleJobsDto):
    return {
        "version": "0.1.0",
        "env": settings.env,
        "pb_url": settings.pb_url,
        "pb_email": settings.pb_email,
        "redis_dsn": settings.redis_dsn,
    }
