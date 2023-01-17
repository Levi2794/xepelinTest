class MissingPrivateKeyPassphraseException(BaseException):
    def __init__(self):
        super().__init__("Passphrase for private key not provided")
