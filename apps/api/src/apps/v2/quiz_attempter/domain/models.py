from dataclasses import dataclass, field

from src.lib.utils import genID


@dataclass(slots=True, kw_only=True)
class Feedback:
    overview: str = field(default="")
    problem_topics: list[str] = field(default_factory=list)
    uncovered_topics: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Choice:
    idx: int
    correct: bool
    item_id: str


@dataclass(slots=True, kw_only=True)
class Attempt:
    feedback: Feedback | None = None
    id: str = field(default_factory=genID)
    choices: list[Choice] = field(default_factory=list)
    quiz_id: str
    user_id: str

    @classmethod
    def create(cls, quiz_id: str, user_id: str):
        return cls(
            quiz_id=quiz_id,
            user_id=user_id,
        )
