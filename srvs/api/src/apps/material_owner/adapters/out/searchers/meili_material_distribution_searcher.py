"""
MeiliMaterialDistributionSearcher - равномерное распределение чанков по материалам.

Используется когда нет конкретного запроса, для равномерного выбора чанков
из разных материалов (например, при пустом запросе).
"""

import logging
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient

from ....domain.models import MaterialChunk
from ....domain.out import Searcher, LLMTools

from ..meili_material_indexer import EMBEDDER_NAME, Doc


class MeiliMaterialDistributionSearcher(Searcher):
    """
    Searcher для равномерного распределения чанков по материалам.

    Используется когда нет конкретного запроса. Получает чанки из всех указанных
    материалов и распределяет их равномерно, чтобы каждый материал был представлен.
    """

    def __init__(self, lf: Langfuse, llm_tools: LLMTools, meili: AsyncClient):
        self._lf = lf
        self._llm_tools = llm_tools
        self._meili = meili
        self._material_index = meili.index(EMBEDDER_NAME)

    async def search(
        self,
        user_id: str,
        query: str,
        material_ids: list[str],
        limit: int,
        ratio: float,  # Для distribution searcher ratio всегда 0.0, но параметр нужен для совместимости с Protocol
    ) -> list[MaterialChunk]:
        """
        Получает чанки, равномерно распределенные по материалам.

        Для каждого материала получает N чанков, где N = limit / количество материалов.
        Это обеспечивает равномерное представление всех материалов в результатах.

        Args:
            user_id: ID пользователя
            query: Запрос (игнорируется для distribution поиска)
            material_ids: Список ID материалов для поиска
            limit: Максимальное количество результатов
            ratio: Игнорируется (всегда используется 0.0 - только keyword поиск)

        Returns:
            Список равномерно распределенных чанков
        """
        if not material_ids:
            logging.warning("No material_ids provided for distribution search")
            return []

        logging.info(
            f"Meili Distribution Search for {len(material_ids)} materials, limit={limit}"
        )

        # Вычисляем количество чанков на материал
        num_materials = len(material_ids)
        chunks_per_material = max(1, limit // num_materials)

        logging.info(f"Fetching {chunks_per_material} chunks per material")

        # Для каждого материала делаем отдельный запрос на получение N чанков
        all_chunks: list[MaterialChunk] = []

        for material_id in material_ids:
            # Формируем фильтр для конкретного материала
            f = f"userId = {user_id} AND materialId = {material_id}"

            # Получаем N чанков для этого материала
            res = await self._material_index.search(
                query="*",  # Получаем все документы
                hybrid=None,  # Без semantic поиска
                ranking_score_threshold=0,
                filter=f,
                limit=chunks_per_material,
            )

            # Преобразуем результаты в MaterialChunk
            docs: list[Doc] = [Doc(**hit) for hit in res.hits]
            chunks = [self._doc_to_chunk(doc) for doc in docs]

            all_chunks.extend(chunks)

            logging.debug(f"Material {material_id}: fetched {len(chunks)} chunks")

        # Сортируем финальный результат по material_id и idx для упорядоченности
        all_chunks.sort(key=lambda c: (c.material_id, c.idx))

        logging.info(
            f"Distributed {len(all_chunks)} chunks from {num_materials} materials"
        )

        return all_chunks[:limit]

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
