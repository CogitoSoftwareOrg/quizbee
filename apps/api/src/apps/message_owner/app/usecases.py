import logging
from ..domain.models import Message, MessageRole
from ..domain.ports import MessageRepository

from ..domain._in import (
    GetAttemptHistoryCmd,
    MessageOwnerApp,
    StartMessageCmd,
    FinalizeMessageCmd,
)

logger = logging.getLogger(__name__)


class MessageOwnerAppImpl(MessageOwnerApp):
    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def get_attempt_history(self, cmd: GetAttemptHistoryCmd) -> list[Message]:
        logger.info(f"Getting attempt history for attempt {cmd.attempt_id}")
        return await self.message_repository.get_attempt(cmd.attempt_id, cmd.limit)

    async def start_message(self, cmd: StartMessageCmd) -> Message:
        logger.info(f"Starting message for attempt {cmd.attempt_id}")
        message = Message.create(cmd.attempt_id, MessageRole.AI, cmd.item_id)
        message.to_streaming()
        await self.message_repository.create([message])
        return message

    async def finalize_message(self, cmd: FinalizeMessageCmd):
        logger.info(f"Finalizing message {cmd.message_id}")
        message = await self.message_repository.get(cmd.message_id)
        message.to_final(cmd.content, cmd.metadata)
        await self.message_repository.update([message])
