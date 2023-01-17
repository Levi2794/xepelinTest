class BaseException(Exception):
    def __init__(self, message=None, original_exception=None):
        self.message = message
        self.original_exception = original_exception

    def __str__(self) -> str:
        message = f"{self.__class__.__name__} has been raised"

        if self.message:
            message += f": {self.message}"

        if self.original_exception:
            message += f"\nOriginal Exception -- {self.original_exception.__class__.__name__}: {self.original_exception.__str__()}"

        return message
