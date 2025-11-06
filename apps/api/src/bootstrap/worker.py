import logging
from arq.connections import RedisSettings, create_pool

from src.apps.edge_api.adapters.in_.events.subscribers import (
    start_quiz_job,
    finalize_quiz_job,
    generate_quiz_items_job,
    finalize_attempt_job,
    add_material_job,
    remove_material_job,
)

from src.lib.di import init_global_deps
from src.lib.health import update_worker_heartbeat
from arq.cron import cron

from src.apps.llm_tools.di import init_llm_tools_app
from src.apps.user_auth.di import init_auth_user_app
from src.apps.material_search.di import init_material_search_app
from src.apps.quiz_generator.di import init_quiz_generator_app
from src.apps.message_owner.di import init_message_owner_app
from src.apps.quiz_attempter.di import init_quiz_attempter_app
from src.apps.edge_api.di import init_edge_api_app

from src.lib.settings import settings

from src.apps.edge_api.domain.constants import ARQ_QUEUE_NAME


logger = logging.getLogger(__name__)


async def worker_heartbeat_task(ctx):
    """Periodic task to update worker heartbeat in Redis."""
    arq_pool = ctx["arq_pool"]
    await update_worker_heartbeat(arq_pool)


async def startup(ctx):
    # GLOBAL
    admin_pb, _, meili, http = init_global_deps()

    # V2 LLM TOOLS
    llm_tools = init_llm_tools_app()

    # V2 USER AUTH
    auth_user_app = init_auth_user_app()

    # V2 MATERIAL SEARCH
    material_search_app = await init_material_search_app(llm_tools=llm_tools)

    # V2 QUIZ GENERATOR
    quiz_generator_app = await init_quiz_generator_app(
        llm_tools=llm_tools, material_search=material_search_app
    )

    # V2 MESSAGE OWNER
    message_owner_app = init_message_owner_app()

    # V2 QUIZ ATTEMPTER
    quiz_attempter_app = init_quiz_attempter_app(
        message_owner=message_owner_app, llm_tools=llm_tools
    )

    # V2 EDGE API
    edge_api_app = init_edge_api_app(
        auth_user_app=auth_user_app,
        quiz_generator_app=quiz_generator_app,
        quiz_attempter_app=quiz_attempter_app,
        material_search_app=material_search_app,
    )

    redis_settings = RedisSettings.from_dsn(settings.redis_dsn)
    arq_pool = await create_pool(redis_settings)
    ctx["arq_pool"] = arq_pool

    await update_worker_heartbeat(arq_pool)
    logger.info("Worker heartbeat initialized")

    ctx["edge"] = edge_api_app
    ctx["pb"] = admin_pb
    ctx["meili"] = meili
    ctx["http"] = http


async def shutdown(ctx):
    await ctx["http"].aclose()
    await ctx["meili"].aclose()
    await ctx["arq_pool"].close()


class WorkerSettings:
    max_jobs = 32
    queue_name = ARQ_QUEUE_NAME
    redis_settings = RedisSettings.from_dsn(settings.redis_dsn)
    functions = [
        start_quiz_job,
        finalize_quiz_job,
        generate_quiz_items_job,
        finalize_attempt_job,
        add_material_job,
        remove_material_job,
    ]
    cron_jobs = [
        cron(
            worker_heartbeat_task,
            second={0, 10, 20, 30, 40, 50},
        ),
    ]
    on_startup = startup
    on_shutdown = shutdown
