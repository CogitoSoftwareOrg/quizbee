import logging
import redis.asyncio as redis
import asyncio
import re
from dataclasses import dataclass

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.material_owner.domain.models import MaterialChunk, SearchType
from src.apps.user_owner.domain._in import Principal
from src.lib.distributed_lock import DistributedLock

from ..domain._in import GenMode, GenerateCmd, QuizGenerator
from ..domain.errors import NotQuizOwnerError
from ..domain.out import PatchGenerator, PatchGeneratorDto, QuizIndexer, QuizRepository
from ..domain.models import Quiz, QuizItem
from ..domain.constants import HOLDOUT, PATCH_CHUNK_TOKEN_LIMIT, PATCH_LIMIT

from .errors import NoItemsReadyForGenerationError

logger = logging.getLogger(__name__)

PAGE_MARKER_PATTERN = re.compile(r'\{quizbee_page_number_(\d+)\}')


@dataclass
class SubChunk:
    chunk_id: str
    page: int
    content: str
    material_id: str
    title: str


def split_chunk_by_pages(
    chunk_id: str,
    content: str,
    pages: list[int],
    material_id: str,
    title: str,
) -> list[SubChunk]:
    if not pages or len(pages) <= 1:
        page = pages[0] if pages else 0
        clean_content = PAGE_MARKER_PATTERN.sub('', content).strip()
        return [SubChunk(
            chunk_id=chunk_id,
            page=page,
            content=clean_content,
            material_id=material_id,
            title=title,
        )]

    sub_chunks: list[SubChunk] = []
    parts = PAGE_MARKER_PATTERN.split(content)

    current_page = pages[0]
    for i, part in enumerate(parts):
        if i % 2 == 1:
            current_page = int(part)
        else:
            clean_part = part.strip()
            if clean_part:
                sub_chunks.append(SubChunk(
                    chunk_id=chunk_id,
                    page=current_page,
                    content=clean_part,
                    material_id=material_id,
                    title=title,
                ))

    return sub_chunks if sub_chunks else [SubChunk(
        chunk_id=chunk_id,
        page=pages[0],
        content=PAGE_MARKER_PATTERN.sub('', content).strip(),
        material_id=material_id,
        title=title,
    )]


