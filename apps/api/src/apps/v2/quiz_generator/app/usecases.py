import logging

from src.apps.v2.llm_tools.app.contracts import LLMToolsApp
from src.apps.v2.material_search.app.contracts import MaterialSearchApp, SearchCmd
from src.apps.v2.user_auth.app.contracts import Principal

from ..domain.ports import (
    QuizFinalizer,
    PatchGenerator,
    QuizIndexer,
    QuizRepository,
)
from ..domain.models import Quiz, QuizStatus
from ..domain.constants import PATCH_LIMIT
from ..domain.errors import (
    NotQuizOwnerError,
    NotEnoughQuizItemsError,
    QuizNotAnsweredError,
)

from .contracts import (
    GenerateCmd,
    FinalizeQuizCmd,
    GenMode,
    QuizGeneratorApp,
)


class QuizGeneratorAppImpl(QuizGeneratorApp):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        quiz_indexer: QuizIndexer,
        llm_tools: LLMToolsApp,
        material_search: MaterialSearchApp,
        patch_generator: PatchGenerator,
        finalizer: QuizFinalizer,
    ):
        self.quiz_repository = quiz_repository
        self.quiz_indexer = quiz_indexer
        self.material_search = material_search
        self.llm_tools = llm_tools
        self.patch_generator = patch_generator
        self.finalizer = finalizer

    async def generate(self, cmd: GenerateCmd) -> None:
        quiz = await self.quiz_repository.get(cmd.quiz_id)

        if quiz.author_id != cmd.user.id:
            raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)
        stored = cmd.user.remaining
        cost = PATCH_LIMIT
        if cost > cmd.user.remaining:
            raise NotEnoughQuizItemsError(
                quiz_id=cmd.quiz_id,
                user_id=cmd.user.id,
                cost=cost,
                stored=stored,
            )

        if cmd.mode == GenMode.Regenerate:
            logging.info(f"Incrementing generation for quiz {cmd.quiz_id}")
            quiz.increment_generation()
            await self.quiz_repository.save(quiz)

        quiz.generate_patch()
        await self.quiz_repository.save(quiz)

        await self.patch_generator.generate(quiz, cmd.cache_key)

    async def finalize(self, cmd: FinalizeQuizCmd) -> None:
        quiz = await self.quiz_repository.get(cmd.quiz_id)
        if quiz.author_id != cmd.user.id:
            raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

        quiz.to_answered()
        await self.quiz_repository.save(quiz)
        await self.finalizer.finalize(quiz, cmd.cache_key)

        await self.quiz_indexer.index(quiz)

    async def start(self, cmd: GenerateCmd) -> None:
        quiz = await self.quiz_repository.get(cmd.quiz_id)
        quiz.to_preparing()
        await self.quiz_repository.save(quiz)

        if quiz.need_build_material_content:
            await self._build_material_content(quiz, quiz.length * 2000, cmd.user)
            await self.quiz_repository.save(quiz)

        if quiz.avoid_repeat:
            logging.info(f"Avoiding repeat for quiz {quiz.id}")
            await self._estimate_summary(quiz, 7_000)
            similar_quizes = await self.quiz_indexer.search(
                user_id=quiz.author_id,
                query=f"title:{quiz.title} query:{quiz.query} Summary:{quiz.summary}",
                limit=10,
                ratio=0.5,
                threshold=0.4,
            )

            logging.info(
                f"Found {len(similar_quizes)} similar quizes for quiz {quiz.id}"
            )
            if len(similar_quizes) > 0:
                questions = list(
                    set(
                        [
                            q.question
                            for quiz in similar_quizes
                            for q in quiz.items
                            if q.question
                        ]
                    )
                )
                logging.info(
                    f"Adding negative questions for quiz {quiz.id} questions: {len(questions)}"
                )
                quiz.add_negative_questions(questions)
                await self.quiz_repository.save(quiz)

        quiz.to_creating()
        quiz.increment_generation()
        await self.quiz_repository.save(quiz)

        await self.generate(cmd)

    async def _build_material_content(
        self, quiz: Quiz, token_limit: int, user: Principal
    ) -> None:
        logging.info(f"Building material content for quiz {quiz.id}")
        chunks = await self.material_search.search(
            SearchCmd(
                query=quiz.query,
                user=user,
                material_ids=[m.id for m in quiz.materials],
                limit_tokens=token_limit,
            )
        )
        logging.info(f"Found {len(chunks)} chunks for quiz {quiz.id}")
        content = "\n<CHUNK>\n".join([c.content for c in chunks])
        quiz.set_material_content(content)

    async def _estimate_summary(self, quiz: Quiz, token_limit):
        logging.info(f"Estimating summary for quiz {quiz.id}")
        summary = ""
        text_chunks = quiz.material_content.split("\n<CHUNK>\n")
        for chunk in text_chunks:
            token_limit -= self.llm_tools.count_text(chunk)
            if token_limit < 0:
                break
            summary += f"\n<CHUNK>\n{chunk}"
        quiz.set_summary(summary)
