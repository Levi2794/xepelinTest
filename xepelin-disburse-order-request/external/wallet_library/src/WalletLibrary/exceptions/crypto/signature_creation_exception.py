class SignatureCreationException(BaseException):
    def __init__(self, original_exception):
        super().__init__("Signature could not be created", original_exception)
