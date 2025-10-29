from dataclasses import dataclass, field

from src.lib.utils import genID

from .refs import MessageRef, QuizRef, Choice


@dataclass(slots=True, kw_only=True)
class Feedback:
    overview: str = field(default="")
    problem_topics: list[str] = field(default_factory=list)
    uncovered_topics: list[str] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Attempt:
    id: str = field(default_factory=genID)
    user_id: str
    message_history: list[MessageRef] = field(default_factory=list)
    feedback: Feedback | None = None
    quiz: QuizRef
    choices: list[Choice] = field(default_factory=list)

    @classmethod
    def create(cls, quiz: QuizRef, user_id: str):
        return cls(
            quiz=quiz,
            user_id=user_id,
        )

    def get_item(self, item_id: str):
        for item in self.quiz.items:
            if item == item_id:
                return item
        raise ValueError(f"Item {item_id} not found")
