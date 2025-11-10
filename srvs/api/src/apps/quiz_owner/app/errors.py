class NoItemsReadyForGenerationError(Exception):
    def __init__(self, quiz_id: str):
        self.quiz_id = quiz_id
        super().__init__(f"No items ready for generation in quiz {quiz_id}")
