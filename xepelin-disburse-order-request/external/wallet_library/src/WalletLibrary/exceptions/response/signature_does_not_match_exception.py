class SignatureDoesNotMatchException(BaseException):
    def __init__(self):
        super().__init__("Signature does not match the string provided, possible data tampering.")
