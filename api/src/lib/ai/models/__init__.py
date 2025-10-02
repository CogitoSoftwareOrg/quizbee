from typing import Union
from pydantic import BaseModel


from .quizer import *
from .feedbacker import *
from .explainer import *
from .summarizer import *


AgentPayload = Annotated[
    Union[QuizerOutput, ExplainerOutput, FeedbackerOutput, SummarizerOutput],
    Field(discriminator="mode"),
]


class AgentEnvelope(BaseModel):
    data: AgentPayload
