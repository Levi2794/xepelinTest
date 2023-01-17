class RequestException(BaseException):
    def __init__(self, original_exception):
        super().__init__("Request to Wallet failed", original_exception)