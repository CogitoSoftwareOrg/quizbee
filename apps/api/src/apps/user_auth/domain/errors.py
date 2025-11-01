class NoTokenError(Exception):
    def __init__(self, message="Authentication token missing or invalid."):
        self.message = message
        super().__init__(self.message)


class ForbiddenError(Exception):
    def __init__(self, message="Forbidden"):
        self.message = message
        super().__init__(self.message)
