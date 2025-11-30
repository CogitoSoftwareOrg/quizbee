import asyncio
import logging
import numpy as np
from sklearn.cluster import MiniBatchKMeans

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal

from ...domain.models import Quiz

logger = logging.getLogger(__name__)


class KMeansQuizClusterer:
    def __init__(
        self,
        material_app: MaterialApp,
    ):
        self._material_app = material_app

    async def cluster(self, quiz: Quiz, user: Principal) -> list[list[float]]:
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                all_chunks=True,
            )
        )

        chunks_with_vectors = [
            c for c in chunks if c.vector is not None
        ]
        logger.info(
            f"Found {len(chunks_with_vectors)} chunks with vectors for quiz {quiz.id}"
        )

        if not chunks_with_vectors:
            logger.warning(
                f"No valid chunks found for quiz {quiz.id}, returning empty cluster vectors"
            )
            return []

        embeddings = np.array([c.vector for c in chunks_with_vectors], dtype=np.float32)
        n_samples = len(chunks_with_vectors)

        if n_samples < quiz.length:
            logger.warning(
                f"Not enough chunks for quiz {quiz.id}: found {n_samples} chunks, "
                f"but quiz length is {quiz.length}. Using all available vectors."
            )
            return embeddings.tolist()

        return await asyncio.to_thread(
            self._run_clustering, quiz.id, quiz.length, embeddings
        )

    def _run_clustering(
        self,
        quiz_id: str,
        quiz_length: int,
        embeddings: np.ndarray,
    ) -> list[list[float]]:
        n_samples = embeddings.shape[0]
        n_clusters = min(quiz_length, n_samples)

        logger.info(
            f"Starting KMeans clustering for quiz {quiz_id}: {n_samples} documents → {n_clusters} clusters"
        )

        kmeans = MiniBatchKMeans(
            n_clusters=n_clusters,
            random_state=505,
            batch_size=min(256, n_samples),
            n_init=3,
        )
        kmeans.fit(embeddings)

        centers = kmeans.cluster_centers_.tolist()

        logger.info(f"Calculated {len(centers)} cluster centers for quiz {quiz_id}")

        return centers
