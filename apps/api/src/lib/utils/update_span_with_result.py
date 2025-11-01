from typing import Any
from langfuse import Langfuse
from langfuse import LangfuseSpan
from pydantic_ai import AgentRunResult
from pydantic_ai.result import StreamedRunResult


from src.lib.config.llms import LLMS, LLMCosts


async def update_span_with_result(
    lf: Langfuse,
    result: StreamedRunResult | AgentRunResult | Any,
    span: LangfuseSpan,
    user_id: str,
    session_id: str,
    model: LLMS,
    # costs: LLMCosts,
):
    if isinstance(result, StreamedRunResult):
        output = await result.get_output()
    elif isinstance(result, AgentRunResult):
        output = result.output
    else:
        raise ValueError(f"Unexpected result type: {type(result)}")

    messages = result.all_messages()

    usage = result.usage()
    input_nc = usage.input_tokens - usage.cache_read_tokens
    input_cah = usage.cache_read_tokens
    outp = usage.output_tokens

    # input_nc_price = round(input_nc * costs.input_nc, 4)
    # input_cah_price = round(input_cah * costs.input_cah, 4)
    # outp_price = round(outp * costs.output, 4)

    lf.update_current_generation(
        input=messages,
        output=output,
        model=model,
        usage_details={
            "input": input_nc,
            "input_cache_read": input_cah,
            "output": outp,
        },
    )
    span.update_trace(
        user_id=user_id,
        session_id=session_id,
    )
