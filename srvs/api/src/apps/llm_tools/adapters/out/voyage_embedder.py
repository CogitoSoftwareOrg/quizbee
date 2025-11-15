import numpy as np
from bertopic.backend import BaseEmbedder
from voyageai.client import Client
from voyageai.client_async import AsyncClient

from src.lib.settings import settings

from ...domain.out import Vectorizer

BATCH_SIZE = 128


class VoyageEmbedder(Vectorizer, BaseEmbedder):
    """Voyage AI embedder for BERTopic - inherits from BaseEmbedder"""

    def __init__(self, model: str = "voyage-3.5-lite"):
        super().__init__()

        self._client = Client(api_key=settings.voyageai_api_key)
        self._aclient = AsyncClient(api_key=settings.voyageai_api_key)
        self._model = model

    async def vectorize(self, chunks: list[str], verbose: bool = False) -> np.ndarray:
        """Synchronous embed method required by BaseEmbedder"""
        if not chunks:
            return np.array([], dtype=np.float32)

        all_embeddings = []

        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            result = await self._aclient.embed(
                batch,
                model=self._model,
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)

        embeddings = np.array(all_embeddings, dtype=np.float32)
        return embeddings

    def embed(self, documents: list[str], verbose: bool = False) -> np.ndarray:
        """Synchronous embed method required by BaseEmbedder"""
        if not documents:
            return np.array([], dtype=np.float32)

        all_embeddings = []

        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i : i + BATCH_SIZE]
            result = self._client.embed(
                batch,
                model=self._model,
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)

        embeddings = np.array(all_embeddings, dtype=np.float32)
        return embeddings
