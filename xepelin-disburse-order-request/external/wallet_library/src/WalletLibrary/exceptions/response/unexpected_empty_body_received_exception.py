class UnexpectedEmptyBodyReceivedException(BaseException):
    def __init__(self):
        super().__init__("Unexpected empty body received from Wallet (after decryption)")