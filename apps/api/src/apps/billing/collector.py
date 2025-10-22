from pydantic_ai.usage import RunUsage


# from api.config import LLMS


class UsageCollector:
    def __init__(self):
        self._usages: dict[str, RunUsage] = {}
        for model in ("gemini", "gpt-4o-mini", "claude-3-opus-20240229"):
            self._usages[model] = RunUsage()

    @property
    def usages(self) -> dict[str, RunUsage]:
        return self._usages

    def add(self, model: str, usage: RunUsage):
        self._usages[model].input_tokens += usage.input_tokens
        self._usages[model].output_tokens += usage.output_tokens
        self._usages[model].cache_read_tokens += usage.cache_read_tokens
