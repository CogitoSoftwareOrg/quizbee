import logging
from dataclasses import asdict
from typing import Any, AsyncGenerator

from src.apps.v2.user_auth.app.contracts import AuthUserApp
from src.apps.v2.message_owner.app.contracts import MessageOwnerApp, StartMessageCmd
from src.apps.v2.message_owner.domain.models import Message, Role, Status
from src.apps.v2.llm_tools.app.contracts import LLMToolsApp

from ..domain.models import Attempt
from ..domain.refs import MessageRef, MessageRole, MessageStatus, MessageMetadata
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
        message_owner: MessageOwnerApp,
        llm_tools: LLMToolsApp,
    ):
        self.attempt_repository = attempt_repository
        self.user_auth = user_auth
        self.explainer = explainer
        self.message_owner = message_owner
        self.llm_tools = llm_tools

    async def finalize(self, cmd: FinalizeCmd) -> None:
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.token)

    async def ask_explainer(
        self, cmd: AskExplainerCmd
    ) -> AsyncGenerator[AskExplainerOutput, None]:
        logging.info(f"Ask explainer: {cmd.attempt_id}")
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.token)

        ai_message = await self.message_owner.start_message(
            StartMessageCmd(attempt_id=attempt.id)
        )
        ai_message_ref = self._to_message_ref(ai_message)

        item = attempt.get_item(cmd.item_id)

        logging.info(f"Explain attempt: {attempt.id}")
        async for message in self.explainer.explain(
            cmd.query, attempt, item, ai_message_ref, cmd.cache_key
        ):
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

    def _to_message_ref(self, message: Message) -> MessageRef:
        return MessageRef(
            id=message.id,
            attempt_id=message.attempt_id,
            content=message.content,
            role=MessageRole.AI if message.role == Role.AI else MessageRole.USER,
            status=(
                MessageStatus.FINAL
                if message.status == Status.FINAL
                else MessageStatus.STREAMING
            ),
            metadata=MessageMetadata(
                tool_calls=message.metadata.tool_calls,
                tool_results=message.metadata.tool_results,
            ),
        )
