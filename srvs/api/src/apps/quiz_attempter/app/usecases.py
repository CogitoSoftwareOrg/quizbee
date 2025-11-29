import logging
from typing import AsyncGenerator

from src.apps.user_owner.domain._in import AuthUserApp, Principal
from src.apps.message_owner.domain._in import (
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
from src.apps.llm_tools.domain._in import LLMToolsApp
from src.apps.user_owner.domain.models import Tariff
from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.material_owner.domain.constants import RAG_CHUNK_TOKEN_LIMIT
from src.apps.material_owner.domain.models import SearchType


from ..domain.models import Attempt
from ..domain.refs import (
    MessageRef,
    MessageRoleRef,
    MessageStatusRef,
    MessageMetadataRef,
    QuizItemRef,
)
from ..domain.out import AttemptRepository, Explainer, AttemptFinalizer
from ..domain.errors import NotAttemptOwnerError, AttemptAlreadyFinalizedError

from ..domain._in import (
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
        material_app: MaterialApp,
    ):
        self.attempt_repository = attempt_repository
        self.explainer = explainer
        self.message_owner = message_owner
        self.finalizer = finalizer
        self._material_app = material_app
        self._llm_tools = llm_tools

    async def finalize(self, cmd: FinalizeAttemptCmd) -> None:
        logger.info(f"Finalize attempt: {cmd.attempt_id}")
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.user)
        await self.finalizer.finalize(attempt, cmd.cache_key)
        await self.attempt_repository.update(attempt)

    async def ask_explainer(
        self, cmd: AskExplainerCmd
    ) -> AsyncGenerator[AskExplainerResult, None]:
        logger.info(f"Ask explainer: {cmd.attempt_id}")
        attempt = await self.attempt_repository.get(cmd.attempt_id)
        await self.validate_attempt(attempt, cmd.user, with_feedback=False)

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

        q_vec = (await self._llm_tools.vectorize([cmd.query]))[0].tolist()
        material_ids = attempt.quiz.material_ids
        chunks = await self._material_app.search(
            SearchCmd(
                limit_tokens=RAG_CHUNK_TOKEN_LIMIT,
                user=cmd.user,
                material_ids=material_ids,
                vectors=[q_vec],
                search_type=SearchType.VECTOR,
            )
        )

        logger.info(
            f"Explain attempt: {attempt.id} with material content: {len(attempt.quiz.material_ids)}"
        )
        async for chunk in self.explainer.explain(
            cmd.query, attempt, item, ai_message_ref, cmd.cache_key, chunks
        ):
            logger.debug(f"Message: {len(chunk.content)} chars, id: {chunk.id}")
            status = "chunk" if chunk.status == "streaming" else "done"

            if chunk.status == MessageStatus.FINAL:
                await self.message_owner.finalize_message(
                    FinalizeMessageCmd(
                        message_id=chunk.id,
                        content=chunk.content,
                        metadata=self._to_message_metadata(chunk.metadata),
                    )
                )

            yield AskExplainerResult(
                text=chunk.content, msg_id=chunk.id, i=0, status=status
            )

    async def validate_attempt(
        self, attempt: Attempt, user: Principal, with_feedback=True
    ) -> None:
        if attempt.user_id != user.id:
            raise NotAttemptOwnerError(
                attempt_id=attempt.id, user_id=user.id, quiz_id=attempt.quiz.id
            )
        if with_feedback and attempt.feedback is not None:
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
