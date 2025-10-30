class NotEnoughQuizItemsError(Exception):
    def __init__(self, quiz_id: str, user_id: str, cost: int, stored: int):
        self.quiz_id = quiz_id
        self.user_id = user_id
        self.cost = cost
        self.stored = stored
        super().__init__(f"Not enough quiz items for quiz {quiz_id} by user {user_id}")
