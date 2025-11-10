"""
MeiliMaterialQuerySearcher - поиск по запросу пользователя.

Использует гибридный поиск (semantic + keyword) с настраиваемым ratio.
"""

import logging
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid

from src.lib.config import LLMS

from ....domain.models import MaterialChunk
from ....domain.out import SearchDto, Searcher, LLMTools

from ..meili_material_indexer import EMBEDDER_NAME, Doc


class MeiliMaterialQuerySearcher(Searcher):
    """
    Searcher для поиска материалов по запросу пользователя.

    Использует гибридный поиск MeiliSearch с комбинацией семантического
    и keyword поиска для более точных результатов.
    """

    def __init__(self, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient):
        self._lf = lf
        self._llm_tools = llm_tools
        self._meili = meili
        self._material_index = meili.index(EMBEDDER_NAME)

    async def search(
        self,
        dto: SearchDto,
    ) -> list[MaterialChunk]:
        """
        Ищет материалы по запросу пользователя.

        Args:
            user_id: ID пользователя
            query: Поисковый запрос
            material_ids: Список ID материалов для поиска
            limit: Максимальное количество результатов
            ratio: Соотношение semantic/keyword поиска (0.0 - только keyword, 1.0 - только semantic)

        Returns:
            Список найденных чанков материалов
        """
        # Формируем фильтр для MeiliSearch
        f = f"userId = {dto.user_id}"
        if dto.material_ids:
            f += f" AND materialId IN [{','.join(dto.material_ids)}]"

        logging.info(f"Meili Query Search... {f}, ratio={dto.ratio}")

        # Считаем токены для логирования
        total_tokens = self._llm_tools.count_text(
            dto.query, LLMS.TEXT_EMBEDDING_3_SMALL
        )

        # Настраиваем гибридный поиск
        hybrid = (
            Hybrid(
                semantic_ratio=dto.ratio,
                embedder=EMBEDDER_NAME,
            )
            if dto.ratio > 0
            else None
        )

        # Выполняем поиск
        res = await self._material_index.search(
            query=dto.query,
            hybrid=hybrid,
            ranking_score_threshold=0,  # Для query поиска не используем threshold
            filter=f,
            limit=dto.limit,
        )

        # Логируем в Langfuse
        if hybrid is not None:
            self._log_langfuse(dto.user_id, "", total_tokens, "material-query-search")

        # Преобразуем результаты в MaterialChunk
        docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
        chunks = [self._doc_to_chunk(doc) for doc in docs]

        logging.info(f"Found {len(chunks)} chunks for query search")
        return chunks

    def _doc_to_chunk(self, doc: Doc) -> MaterialChunk:
        """Преобразует Doc в MaterialChunk."""
        idx = doc.id.split("-")[-1]

        if not idx.isdigit():
            raise ValueError(f"Invalid chunk id: {doc.id}")
        idx = int(idx)

        return MaterialChunk(
            id=doc.id,
            idx=int(idx),
            material_id=doc.materialId,
            title=doc.title,
            content=doc.content,
        )

    def _log_langfuse(
        self, user_id: str, session_id: str, total_tokens: int, name: str
    ) -> None:
        """Логирует использование в Langfuse."""
        with self._lf.start_as_current_span(name=name) as span:
            self._lf.update_current_generation(
                model=LLMS.TEXT_EMBEDDING_3_SMALL,
                usage_details={
                    "total": total_tokens,
                },
            )
            span.update_trace(
                input=f"User: {user_id}, Session: {session_id}",
                output=f"Total tokens: {total_tokens}",
                user_id=user_id,
                session_id=session_id,
            )
