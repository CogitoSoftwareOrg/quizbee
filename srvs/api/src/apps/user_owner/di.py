from pocketbase import PocketBase

from .domain.out import UserVerifier, UserRepository

from .app.usecases import AuthUserAppImpl
from .adapters.out import PBUserRepository, PBUserVerifier


def init_user_auth_deps(admin_pb: PocketBase):
    user_repository = PBUserRepository(admin_pb)
    user_verifier = PBUserVerifier(user_repository=user_repository)
    return user_verifier, user_repository


def init_auth_user_app(
    user_verifier: UserVerifier,
    user_repository: UserRepository,
) -> AuthUserAppImpl:
    """Factory for AuthUserApp - all dependencies explicit"""
    return AuthUserAppImpl(user_verifier=user_verifier, user_repository=user_repository)
