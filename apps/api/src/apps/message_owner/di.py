from pocketbase import PocketBase

from src.lib.di import init_global_deps

from .domain.ports import MessageRepository
from .app.usecases import MessageOwnerAppImpl
from .adapters.out import PBMessageRepository


def init_message_owner_deps(admin_pb: PocketBase):
    message_repository = PBMessageRepository(admin_pb)
    return message_repository


def init_message_owner_app(message_repository: MessageRepository | None = None):
    if message_repository is None:
        admin_pb, _, _, _ = init_global_deps()
        message_repository = init_message_owner_deps(admin_pb)

    return MessageOwnerAppImpl(message_repository=message_repository)
