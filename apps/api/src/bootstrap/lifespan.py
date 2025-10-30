from fastapi import FastAPI
import logging
import contextlib
from contextlib import asynccontextmanager
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
import httpx
from pocketbase import PocketBase

from src.apps.v2.quiz_generator.di import init_quiz_generator_app
from src.apps.v2.edge_api.di import init_edge_api_app
from src.lib.settings import settings

from src.apps.v2.llm_tools.di import init_llm_tools
from src.apps.v2.llm_tools.adapters.out import (
    TiktokenTokenizer,
    OpenAIImageTokenizer,
    SimpleChunker,
)

from src.apps.v2.user_auth.di import init_auth_user_app
from src.apps.v2.user_auth.adapters.out import PBUserVerifier, PBUserRepository

from src.apps.v2.material_search.di import (
    init_material_search_app,
)
from src.apps.v2.material_search.adapters.out import (
    FitzPDFParser,
    MeiliMaterialIndexer,
    PBMaterialRepository,
)

from src.apps.v2.message_owner.di import init_message_owner_app
from src.apps.v2.message_owner.adapters.out import PBMessageRepository

from src.apps.v2.quiz_attempter.di import init_quiz_attempter_app

from .mcp import mcp
from .di import (
    init_llm_tools_deps,
    init_material_search_deps,
    init_message_owner_deps,
    init_quiz_generator_deps,
    init_quiz_attempter_deps,
    init_user_auth_deps,
    init_global_deps,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # INIT LOGIC
    logger.info("Starting Quizbee API server")

    # GLOBAL
    admin_pb, lf, meili, http = init_global_deps()

    # V2 LLM TOOLS
    text_tokenizer, image_tokenizer, chunker = init_llm_tools_deps()
    llm_tools = init_llm_tools(
        text_tokenizer=text_tokenizer,
        image_tokenizer=image_tokenizer,
        chunker=chunker,
    )

    # V2 USER AUTH
    user_verifier, user_repository = init_user_auth_deps(admin_pb=admin_pb)
    auth_user_app = init_auth_user_app(
        user_verifier=user_verifier, user_repository=user_repository
    )

    # V2 MATERIAL SEARCH
    material_repository, pdf_parser, material_indexer = await init_material_search_deps(
        admin_pb=admin_pb,
        meili=meili,
        llm_tools=llm_tools,
    )
    material_search_app = init_material_search_app(
        llm_tools=llm_tools,
        pdf_parser=pdf_parser,
        indexer=material_indexer,
        material_repository=material_repository,
    )

    # V2 QUIZ GENERATOR
    quiz_repository, patch_generator, finalizer, quiz_indexer = (
        await init_quiz_generator_deps(
            meili=meili,
            lf=lf,
            admin_pb=admin_pb,
            http=http,
            llm_tools=llm_tools,
        )
    )
    quiz_generator_app = init_quiz_generator_app(
        llm_tools=llm_tools,
        material_search=material_search_app,
        quiz_repository=quiz_repository,
        quiz_indexer=quiz_indexer,
        patch_generator=patch_generator,
        finalizer=finalizer,
    )

    # V2 MESSAGE OWNER
    message_repository = init_message_owner_deps(admin_pb=admin_pb)
    message_owner_app = init_message_owner_app(message_repository=message_repository)

    # V2 QUIZ ATTEMPTER
    attempt_repository, explainer, finalizer = init_quiz_attempter_deps(
        lf=lf,
        admin_pb=admin_pb,
        http=http,
        llm_tools=llm_tools,
    )
    quiz_attempter_app = init_quiz_attempter_app(
        attempt_repository=attempt_repository,
        explainer=explainer,
        message_owner=message_owner_app,
        llm_tools=llm_tools,
        finalizer=finalizer,
    )

    # V2 EDGE API
    edge_api_app = init_edge_api_app(
        auth_user_app=auth_user_app,
        quiz_generator_app=quiz_generator_app,
        quiz_attempter_app=quiz_attempter_app,
        material_search_app=material_search_app,
    )

    app.state.edge_api_app = edge_api_app

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield

    # CLEANUP LOGIC
    logger.info("Shutting down Quizbee API server")
    # await app.state.meili_client.aclose()
    await http.aclose()
    await meili.aclose()
