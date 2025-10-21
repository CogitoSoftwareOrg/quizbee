from typing import Any
from langfuse import LangfuseSpan
from pydantic_ai.result import StreamedRunResult


from lib.config.llms import LLMCosts


async def update_span_with_result(
    result: StreamedRunResult | Any,
    span: LangfuseSpan,
    user_id: str,
    session_id: str,
    # costs: LLMCosts,
):
    output = await result.get_output()

    usage = result.usage()
    input_nc = usage.input_tokens - usage.cache_read_tokens
    input_cah = usage.cache_read_tokens
    outp = usage.output_tokens

    # input_nc_price = round(input_nc * costs.input_nc, 4)
    # input_cah_price = round(input_cah * costs.input_cah, 4)
    # outp_price = round(outp * costs.output, 4)

    span.update(
        usage_details={
            "input": input_nc,
            "input_cache_read": input_cah,
            "output_tokens": outp,
        }
    )
    span.update_trace(
        input="DIMA PRIVET! :3",
        output=output,
        user_id=user_id,
        session_id=session_id,
    )
