import asyncio
import contextlib
import logging
from dataclasses import dataclass
from typing import Any, Literal, AsyncIterable

from langfuse import Langfuse
from pydantic import BaseModel
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelRequestPart,
    RunContext,
    SystemPromptPart,
    UserPromptPart,
    ToolCallPart,
    ToolReturn,
    ModelResponse,
    ToolReturnPart,
    TextPart,
)

from src.apps.material_owner.domain._in import MaterialApp, SearchCmd
from src.apps.material_owner.domain.models import MaterialChunk, SearchType
from src.apps.material_owner.domain.constants import RAG_CHUNK_TOKEN_LIMIT
from src.apps.llm_tools.domain._in import LLMToolsApp
from src.lib.config import LLMS
from src.lib.settings import settings
from src.lib.utils import update_span_with_result

from ....domain.models import (
    Attempt,
    QuizRef,
)
from ....domain.refs import (
    MessageRef,
    QuizItemRef,
    MessageRoleRef,
    MessageStatusRef,
    MessageMetadataRef,
)
from ....domain.out import Explainer

EXPLAINER_LLM = LLMS.GROK_4_1_FAST
RETRIES = 5
RERANK_QUERY_PREFIX = "Find educational content that thoroughly can explain:"


@dataclass
class AIGrokExplainerDeps:
    quiz: QuizRef
    current_item: QuizItemRef
    chunks: list[MaterialChunk]


logger = logging.getLogger(__name__)


class AIGrokExplainer(Explainer):
    def __init__(self, lf: Langfuse, material_app: MaterialApp, llm_tools: LLMToolsApp):
        self._lf = lf
        self._material_app = material_app
        self._llm_tools = llm_tools
        self._ai = Agent(
            history_processors=[self._inject_system_prompt],
            deps_type=AIGrokExplainerDeps,
            model=EXPLAINER_LLM,
            output_type=str,
            retries=RETRIES,
        )

    async def explain(
        self,
        query: str,
        attempt: Attempt,
        item: QuizItemRef,
        ai_msg: MessageRef,
        cache_key: str,
        material_ids: list[str],
        user: Any,
    ) -> AsyncIterable[MessageRef]:
        search_query = self._build_search_query(query, item)
        logger.info(f"Explainer search_query: '{search_query[:200]}...'")
        
        chunks = await self._search_chunks(search_query, material_ids, user)
        logger.info(f"Explainer found {len(chunks)} chunks")
        
        queue: asyncio.Queue[MessageRef | None] = asyncio.Queue()
        deps = AIGrokExplainerDeps(quiz=attempt.quiz, current_item=item, chunks=chunks)

        async def producer():
            with self._lf.start_as_current_span(name="explainer-agent") as span:
                content = ""
                run = None
                try:
                    async with self._ai.run_stream(
                        query or "Generate explanation",
                        message_history=self._ai_history(attempt.message_history),
                        deps=deps,
                        model=EXPLAINER_LLM,
                        model_settings={},
                    ) as r:
                        run = r
                        async for output in run.stream_output():
                            delta = output[len(content) :]
                            content += delta

                            await queue.put(
                                MessageRef(
                                    id=ai_msg.id,
                                    attempt_id=attempt.id,
                                    content=delta,
                                    role=MessageRoleRef.AI,
                                    status=MessageStatusRef.STREAMING,
                                    metadata=MessageMetadataRef(),
                                )
                            )

                    await queue.put(
                        MessageRef(
                            id=ai_msg.id,
                            attempt_id=attempt.id,
                            content=content,
                            role=MessageRoleRef.AI,
                            status=MessageStatusRef.FINAL,
                            metadata=MessageMetadataRef(),
                        )
                    )

                finally:
                    with contextlib.suppress(Exception):
                        await update_span_with_result(
                            self._lf,
                            run,
                            span,
                            attempt.user_id,
                            cache_key,
                            EXPLAINER_LLM,
                        )
                    await queue.put(None)

        producer_task = asyncio.create_task(producer())
        try:
            while True:
                message = await queue.get()
                if message is None:
                    break
                yield message
        finally:
            producer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await producer_task

    async def _inject_system_prompt(
        self, ctx: RunContext[AIGrokExplainerDeps], messages: list[ModelMessage]
    ) -> list[ModelMessage]:
        pre_parts = self._build_pre_prompt(ctx.deps)

        return (
            [ModelRequest(parts=pre_parts)]
            + messages
            + [ModelRequest(parts=self._build_material_prompt(ctx.deps.chunks))]
        )

    def _build_material_prompt(
        self, chunks: list[MaterialChunk]
    ) -> list[ModelRequestPart]:
        parts = []
        for chunk in chunks:
            parts.append(UserPromptPart(content=chunk.content))
        return parts

    def _build_pre_prompt(self, deps: AIGrokExplainerDeps) -> list[ModelRequestPart]:
        user_contents = []
        if deps.quiz.query:
            user_contents.append(f"User query:\n{deps.quiz.query}\n")

        if deps.quiz.material_content:
            logger.info(
                f"Attaching quiz materials to prompt: {len(deps.quiz.material_content)}"
            )
            user_contents.append("Quiz materials:\n")
            user_contents.append(deps.quiz.material_content)

        parts = []
        if user_contents:
            parts.append(UserPromptPart(content="\n".join(user_contents)))
        parts.append(
            SystemPromptPart(
                content=self._lf.get_prompt(
                    "explainer/base", label=settings.env
                ).compile(
                    question=deps.current_item.question,
                    answers=deps.current_item.answers,
                    decision=deps.current_item.choice,
                )
            )
        )
        return parts

    def _ai_history(self, history: list[MessageRef]) -> list[ModelMessage]:
        ai: list[ModelMessage] = []

        for msg in history:
            role = msg.role
            meta = msg.metadata
            content = msg.content.strip()
            if len(content) == 0:
                continue

            if role == "user":
                if content:
                    ai.append(
                        ModelRequest(parts=[UserPromptPart(content=f"{content}")])
                    )
            elif role == "ai":
                parts = []
                for tc in meta.tool_calls:
                    parts.append(
                        ToolCallPart(
                            tool_name=tc,
                            args=tc,
                            tool_call_id=tc,
                        )
                    )
                if parts:
                    ai.append(ModelResponse(parts=parts))

                parts = []
                for tr in meta.tool_results:
                    parts.append(
                        ToolReturnPart(
                            content=tr,
                            tool_name=tr,
                            tool_call_id=tr,
                        )
                    )
                if parts:
                    ai.append(ModelRequest(parts=parts))

                if meta.tool_calls and not meta.tool_results:
                    pass
                elif content:
                    ai.append(ModelResponse(parts=[TextPart(content=f"{content}")]))

            else:
                pass

        return ai

    def _build_search_query(self, query: str, item: QuizItemRef) -> str:
        answers_text = " ".join(item.answers)
        return f"{item.question} {answers_text} {query}"

    async def _search_chunks(
        self, search_query: str, material_ids: list[str], user: Any
    ) -> list[MaterialChunk]:
        q_vec = (await self._llm_tools.vectorize([search_query]))[0].tolist()
        
        chunks = await self._material_app.search(
            SearchCmd(
                limit_tokens=RAG_CHUNK_TOKEN_LIMIT,
                user=user,
                material_ids=material_ids,
                vectors=[q_vec],
                query=search_query,
                rerank_prefix=RERANK_QUERY_PREFIX,
                search_type=SearchType.VECTOR,
            )
        )
        return chunks
