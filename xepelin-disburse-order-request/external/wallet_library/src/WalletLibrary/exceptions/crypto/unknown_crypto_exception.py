class UnknownCryptoException(BaseException):
    """Exception raised when an unknown crypto error occurs.

    Attributes:
        message -- explanation of the error
        original_exception -- the original exception, if any
    """

    def __init__(self, original_exception=None):
        super().__init__("Unknown crypto exception was raised", original_exception)
