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
            if item.id == item_id:
                return item
        raise ValueError(f"Item {item_id} not found")

    def set_history(self, history: list[MessageRef]):
        self.message_history = history

    def set_feedback(self, feedback: Feedback):
        self.feedback = feedback

    def quiz_content(self) -> str:
        return "\n".join(
            [
                f"{i+1}. {qi.question}: {qi.answers}"
                for i, qi in enumerate(self.quiz.items)
            ]
        )

    def correct_items_content(self) -> str:
        content = "CORRECT ANSWERS:\n"
        for qi in self.quiz.items:
            if qi.choice and qi.choice.correct:
                content += f"{qi.question}\n"
        return content

    def wrong_items_content(self) -> str:
        content = "WRONG ANSWERS:\n"
        for qi in self.quiz.items:
            if qi.choice and not qi.choice.correct:
                content += f"{qi.question}\n"
        return content
