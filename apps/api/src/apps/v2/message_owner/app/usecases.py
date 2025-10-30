from ..domain.models import Message, Role
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
        return await self.message_repository.get_attempt(cmd.attempt_id, cmd.limit)

    async def start_message(self, cmd: StartMessageCmd) -> Message:
        message = Message.create(cmd.attempt_id, Role.AI)
        message.to_streaming()
        await self.message_repository.save([message])
        return message

    async def finalize_message(self, cmd: FinalizeMessageCmd) -> None:
        message = await self.message_repository.get(cmd.message_id)
        message.to_final(cmd.content, cmd.metadata)
        await self.message_repository.save([message])
        return None
