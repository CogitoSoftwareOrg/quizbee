from fastapi import FastAPI

from .adapters.out import PBMessageRepository
from .domain.ports import MessageRepository
from .app.usecases import MessageOwnerAppImpl


def set_message_owner_app(app: FastAPI, message_repository: MessageRepository):
    app.state.message_owner_app = MessageOwnerAppImpl(
        message_repository=message_repository
    )
