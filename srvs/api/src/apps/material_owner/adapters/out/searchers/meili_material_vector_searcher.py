"""
MeiliMaterialVectorSearcher - поиск по векторам.

Находит наиболее похожие чанки для каждого вектора из списка central_vectors.
Используется для генерации квизов на основе кластеризации.
"""

import logging
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient

from ....domain.models import MaterialChunk
from ....domain.out import SearchDto, Searcher, LLMTools

from ..indexers.meili_material_indexer import EMBEDDER_NAME, Doc


class MeiliMaterialVectorSearcher(Searcher):
    """
    Searcher для поиска материалов по векторам.

    Для каждого вектора из списка находит наиболее похожие чанки
    используя косинусное сходство. Используется для генерации
    квизов на основе кластеризации материалов.
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
        Ищет наиболее похожие чанки для каждого вектора.

        Args:
            dto: SearchDto с параметрами поиска
                - user_id: ID пользователя
                - material_ids: Список ID материалов для поиска
                - limit: Максимальное количество чанков
                - vectors: Список векторов для поиска (должен быть заполнен)

        Returns:
            Список найденных чанков материалов, наиболее похожих на переданные векторы
        """
        if not dto.vectors:
            logging.warning("No vectors provided for vector search")
            return []

        # Формируем фильтр для MeiliSearch
        f = f"userId = {dto.user_id}"
        if dto.material_ids:
            f += f" AND materialId IN [{','.join(dto.material_ids)}]"

        logging.info(
            f"Meili Vector Search... {f}, vectors count: {len(dto.vectors)}, limit: {dto.limit}"
        )

        selected_chunks: list[MaterialChunk] = []
        seen_chunk_ids = set()  # Для дедупликации
        total_tokens = 0  # Счетчик токенов

        # Для каждого центрального вектора делаем отдельный запрос
        for idx, central_vector in enumerate(dto.vectors):
            # Выполняем поиск по вектору в MeiliSearch - находим самый близкий чанк
            try:
                res = await self._material_index.search(
                    query="",  # Пустой query
                    vector=central_vector,  # Прямой поиск по вектору
                    filter=f,
                    limit=1,  # Нужен только самый близкий
                    ranking_score_threshold=0,
                    show_ranking_score=True,
                )
                
                # Преобразуем результаты
                docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
                
                if not docs:
                    logging.debug(f"Vector {idx + 1}/{len(dto.vectors)}: no chunks found")
                    continue
                
                # Берем самый релевантный чанк
                most_relevant = docs[0].to_chunk()
                
                # Получаем соседние чанки (слева и справа)
                neighbor_chunks = await self._get_neighbor_chunks(most_relevant)
                
                # Добавляем чанки с соседями
                added_count = 0
                for chunk in neighbor_chunks:
                    if chunk.id in seen_chunk_ids:
                        continue
                    
                    chunk_tokens = self._llm_tools.count_text(chunk.content)
                    
                    # Проверяем лимит токенов
                    if total_tokens + chunk_tokens > dto.limit * self._llm_tools.chunk_size:
                        logging.debug(
                            f"Reached token limit: {total_tokens + chunk_tokens} > {dto.limit * self._llm_tools.chunk_size}"
                        )
                        break
                    
                    seen_chunk_ids.add(chunk.id)
                    selected_chunks.append(chunk)
                    total_tokens += chunk_tokens
                    added_count += 1
                
                logging.debug(
                    f"Vector {idx + 1}/{len(dto.vectors)}: selected {added_count} chunks (with neighbors), total tokens: {total_tokens}"
                )
                
            except Exception as e:
                logging.error(f"Error searching for vector {idx + 1}: {e}")
                continue

            
            # Если уже достигли лимита токенов, прерываем
            if total_tokens >= dto.limit * self._llm_tools.chunk_size:
                logging.info(f"Stopping early: reached token limit at vector {idx + 1}/{len(dto.vectors)}")
                break

        logging.info(
            f"Vector search complete: {len(selected_chunks)} chunks, {total_tokens} tokens from {len(dto.vectors)} vectors"
        )

        return selected_chunks

    async def _get_neighbor_chunks(
        self, target_chunk: MaterialChunk
    ) -> list[MaterialChunk]:
        """
        Получает чанк вместе с его соседями (предыдущий и следующий).
        
        Args:
            target_chunk: Целевой чанк (самый релевантный)
            
        Returns:
            Список из до 3 чанков: [предыдущий, целевой, следующий] (если они существуют)
        """
        result = []
        
        # Формируем ID соседних чанков
        try:
            current_idx = target_chunk.idx
            base_id = target_chunk.id.rsplit('-', 1)[0]
            
            # Формируем список ID: [предыдущий, текущий, следующий]
            neighbor_ids = []
            if current_idx > 0:
                neighbor_ids.append(f"{base_id}-{current_idx - 1}")  # Предыдущий
            neighbor_ids.append(target_chunk.id)  # Текущий
            neighbor_ids.append(f"{base_id}-{current_idx + 1}")  # Следующий
            
            # Запрашиваем чанки по ID
            f = f"id IN [{','.join(neighbor_ids)}]"
            res = await self._material_index.search(
                query="*",
                filter=f,
                limit=3,
            )
            
            docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
            chunks = [doc.to_chunk() for doc in docs]
            
            # Сортируем по idx
            chunks.sort(key=lambda c: c.idx)
            result = chunks
            
        except Exception as e:
            logging.error(f"Error fetching neighbor chunks: {e}")
            result = [target_chunk]
        
        return result if result else [target_chunk]
