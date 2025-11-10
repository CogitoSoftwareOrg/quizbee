import logging
from src.apps.material_owner.domain._in import MaterialApp

from src.apps.quiz_owner.domain._in import GenMode, GenerateCmd, QuizGenerator
from src.apps.quiz_owner.domain.errors import NotQuizOwnerError
from src.apps.quiz_owner.domain.out import PatchGenerator, QuizIndexer, QuizRepository

logger = logging.getLogger(__name__)


class QuizGeneratorImpl(QuizGenerator):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        quiz_indexer: QuizIndexer,
        material_app: MaterialApp,
        patch_generator: PatchGenerator,
    ):
        self._quiz_repository = quiz_repository
        self._quiz_indexer = quiz_indexer
        self._material_app = material_app
        self._patch_generator = patch_generator

    async def generate(self, cmd: GenerateCmd) -> None:
        quiz = await self._quiz_repository.get(cmd.quiz_id)
        if quiz.author_id != cmd.user.id:
            raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

        if cmd.mode == GenMode.Regenerate:
            logger.info(f"Incrementing generation for quiz {cmd.quiz_id}")
            quiz.increment_generation()
            await self._quiz_repository.update(quiz)

        ready_items = quiz.generate_patch()
        if len(ready_items) == 0:
            logging.warning(
                f"No items ready for generation in quiz {cmd.quiz_id}. "
                f"All items may be FINAL or there are no items."
            )
            return

        await self._patch_generator.generate(quiz, cmd.cache_key)
