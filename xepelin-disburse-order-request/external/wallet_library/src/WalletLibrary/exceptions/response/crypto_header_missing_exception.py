class CryptoHeaderMissingException(BaseException):
    def __init__(self):
        super().__init__("Missing crypto header in response from Wallet")
    