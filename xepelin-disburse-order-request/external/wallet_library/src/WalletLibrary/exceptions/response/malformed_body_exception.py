class MalformedBodyException(BaseException):
    def __init__(self, original_exception):
        super().__init__("Body received from Wallet does not have the expected format",
                         original_exception)
