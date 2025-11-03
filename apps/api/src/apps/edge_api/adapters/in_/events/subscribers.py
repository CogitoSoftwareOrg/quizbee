import logging

from arq import func

from src.apps.edge_api.app.contracts import (
    JobName,
    EdgeAPIApp,
    PublicStartQuizCmd,
    PublicFinalizeQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
)
from src.apps.material_search.app.contracts import MaterialFile

from .deps import ensure_admin_pb

logger = logging.getLogger(__name__)


def job(**opts):
    def deco(fn):
        return func(fn, **opts)

    return deco


@job(name=JobName.start_quiz, max_tries=3)
async def start_quiz_job(ctx, payload: dict):
    logger.info(f"Starting quiz job with payload: {payload}")

    await ensure_admin_pb(ctx)
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicStartQuizCmd(**payload)
    return await edge.start_quiz(cmd)


@job(name=JobName.finalize_quiz, max_tries=3)
async def finalize_quiz_job(ctx, payload: dict):
    logger.info(f"Finalizing quiz job with payload: {payload}")
    await ensure_admin_pb(ctx)
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicFinalizeQuizCmd(**payload)
    return await edge.finalize_quiz(cmd)


@job(name=JobName.generate_quiz_items, max_tries=3)
async def generate_quiz_items_job(ctx, payload: dict):
    logger.info(f"Generating quiz items job with payload: {payload}")
    await ensure_admin_pb(ctx)
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicGenerateQuizItemsCmd(**payload)
    return await edge.generate_quiz_items(cmd)


@job(name=JobName.finalize_attempt, max_tries=3)
async def finalize_attempt_job(ctx, payload: dict):
    logger.info(f"Finalizing attempt job with payload: {payload}")
    await ensure_admin_pb(ctx)
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicFinalizeAttemptCmd(**payload)
    return await edge.finalize_attempt(cmd)


@job(name=JobName.add_material, max_tries=3)
async def add_material_job(ctx, payload: dict):
    logger.info(f"Adding material job with payload: {payload["title"]}")
    await ensure_admin_pb(ctx)

    edge: EdgeAPIApp = ctx["edge"]
    # Reconstruct MaterialFile from dict
    file_dict = payload["file"]
    file = MaterialFile(**file_dict)

    cmd = PublicAddMaterialCmd(
        quiz_id=payload["quiz_id"],
        file=file,
        token=payload["token"],
        cache_key=payload["cache_key"],
        title=payload["title"],
        material_id=payload["material_id"],
    )
    return await edge.add_material(cmd)


# async def ask_explainer_job(ctx, payload: dict):
#     logger.info(f"Asking explainer job with payload: {payload}")
#     edge: EdgeAPIApp = ctx["edge"]
#     cmd = PublicAskExplainerCmd(**payload)
#     async for result in edge.ask_explainer(cmd):
#         yield result
