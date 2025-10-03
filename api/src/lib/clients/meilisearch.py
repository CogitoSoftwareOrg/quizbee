from typing import Annotated
from fastapi import Depends, FastAPI, Request
from meilisearch_python_sdk import (
    AsyncClient,
)
from meilisearch_python_sdk.models.settings import Embedders, OpenAiEmbedder

from lib.config import LLMS
from lib.settings import settings

meiliEmbeddings = {
    "quizSummaries": OpenAiEmbedder(
        source="openAi",
        model=LLMS.TEXT_EMBEDDING_3_SMALL.split(":")[-1],
        api_key=settings.openai_api_key,
        document_template="Summary: {{doc.summary}}",
    ),
}


async def init_meilisearch(app: FastAPI):
    meilisearch_client = AsyncClient(
        settings.meilisearch_url, settings.meilisearch_master_key
    )

    quiz_summaries_index = meilisearch_client.index("quizSummaries")
    await quiz_summaries_index.update_embedders(
        Embedders(embedders=meiliEmbeddings)  # pyright: ignore[reportArgumentType]
    )
    await quiz_summaries_index.update_filterable_attributes(
        [
            "userId",
            "quizId",
        ]
    )

    app.state.meilisearch_client = meilisearch_client


def _get_meilisearch_client(request: Request) -> AsyncClient:
    return request.app.state.meilisearch_client


MeilisearchClient = Annotated[AsyncClient, Depends(_get_meilisearch_client)]
