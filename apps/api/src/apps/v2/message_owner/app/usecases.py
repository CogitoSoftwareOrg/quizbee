import logging
from ..domain.models import Message, MessageRole
from ..domain.ports import MessageRepository

from .contracts import (
    GetAttemptHistoryCmd,
    MessageOwnerApp,
    StartMessageCmd,
    FinalizeMessageCmd,
)


class MessageOwnerAppImpl(MessageOwnerApp):
    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def get_attempt_history(self, cmd: GetAttemptHistoryCmd) -> list[Message]:
        logging.info(f"Getting attempt history for attempt {cmd.attempt_id}")
        return await self.message_repository.get_attempt(cmd.attempt_id, cmd.limit)

    async def start_message(self, cmd: StartMessageCmd) -> Message:
        logging.info(f"Starting message for attempt {cmd.attempt_id}")
        message = Message.create(cmd.attempt_id, MessageRole.AI, cmd.item_id)
        message.to_streaming()
        await self.message_repository.save([message])
        return message

    async def finalize_message(self, cmd: FinalizeMessageCmd) -> None:
        logging.info(f"Finalizing message {cmd.message_id}")
        message = await self.message_repository.get(cmd.message_id)
        message.to_final(cmd.content, cmd.metadata)
        await self.message_repository.save([message])
        return None
