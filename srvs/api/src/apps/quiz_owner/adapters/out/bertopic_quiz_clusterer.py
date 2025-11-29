import asyncio
import logging
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN
from umap import UMAP
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer

from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal

from ...domain.models import Quiz

logger = logging.getLogger(__name__)


class BertopicQuizClusterer:
    def __init__(
        self,
        llm_tools: LLMToolsApp,
        material_app: MaterialApp,
    ):
        self._llm_tools = llm_tools
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
            return []

        embeddings = np.array([c.vector for c in chunks_with_vectors], dtype=np.float32)
        documents = [c.content.strip() for c in chunks_with_vectors]

        n_samples = len(documents)

        if n_samples < quiz.length:
            logger.warning(
                f"Not enough chunks for quiz {quiz.id}: found {n_samples} chunks, "
                f"but quiz length is {quiz.length}. Using all available vectors."
            )
            return embeddings.tolist()

        return await asyncio.to_thread(
            self._run_bertopic, quiz.id, quiz.length, documents, embeddings
        )

    def _run_bertopic(
        self,
        quiz_id: str,
        quiz_length: int,
        documents: list[str],
        embeddings: np.ndarray,
    ) -> list[list[float]]:
        n_samples = len(documents)
        n_features = embeddings.shape[1]

        logger.info(
            f"Starting BERTopic for quiz {quiz_id}: {n_samples} documents, {n_features} embedding dimensions"
        )

        umap_components = min(3, n_samples - 1)
        n_neighbors = min(15, n_samples - 1)
        logger.info(
            f"Configuring UMAP: {n_features} → {umap_components} dimensions (n_neighbors={n_neighbors})"
        )

        umap_model = UMAP(
            n_neighbors=n_neighbors,
            n_components=umap_components,
            min_dist=0.0,
            metric="cosine",
            random_state=505,
        )

        min_cluster_size = max(2, min(15, n_samples // 10))
        logger.info(f"Configuring HDBSCAN: min_cluster_size={min_cluster_size}")

        hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        vectorizer_model = CountVectorizer(
            stop_words="english",
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2),
        )

        ctfidf_model = ClassTfidfTransformer(bm25_weighting=True)

        logger.info(f"Initializing BERTopic for quiz {quiz_id}")
        topic_model = BERTopic(
            embedding_model=self._llm_tools.vectorizer,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=None,
            ctfidf_model=None,
            representation_model=None,
            verbose=False,
            calculate_probabilities=False,
        ).fit(documents, embeddings)

        logger.info(f"Fitting BERTopic on {n_samples} documents for quiz {quiz_id}")
        try:
            # topics, probs = topic_model.transform(documents, embeddings)
            topics = topic_model.topics_
            topic_info = topic_model.get_topic_info()
            n_topics = len(topic_info[topic_info["Topic"] != -1])
            n_outliers = len(topic_info[topic_info["Topic"] == -1])

            logger.info(
                f"BERTopic found {n_topics} topics for quiz {quiz_id} (outliers: {n_outliers})"
            )
           

            logger.info(
                f"🔑 Topic representations for quiz {quiz_id}:"
            )
            for topic_id in sorted(topic_model.get_topics().keys()):
                if topic_id != -1:
                    topic_words = topic_model.get_topic(topic_id)
                    top_5_words = ", ".join([word for word, _ in topic_words[:5]])
                    topic_count = len([t for t in topics if t == topic_id])
                    logger.info(
                        f"  Topic {topic_id} ({topic_count} docs): {top_5_words}"
                    )

            centers = []
            unique_topics = [t for t in np.unique(topics) if t != -1]

            for topic_id in unique_topics:
                topic_mask = topics == topic_id
                topic_embeddings = embeddings[topic_mask]
                center = np.mean(topic_embeddings, axis=0)
                centers.append(center.tolist())
                logger.info(
                    f"Topic {topic_id}: {np.sum(topic_mask)} documents, center computed"
                )

            logger.info(
                f"Final cluster vectors: {len(centers)} vectors for quiz {quiz_id}"
            )

            return centers

        except Exception as e:
            logger.error(
                f"Error running BERTopic for quiz {quiz_id}: {str(e)}", exc_info=True
            )
            logger.warning(f"Falling back to using first {quiz_length} embeddings")
            n_vectors = min(quiz_length, len(embeddings))
            return embeddings[:n_vectors].tolist()
