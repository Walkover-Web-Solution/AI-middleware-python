
class BadRequestException(Exception):
    def __init__(self, message="Bad request"):
        """Initialise the exception with a default message."""
        super().__init__(message)
