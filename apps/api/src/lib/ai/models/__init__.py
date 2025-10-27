from typing import Union
from pydantic import BaseModel, RootModel
from pydantic_ai import ToolOutput


from .quizer import *
from .feedbacker import *
from .explainer import *
from .summarizer import *
from .trimmer import *


AgentPayload = Annotated[
    Union[
        QuizerOutput, ExplainerOutput, FeedbackerOutput, SummarizerOutput, TrimmerOutput
    ],
    Field(discriminator="mode"),
]


class AgentEnvelope(BaseModel):
    data: AgentPayload


# AgentEnvelope = [
#     ToolOutput(QuizerOutput, name="quiz"),
#     ToolOutput(ExplainerOutput, name="explain"),
#     ToolOutput(FeedbackerOutput, name="feedback"),
#     ToolOutput(SummarizerOutput, name="summarize"),
# ]