class QuizGeneratorImpl(QuizGenerator):
    def __init__(
        self,
        quiz_repository: QuizRepository,
        quiz_indexer: QuizIndexer,
        material_app: MaterialApp,
        patch_generator: PatchGenerator,
        redis_client: redis.Redis,
    ):
        self._quiz_repository = quiz_repository
        self._quiz_indexer = quiz_indexer
        self._material_app = material_app
        self._patch_generator = patch_generator
        self._lock = DistributedLock(redis_client, lock_timeout=300)  # 5 min timeout

    async def generate(self, cmd: GenerateCmd) -> None:
        ### эта функция отвечает за генерацию одного патча
        ### используется distributed lock чтобы предотвратить race conditions
        ### при параллельных Continue запросах

        lock_key = f"quiz:generate:{cmd.quiz_id}"

        async with self._lock.lock(lock_key, wait_timeout=60.0):
            logger.info(f"Acquired lock for quiz generation: {cmd.quiz_id}")

            # Read fresh quiz state inside the lock
            quiz = await self._quiz_repository.get(cmd.quiz_id)
            if quiz.author_id != cmd.user.id:
                raise NotQuizOwnerError(quiz_id=cmd.quiz_id, user_id=cmd.user.id)

            if cmd.mode == GenMode.Regenerate:
                logger.info(f"Incrementing generation for quiz {cmd.quiz_id}")
                quiz.increment_generation()
                await self._quiz_repository.update(quiz)

            to_generate = (
                PATCH_LIMIT + HOLDOUT if cmd.mode == GenMode.Start else PATCH_LIMIT
            )

            items_to_generate = quiz.generate_patch(to_generate)
            if len(items_to_generate) == 0:
                logger.warning(
                    f"No items ready for generation in quiz {cmd.quiz_id}. "
                    f"All items may be FINAL or there are no items."
                )
                raise NoItemsReadyForGenerationError(quiz_id=cmd.quiz_id)
            await self._quiz_repository.update(quiz)

            # Generate for each specific item by order to avoid race conditions
            generation_tasks = []
            for idx, item in enumerate(items_to_generate):
                generation_tasks.append(
                    self._run_generation_task(quiz, item, cmd.user, cmd.cache_key)
                )

            await asyncio.gather(*generation_tasks)

            await self._quiz_repository.update(quiz, fresh_generated=True)

            logger.info(f"Generation completed for quiz {cmd.quiz_id}")

    async def _run_generation_task(
        self, quiz: Quiz, item: QuizItem, user: Principal, cache_key: str
    ) -> None:
        chunks: list[MaterialChunk] = []
        sub_chunks: list[SubChunk] = []

        if len(quiz.materials) > 0:
            chunks = await self._relevant_chunks(quiz, item, user)
            for chunk in chunks:
                sub_chunks.extend(split_chunk_by_pages(
                    chunk_id=chunk.id,
                    content=chunk.content,
                    pages=chunk.pages,
                    material_id=chunk.material_id,
                    title=chunk.title,
                ))

        sub_chunk_contents = [sc.content for sc in sub_chunks]

        dto = PatchGeneratorDto(
            quiz=quiz,
            cache_key=cache_key,
            chunks=sub_chunk_contents if sub_chunk_contents else None,
            item_order=item.order,
        )
        
        await self._patch_generator.generate(dto)

        if len(sub_chunks) > 0 and dto.used_chunk_indices is not None:
            used_sub_chunks = [
                sub_chunks[i] for i in dto.used_chunk_indices if i < len(sub_chunks)
            ]
            
            if len(used_sub_chunks) > 0:
                chunk_to_pages: dict[str, set[int]] = {}
                for sc in used_sub_chunks:
                    if sc.chunk_id not in chunk_to_pages:
                        chunk_to_pages[sc.chunk_id] = set()
                    chunk_to_pages[sc.chunk_id].add(sc.page)
                
                used_chunk_ids = list(chunk_to_pages.keys())
                
                chunks_info = await self._material_app.get_chunks_info(used_chunk_ids)
                
                for info in chunks_info:
                    chunk_id = info.get("id", "")
                    if chunk_id in chunk_to_pages:
                        info["pages"] = sorted(chunk_to_pages[chunk_id])
                
                if item.used_chunks is None:
                    item.used_chunks = []
                item.used_chunks.extend(chunks_info)
                await self._material_app.mark_chunks_as_used(used_chunk_ids)
                logger.info(
                    f"Marked {len(used_chunk_ids)} chunks as used "
                    f"(LLM selected {len(used_sub_chunks)} sub-chunks from {len(sub_chunks)} total). "
                    f"Chunks info: {chunks_info}"
                )
            else:
                logger.warning(
                    f"LLM returned used_chunk_indices {dto.used_chunk_indices} but no valid sub-chunks found"
                )
        elif len(sub_chunks) > 0:
            chunk_to_pages: dict[str, set[int]] = {}
            for sc in sub_chunks:
                if sc.chunk_id not in chunk_to_pages:
                    chunk_to_pages[sc.chunk_id] = set()
                chunk_to_pages[sc.chunk_id].add(sc.page)
            
            all_chunk_ids = list(chunk_to_pages.keys())
            chunks_info = await self._material_app.get_chunks_info(all_chunk_ids)
            
            for info in chunks_info:
                chunk_id = info.get("id", "")
                if chunk_id in chunk_to_pages:
                    info["pages"] = sorted(chunk_to_pages[chunk_id])
            
            if item.used_chunks is None:
                item.used_chunks = []
            item.used_chunks.extend(chunks_info)
            logger.warning(
                f"LLM did not return used_chunk_indices, marking all {len(all_chunk_ids)} chunks as used. "
                f"Chunks info: {chunks_info}"
            )
            await self._material_app.mark_chunks_as_used(all_chunk_ids)

    async def _relevant_chunks(
        self, quiz: Quiz, item: QuizItem, user: Principal
    ) -> list[MaterialChunk]:
        num_clusters = len(quiz.cluster_vectors)
        vector = quiz.cluster_vectors[item.order % num_clusters]
        
        logger.info(f"Searching for item {item.order} with vector cluster {item.order % num_clusters}")

        chunks = await self._material_app.search(
            SearchCmd(
                user=user,
                material_ids=[m.id for m in quiz.materials],
                limit_tokens=PATCH_CHUNK_TOKEN_LIMIT,
                vectors=[vector],
                search_type=SearchType.GENERATOR,
            )
        )

        logger.info(f"Found {len(chunks)} chunks for item {item.order}")
        return chunks
