class OrderAlreadyExists(Exception):
    def __init__(self, message=None, original_exception=None):
        self.message = message
        self.original_exception = original_exception
