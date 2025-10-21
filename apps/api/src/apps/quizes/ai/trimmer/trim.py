import logging
from typing import List, Dict

from lib.ai.models import TrimmerDeps
from lib.clients import langfuse_client

from .agent import trimmer_agent


async def trim_content(
    contents: str,
    query: str,
    user_id: str | None = None,
    session_id: str | None = None,
) -> List[Dict[str, int]]:
    """
    Analyze table of contents and user query to determine which page ranges to include.
    
    Args:
        contents: JSON string representing the table of contents
        query: User's query about what content to include
        user_id: Optional user ID for tracking
        session_id: Optional session ID for tracking
        
    Returns:
        List of page ranges as dictionaries with 'start' and 'end' keys
        Example: [{'start': 100, 'end': 120}, {'start': 140, 'end': 170}]
    """
    
    with langfuse_client.start_as_current_span(name="content-trim") as span:
        res = await trimmer_agent.run(
            deps=TrimmerDeps(
                contents=contents,
                query=query,
            ),
        )
        
        payload = res.output
        
        page_ranges = [
            {"start": pr.start, "end": pr.end} 
            for pr in payload.page_ranges
        ]
        
        usage = res.usage()
        
        logging.info(
            f"Trimmer determined {len(page_ranges)} page range(s): {page_ranges}"
        )
        logging.info(f"Reasoning: {payload.reasoning}")
        
        if span:
            span.update_trace(
                input=f"Query: {query}",
                output=f"Page ranges: {page_ranges}",
                user_id=user_id or "unknown",
                session_id=session_id or "unknown",
                metadata={
                    "page_ranges": page_ranges,
                    "reasoning": payload.reasoning,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                },
            )
        
        return page_ranges
