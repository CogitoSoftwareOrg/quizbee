import logging

from src.apps.v2.edge_api.app.contracts import (
    EdgeAPIApp,
    PublicStartQuizCmd,
    PublicFinalizeQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
)

logger = logging.getLogger(__name__)


async def start_quiz_job(ctx, payload: dict):
    logger.info(f"Starting quiz job with payload: {payload}")
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicStartQuizCmd(**payload)
    return await edge.start_quiz(cmd)


async def finalize_quiz_job(ctx, payload: dict):
    logger.info(f"Finalizing quiz job with payload: {payload}")
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicFinalizeQuizCmd(**payload)
    return await edge.finalize_quiz(cmd)


async def generate_quiz_items_job(ctx, payload: dict):
    logger.info(f"Generating quiz items job with payload: {payload}")
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicGenerateQuizItemsCmd(**payload)
    return await edge.generate_quiz_items(cmd)


async def finalize_attempt_job(ctx, payload: dict):
    logger.info(f"Finalizing attempt job with payload: {payload}")
    edge: EdgeAPIApp = ctx["edge"]
    cmd = PublicFinalizeAttemptCmd(**payload)
    return await edge.finalize_attempt(cmd)


# async def add_material_job(ctx, payload: dict):
#     logger.info(f"Adding material job with payload: {payload}")
#     edge: EdgeAPIApp = ctx["edge"]
#     cmd = PublicAddMaterialCmd(**payload)
#     return await edge.add_material(cmd)


# async def ask_explainer_job(ctx, payload: dict):
#     logger.info(f"Asking explainer job with payload: {payload}")
#     edge: EdgeAPIApp = ctx["edge"]
#     cmd = PublicAskExplainerCmd(**payload)
#     async for result in edge.ask_explainer(cmd):
#         yield result
