"""
MeiliMaterialVectorSearcher - поиск по векторам.

Находит наиболее похожие чанки для каждого вектора из списка central_vectors.
Используется для генерации квизов на основе кластеризации.
"""

import logging
import random
from langfuse import Langfuse
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.search import Hybrid

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
            # Выполняем поиск по вектору в MeiliSearch - находим топ-10 ближайших чанков
            try:
                res = await self._material_index.search(
                    query="",  # Пустой query
                    vector=central_vector,  # Прямой поиск по вектору
                    hybrid=Hybrid(semantic_ratio=1.0, embedder=EMBEDDER_NAME),  # Только векторный поиск
                    filter=f,
                    limit=10,  # Берем топ-10 для выбора неиспользованного
                    ranking_score_threshold=0,
                    show_ranking_score=True,
                )
                
                # Преобразуем результаты
                docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
                
                if not docs:
                    logging.debug(f"Vector {idx + 1}/{len(dto.vectors)}: no chunks found")
                    continue
                
                # Конвертируем в чанки
                candidate_chunks = [doc.to_chunk() for doc in docs]
                
                # Выбираем первый неиспользованный чанк, либо случайный если все использованы
                most_relevant = None
                unused_chunks = [c for c in candidate_chunks if not c.used]
                
                if unused_chunks:
                    most_relevant = unused_chunks[0]
                    logging.debug(
                        f"Vector {idx + 1}/{len(dto.vectors)}: selected unused chunk {most_relevant.id} "
                        f"(idx={most_relevant.idx}, rank 1/{len(unused_chunks)} unused)"
                    )
                else:
                    # Все чанки использованы - берем случайный
                    most_relevant = random.choice(candidate_chunks)
                    logging.debug(
                        f"Vector {idx + 1}/{len(dto.vectors)}: all {len(candidate_chunks)} chunks are used, "
                        f"selected random chunk {most_relevant.id} (idx={most_relevant.idx})"
                    )
                
                # Получаем соседние чанки (слева и справа)
                neighbor_chunks = await self._get_neighbor_chunks(most_relevant)
                
                logging.debug(
                    f"Vector {idx + 1}/{len(dto.vectors)}: found {len(neighbor_chunks)} neighbor chunks for chunk {most_relevant.id} (idx={most_relevant.idx})"
                )
                
                # Добавляем чанки с соседями
                added_count = 0
                skipped_duplicate = 0
                skipped_limit = 0
                
                for chunk in neighbor_chunks:
                    if chunk.id in seen_chunk_ids:
                        logging.debug(f"  Chunk {chunk.id} (idx={chunk.idx}) already seen, skipping")
                        skipped_duplicate += 1
                        continue
                    
                    chunk_tokens = self._llm_tools.count_text(chunk.content)
                    
                    # Проверяем лимит токенов
                    if total_tokens + chunk_tokens > dto.limit * self._llm_tools.chunk_size:
                        logging.debug(
                            f"  Chunk {chunk.id} (idx={chunk.idx}) exceeds token limit: {total_tokens + chunk_tokens} > {dto.limit * self._llm_tools.chunk_size}, skipping remaining"
                        )
                        skipped_limit += 1
                        break
                    
                    logging.debug(f"  Adding chunk {chunk.id} (idx={chunk.idx}, tokens={chunk_tokens})")
                    seen_chunk_ids.add(chunk.id)
                    selected_chunks.append(chunk)
                    total_tokens += chunk_tokens
                    added_count += 1
                
                logging.debug(
                    f"Vector {idx + 1}/{len(dto.vectors)}: selected {added_count} chunks (skipped {skipped_duplicate} duplicates, {skipped_limit} over limit), total tokens: {total_tokens}"
                )
                
            except Exception as e:
                logging.error(f"Error searching for vector {idx + 1}: {e}")
                continue

            
            

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
        
        # Формируем фильтр для поиска соседних чанков
        try:
            current_idx = target_chunk.idx
            material_id = target_chunk.material_id
            
            # Определяем диапазон индексов
            min_idx = max(0, current_idx - 1)  # Не меньше 0
            max_idx = current_idx + 1
            
            # Запрашиваем чанки по materialId и диапазону idx
            # Используем >= и <= для диапазона (более эффективно чем OR)
            f = f"materialId = {material_id} AND idx >= {min_idx} AND idx <= {max_idx}"
            
            res = await self._material_index.search(
                query="*",
                filter=f,
                limit=3,
                retrieve_vectors=False,  # Векторы не нужны для соседей
            )
            
            docs: list[Doc] = [Doc.from_hit(hit) for hit in res.hits]
            chunks = [doc.to_chunk() for doc in docs]
            
            # Сортируем по idx
            chunks.sort(key=lambda c: c.idx)
            result = chunks
            
            logging.debug(
                f"_get_neighbor_chunks for material {material_id}, idx {current_idx}: "
                f"found {len(result)} chunks with indices {[c.idx for c in result]}"
            )
            
        except Exception as e:
            logging.error(f"Error fetching neighbor chunks: {e}")
            result = [target_chunk]
        
        return result if result else [target_chunk]
