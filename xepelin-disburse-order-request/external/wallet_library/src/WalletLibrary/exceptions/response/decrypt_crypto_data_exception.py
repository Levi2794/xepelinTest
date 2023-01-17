class DecryptCryptoDataException(BaseException):
    def __init__(self, original_exception):
        super().__init__("Crypto data could not be decrypted", original_exception)
