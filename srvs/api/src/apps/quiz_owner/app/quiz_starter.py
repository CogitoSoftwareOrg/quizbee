import logging
import numpy as np
from sklearn.cluster import KMeans

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
        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                all_chunks=True,
            )
        )
        
        # Сразу фильтруем и конвертируем в numpy - одна итерация вместо двух
        vector_list = [c.vector for c in chunks if c.vector is not None]
        
        if not vector_list:
            quiz.set_cluster_vectors([])
            return
        
        vectors = np.array(vector_list, dtype=np.float32)  # float32 вместо float64 - экономия памяти в 2 раза
        n_clusters = min(quiz.length, len(vectors))
        
        if n_clusters == len(vectors):
            # If we need as many clusters as vectors, just use the vectors
            centers = vectors.tolist()
        else:
            # Perform KMeans clustering
            # max_iter=200 вместо дефолтных 300 - быстрее
            # algorithm='elkan' - быстрее для плотных данных (embeddings)
            kmeans = KMeans(
                n_clusters=n_clusters, 
                random_state=505, 
                n_init=10,
                max_iter=200,
                algorithm='elkan'
            )
            kmeans.fit(vectors)
            centers = kmeans.cluster_centers_.tolist()

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

    def _build_query(self, quiz: Quiz):
        return f"""
Quiz title: {quiz.title}
Query: {quiz.query}
Summary: {quiz.summary}    
"""
