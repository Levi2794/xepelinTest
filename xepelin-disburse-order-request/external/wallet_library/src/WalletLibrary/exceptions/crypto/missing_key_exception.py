class MissingKeyException(BaseException):
    def __init__(self, type):
        super().__init__(f"{type.capitalize()} key not provided")
