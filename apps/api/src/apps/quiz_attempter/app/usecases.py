import logging
from typing import AsyncGenerator

from src.apps.user_auth.app.contracts import AuthUserApp, Principal
from src.apps.message_owner.app.contracts import (
    MessageOwnerApp,
    StartMessageCmd,
    GetAttemptHistoryCmd,
    FinalizeMessageCmd,
)
from src.apps.message_owner.domain.models import (
    Message,
    MessageMetadata,
    MessageRole,
    MessageStatus,
)
from src.apps.llm_tools.app.contracts import LLMToolsApp

from ..domain.models import Attempt
from ..domain.refs import (
    MessageRef,
    MessageRoleRef,
    MessageStatusRef,
    MessageMetadataRef,
)
from ..domain.ports import AttemptRepository, Explainer, AttemptFinalizer
from ..domain.errors import NotAttemptOwnerError, AttemptAlreadyFinalizedError

from .contracts import (
    AskExplainerCmd,
    AskExplainerResult,
    QuizAttempterApp,
    FinalizeAttemptCmd,
)

logger = logging.getLogger(__name__)


class QuizAttempterAppImpl(QuizAttempterApp):
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        explainer: Explainer,
        message_owner: MessageOwnerApp,
        llm_tools: LLMToolsApp,
        finalizer: AttemptFinalizer,
    ):
        self.attempt_repository = attempt_repository
        self.explainer = explainer
        self.message_owner = message_owner
        self.llm_tools = llm_tools
        self.finalizer = finalizer

    async def finalize(self, cmd: FinalizeAttemptCmd) -> None:
        logger.info(f"Finalize attempt: {cmd.attempt_id}")
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.user)
        await self.finalizer.finalize(attempt, cmd.cache_key)

    async def ask_explainer(
        self, cmd: AskExplainerCmd
    ) -> AsyncGenerator[AskExplainerResult, None]:
        logger.info(f"Ask explainer: {cmd.attempt_id}")
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.user)

        ai_message = await self.message_owner.start_message(
            StartMessageCmd(attempt_id=attempt.id, item_id=cmd.item_id)
        )
        ai_message_ref = self._to_message_ref(ai_message)

        history = await self.message_owner.get_attempt_history(
            GetAttemptHistoryCmd(attempt_id=attempt.id, limit=100)
        )
        history = [self._to_message_ref(msg) for msg in history]
        history = self._trim_history(history)
        attempt.set_history(history)

        item = attempt.get_item(cmd.item_id)

        logger.info(f"Explain attempt: {attempt.id}")
        async for message in self.explainer.explain(
            cmd.query, attempt, item, ai_message_ref, cmd.cache_key
        ):
            logger.debug(f"Message: {len(message.content)} chars, id: {message.id}")
            status = "chunk" if message.status == "streaming" else "done"

            if message.status == MessageStatus.FINAL:
                await self.message_owner.finalize_message(
                    FinalizeMessageCmd(
                        message_id=message.id,
                        content=message.content,
                        metadata=self._to_message_metadata(message.metadata),
                    )
                )

            yield AskExplainerResult(
                text=message.content, msg_id=message.id, i=0, status=status
            )

    async def validate_attempt(self, attempt: Attempt, user: Principal) -> None:
        if attempt.user_id != user.id:
            raise NotAttemptOwnerError(
                attempt_id=attempt.id, user_id=user.id, quiz_id=attempt.quiz.id
            )
        if attempt.feedback is not None:
            raise AttemptAlreadyFinalizedError(
                attempt_id=attempt.id, user_id=user.id, quiz_id=attempt.quiz.id
            )

    def _trim_history(self, history: list[MessageRef]) -> list[MessageRef]:
        return history

    def _to_message_ref(self, message: Message) -> MessageRef:
        return MessageRef(
            id=message.id,
            attempt_id=message.attempt_id,
            content=message.content,
            role=self._to_message_role_ref(message.role),
            status=self._to_message_status_ref(message.status),
            metadata=self._to_message_metadata_ref(message.metadata),
        )

    def _to_message_metadata_ref(self, metadata: MessageMetadata) -> MessageMetadataRef:
        return MessageMetadataRef(
            tool_calls=metadata.tool_calls,
            tool_results=metadata.tool_results,
        )

    def _to_message_status_ref(self, status: MessageStatus) -> MessageStatusRef:
        return (
            MessageStatusRef.FINAL
            if status == MessageStatus.FINAL
            else MessageStatusRef.STREAMING
        )

    def _to_message_role_ref(self, role: MessageRole) -> MessageRoleRef:
        return MessageRoleRef.AI if role == MessageRole.AI else MessageRoleRef.USER

    def _to_message_metadata(self, metadata: MessageMetadataRef) -> MessageMetadata:
        return MessageMetadata(
            tool_calls=metadata.tool_calls,
            tool_results=metadata.tool_results,
        )
