import logging
from typing import Any, AsyncGenerator

from src.apps.v2.user_auth.app.contracts import AuthUserApp, Principal

from ..domain.models import Attempt
from ..domain.ports import AttemptRepository, Explainer
from ..domain.errors import NotAttemptOwnerError, AttemptAlreadyFinalizedError

from .contracts import (
    AskExplainerCmd,
    AskExplainerOutput,
    QuizAttempterApp,
    FinalizeCmd,
)


class QuizAttempterAppImpl(QuizAttempterApp):
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        user_auth: AuthUserApp,
        explainer: Explainer,
    ):
        self.attempt_repository = attempt_repository
        self.user_auth = user_auth
        self.explainer = explainer

    async def finalize(self, cmd: FinalizeCmd) -> None:
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.token)

    async def ask_explainer(
        self, cmd: AskExplainerCmd
    ) -> AsyncGenerator[AskExplainerOutput, None]:
        logging.info(f"Ask explainer: {cmd.attempt_id}")
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.token)

        item = attempt.get_item(cmd.item_id)

        logging.info(f"Explain attempt: {attempt.id}")
        async for message in self.explainer.explain(cmd.query, attempt, item, cache_key):
            logging.info(f"Message: {len(message.content)} chars, id: {message.id}")
            status = "chunk" if message.status == "streaming" else "done"
            yield AskExplainerOutput(
                text=message.content, msg_id=message.id, i=0, status=status
            )

    async def validate_attempt(self, attempt: Attempt, token: str) -> None:
        user = await self.user_auth.validate(token)
        if attempt.user_id != user.id:
            raise NotAttemptOwnerError(
                attempt_id=attempt.id, user_id=user.id, quiz_id=attempt.quiz.id
            )
        if attempt.feedback is not None:
            raise AttemptAlreadyFinalizedError(
                attempt_id=attempt.id, user_id=user.id, quiz_id=attempt.quiz.id
            )
