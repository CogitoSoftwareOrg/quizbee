from .domain.ports import UserVerifier, UserRepository


from .app.contracts import AuthUserApp
from .app.usecases import AuthUserAppImpl


def init_auth_user_app(user_verifier: UserVerifier, user_repository: UserRepository):
    return AuthUserAppImpl(user_verifier, user_repository)
