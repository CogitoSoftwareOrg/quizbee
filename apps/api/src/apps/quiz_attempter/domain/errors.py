class NotAttemptOwnerError(Exception):
    def __init__(self, attempt_id: str, user_id: str, quiz_id: str):
        self.attempt_id = attempt_id
        self.user_id = user_id
        self.quiz_id = quiz_id
        super().__init__(
            f"Attempt {attempt_id} is not owned by user {user_id} for quiz {quiz_id}"
        )


class AttemptAlreadyFinalizedError(Exception):
    def __init__(self, attempt_id: str, user_id: str, quiz_id: str):
        self.attempt_id = attempt_id
        self.user_id = user_id
        self.quiz_id = quiz_id
        super().__init__(
            f"Attempt {attempt_id} has already been finalized for quiz {quiz_id} and user {user_id}"
        )
