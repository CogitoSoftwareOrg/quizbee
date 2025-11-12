import logging
import numpy as np
import voyageai
from sklearn.feature_extraction.text import CountVectorizer
from hdbscan import HDBSCAN
from umap import UMAP
from bertopic import BERTopic
from bertopic.backend import BaseEmbedder
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance

from src.lib.config import LLMS
from src.lib.settings import settings
from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal

from ..domain._in import QuizStarter, GenerateCmd
from ..domain.out import QuizIndexer, QuizRepository
from ..domain.models import Quiz
from ..domain.constants import SUMMARY_TOKEN_LIMIT

logger = logging.getLogger(__name__)


class VoyageEmbedder(BaseEmbedder):
    """Voyage AI embedder for BERTopic - inherits from BaseEmbedder"""
    
    def __init__(self, model: str = "voyage-3.5-lite", api_key: str | None = None):
        super().__init__()
        self.client = voyageai.Client(api_key=api_key or settings.voyage_api_key)
        self.model = model
    
    def embed(self, documents: list[str], verbose: bool = False) -> np.ndarray:
        """Synchronous embed method required by BaseEmbedder"""
        if not documents:
            return np.array([], dtype=np.float32)
        
        batch_size = 128
        all_embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            result = self.client.embed(
                batch,
                model=self.model,
                input_type="document",
            )
            all_embeddings.extend(result.embeddings)
        
        embeddings = np.array(all_embeddings, dtype=np.float32)
        return embeddings


