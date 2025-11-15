from src.lib.settings import settings

ARQ_QUEUE_NAME = f"arq:queue:{settings.arq_job_prefix}{settings.env}"
