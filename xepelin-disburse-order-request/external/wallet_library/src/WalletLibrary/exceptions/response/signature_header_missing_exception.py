class SignatureHeaderMissingException(BaseException):
    def __init__(self):
        super().__init__("Missing signature header in response from Wallet")
    