from src.apps.v2.edge_api.app.contracts import (
    EdgeAPIApp,
    PublicStartQuizCmd,
    PublicFinalizeQuizCmd,
    PublicGenerateQuizItemsCmd,
    PublicFinalizeAttemptCmd,
    PublicAskExplainerCmd,
    PublicAddMaterialCmd,
)


async def start_quiz_job(ctx, payload: dict):
    edge: EdgeAPIApp = ctx["edge_api"]
    cmd = PublicStartQuizCmd(**payload)
    return await edge.start_quiz(cmd)


async def finalize_quiz_job(ctx, payload: dict):
    edge: EdgeAPIApp = ctx["edge_api"]
    cmd = PublicFinalizeQuizCmd(**payload)
    return await edge.finalize_quiz(cmd)


async def generate_quiz_items_job(ctx, payload: dict):
    edge: EdgeAPIApp = ctx["edge_api"]
    cmd = PublicGenerateQuizItemsCmd(**payload)
    return await edge.generate_quiz_items(cmd)


async def finalize_attempt_job(ctx, payload: dict):
    edge: EdgeAPIApp = ctx["edge_api"]
    cmd = PublicFinalizeAttemptCmd(**payload)
    return await edge.finalize_attempt(cmd)


async def add_material_job(ctx, payload: dict):
    edge: EdgeAPIApp = ctx["edge_api"]
    cmd = PublicAddMaterialCmd(**payload)
    return await edge.add_material(cmd)


async def ask_explainer_job(ctx, payload: dict):
    edge: EdgeAPIApp = ctx["edge_api"]
    cmd = PublicAskExplainerCmd(**payload)
    async for result in edge.ask_explainer(cmd):
        yield result
