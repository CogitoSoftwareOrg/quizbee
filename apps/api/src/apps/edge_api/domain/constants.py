from src.lib.settings import settings

PATCH_LIMIT = 5

ARQ_QUEUE_NAME = f"arq:queue:{settings.arq_job_prefix}{settings.env}"
