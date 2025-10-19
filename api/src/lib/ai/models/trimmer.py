from typing import Annotated, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass


@dataclass
class TrimmerDeps:
    """Dependencies for the Trimmer agent."""
    contents: str  # JSON string representing table of contents
    query: str  # User's query about what content to include


class PageRange(BaseModel):
    """Represents a range of pages to include."""
    start: Annotated[int, Field(description="Starting page number (inclusive)")]
    end: Annotated[int, Field(description="Ending page number (inclusive)")]


class TrimmerOutput(BaseModel):
    """Output from the Trimmer agent containing page ranges to include."""
    mode: Literal["trim"]
    page_ranges: Annotated[
        list[PageRange],
        Field(
            description="List of page ranges to include based on user query. Example: [{'start': 100, 'end': 120}, {'start': 140, 'end': 170}]"
        ),
    ]
    reasoning: Annotated[
        str,
        Field(
            description="Brief explanation of why these page ranges were selected based on the table of contents and user query"
        ),
    ]
