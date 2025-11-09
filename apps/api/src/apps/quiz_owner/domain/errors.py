class InvalidQuiz(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotQuizOwnerError(Exception):
    def __init__(self, quiz_id: str, user_id: str):
        self.quiz_id = quiz_id
        self.user_id = user_id
        super().__init__(f"Quiz {quiz_id} is not owned by user {user_id}")


class NotEnoughQuizItemsError(Exception):
    def __init__(self, quiz_id: str, user_id: str, cost: int, stored: int):
        self.quiz_id = quiz_id
        self.user_id = user_id
        self.cost = cost
        self.stored = stored
        super().__init__(f"Quota exceeded for quiz {quiz_id} by user {user_id}")


class QuizNotAnsweredError(Exception):
    def __init__(self, quiz_id: str):
        self.quiz_id = quiz_id
        super().__init__(f"Quiz {quiz_id} is not in answered status")