class QuizStarterImpl(QuizStarter):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        material_app: MaterialApp,
        quiz_indexer: QuizIndexer,
    ):
        self._material_app = material_app
        self._quiz_indexer = quiz_indexer
        self._quiz_repository = quiz_repository

    async def start(self, cmd: GenerateCmd) -> None:
        quiz = await self._quiz_repository.get(cmd.quiz_id)
        quiz.to_preparing()
        await self._quiz_repository.update(quiz)

        logger.info(f"Building cluster vectors for quiz {quiz.id}")
        await self._build_cluster_vectors(quiz, cmd.user)
        if quiz.avoid_repeat:
            logger.info(f"Building quiz summary for quiz {quiz.id}")
            await self._build_quiz_summary(quiz, cmd.user)

            logger.info(f"Searching for similar quizes for quiz {quiz.id}")
            similar_quizes = await self._quiz_indexer.search(
                user_id=quiz.author_id,
                query=self._build_query(quiz),
                limit=10,
                ratio=0.5,
                threshold=0.0,
            )

            logger.info(
                f"Found {len(similar_quizes)} similar quizes for quiz {quiz.id}"
            )

            quiz.merge_similar_quizes(similar_quizes)

        quiz.to_creating()
        quiz.increment_generation()
        await self._quiz_repository.update(quiz)

    async def _build_cluster_vectors(self, quiz: Quiz, user: Principal) -> None:
        """
        Build cluster vectors using BERTopic algorithm with pre-computed embeddings:
        1. Get embeddings from chunks (already computed)
        2. Use BERTopic with UMAP + HDBSCAN for clustering
        3. Extract topic representations with c-TF-IDF
        """
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                all_chunks=True,
            )
        )
        
        # Filter chunks with vectors and content
        chunks_with_vectors = [c for c in chunks if c.vector is not None and c.content and c.content.strip()]
        logger.info(f"Found {len(chunks_with_vectors)} chunks with vectors and content for quiz {quiz.id}")
        
        if not chunks_with_vectors:
            logger.warning(f"No valid chunks found for quiz {quiz.id}, setting empty cluster vectors")
            quiz.set_cluster_vectors([])
            return
        
        # Extract embeddings and documents
        embeddings = np.array([c.vector for c in chunks_with_vectors], dtype=np.float32)
        documents = [c.content.strip() for c in chunks_with_vectors]
        
        n_samples = len(documents)
        n_features = embeddings.shape[1]
        
        logger.info(f"Starting BERTopic for quiz {quiz.id}: {n_samples} documents, {n_features} embedding dimensions")
        
        # If not enough chunks, use all available vectors
        if n_samples < quiz.length:
            logger.warning(
                f"Not enough chunks for quiz {quiz.id}: found {n_samples} chunks, "
                f"but quiz length is {quiz.length}. Using all available vectors."
            )
            quiz.set_cluster_vectors(embeddings.tolist())
            return
        
        # Configure BERTopic components
        # Step 1: UMAP for dimensionality reduction
        umap_components = min(5, n_samples - 1)
        n_neighbors = min(15, n_samples - 1)
        logger.info(f"Configuring UMAP: {n_features} → {umap_components} dimensions (n_neighbors={n_neighbors})")
        
        umap_model = UMAP(
            n_neighbors=n_neighbors,
            n_components=umap_components,
            min_dist=0.0,
            metric='cosine',
            random_state=505
        )
        
        # Step 2: HDBSCAN for clustering
        min_cluster_size = max(2, min(15, n_samples // 10))
        logger.info(f"Configuring HDBSCAN: min_cluster_size={min_cluster_size}")
        
        hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )
        
        # Step 3: CountVectorizer for tokenization
        vectorizer_model = CountVectorizer(
            stop_words='english',
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2)  # unigrams and bigrams
        )
        
        # Step 4: c-TF-IDF for topic representation
        ctfidf_model = ClassTfidfTransformer(bm25_weighting=True)
        
        # Step 5: Create Voyage AI embedder for representation models
        voyage_embedder = VoyageEmbedder(
            model="voyage-3.5-lite",
            api_key=settings.voyageai_api_key
        )
        
        # Step 6: Configure multi-aspect topic representations
        main_representation = KeyBERTInspired(
            top_n_words=10,
            nr_repr_docs=5,
            nr_samples=min(500, n_samples),
            nr_candidate_words=100,
            random_state=42
        )
        
        aspect_representation = MaximalMarginalRelevance(diversity=0.3)
        
        representation_model = {
            "Main": main_representation,
            # "Diversity": aspect_representation,
        }
       
        
        logger.info(f"Configured multi-aspect representations for quiz {quiz.id}")
        logger.info(f"  - Main: KeyBERTInspired (top_n_words=10)")
        logger.info(f"  - Diversity: MaximalMarginalRelevance (diversity=0.5)")
        
        # Initialize BERTopic with pre-computed embeddings
        logger.info(f"Initializing BERTopic for quiz {quiz.id}")
        topic_model = BERTopic(
            embedding_model=voyage_embedder,
            min_topic_size=25, # можно как то по умному ставить, ПОКА ЧТО ПОЧЕМУ ТО НЕ РАБОТАЕТ 
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            ctfidf_model=ctfidf_model,
            representation_model=representation_model,
            verbose=True,
            calculate_probabilities=True
        ).fit(documents, embeddings)
        
        # Fit BERTopic with pre-computed embeddings
        logger.info(f"Fitting BERTopic on {n_samples} documents for quiz {quiz.id}")
        try:
    
            topics, probs = topic_model.transform(documents, embeddings)
            # Get topic info
            topic_info = topic_model.get_topic_info()
            n_topics = len(topic_info[topic_info['Topic'] != -1])
            n_outliers = len(topic_info[topic_info['Topic'] == -1])
            
            logger.info(f"BERTopic found {n_topics} topics for quiz {quiz.id} (outliers: {n_outliers})")
            logger.info(f"Topic distribution:\n{topic_info.to_string()}")
            
            logger.info(f"🔑 KeyBERT-enhanced topic representations for quiz {quiz.id}:")
            for topic_id in sorted(topic_model.get_topics().keys()):
                if topic_id != -1:
                    topic_words = topic_model.get_topic(topic_id)
                    top_5_words = ', '.join([word for word, _ in topic_words[:5]])
                    
                    topic_count = len([t for t in topics if t == topic_id])
                    
                    logger.info(
                        f"  Topic {topic_id} ({topic_count} docs): {top_5_words}"
                    )
            
            # Get representative vectors for each topic (centroids of documents in each topic)
            centers = []
            unique_topics = [t for t in np.unique(topics) if t != -1]
            
            for topic_id in unique_topics:
                topic_mask = topics == topic_id
                topic_embeddings = embeddings[topic_mask]
                # Use mean as representative vector
                center = np.mean(topic_embeddings, axis=0)
                centers.append(center.tolist())
                logger.info(f"Topic {topic_id}: {np.sum(topic_mask)} documents, center computed")
            
            # If we have fewer topics than desired quiz length, add outlier vectors
            if len(centers) < quiz.length:
                logger.info(
                    f"Only {len(centers)} topics found, but quiz length is {quiz.length}. "
                    f"Adding outlier vectors."
                )
                outlier_mask = topics == -1
                if np.any(outlier_mask):
                    outlier_embeddings = embeddings[outlier_mask]
                    additional_needed = quiz.length - len(centers)
                    centers.extend(outlier_embeddings[:additional_needed].tolist())
                    logger.info(f"Added {min(additional_needed, len(outlier_embeddings))} outlier vectors")
            
            # If still need more, sample from existing vectors
            if len(centers) < quiz.length:
                additional_needed = quiz.length - len(centers)
                remaining_vectors = [v.tolist() for v in embeddings if v.tolist() not in centers]
                centers.extend(remaining_vectors[:additional_needed])
                logger.info(f"Added {min(additional_needed, len(remaining_vectors))} additional vectors")
            
            # Limit to quiz length
            centers = centers[:quiz.length]
            logger.info(f"Final cluster vectors: {len(centers)} vectors for quiz {quiz.id}")
            
            quiz.set_cluster_vectors(centers)
            
        except Exception as e:
            logger.error(f"Error running BERTopic for quiz {quiz.id}: {str(e)}", exc_info=True)
            # Fallback: use first N embeddings
            logger.warning(f"Falling back to using first {quiz.length} embeddings")
            n_vectors = min(quiz.length, len(embeddings))
            quiz.set_cluster_vectors(embeddings[:n_vectors].tolist())

    async def _build_quiz_summary(self, quiz: Quiz, user: Principal) -> None:
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                limit_tokens=SUMMARY_TOKEN_LIMIT,
                vectors=quiz.cluster_vectors,
            )
        )
        summary = "\n<CHUNK>\n".join([c.content for c in chunks])
        quiz.set_summary(summary)

        # Отмечаем использованные чанки
        # chunk_ids = [c.id for c in chunks]
        # await self._material_app.mark_chunks_as_used(chunk_ids)
        # logger.info(f"Marked {len(chunk_ids)} chunks as used for quiz {quiz.id}")

    def _build_query(self, quiz: Quiz):
        return f"""
Quiz title: {quiz.title}
Query: {quiz.query}
Summary: {quiz.summary}    
"""
