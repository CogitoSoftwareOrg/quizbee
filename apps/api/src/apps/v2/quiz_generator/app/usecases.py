from src.apps.v2.llm_tools.app.contracts import LLMToolsApp
from src.apps.v2.material_search.app.contracts import MaterialSearchApp, SearchCmd

from ..domain.ports import AttemptRepository, QuizIndexer, QuizRepository
from ..domain.models import Quiz, Attempt

from .contracts import GenerateCmd, FinilizeCmd, GenMode, QuizGeneratorApp


class QuizGeneratorAppImpl(QuizGeneratorApp):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        attempt_repository: AttemptRepository,
        quiz_indexer: QuizIndexer,
        llm_tools: LLMToolsApp,
        material_search: MaterialSearchApp,
    ):
        self.quiz_repository = quiz_repository
        self.attempt_repository = attempt_repository
        self.quiz_indexer = quiz_indexer
        self.material_search = material_search
        self.llm_tools = llm_tools

    async def generate(self, cmd: GenerateCmd) -> None:
        pass

    async def finilize(self, cmd: FinilizeCmd) -> None:
        pass

    async def start(self, cmd: GenerateCmd) -> None:
        quiz = await self.quiz_repository.get(cmd.quiz_id)
        quiz.to_preparing()
        await self.quiz_repository.save(quiz)

        attempt = Attempt.create(cmd.quiz_id, cmd.user_id)
        await self.attempt_repository.save(attempt)

        if quiz.need_build_material_content:
            await self._build_material_content(quiz)
            await self.quiz_repository.save(quiz)

        await self._estimate_summary(quiz)
        



    async def _build_material_content(self, quiz: Quiz, token_limit=70_000) -> None:
        chunks = await self.material_search.search(
            SearchCmd(
                query=quiz.query,
                user_id=quiz.author_id,
                material_ids=[m.id for m in quiz.materials],
                limit_tokens=token_limit,
            )
        )
        content = "\n<CHUNK>\n".join([c.content for c in chunks])
        quiz.set_material_content(content)

    async def _estimate_summary(self, quiz: Quiz, token_limit=7_000):
        summary = ""
        text_chunks = quiz.material_content.split("\n<CHUNK>\n")
        for chunk in text_chunks:
            token_limit -= self.llm_tools.count_text(chunk)
            if token_limit < 0:
                break
            summary += f"\n<CHUNK>\n{chunk}"
        quiz.set_summary(summary)
