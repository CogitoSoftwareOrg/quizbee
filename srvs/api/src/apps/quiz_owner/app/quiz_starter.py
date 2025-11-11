import logging
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from hdbscan import HDBSCAN
from umap import UMAP

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal

from ..domain._in import QuizStarter, GenerateCmd
from ..domain.out import QuizIndexer, QuizRepository
from ..domain.models import Quiz
from ..domain.constants import SUMMARY_TOKEN_LIMIT

logger = logging.getLogger(__name__)


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
        Build cluster vectors using BERTopic-like algorithm:
        1. Get embeddings from chunks
        2. Reduce dimensionality with UMAP to 5 dimensions
        3. Cluster with HDBSCAN
        4. Extract topic representations with CountVectorizer + TF-IDF
        """
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                all_chunks=True,
            )
        )
        
        # Filter chunks with vectors
        chunks_with_vectors = [c for c in chunks if c.vector is not None]
        logger.info(f"Found {len(chunks_with_vectors)} chunks with vectors for quiz {quiz.id}")
        if not chunks_with_vectors:
            logger.warning(f"No vectors found for quiz {quiz.id}, setting empty cluster vectors")
            quiz.set_cluster_vectors([])
            return
        
        vectors = np.array([c.vector for c in chunks_with_vectors], dtype=np.float32)
        n_samples = len(vectors)
        n_features = vectors.shape[1]
        
        logger.info(f"Starting dimensionality reduction for quiz {quiz.id}: {n_samples} samples, {n_features} features")
        
        # If not enough chunks, use all available vectors
        if n_samples < quiz.length:
            logger.warning(
                f"Not enough chunks for quiz {quiz.id}: found {n_samples} chunks, "
                f"but quiz length is {quiz.length}. Using all available vectors."
            )
            quiz.set_cluster_vectors(vectors.tolist())
            return
        
        # Step 1: Reduce with UMAP to 5 dimensions
        umap_components = min(5, n_samples - 1)
        n_neighbors = min(15, n_samples - 1)
        logger.info(f"Step 1: UMAP reducing from {n_features} to {umap_components} components (n_neighbors={n_neighbors}) for quiz {quiz.id}")
        
        umap_model = UMAP(
            n_neighbors=n_neighbors,
            n_components=umap_components,
            min_dist=0.0,
            metric='cosine',
            random_state=505
        )
        reduced_vectors = umap_model.fit_transform(vectors)
        logger.info(f"UMAP complete: {reduced_vectors.shape[0]} samples × {reduced_vectors.shape[1]} dimensions")
        
        # Step 2: Cluster with HDBSCAN
        min_cluster_size = max(2, min(15, n_samples // 10))
        logger.info(f"Step 2: Clustering with HDBSCAN (min_cluster_size={min_cluster_size}) for quiz {quiz.id}")
        
        hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=False
        )
        cluster_labels = hdbscan_model.fit_predict(reduced_vectors)
        
        unique_clusters = [label for label in np.unique(cluster_labels) if label != -1]
        n_clusters = len(unique_clusters)
        
        logger.info(f"Found {n_clusters} clusters for quiz {quiz.id} (noise points: {np.sum(cluster_labels == -1)})")
        
        if n_clusters == 0:
            logger.warning(f"HDBSCAN found no clusters for quiz {quiz.id}, using all vectors")
            n_vectors = min(quiz.length, len(vectors))
            quiz.set_cluster_vectors(vectors[:n_vectors].tolist())
            return
        
        # Step 3: Extract topic representations using CountVectorizer + TF-IDF
        # Group chunks by cluster
        cluster_documents = {}
        for idx, label in enumerate(cluster_labels):
            if label != -1:  # Skip noise points
                if label not in cluster_documents:
                    cluster_documents[label] = []
                chunk_content = chunks_with_vectors[idx].content
                # Log first few chunks to see what we're getting
                if len(cluster_documents[label]) < 3:
                    content_preview = (chunk_content[:100] if chunk_content else "(empty)").replace('\n', ' ')
                    logger.info(f"  Chunk sample for cluster {label}: '{content_preview}...' (len={len(chunk_content) if chunk_content else 0})")
                cluster_documents[label].append(chunk_content)
        
        logger.info(f"Grouped chunks into {len(cluster_documents)} clusters for quiz {quiz.id}")
        for label, docs in cluster_documents.items():
            # Count non-empty chunks
            non_empty = sum(1 for d in docs if d and d.strip())
            total_content_chars = sum(len(d) for d in docs if d)
            logger.info(f"  Cluster {label}: {len(docs)} chunks ({non_empty} non-empty, {total_content_chars} total chars)")
        
        # Combine all documents in each cluster into one document, filtering empty ones
        cluster_texts = []
        for label in sorted(cluster_documents.keys()):
            # Filter out empty or whitespace-only chunks
            non_empty_chunks = [chunk.strip() for chunk in cluster_documents[label] if chunk and chunk.strip()]
            if non_empty_chunks:
                cluster_text = " ".join(non_empty_chunks)
                cluster_texts.append(cluster_text)
                logger.info(f"  Cluster {label} combined text: {len(non_empty_chunks)} chunks → {len(cluster_text)} chars")
            else:
                logger.warning(f"  Cluster {label} has no non-empty chunks, skipping")
        
        if not cluster_texts:
            logger.warning(f"No non-empty cluster texts generated for quiz {quiz.id}")
            quiz.set_cluster_vectors(vectors[:min(quiz.length, len(vectors))].tolist())
            return
        
        # Debug: Log cluster text statistics
        total_chars = sum(len(text) for text in cluster_texts)
        avg_chars = total_chars / len(cluster_texts) if cluster_texts else 0
        logger.info(f"Cluster texts stats for quiz {quiz.id}: {len(cluster_texts)} clusters, {total_chars} total chars, {avg_chars:.0f} avg chars per cluster")
        
        # Log preview of each cluster text
        for idx, text in enumerate(cluster_texts):
            text_preview = text[:150].replace('\n', ' ') if text else "(empty)"
            logger.info(f"  Cluster {idx} preview ({len(text)} chars): {text_preview}...")
        
        # Apply CountVectorizer with multiple fallback strategies
        # Try with English stop words first, if that fails, try without stop words
        vectorizer = CountVectorizer(
            max_features=100,  # Top 100 words per topic
            stop_words='english',
            min_df=1,
            max_df=0.95,
            token_pattern=r'(?u)\b\w+\b',  # Match words with 1+ characters (more permissive)
            lowercase=True
        )
        
        topic_extraction_successful = False
        
        try:
            logger.info(f"Attempting topic extraction with English stop words for quiz {quiz.id}")
            word_counts = vectorizer.fit_transform(cluster_texts)
            logger.info(f"Vocabulary size: {len(vectorizer.get_feature_names_out())} words")
            
            # Apply TF-IDF (class-based TF-IDF as per BERTopic)
            tfidf = TfidfTransformer()
            tfidf_matrix = tfidf.fit_transform(word_counts)
            
            # Get feature names (words)
            feature_names = vectorizer.get_feature_names_out()
            logger.info(f"Sample vocabulary (first 10 words): {', '.join(feature_names[:10])}")
            
            # Extract top N words per cluster to represent topics
            n_words = 10
            topic_words = {}
            
            logger.info(f"Extracted topic representations for quiz {quiz.id}:")
            for cluster_idx in range(tfidf_matrix.shape[0]):
                # Get top words for this cluster
                top_indices = tfidf_matrix[cluster_idx].toarray()[0].argsort()[-n_words:][::-1]
                top_words = [feature_names[i] for i in top_indices]
                cluster_label = sorted(cluster_documents.keys())[cluster_idx]
                topic_words[cluster_label] = top_words
                
                # Log the topic name (top 5 words that represent this topic)
                topic_name = ', '.join(top_words[:5])
                logger.info(f"  Topic {cluster_label}: {topic_name}")
            
            # Log summary of all topics
            all_topic_names = [', '.join(words[:3]) for words in topic_words.values()]
            logger.info(f"Summary - {len(topic_words)} topics found for quiz {quiz.id}: {' | '.join(all_topic_names)}")
            topic_extraction_successful = True
            
        except ValueError as e:
            if "empty vocabulary" in str(e):
                # Retry without stop words (might be non-English content or very technical)
                logger.warning(f"Empty vocabulary with English stop words for quiz {quiz.id}: {str(e)}")
                logger.info(f"Retrying without stop words for quiz {quiz.id}")
                try:
                    vectorizer_no_stop = CountVectorizer(
                        max_features=100,
                        min_df=1,
                        max_df=0.95,
                        token_pattern=r'(?u)\b\w+\b',  # Match any word characters
                        lowercase=True
                    )
                    word_counts = vectorizer_no_stop.fit_transform(cluster_texts)
                    logger.info(f"Vocabulary size (no stop words): {len(vectorizer_no_stop.get_feature_names_out())} words")
                    
                    tfidf = TfidfTransformer()
                    tfidf_matrix = tfidf.fit_transform(word_counts)
                    feature_names = vectorizer_no_stop.get_feature_names_out()
                    logger.info(f"Sample vocabulary (first 10 words): {', '.join(feature_names[:10])}")
                    
                    n_words = 10
                    logger.info(f"Extracted topic representations for quiz {quiz.id} (without stop words):")
                    for cluster_idx in range(tfidf_matrix.shape[0]):
                        top_indices = tfidf_matrix[cluster_idx].toarray()[0].argsort()[-n_words:][::-1]
                        top_words = [feature_names[i] for i in top_indices]
                        cluster_label = sorted(cluster_documents.keys())[cluster_idx]
                        topic_name = ', '.join(top_words[:5])
                        logger.info(f"  Topic {cluster_label}: {topic_name}")
                    topic_extraction_successful = True
                except ValueError as e2:
                    # Last resort: try with character n-grams
                    logger.warning(f"Still empty vocabulary without stop words for quiz {quiz.id}: {str(e2)}")
                    logger.info(f"Trying character n-grams for quiz {quiz.id}")
                    try:
                        vectorizer_chars = CountVectorizer(
                            max_features=50,
                            analyzer='char_wb',  # Character n-grams within word boundaries
                            ngram_range=(3, 6),  # 3-6 character sequences
                            min_df=1
                        )
                        word_counts = vectorizer_chars.fit_transform(cluster_texts)
                        feature_names = vectorizer_chars.get_feature_names_out()
                        logger.info(f"Character n-gram vocabulary size: {len(feature_names)} patterns")
                        
                        logger.info(f"Extracted character-based patterns for quiz {quiz.id}:")
                        for cluster_idx, cluster_label in enumerate(sorted(cluster_documents.keys())):
                            top_indices = word_counts[cluster_idx].toarray()[0].argsort()[-5:][::-1]
                            top_patterns = [feature_names[i] for i in top_indices if word_counts[cluster_idx, i] > 0]
                            if top_patterns:
                                logger.info(f"  Cluster {cluster_label}: {', '.join(top_patterns)}")
                        topic_extraction_successful = True
                    except Exception as e3:
                        logger.error(f"Failed all topic extraction methods for quiz {quiz.id}: {str(e3)}")
                        # Log sample of cluster texts for debugging
                        logger.info(f"Cluster text samples for debugging:")
                        for idx, text in enumerate(cluster_texts[:2]):
                            preview = text[:300] if text else "(empty)"
                            logger.info(f"  Cluster {idx} ({len(text)} chars): {preview}")
                except Exception as e2:
                    logger.error(f"Unexpected error without stop words for quiz {quiz.id}: {str(e2)}")
            else:
                logger.error(f"ValueError in topic extraction for quiz {quiz.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error extracting topic words for quiz {quiz.id}: {str(e)}")
        
        if not topic_extraction_successful:
            logger.warning(f"Could not extract meaningful topics for quiz {quiz.id}, proceeding with cluster vectors only")
        
        # Step 4: Get representative vectors for each cluster (centroids)
        # Even though HDBSCAN doesn't assume centroid-based clusters,
        # we still need representative vectors for the quiz generation
        centers = []
        for label in unique_clusters:
            cluster_mask = cluster_labels == label
            cluster_vectors = vectors[cluster_mask]
            # Use mean as representative vector
            center = np.mean(cluster_vectors, axis=0)
            centers.append(center.tolist())
        
        # If we have fewer clusters than desired quiz length, pad with additional vectors
        if len(centers) < quiz.length:
            logger.info(
                f"Only {len(centers)} clusters found, but quiz length is {quiz.length}. "
                f"Adding additional representative vectors."
            )
            # Add noise points' vectors if available
            noise_mask = cluster_labels == -1
            if np.any(noise_mask):
                noise_vectors = vectors[noise_mask]
                additional_needed = quiz.length - len(centers)
                centers.extend(noise_vectors[:additional_needed].tolist())
        
        # If we still need more, sample from existing vectors
        if len(centers) < quiz.length:
            additional_needed = quiz.length - len(centers)
            remaining_vectors = [v.tolist() for v in vectors if v.tolist() not in centers]
            centers.extend(remaining_vectors[:additional_needed])
        
        # Limit to quiz length
        centers = centers[:quiz.length]
        
        quiz.set_cluster_vectors(centers)

    async def _build_quiz_summary(self, quiz: Quiz, user: Principal) -> None:
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                limit_tokens=SUMMARY_TOKEN_LIMIT,
                vectors = quiz.cluster_vectors,
            )
        )
        summary = "\n<CHUNK>\n".join([c.content for c in chunks])
        quiz.set_summary(summary)
        
        # Отмечаем использованные чанки
        chunk_ids = [c.id for c in chunks]
        await self._material_app.mark_chunks_as_used(chunk_ids)
        logger.info(f"Marked {len(chunk_ids)} chunks as used for quiz {quiz.id}")

    def _build_query(self, quiz: Quiz):
        return f"""
Quiz title: {quiz.title}
Query: {quiz.query}
Summary: {quiz.summary}    
"""
