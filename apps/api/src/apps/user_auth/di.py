from pocketbase import PocketBase

from src.lib.di import init_global_deps

from .domain.ports import UserVerifier, UserRepository

from .app.usecases import AuthUserAppImpl
from .adapters.out import PBUserRepository, PBUserVerifier


def init_user_auth_deps(admin_pb: PocketBase):
    user_repository = PBUserRepository(admin_pb)
    user_verifier = PBUserVerifier(user_repository=user_repository)
    return user_verifier, user_repository


def init_auth_user_app(
    user_verifier: UserVerifier | None = None,
    user_repository: UserRepository | None = None,
):
    if user_verifier is None or user_repository is None:
        admin_pb, _, _, _ = init_global_deps()

        user_verifier, user_repository = init_user_auth_deps(admin_pb)
        user_verifier = user_verifier or default_user_verifier
        user_repository = user_repository or default_user_repository

    return AuthUserAppImpl(user_verifier=user_verifier, user_repository=user_repository)
