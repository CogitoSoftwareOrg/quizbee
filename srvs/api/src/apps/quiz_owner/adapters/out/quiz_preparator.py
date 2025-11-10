import logging

from src.apps.material_owner.domain._in import MaterialApp

from ...domain.out import QuizPreparator
from ...domain.models import Quiz

logger = logging.getLogger(__name__)


class QuizPreparatorImpl(QuizPreparator):
    def __init__(self, material_app: MaterialApp):
        self._material_app = material_app

    async def prepare(self, quiz: Quiz) -> None: ...

    async def _build_material_vectors(self, quiz: Quiz) -> None: ...
