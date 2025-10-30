from .domain.ports import MessageRepository
from .app.usecases import MessageOwnerAppImpl


def init_message_owner_app(message_repository: MessageRepository):
    return MessageOwnerAppImpl(message_repository=message_repository)
