from pocketbase.models.dtos import Record
from dataclasses import dataclass
from pydantic_ai import Agent

from src.lib.ai import AgentEnvelope
from src.lib.clients import HTTPAsyncClient
from src.lib.config import LLMS

ORCHESTRATOR_LLM = LLMS.GPT_5_MINI


@dataclass
class OrchestratorDeps:
    http: HTTPAsyncClient
    quiz: Record
    prev_quiz_items: list[Record]
    materials: list[Record]


orchestrator_agent = Agent(
    model=ORCHESTRATOR_LLM,
    deps_type=OrchestratorDeps,
    instrument=True,
    output_type=AgentEnvelope,
)
