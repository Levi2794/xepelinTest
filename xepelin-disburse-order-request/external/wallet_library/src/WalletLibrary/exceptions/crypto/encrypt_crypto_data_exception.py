class EncryptCryptoDataException(BaseException):
    def __init__(self, original_exception):
        super().__init__("", original_exception)
