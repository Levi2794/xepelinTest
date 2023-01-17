class BadJsonReceivedException(BaseException):
    def __init__(self, before_encryption, original_exception):
        if before_encryption:
            suffix = " (before decryption)"
        else:
            suffix = " (after decryption)"

        super().__init__(
            f"Bad JSON response from Wallet{suffix}", original_exception)
