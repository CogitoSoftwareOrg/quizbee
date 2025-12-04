import asyncio
import logging
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_distances

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

    async def cluster(
        self, quiz: Quiz, user: Principal, chunks_per_question: int
    ) -> tuple[list[list[float]], list[float]]:
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                all_chunks=True,
            )
        )
        logger.info(f"Found {len(chunks)} chunks for quiz {quiz.id}")

        chunks_with_vectors = [
            c
            for c in chunks
            if c.vector is not None and c.content and c.content.strip()
        ]
        logger.info(
            f"Found {len(chunks_with_vectors)} chunks with vectors and content for quiz {quiz.id}"
        )

        if not chunks_with_vectors:
            logger.warning(
                f"No valid chunks found for quiz {quiz.id}, returning empty cluster vectors"
            )
            return [], []

        embeddings = np.array([c.vector for c in chunks_with_vectors], dtype=np.float32)
        n_samples = len(chunks_with_vectors)

        

        if n_samples < quiz.length:
            logger.warning(
                f"Not enough chunks for quiz {quiz.id}: found {n_samples} chunks, "
                f"but quiz length is {quiz.length}. Using all available vectors."
            )
            centers = embeddings.tolist()
            thresholds = [1.0] * n_samples
            return self._reorder_clusters(centers, thresholds)

        return await asyncio.to_thread(
            self._run_clustering, quiz.id, quiz.length, embeddings
        )

    def _run_clustering(
        self,
        quiz_id: str,
        quiz_length: int,
        embeddings: np.ndarray,
    ) -> tuple[list[list[float]], list[float]]:
        n_samples = embeddings.shape[0]
        n_features = embeddings.shape[1]
        n_clusters = min(quiz_length, n_samples)

        logger.info(
            f"Starting PCA+KMeans for quiz {quiz_id}: {n_samples} documents, {n_features} embedding dimensions"
        )

        pca_components = min(50, n_samples - 1, n_features)
        logger.info(f"Configuring PCA: {n_features} → {pca_components} dimensions")

        pca = PCA(n_components=pca_components, random_state=505)
        reduced_embeddings = pca.fit_transform(embeddings)

        logger.info(f"Configuring KMeans: n_clusters={n_clusters}")

        if n_samples > 1000:
            reassignment_ratio = 0.0
        elif n_samples < 50:
            reassignment_ratio = 0.07
        else:
            reassignment_ratio = 0.01

        kmeans = MiniBatchKMeans(
            n_clusters=n_clusters,
            reassignment_ratio=reassignment_ratio,
            random_state=505,
            batch_size=min(256, n_samples),
            n_init=3,
        )

        try:
            labels = kmeans.fit_predict(reduced_embeddings)

            unique_clusters = np.unique(labels)
            logger.info(f"KMeans found {len(unique_clusters)} clusters for quiz {quiz_id}")

            logger.info(f"🔑 Cluster analysis for quiz {quiz_id}:")

            centers = []
            thresholds = []

            for cluster_id in sorted(unique_clusters):
                cluster_mask = labels == cluster_id
                cluster_embeddings = embeddings[cluster_mask]
                cluster_count = int(np.sum(cluster_mask))

                center = np.mean(cluster_embeddings, axis=0)
                center_normalized = center / np.linalg.norm(center)

                embeddings_normalized = cluster_embeddings / np.linalg.norm(
                    cluster_embeddings, axis=1, keepdims=True
                )
                cosine_similarities = np.dot(embeddings_normalized, center_normalized)

                min_similarity = float(np.min(cosine_similarities))
                margin = 0.1
                threshold = min_similarity - margin

                centers.append(center.tolist())
                thresholds.append(threshold)

                logger.info(
                    f"  Cluster {cluster_id} ({cluster_count} docs): threshold={threshold:.4f} (min={min_similarity:.4f})"
                )

            # Reorder to maximize distance between adjacent clusters
            if n_samples < quiz_length * 4:
                centers, thresholds = self._reorder_clusters(centers, thresholds)

            logger.info(
                f"Final cluster vectors: {len(centers)} vectors, "
                f"thresholds: {[f'{t:.4f}' for t in thresholds]} for quiz {quiz_id}"
            )

            return centers, thresholds

        except Exception as e:
            logger.error(
                f"Error running PCA+KMeans for quiz {quiz_id}: {str(e)}", exc_info=True
            )
            logger.warning(f"Falling back to using first {quiz_length} embeddings")
            n_vectors = min(quiz_length, len(embeddings))
            return embeddings[:n_vectors].tolist(), []

    def _reorder_clusters(
        self, centers: list[list[float]], thresholds: list[float]
    ) -> tuple[list[list[float]], list[float]]:
        n = len(centers)
        if n < 2:
            return centers, thresholds

        # Calculate distance matrix
        dists = cosine_distances(np.array(centers))

        # Greedy farthest traversal
        path = [0]
        visited = {0}

        for _ in range(n - 1):
            current = path[-1]
            # Find unvisited node with max distance
            candidates = [i for i in range(n) if i not in visited]
            # dists[current, i] is the distance
            next_idx = max(candidates, key=lambda i: dists[current, i])
            path.append(next_idx)
            visited.add(next_idx)

        logger.info(f"Reordered clusters for separation: {path}")

        return [centers[i] for i in path], [thresholds[i] for i in path]
