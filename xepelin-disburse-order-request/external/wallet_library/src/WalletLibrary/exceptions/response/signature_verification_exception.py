class SignatureVerificationException(BaseException):
    def __init__(self, original_exception: Exception):
        super().__init__("Signature could not be verified", original_exception)
