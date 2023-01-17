class InvalidIdentifierException(BaseException):
    def __init__(self, identifier):
        super().__init__(f"Invalid identifier: '{identifier}'")
