from arq.connections import RedisSettings
from arq import cron

# from src.edge.usecases import EdgeAPI, USECASE_MAP, Context

# async def startup(ctx):
#     # инициализируй зависимости (БД, сервисы и т.п.)
#     ctx["edge_api"] = EdgeAPI(Context(
#         quiz_gen=QuizGeneratorAppDeps(...),
#         quiz_attempt=QuizAttempterAppDeps(...),
#         material_search=MaterialSearchAppDeps(...),
#     ))

# async def edgeapi_run(ctx, use_case: str, payload: dict, trace_id: str | None = None):
#     edge_api: EdgeAPI = ctx["edge_api"]
#     handler = USECASE_MAP.get(use_case)
#     if not handler:
#         # лог + DLQ
#         return {"ok": False, "error": f"unknown use_case {use_case}"}

#     # желательно валидацию payload → команду (pydantic/dataclass)
#     cmd = payload_to_cmd(use_case, payload)  # напиши маппер

#     # таймаут/ретраи по месту
#     try:
#         # пример таймаута:
#         return await asyncio.wait_for(handler(edge_api, cmd), timeout=120)
#     except asyncio.TimeoutError:
#         raise  # пусть arq ретраит
#     except Exception as e:
#         # лог + можно кинуть в DLQ
#         raise

# class WorkerSettings:
#     redis_settings = RedisSettings()
#     functions = [edgeapi_run]
#     on_startup = startup
#     max_jobs = 200
