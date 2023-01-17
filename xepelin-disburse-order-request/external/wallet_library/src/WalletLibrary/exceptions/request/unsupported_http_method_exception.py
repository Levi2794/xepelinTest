class UnsupportedHttpMethodException(BaseException):
    def __init__(self, method):
        super().__init__(f"Unsupported HTTP method: {method}")
