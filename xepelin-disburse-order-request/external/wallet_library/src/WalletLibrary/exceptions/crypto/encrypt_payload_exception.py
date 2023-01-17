class EncryptPayloadException(BaseException):
    def __init__(self, original_exception):
        super().__init__("Payload could not be encrypted", original_exception)
