from fastapi import FastAPI

from src.apps.material_search.app.contracts import MaterialApp
from src.apps.llm_tools.app.contracts import LLMToolsApp


from .domain.ports import (
    QuizFinalizer,
    QuizRepository,
    QuizIndexer,
    PatchGenerator,
)
from .app.usecases import QuizGeneratorAppImpl


def init_quiz_generator_app(
    llm_tools: LLMToolsApp,
    material_search: MaterialApp,
    quiz_repository: QuizRepository,
    quiz_indexer: QuizIndexer,
    patch_generator: PatchGenerator,
    finalizer: QuizFinalizer,
):
    return QuizGeneratorAppImpl(
        quiz_repository=quiz_repository,
        quiz_indexer=quiz_indexer,
        llm_tools=llm_tools,
        material_search=material_search,
        patch_generator=patch_generator,
        finalizer=finalizer,
    )
