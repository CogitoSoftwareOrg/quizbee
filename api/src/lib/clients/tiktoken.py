import tiktoken

from lib.config import LLMS

ENCODERS = {
    llm: tiktoken.encoding_for_model(llm.split(":")[-1])
    for llm in LLMS
    if "openai" in llm and llm != LLMS.GPT_5
}
