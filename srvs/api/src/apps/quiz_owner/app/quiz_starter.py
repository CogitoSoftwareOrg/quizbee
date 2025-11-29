import logging

from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.user_owner.domain._in import Principal

from ..domain._in import QuizStarter, GenerateCmd
from ..domain.out import QuizIndexer, QuizRepository, QuizClusterer
from ..domain.models import Quiz
from ..domain.constants import SUMMARY_TOKEN_LIMIT
from ..adapters.out.quiz_preprocesser import QuizPreprocessor

logger = logging.getLogger(__name__)


class QuizStarterImpl(QuizStarter):
    def __init__(
        self,
        llm_tools: LLMToolsApp,
        quiz_repository: QuizRepository,
        material_app: MaterialApp,
        quiz_indexer: QuizIndexer,
        quiz_preprocessor: QuizPreprocessor,
        quiz_clusterer: QuizClusterer,
    ):
        self._llm_tools = llm_tools
        self._material_app = material_app
        self._quiz_indexer = quiz_indexer
        self._quiz_repository = quiz_repository
        self._quiz_preprocessor = quiz_preprocessor
        self._quiz_clusterer = quiz_clusterer

    async def start(self, cmd: GenerateCmd) -> None:
        quiz = await self._quiz_repository.get(cmd.quiz_id)
        quiz.to_preparing()
        await self._quiz_repository.update(quiz)

        logger.info(f"Building table of contents for quiz {quiz.id}")
        await self._build_table_of_contents(quiz, cmd.user)

        topics_vectors = None
        if quiz.query and len(quiz.materials) > 0:
            logger.info(f"Preprocessing query for quiz {quiz.id}")
            topics_vectors = await self._preprocess_query(quiz)

        logger.info(f"Building cluster vectors for quiz {quiz.id}")

        if topics_vectors:
            logger.info(f"Using {len(topics_vectors)} topic vectors from preprocessor")
            quiz.set_cluster_vectors(topics_vectors)
        elif len(quiz.materials) > 0:
            cluster_vectors = await self._quiz_clusterer.cluster(quiz, cmd.user)
            quiz.set_cluster_vectors(cluster_vectors)
        else:
            quiz.set_cluster_vectors([])

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

    async def _build_table_of_contents(self, quiz: Quiz, user: Principal) -> None:
        """
        Build table of contents from materials marked as books.
        Stores TOC in quiz.table_of_contents as {material_id: toc}
        """
        if not quiz.materials:
            logger.info(f"No materials for quiz {quiz.id}, skipping TOC build")
            return

        book_materials = [m for m in quiz.materials if m.is_book]
        if not book_materials:
            logger.info(f"No book materials for quiz {quiz.id}, skipping TOC build")
            return

        logger.info(
            f"Building TOC for quiz {quiz.id} from {len(book_materials)} book materials"
        )

        table_of_contents = {}
        for material_ref in book_materials:
            try:
                material = await self._material_app.get_material(material_ref.id)
                if material and hasattr(material, "contents") and material.contents:
                    table_of_contents[material_ref.id] = material.contents
                    logger.info(
                        f"Added TOC for material {material_ref.id} ({material.title})"
                    )
                else:
                    logger.warning(
                        f"Material {material_ref.id} has no table_of_contents"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to get TOC for material {material_ref.id}: {e}",
                    exc_info=True,
                )

        if table_of_contents:
            quiz.set_table_of_contents(table_of_contents)
            logger.info(
                f"Set TOC for quiz {quiz.id} with {len(table_of_contents)} materials"
            )
        else:
            logger.info(f"No TOC found for quiz {quiz.id}")

    async def _preprocess_query(self, quiz: Quiz) -> list[list[float]] | None:
        """
        Preprocess and enhance the user query using QuizPreprocessor.
        Updates quiz.gen_config with enhanced instructions and topics.
        Returns topic vectors if topics were generated, None otherwise.
        """
        if not quiz.query:
            logger.info(f"No query for quiz {quiz.id}, skipping preprocessing")
            return None

        try:
            cache_key = f"quiz_preprocess_{quiz.id}"
            enhanced_instructions, topics = await self._quiz_preprocessor.enhance_query(
                quiz=quiz,
                cache_key=cache_key,
            )

            if enhanced_instructions:
                quiz.gen_config.additional_instructions.append(enhanced_instructions)
                logger.info(
                    f"Added enhanced instructions to quiz {quiz.id}: {enhanced_instructions}"
                )

            if topics and len(topics) > 0:
                quiz.gen_config.more_on_topic.extend(topics)
                logger.info(f"Added {len(topics)} topics to quiz {quiz.id}: {topics}")

                logger.info(f"Embedding {len(topics)} topics for quiz {quiz.id}")
                topic_vectors = await self._llm_tools.vectorize(topics)
                logger.info(f"Generated {len(topic_vectors)} topic vectors")
                topic_vectors = topic_vectors.tolist()
                return topic_vectors

            logger.info(f"Query preprocessing completed for quiz {quiz.id}")
            return None

        except Exception as e:
            logger.error(
                f"Failed to preprocess query for quiz {quiz.id}: {e}",
                exc_info=True,
            )
            logger.warning(f"Continuing without query preprocessing for quiz {quiz.id}")
            return None
