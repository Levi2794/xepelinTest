class LoadKeyException(BaseException):
    def __init__(self, type, original_exception):
        super().__init__(f"Error loading {type} RSA key", original_exception)
